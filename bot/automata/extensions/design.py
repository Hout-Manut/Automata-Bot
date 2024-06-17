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
    # Create a modal
    modal = automata.InputFAModal()
    builder = modal.build_response(ctx.app.d.miru)

    # Create a modal response
    await builder.create_modal_response(ctx.interaction)

    # Start the modal
    ctx.app.d.miru.start_modal(modal)

    # Wait for the modal to finish
    await modal.wait()

    # Create a response for the initial interaction
    await modal.ctx.interaction.create_initial_response(
        hikari.ResponseType.DEFERRED_MESSAGE_CREATE,
    )

    # Get the FA from the modal
    fa = modal.fa

    # Save the FA to the database
    modal.fa.save_to_db(ctx)

    # Create a design menu
    design_menu = menu.Menu(timeout=600)
    builder = await design_menu.build_response_async(
        ctx.app.d.miru,
        automata.MainScreen(design_menu, fa=fa, inter=ctx)
    )

    # Create a followup response for the initial interaction
    await builder.create_followup(ctx.interaction)

    # Delete the initial response
    await modal.ctx.interaction.delete_initial_response()

    # Start the design menu
    ctx.app.d.miru.start_view(design_menu)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(design_command)
