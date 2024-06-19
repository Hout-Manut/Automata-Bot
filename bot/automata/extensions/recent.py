import hikari
import lightbulb

from ._history_autocomplete import history_autocomplete

recent_plugin = lightbulb.Plugin('recent')


@recent_plugin.command
@lightbulb.option('recent', 'Show recent inputs', autocomplete=True)
@lightbulb.command('recent', 'Show recent inputs')
@lightbulb.implements(lightbulb.SlashCommand)
async def recent_cmd(ctx: lightbulb.SlashContext) -> None:
    fa_name = ctx.options.recent.split(" ~ ")[0]
    print("Found: ", fa_name)

    await ctx.respond('Fuck u panavath')


@recent_cmd.autocomplete("history")
async def autocomplete_history(
    opt: hikari.AutocompleteInteractionOption,
    inter: hikari.AutocompleteInteraction,
) -> list[str]:
    return await history_autocomplete(opt, inter)


def load(bot: lightbulb.BotApp):
    bot.add_plugin(recent_plugin)
