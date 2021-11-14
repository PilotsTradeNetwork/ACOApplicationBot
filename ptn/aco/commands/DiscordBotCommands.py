import datetime
import os
import sys

import discord
from discord.ext import commands
from discord_slash.utils.manage_commands import remove_all_commands

from ptn.aco.constants import bot_guild_id, TOKEN, get_bot_control_channel, get_member_role_id, bot
from ptn.aco._metadata import __version__
from ptn.aco.database.database import affiliator_db, affiliator_lock, affiliator_conn


class DiscordBotCommands(commands.Cog):
    def __init__(self, bot):
        """
        This class is a collection of generic blocks used throughout the booze bot.

        :param discord.ext.commands.Bot bot: The discord bot object
        """
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """
        We create a listener for the connection event.

        :returns: None
        """
        print(f'{self.bot.user.name} has connected to Discord server version: {__version__}')
        bot_channel = self.bot.get_channel(get_bot_control_channel())
        await bot_channel.send(f'{self.bot.user.name} has connected to Discord server Booze bot version: {__version__}')

    @commands.Cog.listener()
    async def on_disconnect(self):
        print(f'Booze bot has disconnected from discord server, version: {__version__}.')

    @commands.command(name='ping', help='Ping the bot')
    @commands.has_role('Admin')
    async def ping(self, ctx):
        """
        Ping the bot and get a response

        :param discord.Context ctx: The Discord context object
        :returns: None
        """
        await ctx.send(f"**Avast Ye Landlubber! {self.bot.user.name} is here!**")

    # quit the bot
    @commands.command(name='exit', help="Stops the bots process on the VM, ending all functions.")
    @commands.has_role('Admin')
    async def exit(self, ctx):
        """
        Stop-quit command for the bot.

        :param discord.ext.commands.Context ctx: The Discord context object
        :returns: None
        """
        print(f'User {ctx.author} requested to exit')
        await remove_all_commands(self.bot.user.id, TOKEN, [bot_guild_id()])
        await ctx.send(f"Ahoy! k thx bye")
        await sys.exit("User requested exit.")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """
        A listener that fires off on a particular error case.

        :param discord.ext.commands.Context ctx: The discord context object
        :param discord.ext.commands.errors error: The error object
        :returns: None
        """
        if isinstance(error, commands.BadArgument):
            await ctx.send('**Bad argument!**')
        elif isinstance(error, commands.CommandNotFound):
            await ctx.send("**Invalid command.**")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('**Please include all required parameters.** Use b.help <command> for details.')
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send('**You must be a Carrier Owner to use this command.**')
        else:
            await ctx.send(f"Sorry, that didn't work. Check your syntax and permissions, error: {error}")

    @commands.command(name='update', help="Restarts the bot.")
    @commands.has_role('Admin')
    async def update(self, ctx):
        """
        Restarts the application for updates to take affect on the local system.
        """
        print(f'Restarting the application to perform updates requested by {ctx.author}')
        os.execv(sys.executable, ['python'] + sys.argv)

    @commands.command(name='version', help="Logs the bot version")
    @commands.has_role('Admin')
    async def version(self, ctx):
        """
        Logs the bot version

        :param discord.ext.commands.Context ctx: The Discord context object
        :returns: None
        """
        print(f'User {ctx.author} requested the version: {__version__}.')
        await ctx.send(f"Avast Ye Landlubber! {self.bot.user.name} is on version: {__version__}.")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """
        We create a listener for the member update event.

        :returns: None
        """

        # Check if the user had the member role initially.
        bot_guild = bot.get_guild(bot_guild_id())
        member_role = discord.utils.get(bot_guild.roles, id=get_member_role_id())
        initial = member_role in before.roles
        post = member_role in after.roles

        # Compare them, if they changed we need to do something
        if initial != post:
            change = 'Added' if post else 'Removed'
            print(f'Member role {change} for user: {before}')

            if post:
                # Add the role - add to DB
                affiliator_db.execute(
                    "SELECT * FROM membertracking WHERE discord_username LIKE (?)", (f'%{before}%',)
                )
                user = affiliator_db.fetchone()

                if user:
                    print(f'Some problem - user {before} is already in the tracking DB with the data: {dict(user)}.')
                    return

                try:
                    affiliator_lock.acquire()
                    affiliator_db.execute(
                        '''INSERT INTO membertracking VALUES(NULL, ?, ?)''',
                        (
                            str(before),
                            datetime.datetime.now()
                        )
                    )
                    affiliator_conn.commit()
                finally:
                    affiliator_lock.release()
                    print(f'Member tracking status was added into DB for user: {before} at {datetime.datetime.now()}')
            else:
                # Remove the role - delete from DB if it is there
                affiliator_db.execute(
                    "SELECT * FROM membertracking WHERE discord_username LIKE (?)", (f'%{before}%',)
                )
                user = dict(affiliator_db.fetchone())
                if not user:
                    print(f'User had the member role removed, but was not in the DB: {before}')
                    return

                try:
                    affiliator_lock.acquire()
                    affiliator_db.execute(
                        "DELETE FROM membertracking WHERE discord_username LIKE (?)", (f'%{before.name}%',)
                    )
                    affiliator_conn.commit()
                    print(f'Member tracking status was deleted from DB for user: {before} at {datetime.datetime.now()}')
                finally:
                    affiliator_lock.release()


