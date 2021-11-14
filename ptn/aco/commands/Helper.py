import discord
from discord.ext import commands
from discord_slash import SlashContext, cog_ext
from discord_slash.utils.manage_commands import create_option, create_choice

from ptn.aco.constants import bot_guild_id


class Helper(commands.Cog):

    """
    This class is a collection of helper commands for the booze bot
    """

    @cog_ext.cog_slash(
        name='affiliiate_bot_help',
        guild_ids=[bot_guild_id()],
        description='Returns some information for each command.',
        options=[
            create_option(
                name='command',
                description='The command you want help with',
                option_type=3,
                required=True,
                choices=[
                    create_choice(
                        name='scan_aco_applications',
                        value='scan_aco_applications'
                    ),
                    create_choice(
                        name='find_user',
                        value='find_user'
                    ),
                    create_choice(
                        name='grant_affiliate_status',
                        value='grant_affiliate_status'
                    ),
                ]
            ),
        ]
    )
    async def get_help(self, ctx: SlashContext, command: str):
        """
        Returns a help context message privately to the user.

        :param ctx:
        :param command:
        :returns: None
        """
        print(f'User {ctx.author} has requested help for command: {command}')
        # For each value we just populate some data.
        if command == 'grant_affiliate_status':
            params = [
                {
                    'name': 'user',
                    'type': 'string',
                    'description': 'The user to grant the role too.'
                }
            ]
            method_desc = 'Grants or removes the ACO role to the provided user'
            roles = ['Admin', 'Mod']
        elif command == 'scan_aco_applications':
            params = None
            method_desc = 'Starts a manual scan for new applications. Triggers automatically every 24 hours.'
            roles = ['Admin', 'Mod']
        elif command == 'find_user':
            params = [
                {
                    'name': 'user',
                    'type': 'string',
                    'description': 'The user to look for. Case sensitive matching.'
                }
            ]
            method_desc = 'Searches the roles for a user'
            roles = ['Admin', 'Mod']
        else:
            print('User did not provide a valid command.')
            return await ctx.send(f'Unknown handling for command: {command}.')

        response_embed = discord.Embed(
            title=f'ACO Bot knows the following for: {command}.',
            description=f'**Description**: {method_desc}\n'
                        f'**Required Roles**: {", ".join(roles)}.\n'
                        f'**Params**: '
        )

        # Go build some fields for each param and log the information into it
        if params:
            for param in params:
                response_embed.add_field(
                    name=f'• {param["name"]}:',
                    value=f'- Description: {param["description"]}.\n'
                          f'- Type: {param["type"]}.',
                    inline=False
                )
        else:
            # In the case of no params, just append None to the description.
            response_embed.description += 'None.'

        print(f"Returning the response to: {ctx.author}")
        await ctx.send(embed=response_embed, hidden=True)
