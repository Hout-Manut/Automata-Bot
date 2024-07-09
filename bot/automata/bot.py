import hikari
import lightbulb
from lightbulb.ext import tasks

from .extensions import _history_autocomplete as history

def run(bot: lightbulb.BotApp) -> None:
    """Starts the bot."""
    tasks.load(bot)

    bot.run(
        status=hikari.Status.ONLINE,
        activity=hikari.Activity(
            name="FA diagrams.",
            type=hikari.ActivityType.WATCHING
        )
    )


@tasks.task(m=1, auto_start=True)
async def clear_cache_task() -> None:
    await history.clear_cache()
