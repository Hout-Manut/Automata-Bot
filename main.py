import hikari
import lightbulb
import miru

import bot.automata as automata
from bot.automata import TOKEN, DEFAULT_GUILDS

bot = lightbulb.BotApp(
    token=TOKEN,
    default_enabled_guilds=DEFAULT_GUILDS,
    intents=hikari.Intents.ALL,
    help_class=None,
    ignore_bots=True,
    prefix="+",
)

bot.d.miru = miru.Client(bot, ignore_unknown_interactions=True)


bot.load_extensions_from("bot/automata/extensions")

if __name__ == '__main__':
    automata.run(bot)
