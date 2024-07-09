import hikari
import hikari.errors
import lightbulb
import miru
import mysql.connector
from mysql.connector import Error as SQLError

from bot.automata import (
    run,
    TOKEN,
    DEFAULT_GUILDS,
    DB_HOST,
    DB_USER,
    DB_PASSWORD,
    DB_NAME
)


# Initialize bot application
bot = lightbulb.BotApp(
    token=TOKEN,
    default_enabled_guilds=DEFAULT_GUILDS,
    intents=hikari.Intents.ALL,
    help_class=None,
    ignore_bots=True,
)


bot.d.miru = miru.Client(bot, ignore_unknown_interactions=True)


try:
    db: mysql.connector.MySQLConnection = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )

    if db.is_connected():
        bot.d.db = db
        bot.d.cursor = db.cursor()
    else:
        raise SQLError

except SQLError:
    print("Database connection failed. Please check your environment variables.")
    exit()


bot.load_extensions_from("bot/automata/extensions")


if __name__ == '__main__':
    run(bot)
