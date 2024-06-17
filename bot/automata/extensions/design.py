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
    print("Starting design command")

    # Create a modal
    modal = automata.InputFAModal()
    builder = modal.build_response(ctx.app.d.miru)
    print("Created modal builder")

    # Create a modal response
    await builder.create_modal_response(ctx.interaction)
    print("Created modal response")

    # Start the modal
    ctx.app.d.miru.start_modal(modal)
    print("Started modal")

    # Wait for the modal to finish
    await modal.wait()
    print("Modal finished")

    # Create a response for the initial interaction
    await modal.ctx.interaction.create_initial_response(
        hikari.ResponseType.DEFERRED_MESSAGE_CREATE,
    )
    print("Created initial response")

    # Get the FA from the modal
    fa = modal.fa

    # Save the FA to the database
    print("Saving FA to database")
    modal.fa.save_to_db(ctx)

    # Create a design menu
    design_menu = menu.Menu(timeout=600)
    builder = await design_menu.build_response_async(
        ctx.app.d.miru,
        automata.MainScreen(design_menu, fa=fa, inter=ctx)
    )
    print("Created design menu builder")

    # Create a followup response for the initial interaction
    await builder.create_followup(ctx.interaction)
    print("Created followup response")

    # Delete the initial response
    await modal.ctx.interaction.delete_initial_response()
    print("Deleted initial response")

    # Start the design menu
    ctx.app.d.miru.start_view(design_menu)
    print("Design command finished")

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(design_command)
