"""
This module manages the command for design.

Only this plugin has comments because of repetitiveness.
Also I think you wouldn't need to know about Discord stuffs and only the Automata stuffs.
"""

import hikari
import lightbulb
from hikari.commands import CommandChoice

import bot.automata as automata
from ._history_autocomplete import history_autocomplete

# Initialize plugin object
design_plugin = lightbulb.Plugin("design")


# Add the command to the plugin
@design_plugin.command
@lightbulb.option(            # Optional option for recent FA
    "recent",                 # Option name
    "Your recent FA inputs",  # Option description
    autocomplete=True,
    required=False,
    default=""
)
@lightbulb.command("design", "Design an automaton")  # Command name and description
@lightbulb.implements(lightbulb.SlashCommand)        # Type of command (this one is a slash command)
async def design_cmd(ctx: lightbulb.SlashContext) -> None:
    """
    Executes when the command is called.

    Args:
        ctx: This is automatically passed by the bot with the context of the command. such as the user, channel, and guild.
    """

    # Create a defer message to notify the user that the command is being processed
    # This will show a `Bot is thinking...` message
    if ctx.options.recent != "":
        await ctx.interaction.create_initial_response(
            hikari.ResponseType.DEFERRED_MESSAGE_CREATE
        )

    # Get the FA depends on the command usage
    # Hover over the function to see detailed docstring
    fa = await automata.FA.ask_or_get_fa(ctx)

    # Create the menu
    # Menus are the main UI for the bot with navigation buttons.
    menu = automata.AutomataMenu(fa, ctx, timeout=600)
    builder = await menu.build_response_async(
        ctx.app.d.miru,
        automata.MainScreen(menu)
    )
    # Update the defer message with the menu
    message = await builder.create_followup(ctx.interaction)

    # Start the view to listen for interactions
    # Views are the buttons below the menu
    ctx.app.d.miru.start_view(menu, bind_to=message)


# Add the autocomplete to the command
@design_cmd.autocomplete("recent")
async def recent_fa_autocomplete(
    opt: hikari.AutocompleteInteractionOption,
    inter: hikari.AutocompleteInteraction,
) -> list[CommandChoice]:
    """
    Executes every time the user types something in the recent option.

    Args:
        opt: The option that is being autocompleted
        inter: The interaction that triggered the autocompletion

    Returns:
        A list of CommandChoices. Maximum of 25 because of Discord's limit.
    """
    return await history_autocomplete(opt, inter, design_plugin)


# Load the plugin into the bot
def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(design_plugin)
