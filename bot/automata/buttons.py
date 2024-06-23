import hikari
import miru
from miru.ext import menu

from . import classes


class ConvertButton(menu.ScreenButton):

    def __init__(
        self,
        label: str = "Convert to DFA",
        *,
        emoji: hikari.Emoji | str | None = None,
        style: hikari.ButtonStyle = hikari.ButtonStyle.PRIMARY,
        disabled: bool = False,
        custom_id: str | None = None,
        row: int | None = None,
        position: int | None = None,
        autodefer: bool | miru.AutodeferOptions | hikari.UndefinedType = hikari.UNDEFINED
    ) -> None:
        super().__init__(
            label,
            emoji=emoji,
            style=style,
            disabled=disabled,
            custom_id=custom_id,
            row=row,
            position=position,
            autodefer=autodefer
        )

    async def callback(self, ctx: miru.ViewContext) -> None:
        new_fa, result = self.screen.menu.fa.convert()
        self.menu.fa = new_fa
        self.menu.fa.save_to_db(self.menu.ctx)
        self.disabled = True
        await self.menu.update_message(await self.screen.build_content(result.get_embed()))


class MinimizeButton(menu.ScreenButton):

    def __init__(
        self,
        fa: classes.FA | None = None,
        label: str = "Minimize DFA",
        *,
        emoji: hikari.Emoji | str | None = None,
        style: hikari.ButtonStyle = hikari.ButtonStyle.PRIMARY,
        disabled: bool = False,
        custom_id: str | None = None,
        row: int | None = None,
        position: int | None = None,
        autodefer: bool | miru.AutodeferOptions | hikari.UndefinedType = hikari.UNDEFINED
    ) -> None:
        if fa:
            disabled = not fa.is_minimizable
        super().__init__(
            label,
            emoji=emoji,
            style=style,
            disabled=disabled,
            custom_id=custom_id,
            row=row,
            position=position,
            autodefer=autodefer
        )

    async def callback(self, ctx: miru.ViewContext) -> None:
        new_fa, result = self.menu.fa.minimize()
        self.disabled = True
        self.menu.fa = new_fa
        await self.menu.update_message(await self.screen.build_content(result.get_embed()))
