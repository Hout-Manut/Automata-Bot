import hikari
import hikari.commands
import lightbulb
import miru
from miru.ext import menu

import bot.automata as automata
from ._history_autocomplete import history_autocomplete



design_plugin = lightbulb.Plugin("design")


@design_plugin.command
@lightbulb.option("recent", "Recent FA inputs", autocomplete=True, required=False, default="")
@lightbulb.command("design", "Design an automation")
@lightbulb.implements(lightbulb.SlashCommand)
async def design_cmd(ctx: lightbulb.SlashContext) -> None:
    if ctx.options.recent != "":
        await ctx.interaction.create_initial_response(
            hikari.ResponseType.DEFERRED_MESSAGE_CREATE
        )


    fa = await automata.FA.ask_or_get_fa(ctx)

    menu = automata.AutomataMenu(fa, ctx, timeout=600)
    builder = await menu.build_response_async(
        ctx.app.d.miru,
        automata.MainScreen(menu)
    )
    message = await builder.create_followup(ctx.interaction)

    ctx.app.d.miru.start_view(menu, bind_to=message)


@design_cmd.autocomplete("recent")
async def recent_fa_autocomplete(
    opt: hikari.AutocompleteInteractionOption,
    inter: hikari.AutocompleteInteraction,
) -> list[hikari.commands.CommandChoice]:
    return await history_autocomplete(opt, inter, design_plugin)


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(design_plugin)
