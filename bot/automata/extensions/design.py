import hikari
import lightbulb
import miru

import bot.automata as automata

design_command = lightbulb.Plugin("design")


@design_command.command
@lightbulb.command("design", "Design an automation.")
@lightbulb.implements(lightbulb.SlashCommand)
async def design_cmd(ctx: lightbulb.SlashContext) -> None:
    modal = automata.FormModal(title="Enter FA data.")
    builder = modal.build_response(ctx.app.d.miru)
    ctx.app.d.miru.start_modal(modal)
    await builder.create_modal_response(ctx.interaction)
    await modal.wait()

    is_dfa = modal.is_dfa
    desc = "Non-deterministic" if not is_dfa else "Deterministic"

    embed = hikari.Embed(
        title=f"{desc} Finite Automation",
        color=0x00CC00
    )
    states = ", ".join(modal.fa.states)
    embed.add_field(name="States", value=f"{{{states}}}")

    inputs = ", ".join(modal.fa.inputs)
    embed.add_field(name="Inputs", value=f"{{{inputs}}}")

    embed.add_field(name="Initial State", value=modal.fa.initial)

    finals = ", ".join(modal.fa.finals)
    embed.add_field(name="Final States", value=f"{{{finals}}}")

    tf = ""
    for (k0, k1), v in modal.fa.transitions.items():
        tf += f"({k0}, {k1}) = {{{', '.join(v)}}}\n"
    embed.add_field(name=f"Transition Functions", value=tf)

    path = modal.fa.draw_graph()
    path = "C:/Users/Manut/Desktop/Automata Bot/" + path
    image = hikari.File(path, filename="automata.png")
    embed.set_image(image)

    await modal.ctx.respond(embed=embed)



def load(bot: lightbulb.BotApp):
    bot.add_plugin(design_command)
