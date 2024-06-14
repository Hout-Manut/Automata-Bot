import hikari
import lightbulb

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

    desc = "Deterministic" if modal.is_dfa else "Non-deterministic"

    embed = hikari.Embed(
        title=f"{desc} Finite Automation Design",
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
        k1 = "ε" if k1 == "" else k1
        tf += f"({k0}, {k1}) = {{{', '.join(v)}}}\n"
    embed.add_field(name=f"Transition Functions", value=tf)

    path = modal.fa.draw_diagram()
    path = "C:/Users/Manut/Desktop/Automata Bot/" + path
    image = hikari.File(path, filename="automata.png")
    embed.set_image(image)

    modal.fa.save_to_db()

    await modal.ctx.respond(embed=embed)


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(design_command)
