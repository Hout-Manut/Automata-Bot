"""
This module manages the command for minimizing FA.
"""

import hikari
import lightbulb
from hikari.commands import CommandChoice

import bot.automata as automata
from ._history_autocomplete import history_autocomplete

minimize_plugin = lightbulb.Plugin("minimize")


@minimize_plugin.command
@lightbulb.command("minimize", "Minimize an FA")
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def minimize_cmd(ctx: lightbulb.SlashCommandGroup) -> None: ...


@minimize_cmd.child
@lightbulb.option(
    "recent",
    "Your recent FA inputs",
    autocomplete=True,
    required=False,
    default="",
)
@lightbulb.command("dfa", "Minimize a DFA")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def nfa_cmd(ctx: lightbulb.SlashContext) -> None:
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


@nfa_cmd.autocomplete("recent")
async def autocomplete_history(
    opt: hikari.AutocompleteInteractionOption,
    inter: hikari.AutocompleteInteraction,
) -> list[CommandChoice]:
    return await history_autocomplete(opt, inter, minimize_plugin)


def load(bot: lightbulb.BotApp):
    bot.add_plugin(minimize_plugin)
