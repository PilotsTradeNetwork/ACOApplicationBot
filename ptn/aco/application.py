import asyncio

from ptn.aco.commands.DatabaseInteraction import DatabaseInteraction
from ptn.aco.commands.DiscordBotCommands import DiscordBotCommands
from ptn.aco.modules.Helper import Helper
from ptn.aco.constants import TOKEN, _production
from ptn.aco.database.database import build_database_on_startup
from ptn.aco.bot import bot

print(f'The affiliator bot is connecting against production: {_production}.')


def run():
    asyncio.run(aco())


async def aco():
    """
    Logic to build the bot and run the script.

    :returns: None
    """
    build_database_on_startup()
    await bot.add_cog(DiscordBotCommands(bot))
    await bot.add_cog(DatabaseInteraction())
    await bot.add_cog(Helper())
    await bot.start(TOKEN)


if __name__ == '__main__':
    run()
