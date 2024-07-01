import hikari
import hikari.commands
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
    fa = await automata.FA.ask_or_get_fa(ctx)

    menu = automata.AutomataMenu(fa, ctx, timeout=600)
    builder = await menu.build_response_async(
        ctx.app.d.miru,
        automata.MainScreen(menu)
    )
    message = await builder.create_followup(ctx.interaction)

    ctx.app.d.miru.start_view(menu, bind_to=message)


@test_cmd.child
@lightbulb.option(
    "recent", "Your recent FA inputs", autocomplete=True, required=False, default=""
)
@lightbulb.command("string", "Test if the string is accepted or not")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def test_str_cmd(ctx: lightbulb.SlashContext) -> None:
    if ctx.options.recent != "":
        await ctx.interaction.create_initial_response(
            hikari.ResponseType.DEFERRED_MESSAGE_CREATE
        )

    fa = await automata.FA.ask_or_get_fa(ctx)

    # modal.fa.save_to_db(ctx)
    menu = automata.AutomataMenu(fa, ctx, timeout=600)
    builder = await menu.build_response_async(
        ctx.app.d.miru,
        automata.TestStringScreen(menu)
    )
    message = await builder.create_followup(ctx.interaction)

    ctx.app.d.miru.start_view(menu, bind_to=message)


@test_str_cmd.autocomplete("recent")
async def autocomplete_history(
    opt: hikari.AutocompleteInteractionOption,
    inter: hikari.AutocompleteInteraction,
) -> list[str]:
    return await history_autocomplete(opt, inter, test_plugin)


def load(bot: lightbulb.BotApp):
    bot.add_plugin(test_plugin)
    global client
    client = miru.Client(bot)
