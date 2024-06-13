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

    embed_title = "Deterministic" if modal.is_dfa else "Non-deterministic"
    embed_title = f"{embed_title} Finite Automation"

    embed = modal.fa.get_embed(title=embed_title)
    embed.set_image(modal.fa.get_diagram())

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
        ...
    else:
        modal = automata.FormModal(title="Enter FA data.")
        builder = modal.build_response(ctx.app.d.miru)
        ctx.app.d.miru.start_modal(modal)
        await builder.create_modal_response(ctx.interaction)
        await modal.wait()

        fa = modal.fa
        ctx = modal.ctx

    embed = hikari.Embed(title="FA String Test")
    string = ""
    embed.add_field(name="String", value="ε" if string == "" else string)
    embed.add_field(name="Status", value="Failed")
    embed.add_field(name="Current State", value=fa.initial)

    name = "State" if len(modal.fa.states) == 1 else "States"
    states = ", ".join(modal.fa.states)
    embed.add_field(name=name, value=f"{{{states}}}", inline=True)

    name = "Input" if len(modal.fa.states) == 1 else "Inputs"
    inputs = ", ".join(modal.fa.inputs)
    embed.add_field(name=name, value=f"{{{inputs}}}", inline=True)

    embed.add_field(name="Initial State", value=modal.fa.initial, inline=True)

    finals = ", ".join(modal.fa.finals)
    name = "Final State" if len(modal.fa.finals) == 1 else "Final States"
    embed.add_field(name=name, value=f"{{{finals}}}", inline=True)

    tf = ""
    for (k0, k1), v in modal.fa.transitions.items():
        k1 = "ε" if k1 == "" else k1
        tf += f"({k0}, {k1}) = {{{', '.join(v)}}}\n"
    embed.add_field(name=f"Transition Functions", value=tf, inline=True)

    embed.set_footer(text='Send messages to enter. (-{num} to backspace)')
    path = modal.fa.draw_graph()
    path = "C:/Users/Manut/Desktop/Automata Bot/" + path
    image = hikari.File(path, filename="automata.png")
    embed.set_image(image)
    embed.set_author()
    embed.set_thumbnail

    await ctx.interaction.create_initial_response(
        hikari.ResponseType.MESSAGE_CREATE,
        embed=embed,
    )

    backspace_pattern = re.compile(r"-(\d+)\s*$")
    def check(event: hikari.MessageCreateEvent) -> bool:
        is_author = event.author_id == ctx.author.id
        in_channel = event.channel_id == ctx.channel_id
        if not is_author or not in_channel:
            return False
        content = event.message.content
        has_valid_symbol = set(content).issubset(fa.inputs)

        match = backspace_pattern.match(content)
        return has_valid_symbol or match is not None

    async def get_user_response() -> hikari.MessageCreateEvent:
        user_input = await test_plugin.bot.wait_for(
            hikari.MessageCreateEvent, predicate=check, timeout=300
        )
        return user_input

    try:
        while True:
            result = fa.check_string(string)
            if result.is_accepted:
                embed.color = 0x00CC00
                embed.edit_field(1, hikari.UNDEFINED, "Passed")
            else:
                embed.color = 0xCC0000
                embed.edit_field(1, hikari.UNDEFINED, "Failed")

            embed.edit_field(0, hikari.UNDEFINED, "ε" if string == "" else string)
            embed.edit_field(2, hikari.UNDEFINED, result.last_state)
            await ctx.interaction.edit_initial_response(embed)
            new_input = await get_user_response()

            content = "" if not new_input.message.content else new_input.message.content
            if content.startswith("-"):
                string = string[:-int(content[1:])]
            else:
                string += content

            await new_input.message.delete()
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
