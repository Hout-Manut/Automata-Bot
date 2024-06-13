import hikari
import lightbulb
import miru

class TestStringButton(miru.Button):

    def __init__(
        self,
        testable: bool | None = None,
        label: str = "Test a String",
        *,
        emoji: hikari.Emoji | str | None = None,
        style: hikari.InteractiveButtonTypesT = hikari.ButtonStyle.SECONDARY,
        disabled: bool | None = None,
        custom_id: str | None = None,
        row: int = 0,
        position: int | None = None,
        autodefer: (
            bool | miru.AutodeferOptions | hikari.UndefinedType
        ) = hikari.UNDEFINED,
    ) -> None:
        disabled = False if testable is None else not testable

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


class ConvertButton(miru.Button):

    def __init__(
        self,
        convertable: bool | None = None,
        label: str = "Convert to DFA",
        *,
        emoji: hikari.Emoji | str | None = None,
        style: hikari.InteractiveButtonTypesT = hikari.ButtonStyle.SECONDARY,
        disabled: bool | None = None,
        custom_id: str | None = None,
        row: int = 0,
        position: int | None = None,
        autodefer: (
            bool | miru.AutodeferOptions | hikari.UndefinedType
        ) = hikari.UNDEFINED,
    ) -> None:
        disabled = (
            (True if self.view.fa.is_dfa else False)
            if convertable is None
            else not convertable
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


class MinimizeButton(miru.Button):

    def __init__(
        self,
        minimizeable: bool | None = None,
        label: str = "Minimize a DFA",
        *,
        emoji: hikari.Emoji | str | None = None,
        style: hikari.InteractiveButtonTypesT = hikari.ButtonStyle.SECONDARY,
        disabled: bool | None = None,
        custom_id: str | None = None,
        row: int = 0,
        position: int | None = None,
        autodefer: (
            bool | miru.AutodeferOptions | hikari.UndefinedType
        ) = hikari.UNDEFINED,
    ) -> None:
        disabled = (
            (True if self.view.fa.is_minimized else False)
            if minimizeable is None
            else not minimizeable
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