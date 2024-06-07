import hikari
import lightbulb
import miru

from ._history_autocomplete import history_autocomplete

convert_command = lightbulb.Plugin("convert")


@convert_command.command
@lightbulb.command("convert", "Conversion")
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def convert_cmd(ctx: lightbulb.SlashCommandGroup) -> None: ...


@convert_cmd.child
@lightbulb.option(
    "history", "Your past saved FAs", autocomplete=True, required=False, default=""
)
@lightbulb.command("nfa_to_dfa", "Convert a NFA to a DFA")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def nfa_dfa_cmd(ctx: lightbulb.SlashSubCommand) -> None:
    await ctx.interaction.create_initial_response(
        hikari.ResponseType.MESSAGE_CREATE, "Hi"
    )
    return


@nfa_dfa_cmd.autocomplete("history")
async def autocomplete_history(
    opt: hikari.AutocompleteInteractionOption,
    inter: hikari.AutocompleteInteraction,
) -> list[str]:
    return await history_autocomplete(opt, inter)


def load(bot: lightbulb.BotApp):
    bot.add_plugin(convert_command)
