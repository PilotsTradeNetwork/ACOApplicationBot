"""
ErrorHandler.py

Our custom global error handler for the bot. v1 is directly imported from MAB

Dependends on: constants
"""

# import discord.py
import discord
from discord import Interaction, app_commands
from discord.app_commands import AppCommandError

# import local constants
import ptn.aco.constants as constants


# custom errors
class CommandChannelError(app_commands.CheckFailure):  # channel check error
    def __init__(self, permitted_channel, formatted_channel_list):
        self.permitted_channel = permitted_channel
        self.formatted_channel_list = formatted_channel_list
        super().__init__(permitted_channel, formatted_channel_list, "Channel check error raised")

    pass


class CommandRoleError(app_commands.CheckFailure):  # role check error
    def __init__(self, permitted_roles, formatted_role_list):
        self.permitted_roles = permitted_roles
        self.formatted_role_list = formatted_role_list
        super().__init__(permitted_roles, formatted_role_list, "Role check error raised")

    pass


class CommandPermissionError(app_commands.CheckFailure):  # channel send permission failure
    pass


class GenericError(Exception):  # generic error
    pass


class BadRequestError(Exception):  # 400 Bad Request from HTTPException
    def __init__(self, exception):
        print("Received BadRequestError def init")

    pass


class CustomError(Exception):  # an error handler that hides the Exception text from the user, but shows custom text
    # sent from the source instead
    def __init__(self, message, isprivate=True):
        self.message = message
        self.isprivate = isprivate
        super().__init__(self.message, "CustomError raised")


"""
A primitive global error handler for all app commands (slash & ctx menus)

returns: the error message to the user and log
"""


async def on_generic_error(
        spamchannel,
        interaction: Interaction,
        error
):  # an error handler for our custom errors
    try:  # this outputs the error to bot-spam for logging purposes
        spam_embed = discord.Embed(
            description=f"Error from `{interaction.command.name}` in <#{interaction.channel.id}> called by <@{interaction.user.id}>: ```{error}```",
            color=constants.EMBED_COLOUR_ERROR
        )
        await spamchannel.send(embed=spam_embed)
    except Exception as e:
        print(e)
        try:
            spam_embed = discord.Embed(
                description=f"Error from `{interaction}` in <#{interaction.channel.id}> called by <@{interaction.user.id}>: ```{error}```",
                color=constants.EMBED_COLOUR_ERROR
            )
            await spamchannel.send(embed=spam_embed)
        except Exception as e:
            print(e)

    if isinstance(error, BadRequestError):  # 400 Bad Request from HTTPException
        print(f"Received HTTPException: {error}")

        if "emoji" in str(error):  # emoji is invalid
            print("Error caused by invalid emoji")
            message = '**Emoji Error**\n\nSorry, the emoji you chose is not recognised by Discord as a valid emoji.\n\n' \
                      'Some emojis are based on complex ZWJ sequences and may not be fully supported by all platforms.\n\n' \
                      'You can try picking your desired emoji from Discord\'s (non-custom) emoji selector, sending it in a message, and copying the result.'
        elif "custom id" in str(error):  # duplicate custom id
            print("Error caused by duplicate custom id")
            message = 'This message already appears to have a button associated with that role.'
        else:  # dunno lol
            message = error

        embed = discord.Embed(
            description=f"❌ {message}",
            color=constants.EMBED_COLOUR_ERROR
        )
        try:
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except:
            await interaction.followup.send(embed=embed, ephemeral=True)

    if isinstance(error,
                  GenericError):  # Our bog-standard "hey, an error!" response. Just displays the raw error text to the user without explanation
        print(f"Generic error raised: {error}")
        embed = discord.Embed(
            description=f"❌ {error}",
            color=constants.EMBED_COLOUR_ERROR
        )
        try:
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except:
            await interaction.followup.send(embed=embed, ephemeral=True)

    elif isinstance(error,
                    CustomError):  # this class receives custom error messages and displays either privately or publicly
        message = error.message
        isprivate = error.isprivate
        print(f"Raised CustomError from {error} with message {message}")
        embed = discord.Embed(
            description=f"❌ {message}",
            color=constants.EMBED_COLOUR_ERROR
        )
        if isprivate:  # message should be ephemeral
            try:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            except:
                await interaction.followup.send(embed=embed, ephemeral=True)
        else:  # message should be public
            try:
                await interaction.response.send_message(embed=embed)
            except:
                await interaction.followup.send(embed=embed)

    else:
        print(f"Error {error} was not caught by on_generic_error")


async def on_app_command_error(
        interaction: Interaction,
        error: AppCommandError
):  # an error handler for discord.py errors
    print(
        f"Error from {interaction.command.name} in {interaction.channel.name} called by {interaction.user.display_name}: {error}")

    try:
        if isinstance(error, CommandChannelError):
            print("Channel check error raised")
            formatted_channel_list = error.formatted_channel_list

            embed = discord.Embed(
                description=f"Sorry, you can only run this command out of: {formatted_channel_list}",
                color=constants.EMBED_COLOUR_ERROR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        elif isinstance(error, CommandRoleError):
            print("Role check error raised")
            permitted_roles = error.permitted_roles
            formatted_role_list = error.formatted_role_list
            if len(permitted_roles) > 1:
                embed = discord.Embed(
                    description=f"**Permission denied**: You need one of the following roles to use this command:\n{formatted_role_list}",
                    color=constants.EMBED_COLOUR_ERROR
                )
            else:
                embed = discord.Embed(
                    description=f"**Permission denied**: You need the following role to use this command:\n{formatted_role_list}",
                    color=constants.EMBED_COLOUR_ERROR
                )
            print("notify user")
            await interaction.response.send_message(embed=embed, ephemeral=True)

        elif isinstance(error, CommandPermissionError):
            embed = discord.Embed(
                description="❌ You need permission to send messages in this channel to use this command.",
                color=constants.EMBED_COLOUR_ERROR
            )
            try:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            except:
                await interaction.followup.send(embed=embed, ephemeral=True)

        elif isinstance(error, CustomError):
            message = error.message
            isprivate = error.isprivate
            print(f"Raised CustomError from {error} with message {message}")
            embed = discord.Embed(
                description=f"❌ {message}",
                color=constants.EMBED_COLOUR_ERROR
            )
            if isprivate:  # message should be ephemeral
                try:
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                except:
                    await interaction.followup.send(embed=embed, ephemeral=True)
            else:  # message should be public - use for CCO commands
                try:
                    await interaction.response.send_message(embed=embed)
                except:
                    await interaction.followup.send(embed=embed)

        elif isinstance(error, GenericError):
            print(f"Generic error raised: {error}")
            embed = discord.Embed(
                description=f"❌ {error}",
                color=constants.EMBED_COLOUR_ERROR
            )
            try:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            except:
                await interaction.followup.send(embed=embed, ephemeral=True)

        else:
            print("Othertype error message raised")
            embed = discord.Embed(
                description=f"❌ Unhandled Error: {error}",
                color=constants.EMBED_COLOUR_ERROR
            )
            try:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            except:
                await interaction.followup.send(embed=embed, ephemeral=True)

    except Exception as e:
        print(f"An error occurred in the error handler (lol): {e}")
