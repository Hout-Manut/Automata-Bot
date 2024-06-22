import hikari
import hikari.commands
import lightbulb
import miru

import bot.automata as automata
from ._history_autocomplete import history_autocomplete

convert_plugin = lightbulb.Plugin("convert")


@convert_plugin.command
@lightbulb.command("convert", "Conversion")
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def convert_cmd(ctx: lightbulb.SlashCommandGroup) -> None: ...


@convert_cmd.child
@lightbulb.option(
    "recent", "Your past saved FAs", autocomplete=True, required=False, default=""
)
@lightbulb.command("nfa_to_dfa", "Convert a NFA to a DFA")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def nfa_dfa_cmd(ctx: lightbulb.SlashSubCommand) -> None:
    if ctx.options.recent != "":
        await ctx.interaction.create_initial_response(
            hikari.ResponseType.DEFERRED_MESSAGE_CREATE
        )

    fa = await automata.FA.ask_or_get_fa(ctx)

    # modal.fa.save_to_db(ctx)
    menu = automata.AutomataMenu(fa, ctx, timeout=600)
    builder = await menu.build_response_async(
        ctx.app.d.miru,
        automata.MainScreen(menu)
    )
    message = await builder.create_followup(ctx.interaction)

    ctx.app.d.miru.start_view(menu, bind_to=message)


@nfa_dfa_cmd.autocomplete("recent")
async def autocomplete_history(
    opt: hikari.AutocompleteInteractionOption,
    inter: hikari.AutocompleteInteraction,
) -> hikari.commands.CommandChoice:
    return await history_autocomplete(opt, inter, convert_plugin)


def load(bot: lightbulb.BotApp):
    bot.add_plugin(convert_plugin)
