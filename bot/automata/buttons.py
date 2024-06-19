import hikari
import lightbulb
import miru
from miru.ext import menu

from . import classes


class TestStringButton(menu.ScreenButton):

    def __init__(
        self,
        fa: classes.FA,
        label: str = "Test a String",
        *,
        emoji: hikari.Emoji | str | None = None,
        style: hikari.ButtonStyle = hikari.ButtonStyle.SECONDARY,
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
            autodefer=autodefer)

    def callback(self, context: miru.ViewContext) -> None:
        raise NotImplementedError


class ConvertButton(menu.ScreenButton):

    def __init__(
        self,
        fa: classes.FA,
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
        self.fa = fa
        super().__init__(
            label,
            emoji=emoji,
            style=style,
            disabled=disabled,
            custom_id=custom_id,
            row=row,
            position=position,
            autodefer=autodefer)

    async def callback(self, context: miru.ViewContext) -> None:
        raise NotImplementedError


class MinimizeButton(menu.ScreenButton):

    def __init__(
        self,
        fa: classes.FA,
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
        self.fa = fa
        super().__init__(
            label,
            emoji=emoji,
            style=style,
            disabled=disabled,
            custom_id=custom_id,
            row=row,
            position=position,
            autodefer=autodefer)

    def callback(self, context: miru.ViewContext) -> None:
        raise NotImplementedError


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
