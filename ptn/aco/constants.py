# Production variables
import ast
import os

from discord import Intents
from discord.ext import commands
from discord_slash import SlashCommand
from dotenv import load_dotenv, find_dotenv

# Get the discord token from the local .env file. Deliberately not hosted in the repo or Discord takes the bot down
# because the keys are exposed. DO NOT HOST IN THE REPO. Seriously do not do it ...
load_dotenv(find_dotenv(usecwd=True))

PROD_DISCORD_GUILD = 1081339111111131197  # PTN Discord server
PROD_DB_PATH = os.path.join(os.path.expanduser('~'), 'acobot', 'aco_applications.db')
PROD_DB_DUMPS_PATH = os.path.join(os.path.expanduser('~'), 'acobot', 'dumps', 'aco_applications.sql')
PROD_MOD_ID = 1082235385033273414
PROD_ACO_BOT_CHANNEL = 1082235723610071050  # This is #aco-bot
PROD_ACO_NOTIFICATION_BOT_CHANNEL = 1082235661412741150  # This is #mod-aco-applications
PROD_ADMIN_ID = 1082235384072765461
PROD_MEMBER_ID = 1082235414192082954
PROD_ACO_ROLE_ID = 1084672234666332251

# Testing variables
TEST_DISCORD_GUILD = 818174236480897055  # test Discord server
TEST_DB_PATH = os.path.join(os.path.expanduser('~'), 'acobot', 'aco_applications.db')
TEST_DB_DUMPS_PATH = os.path.join(os.path.expanduser('~'), 'acobot', 'dumps', 'aco_applications.sql')
TEST_MOD_ID = 818174400997228545
TEST_ACO_BOT_CHANNEL = 909365393875947520
TEST_ACO_NOTIFICATION_CHANNEL = 909365393875947520
TEST_ADMIN_ID = 818174400997228545
TEST_MEMBER_ID = 903289848427851847
TEST_ACO_ROLE_ID = 903289778680770590

_production = ast.literal_eval(os.environ.get('PTN_ACO_BOT_PRODUCTION', 'False'))

# Check the folder exists
if not os.path.exists(os.path.dirname(PROD_DB_PATH)):
    print(f'Folder {os.path.dirname(PROD_DB_PATH)} does not exist, making it now.')
    os.mkdir(os.path.dirname(PROD_DB_PATH))

# check the dumps folder exists
if not os.path.exists(os.path.dirname(PROD_DB_DUMPS_PATH)):
    print(f'Folder {os.path.dirname(PROD_DB_DUMPS_PATH)} does not exist, making it now.')
    os.mkdir(os.path.dirname(PROD_DB_DUMPS_PATH))


TOKEN = os.getenv('ACO_BOT_DISCORD_TOKEN_PROD') if _production else os.getenv('ACO_BOT_DISCORD_TOKEN_TESTING')

# The bot object:
bot = commands.Bot(command_prefix='a/', intents=Intents.all())
slash = SlashCommand(bot, sync_commands=True)


def get_db_path():
    """
    Returns the database path. For testing we keep the file locally for ease

    :returns: The path to the db file
    :rtype: str
    """
    return PROD_DB_PATH if _production else TEST_DB_PATH


def bot_guild_id():
    """
    Returns the bots guild ID

    :returns: The guild ID value
    :rtype: int
    """
    return PROD_DISCORD_GUILD if _production else TEST_DISCORD_GUILD


def get_db_dumps_path():
    """
    Returns the path for the database dumps file

    :returns: A string representation of the path
    :rtype: str
    """
    return PROD_DB_DUMPS_PATH if _production else TEST_DB_DUMPS_PATH


def server_mod_role_id():
    """
    Returns the moderator role ID for the server

    :return: The role ID
    :rtype: int
    """
    return PROD_MOD_ID if _production else TEST_MOD_ID


def get_bot_control_channel():
    """
    Returns the channel ID for the bot control channel.

    :return: The channel ID
    :rtype: int
    """
    return PROD_ACO_BOT_CHANNEL if _production else TEST_ACO_BOT_CHANNEL


def server_admin_role_id():
    """
    Wrapper that returns the admin role ID

    :returns: Admin role id
    :rtype: int
    """
    return PROD_ADMIN_ID if _production else TEST_ADMIN_ID


def get_bot_notification_channel():
    """
    Returns the channel ID for the bot notifications channel.

    :return: The channel ID
    :rtype: int
    """
    return PROD_ACO_NOTIFICATION_BOT_CHANNEL if _production else TEST_ACO_NOTIFICATION_CHANNEL


def get_member_role_id():
    """
    Returns the member role ID for the server

    :return: The role ID
    :rtype: int
    """
    return PROD_MEMBER_ID if _production else TEST_MEMBER_ID


def get_server_aco_role_id():
    """
    Returns the ACO role ID for the server

    :return: The role ID
    :rtype: int
    """
    return PROD_ACO_ROLE_ID if _production else TEST_ACO_ROLE_ID
