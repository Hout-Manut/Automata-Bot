import lightbulb
import hikari
from ._history_autocomplete import history_autocomplete

main_recent = lightbulb.Plugin('Recent')
@main_recent.command
@lightbulb.option('history', 'Show recent inputs', autocomplete=True)
@lightbulb.command('recent', 'Show recent inputs')
@lightbulb.implements(lightbulb.SlashCommand)
async def recent_cmd(ctx: lightbulb.SlashContext) -> None:
    await ctx.respond('Fuck u panavath')

@recent_cmd.autocomplete("history")
async def autocomplete_history(
    opt: hikari.AutocompleteInteractionOption,
    inter: hikari.AutocompleteInteraction,
) -> list[str]:
    return await history_autocomplete(opt, inter)

def load(bot: lightbulb.BotApp):
    bot.add_plugin(main_recent)