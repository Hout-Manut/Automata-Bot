import hikari
import hikari.commands
import lightbulb

from ._history_autocomplete import history_autocomplete

recent_plugin = lightbulb.Plugin('recent')


@recent_plugin.command
@lightbulb.option('recent', 'Show recent inputs', autocomplete=True)
@lightbulb.command('recent', 'Show recent inputs')
@lightbulb.implements(lightbulb.SlashCommand)
async def recent_cmd(ctx: lightbulb.SlashContext) -> None:
    fa_name = ctx.options.recent
    print("Found: ", fa_name)

    try:
        fa_id = int(fa_name)
    except ValueError:
        await ctx.respond('Invalid input.', flags=hikari.MessageFlag.EPHEMERAL)
        return

    if fa_id == 0:
        await ctx.respond('Funny.', flags=hikari.MessageFlag.EPHEMERAL)
        return

    await ctx.respond('Fuck u panavath')


@recent_cmd.autocomplete("recent")
async def autocomplete_history(
    opt: hikari.AutocompleteInteractionOption,
    inter: hikari.AutocompleteInteraction,
) -> list[hikari.commands.CommandChoice]:
    return await history_autocomplete(opt, inter, recent_plugin)


def load(bot: lightbulb.BotApp):
    bot.add_plugin(recent_plugin)
