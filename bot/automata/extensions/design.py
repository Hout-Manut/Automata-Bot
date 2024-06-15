import hikari
import lightbulb
import miru
from miru.ext import menu

import bot.automata as automata


design_command = lightbulb.Plugin("design")


@design_command.command
@lightbulb.command("design", "Design an automation.")
@lightbulb.implements(lightbulb.SlashCommand)
async def design_cmd(ctx: lightbulb.SlashContext) -> None:
    modal = automata.InputFAModal()
    builder = modal.build_response(ctx.app.d.miru)
    await builder.create_modal_response(ctx.interaction)
    ctx.app.d.miru.start_modal(modal)
    await modal.wait()

    await modal.ctx.interaction.create_initial_response(
        hikari.ResponseType.DEFERRED_MESSAGE_CREATE,
    )
    print("hi")
    fa = modal.fa
    # ctx = modal.ctx

    design_menu = menu.Menu(timeout=600)
    builder = await design_menu.build_response_async(
        ctx.app.d.miru,
        automata.MainScreen(design_menu, fa=fa, inter=ctx)
    )
    print("hi")
    await builder.create_followup(ctx.interaction)
    print("hi")
    await modal.ctx.interaction.delete_initial_response()
    print("hi")
    ctx.app.d.miru.start_view(design_menu)


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(design_command)
