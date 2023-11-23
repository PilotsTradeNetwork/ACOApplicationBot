from typing import List

import discord
from discord import app_commands
from discord.ext import commands

from ptn.aco.constants import bot_guild_id
from ptn.aco.modules.ErrorHandler import CommandRoleError


class Helper(commands.Cog):
    """
    This class is a collection of helper commands for the booze bot
    """

    @app_commands.command(name='affiliiate_bot_help', description='Returns some information for each command.')
    async def get_help(self, interaction: discord.Interaction, command: str):
        """
        Returns a help context message privately to the user.

        :param interaction:
        :param command:
        :returns: None
        """
        print(f'User {interaction.user} has requested help for command: {command}')
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
            return await interaction.response.send_message(f'Unknown handling for command: {command}.')

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

        print(f"Returning the response to: {interaction.user}")
        await interaction.response.send_message(embed=response_embed, hidden=True)

    @get_help.autocomplete('command')
    async def get_help_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        choices = ['scan_aco_applications', 'find_user', 'grant_affiliate_status']
        return [
            app_commands.Choice(name=choice, value=choice) for choice in choices if current.lower() in choice.lower()
        ]


# trio of helper functions to check a user's permission to run a command based on their roles, and return a helpful
# error if they don't have the correct role(s)
def getrole(ctx, id):  # takes a Discord role ID and returns the role object
    role = discord.utils.get(ctx.guild.roles, id=id)
    return role


async def checkroles_actual(interaction: discord.Interaction, permitted_role_ids):
    try:
        """
        Check if the user has at least one of the permitted roles to run a command
        """
        print(f"checkroles called.")
        author_roles = interaction.user.roles
        permitted_roles = [getrole(interaction, role) for role in permitted_role_ids]
        print(author_roles)
        print(permitted_roles)
        permission = True if any(x in permitted_roles for x in author_roles) else False
        print(f'Permission: {permission}')
        return permission, permitted_roles
    except Exception as e:
        print(e)
    return permission


def check_roles(permitted_role_ids):
    async def checkroles(interaction: discord.Interaction):
        permission, permitted_roles = await checkroles_actual(interaction, permitted_role_ids)
        print("Inherited permission from checkroles")
        if not permission:  # raise our custom error to notify the user gracefully
            role_list = []
            for role in permitted_role_ids:
                role_list.append(f'<@&{role}> ')
                formatted_role_list = " • ".join(role_list)
            try:
                raise CommandRoleError(permitted_roles, formatted_role_list)
            except CommandRoleError as e:
                print(e)
                raise
        return permission

    return app_commands.check(checkroles)
