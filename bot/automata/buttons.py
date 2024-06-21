from typing import Callable

import hikari
import lightbulb
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
        new_fa = await self.screen.menu.fa.convert()
        self.menu.fa = new_fa
        self.menu.fa.save_to_db(self.menu.ctx)
        self.screen.extra.disabled = True
        await self.menu.update_message(await self.screen.build_content())


class MinimizeButton(menu.ScreenButton):

    def __init__(
        self,
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
        await ctx.respond("Not implemented", flags=hikari.MessageFlag.EPHEMERAL)
        return
        new_fa = self.menu.fa.minimize()
        self.disabled = True
        self.menu.fa = new_fa
        await self.menu.update_message(await self.screen.build_content())


class SaveButton(miru.Button):

    def __init__(
        self,
        saveable: bool | None = None,
        label: str = "Save",
        *,
        emoji: hikari.Emoji | str | None = None,
        style: hikari.InteractiveButtonTypesT = hikari.ButtonStyle.SECONDARY,
        disabled: bool | None = None,
        custom_id: str | None = None,
        row: int = 1,
        position: int | None = None,
        autodefer: (
            bool | miru.AutodeferOptions | hikari.UndefinedType
        ) = hikari.UNDEFINED,
    ) -> None:
        disabled = (
            (True if self.view.inter.history != "" else False)
            if saveable is None
            else not saveable
        )

        super().__init__(
            label,
            emoji=emoji,
            style=style,
            disabled=disabled,
            custom_id=custom_id,
            row=row,
            position=position,
            autodefer=autodefer,
        )

    def callback(self, context: miru.ViewContext) -> None:
        raise NotImplementedError


class EditButton(miru.Button):

    def __init__(
        self,
        editable: bool = True,
        label: str = "Edit",
        *,
        emoji: hikari.Emoji | str | None = None,
        style: hikari.InteractiveButtonTypesT = hikari.ButtonStyle.SECONDARY,
        disabled: bool | None = None,
        custom_id: str | None = None,
        row: int = 1,
        position: int | None = None,
        autodefer: (
            bool | miru.AutodeferOptions | hikari.UndefinedType
        ) = hikari.UNDEFINED,
    ) -> None:
        disabled = not editable if disabled is None else disabled

        super().__init__(
            label,
            emoji=emoji,
            style=style,
            disabled=disabled,
            custom_id=custom_id,
            row=row,
            position=position,
            autodefer=autodefer,
        )

    def callback(self, context: miru.ViewContext) -> None:
        raise NotImplementedError


class ExitButton(miru.Button):

    def __init__(
        self,
        exitable: bool = True,
        label: str = "Edit",
        *,
        emoji: hikari.Emoji | str | None = None,
        style: hikari.InteractiveButtonTypesT = hikari.ButtonStyle.DANGER,
        disabled: bool | None = None,
        custom_id: str | None = None,
        row: int = 1,
        position: int | None = None,
        autodefer: (
            bool | miru.AutodeferOptions | hikari.UndefinedType
        ) = hikari.UNDEFINED,
    ) -> None:
        disabled = not exitable if disabled is None else disabled

        super().__init__(
            label,
            emoji=emoji,
            style=style,
            disabled=disabled,
            custom_id=custom_id,
            row=row,
            position=position,
            autodefer=autodefer,
        )

    def callback(self, context: miru.ViewContext) -> None:
        raise NotImplementedError
