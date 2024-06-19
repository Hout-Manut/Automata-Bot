import asyncio
import re

import hikari
import lightbulb
import miru

import bot.automata as automata
from ._history_autocomplete import history_autocomplete

test_plugin = lightbulb.Plugin("test")


@test_plugin.command
@lightbulb.command("test", "Testing")
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def test_cmd(ctx: lightbulb.SlashContext) -> None: ...


@test_cmd.child
@lightbulb.command("fa", "Test if the FA is non-deterministic or deterministic")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def test_fa_cmd(ctx: lightbulb.SlashContext) -> None:
    modal = automata.InputFAModal()
    builder = modal.build_response(ctx.app.d.miru)
    await builder.create_modal_response(ctx.interaction)
    ctx.app.d.miru.start_modal(modal)
    await modal.wait()
    await modal.ctx.interaction.create_initial_response(
        hikari.ResponseType.DEFERRED_MESSAGE_CREATE,
    )

    fa = modal.fa

    modal.fa.save_to_db(ctx)
    menu = automata.AutomataMenu(timeout=600)
    main_screen = automata.MainScreen(menu, fa=fa, inter=ctx)
    builder = await menu.build_response_async(
        ctx.app.d.miru,
        main_screen
    )
    await main_screen.invoke_test_string()
    await builder.create_followup(ctx.interaction)
    await modal.ctx.interaction.delete_initial_response()

    # Start the design menu
    ctx.app.d.miru.start_view(menu)

@test_cmd.child
@lightbulb.option(
    "history", "Your past saved FAs", autocomplete=True, required=False, default=""
)
@lightbulb.command("string", "Test if the string is accepted or not")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def test_str_cmd(ctx: lightbulb.SlashContext) -> None:
    modal = automata.InputFAModal()
    builder = modal.build_response(ctx.app.d.miru)
    await builder.create_modal_response(ctx.interaction)
    ctx.app.d.miru.start_modal(modal)
    await modal.wait()
    await modal.ctx.interaction.create_initial_response(
        hikari.ResponseType.DEFERRED_MESSAGE_CREATE,
    )

    fa = modal.fa

    modal.fa.save_to_db(ctx)
    menu = automata.AutomataMenu(timeout=600)
    main = automata.MainScreen(menu, fa=fa, inter=ctx)
    builder = await menu.build_response_async(
        ctx.app.d.miru,
        main
    )

    await menu.push(automata.TestStringScreen(menu, main))
    await menu.update_message()
    await builder.create_followup(ctx.interaction)
    await modal.ctx.interaction.delete_initial_response()

    ctx.app.d.miru.start_view(menu)


@test_str_cmd.autocomplete("history")
async def autocomplete_history(
    opt: hikari.AutocompleteInteractionOption,
    inter: hikari.AutocompleteInteraction,
) -> list[str]:
    return await history_autocomplete(opt, inter)


def load(bot: lightbulb.BotApp):
    bot.add_plugin(test_plugin)
    global client
    client = miru.Client(bot)
