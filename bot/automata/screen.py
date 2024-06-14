from __future__ import annotations

import hikari
import lightbulb
import miru
from miru.ext import menu

from .classes import FA, Color, ActionOptions


class MainScreen(menu.Screen):

    def __init__(
        self,
        menu: menu.Menu,
        fa: FA | None = None,
    ) -> None:
        super().__init__(menu)

    async def build_content(self) -> menu.ScreenContent:
        return menu.ScreenContent(

        )

    def get_fa_embed(
        self,
        image_ratio: str = "1",
        author_name: str | None = None,
        author_icon: hikari.Resourceish | None = None
    ) -> hikari.Embed:
        title = "Deterministic" if self.fa.is_dfa else "Non-deterministic"
        title += " Finite Automation"
        embed = hikari.Embed(
            title=title,
            description=None,
            color=Color.LIGHT_BLUE
        )
        fa = self.fa

        name = "State" if len(fa.states) == 1 else "States"
        embed.add_field(name, fa.states_str)

        name = "Alphabet" if len(fa.alphabets) == 1 else "Alphabets"
        embed.add_field(name, fa.alphabets_str)

        embed.add_field("Initial State", fa.initial_state)

        name = "State" if len(fa.final_states) == 1 else "States"
        embed.add_field(f"Final {name}", fa.final_states_str)

        name = "Function" if len(fa.t_func) == 1 else "Functions"
        embed.add_field(f"Transition {name}", fa.t_func_str)

        embed.set_image(fa.get_diagram(image_ratio))
        if author_name or author_icon:
            embed.set_author(name=author_name, icon=author_icon)

        return embed

    @menu.button(label="Test a String", style=hikari.ButtonStyle.SECONDARY)
    def test_string_callback(self, ctx: miru.ViewContext, btn: miru.Button) -> None: