from ptn.aco.commands.DatabaseInteraction import DatabaseInteraction
from ptn.aco.commands.DiscordBotCommands import DiscordBotCommands
from ptn.aco.commands.Helper import Helper
from ptn.aco.constants import bot, TOKEN, _production
from ptn.aco.database.database import build_database_on_startup


print(f'The affiliator bot is connecting against production: {_production}.')


def run():
    """
    Logic to build the bot and run the script.

    :returns: None
    """
    build_database_on_startup()
    bot.add_cog(DiscordBotCommands(bot))
    bot.add_cog(DatabaseInteraction())
    bot.add_cog(Helper())
    bot.run(TOKEN)


if __name__ == '__main__':
    run()
