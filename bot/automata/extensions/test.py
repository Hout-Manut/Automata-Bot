import hikari
import lightbulb
import miru

import bot.automata as automata

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

    embed = hikari.Embed(
        title=f"{desc} Finite Automation",
        color=0x00CC00
    )
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
        tf += f"({k0}, {k1}) = {{{', '.join(v)}}}\n"
    embed.add_field(name=f"Transition Functions", value=tf)

    await modal.ctx.respond(embed=embed)
    return


@test_cmd.child
@lightbulb.command("string", "Test if the string is accepted or not")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def test_str_cmd(ctx: lightbulb.SlashContext) -> None:
    await ctx.interaction.create_initial_response(
        hikari.ResponseType.MESSAGE_CREATE, "Hi"
    )
    return


def load(bot: lightbulb.BotApp):
    bot.add_plugin(test_plugin)
    global client
    client = miru.Client(bot)
