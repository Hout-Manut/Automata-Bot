from __future__ import annotations

import hikari
import lightbulb
import miru
from miru.ext import menu

from .classes import FA, Color, ActionOptions


class MainScreen(menu.Screen):

    def __init__(
        self,
        fa: FA | None = None
        menu: menu.Menu
    ) -> None:
        super().__init__(menu)

    async def build_content(self) -> menu.ScreenContent:
        return menu.ScreenContent(

        )

    def get_fa_embed
