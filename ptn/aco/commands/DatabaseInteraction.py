import traceback
from datetime import datetime
import os.path

import discord
from discord import NotFound, HTTPException
from discord.ext import tasks, commands
from discord_slash import cog_ext, SlashContext
from discord_slash.model import SlashCommandPermissionType
from discord_slash.utils.manage_commands import create_permission, create_option
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from discord.ext.commands import Cog

from ptn.aco.UserData import UserData
from ptn.aco.constants import bot_guild_id, server_admin_role_id, server_mod_role_id, bot, get_bot_notification_channel, \
    get_server_aco_role_id
from ptn.aco.database.database import affiliator_db, affiliator_conn, dump_database, affiliator_lock


class InvalidUser(Exception):
    pass


class DatabaseInteraction(Cog):

    @commands.Cog.listener()
    async def on_ready(self):
        print('Starting the polling task')
        await self.timed_scan.start()

    @tasks.loop(minutes=5)
    async def timed_scan(self):
        print(f'Automatic database polling started at {datetime.now()}')
        self.running_scan = True
        await self._update_db()
        self.running_scan = False
        print('Automatic database scan completed, next scan in 2 hours')

    @timed_scan.after_loop
    async def timed_scan_after_loop(self):
        self.running_scan = False
        if self.timed_scan.failed():
            print("timed_scan after_loop().Task has failed.")

    @timed_scan.error
    async def timed_scan_error(self, error):
        self.running_scan = False
        if not self.timed_scan.is_running() or self.timed_scan.failed():
            print("timed_scan error(). task has failed.")
        print(error)
        traceback.print_exc()

    def __init__(self):
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

        if not os.path.join(os.path.expanduser('~'), '.ptnuserdata.json'):
            raise EnvironmentError('Cannot find the user data json file.')

        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            os.path.join(os.path.expanduser('~'), '.ptnuserdata.json'), scope)

        # authorize the client sheet
        self.client = gspread.authorize(credentials)

        affiliator_db.execute(
            "SELECT * FROM trackingforms"
        )
        forms = dict(affiliator_db.fetchone())

        self.worksheet_key = forms['worksheet_key']

        # On which sheet is the actual data.
        self.worksheet_with_data_id = forms['worksheet_with_data_id']

        print(f'Building worksheet with the key: {self.worksheet_key}')
        self.running_scan = False
        try:
            workbook = self.client.open_by_key(self.worksheet_key)
            print(workbook)
            print(len(workbook.worksheets()))
            self.tracking_sheet = workbook.get_worksheet(self.worksheet_with_data_id)
        except gspread.exceptions.APIError as e:
            print(f'Error reading the worksheet: {e}')

    @cog_ext.cog_slash(
        name='find_user',
        guild_ids=[bot_guild_id()],
        description='Debug command to help figure out when we cannot find a users membership details',
        permissions={
            bot_guild_id(): [
                create_permission(server_admin_role_id(), SlashCommandPermissionType.ROLE, True),
                create_permission(server_mod_role_id(), SlashCommandPermissionType.ROLE, True),
                create_permission(bot_guild_id(), SlashCommandPermissionType.ROLE, False),
            ]
        },
    )
    async def find_user_test(self, ctx: SlashContext, member: str):
        print(f'Looking for: {member}')
        bot_guild = bot.get_guild(bot_guild_id())
        dc_user = bot_guild.get_member_named(member)
        print(f'Result: {dc_user}')
        return await ctx.send(f'User {dc_user.name} has roles: {dc_user.roles}')

    @cog_ext.cog_slash(
        name="scan_aco_applications",
        guild_ids=[bot_guild_id()],
        description="Populates the ACO database from the updated google sheet. Admin/Mod role required.",
        permissions={
            bot_guild_id(): [
                create_permission(server_admin_role_id(), SlashCommandPermissionType.ROLE, True),
                create_permission(server_mod_role_id(), SlashCommandPermissionType.ROLE, True),
                create_permission(bot_guild_id(), SlashCommandPermissionType.ROLE, False),
            ]
        },
    )
    async def user_update_database_from_googlesheets(self, ctx: SlashContext):
        """
        Slash command for updating the database from the GoogleSheet.

        :returns: A discord embed to the user.
        :rtype: None
        """
        print(f'User {ctx.author} requested to re-populate the database at {datetime.now()}')
        if self.running_scan:
            return await ctx.send('DB scan is already in progress.')

        try:
            result = await self._update_db()
            msg = 'Check the ACO application channel for new applications' if result['added_count'] > 0 \
                else 'No new applications found'
            embed = discord.Embed(title="ACO DB Update ran successfully.")
            embed.add_field(name='Scan completed', value=msg, inline=False)

            return await ctx.send(embed=embed)

        except ValueError as ex:
            return await ctx.send(str(ex))

    @tasks.loop(minutes=3)
    async def _update_db(self):
        """
        Private method to wrap the DB update commands.

        :returns:
        :rtype:
        """
        if not self.tracking_sheet:
            raise EnvironmentError('Sorry this cannot be ran as we have no form for tracking ACOs presently. '
                                   'Please set a new form first.')

        updated_db = False
        added_count = 0
        embed_list = []  #: [discord.Embed]

        # A JSON form tracking all the records
        records_data = self.tracking_sheet.get_all_records()

        total_users = len(records_data)
        print(f'Updating the database we have: {total_users} records in the tracking form.')
        bot_guild = bot.get_guild(bot_guild_id())

        # First row is the headers, drop them.
        for record in records_data:
            print(record)
            # Iterate over the records and populate the database as required.

            # Check if it is in the database already
            affiliator_db.execute(
                "SELECT * FROM acoapplications WHERE fleet_carrier_id LIKE (?)", (f'%{record["Carrier ID"].upper()}%',)
            )
            userdata = [UserData(user) for user in affiliator_db.fetchall()]
            if len(userdata) > 1:
                raise ValueError(f'{len(userdata)} users are listed with this carrier ID:'
                                 f' {record["Carrier ID"].upper()}. Problem in the DB!')

            if userdata:
                # We have a user object, just check the values and update it if needed.
                print(f'The user for {record["Carrier ID"].upper()} exists, no notification required')

            else:
                added_count += 1
                user = UserData(record)
                print(user.to_dictionary())
                print(f'Application for "{record["Carrier Name"]}" is not yet in the database - adding it')

                # TODO: We could track in DB the member role when it is added, as a reference point and use that
                #  here? Probably overkill?
                try:
                    affiliator_lock.acquire()
                    affiliator_db.execute(''' 
                    INSERT INTO acoapplications VALUES(NULL, ?, ?, ?, ?, ?, ?, ?, ?) 
                    ''', (
                        user.discord_username, user.ptn_nickname, user.cmdr_name,
                        user.fleet_carrier_name, user.fleet_carrier_id, user.ack,
                        user.user_claims_member, user.timestamp
                        )
                    )
                finally:
                    affiliator_lock.release()

                try:
                    dc_user = bot_guild.get_member_named(user.discord_username)
                    if not dc_user:
                        print(f'Invalid user for: {user.discord_username}')
                        raise InvalidUser(f'Invalid user for: {user.discord_username}')

                    print(f'USER: {dir(dc_user)}')
                    print(type(dc_user))
                    member_role = discord.utils.find(lambda r: r.name == 'Member', bot_guild.roles)
                    print(member_role)
                    member = member_role in dc_user.roles
                except (InvalidUser, NotFound, HTTPException) as ex:
                    print(f'Unable to member status for user {user.discord_username}: {ex}')
                    member = 'Unclear'

                embed = discord.Embed(
                    title='New ACO application detected.',
                    description=f'**User:** {user.ptn_nickname} \n'
                                f'**Discord Username:** {user.discord_username}\n'
                                f'**Cmdr Name:** {user.cmdr_name}\n'
                                f'**Fleet Carrier:** {user.fleet_carrier_name} ({user.fleet_carrier_id})\n'
                                f'**Has member role:** {member}.\n'
                                f'**Applied At:** {user.timestamp}'
                )
                embed.set_footer(text='Please validate membership and vote on this proposal')
                embed_list.append(embed)
                updated_db = True
                print('Added ACO application to the database')

        if updated_db:
            # Write the database and then dump the updated SQL
            try:
                affiliator_lock.acquire()
                affiliator_conn.commit()
            finally:
                affiliator_lock.release()
            dump_database()
            print('Wrote the database and dumped the SQL')

            # Send all the notifications now
            notification_channel = bot.get_channel(get_bot_notification_channel())

            await notification_channel.send(f'Priority transmission {len(embed_list)} application'
                                            f'{"s" if len(embed_list) > 1 else ""} incoming.')

            for entry in embed_list:
                message = await notification_channel.send(embed=entry)
                await message.add_reaction('👍')
                await message.add_reaction('👎')

        return {
            'updated_db': updated_db,
            'added_count': added_count,
        }

    @cog_ext.cog_slash(
        name='grant_affiliate_status',
        guild_ids=[bot_guild_id()],
        description='Toggle user\'s ACO role. Admin/Mod role required.',
        options=[
            create_option(
                name='user',
                description='An @ mention of the Discord user to receive/remove the role.',
                option_type=6,  # user
                required=True
            )
        ],
        permissions={
            bot_guild_id(): [
                create_permission(server_admin_role_id(), SlashCommandPermissionType.ROLE, True),
                create_permission(server_mod_role_id(), SlashCommandPermissionType.ROLE, True),
                create_permission(bot_guild_id(), SlashCommandPermissionType.ROLE, False),
            ]
        },
    )
    async def toggle_aco_role(self, ctx: SlashContext, user: discord.Member):
        print(f"toggle_aco_role called by {ctx.author} in {ctx.channel} for {user}")
        # set the target role
        print(f"ACO role ID is {get_server_aco_role_id()}")
        role = discord.utils.get(ctx.guild.roles, id=get_server_aco_role_id())
        print(f"ACO role name is {role.name}")

        if role in user.roles:
            # toggle off
            print(f"{user} is already an ACO, removing the role.")
            try:
                await user.remove_roles(role)
                response = f"{user.display_name} no longer has the ACO role."
                return await ctx.send(content=response)
            except Exception as e:
                print(e)
                await ctx.send(f"Failed removing role from {user}: {e}")
        else:
            # toggle on
            print(f"{user} is not an ACO, adding the role.")
            try:
                await user.add_roles(role)
                print(f"Added ACO role to {user}")
                response = f"{user.display_name} now has the ACO role."
                return await ctx.send(content=response)
            except Exception as e:
                print(e)
                await ctx.send(f"Failed adding role to {user}: {e}")
