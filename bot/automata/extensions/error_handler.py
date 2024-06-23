import hikari
import lightbulb

error = lightbulb.Plugin("error_handler")


class AutomataError(Exception):
    """
    Base class for all errors raised by the program.
    """


class UserError(AutomataError):
    """
    Base class for errors raised by the user using the program.
    """


class InvalidFAError(UserError):
    """
    Raised when the provided FA data is invalid.
    """


class InvalidNFAError(InvalidFAError):
    """
    Raised when the provided NFA data is invalid.
    """


class InvalidDFAError(InvalidFAError):
    """
    Raised when the provided NFA data is invalid.
    """


class NotMinimizeable(InvalidFAError):
    """
    Raised when the provided FA is not minimizable.
    """

class InvalidDBQuery(UserError):
    """
    Raised when the provided query is invalid.
    """


@error.listener(lightbulb.CommandErrorEvent)
async def error_handler(event: lightbulb.CommandErrorEvent) -> None:
    if isinstance(event.exception.__cause__, UserError):
        error = event.exception.__cause__
        await event.context.respond(
            hikari.Embed(
                title=type(
                    error).__name__, description=error.args, color=0xCC0000
            ),
            flags=hikari.MessageFlag.EPHEMERAL,
        )
        return

    if isinstance(event.exception, lightbulb.CommandInvocationError):
        await event.context.respond(
            hikari.Embed(
                title="Error",
                description=f"Something went wrong during invocation of command `{event.context.command.name}`.",
                color=0xCC0000
            ),
            flags=hikari.MessageFlag.EPHEMERAL,
        )
        raise event.exception


def load(tenniel: lightbulb.BotApp) -> None:
    tenniel.add_plugin(error)
