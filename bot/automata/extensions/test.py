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
    modal = automata.FormModal(title="Enter FA data.")
    builder = modal.build_response(ctx.app.d.miru)
    ctx.app.d.miru.start_modal(modal)
    await builder.create_modal_response(ctx.interaction)
    await modal.wait()

    desc = "Deterministic" if modal.is_dfa else "Non-deterministic"

    embed = hikari.Embed(title=f"{desc} Finite Automation", color=0x00CC00)
    name = "State" if len(modal.fa.states) == 1 else "States"
    states = ", ".join(modal.fa.states)
    embed.add_field(name=name, value=f"{{{states}}}")

    name = "Input" if len(modal.fa.states) == 1 else "Inputs"
    inputs = ", ".join(modal.fa.inputs)
    embed.add_field(name=name, value=f"{{{inputs}}}")

    embed.add_field(name="Initial State", value=modal.fa.initial)

    finals = ", ".join(modal.fa.finals)
    name = "Final State" if len(modal.fa.finals) == 1 else "Final States"
    embed.add_field(name=name, value=f"{{{finals}}}")

    tf = ""
    for (k0, k1), v in modal.fa.transitions.items():
        k1 = "ε" if k1 == "" else k1
        tf += f"({k0}, {k1}) = {{{', '.join(v)}}}\n"
    embed.add_field(name=f"Transition Functions", value=tf)

    await modal.ctx.respond(embed=embed)
    return


@test_cmd.child
@lightbulb.option(
    "history", "Your past saved FAs", autocomplete=True, required=False, default=""
)
@lightbulb.command("string", "Test if the string is accepted or not")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def test_str_cmd(ctx: lightbulb.SlashContext) -> None:
    if ctx.options.history != "":
        ... #TODO get the FA data from database
        # fa = ...
    else:
        modal = automata.FormModal(title="Enter FA data.")
        builder = modal.build_response(ctx.app.d.miru)
        ctx.app.d.miru.start_modal(modal)
        await builder.create_modal_response(ctx.interaction)
        await modal.wait()

        fa = modal.fa
        ctx = modal.ctx

    embed = hikari.Embed(title="String FA Test")
    await ctx.interaction.create_initial_response(
        hikari.ResponseType.DEFERRED_MESSAGE_CREATE
    )
    string = ""
    embed.add_field(name="String", value=string)
    embed.add_field(name="Status", value="Failed")
    embed.set_footer(text='Send messages to enter. "-{num} to backspace."')

    def check(event: hikari.MessageCreateEvent) -> bool:
        is_author = event.author_id == ctx.author.id
        in_channel = event.channel_id == ctx.channel_id
        has_valid_symbol = set(event.message.content).issubset(fa.inputs)
        return is_author and in_channel

    async def get_user_response() -> hikari.MessageCreateEvent:
        user_input = await test_plugin.bot.wait_for(
            hikari.MessageCreateEvent, predicate=check, timeout=300
        )
        return user_input
    
    backspace_pattern = re.compile(r"^-(\d)")

    try:
        while True:
            result = fa.check_string(string)
            if result.is_accepted:
                embed.color = 0x00CC00
                embed.edit_field(1, hikari.UNDEFINED, "Passed")
            else:
                embed.color = 0xCC0000
                embed.edit_field(1, value="Failed")

            embed.edit_field(0, hikari.UNDEFINED, string)

            await ctx.interaction.edit_initial_response(embed=embed)
            new_input = await get_user_response()
    except asyncio.TimeoutError:
        embed.set_footer("Timed out.")
        await ctx.interaction.edit_initial_response(embed)

    return


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
