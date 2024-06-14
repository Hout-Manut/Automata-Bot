from __future__ import annotations

import re
from datetime import timedelta

import hikari
import hikari.errors
import lightbulb
import miru

from . import buttons
from .classes import FA, Color, FAStringResult
from .extensions import error_handler as error


class ActionOptions(int):
    DESIGN = 0
    TEST_FA = 1
    TEST_STRING = 2
    CONVERT_TO_DFA = 3
    MINIMIZE_DFA = 4


class FAView(miru.View):

    BACKSPACE_PATTERN = re.compile(r"-(\d+)\s*$")

    def __init__(
        self,
        inter: lightbulb.SlashContext,
        fa: FA,
        *,
        mode: int | ActionOptions = ActionOptions.DESIGN,
        testable: bool | None = None,
        convertable: bool | None = None,
        minimizable: bool | None = None,
        savable: bool | None = None,
        editable: bool = True,
        exitable: bool = True,
        timeout: float | int | timedelta | None = 600,
        autodefer: bool | miru.AutodeferOptions = True
    ) -> None:

        self.inter = inter
        self.fa = fa
        self.mode = mode

        self.test_button = buttons.TestStringButton(testable)
        self.convert_button = buttons.ConvertButton(convertable)
        self.minimize_button = buttons.MinimizeButton(minimizable)
        self.save_button = buttons.SaveButton(savable)
        self.edit_button = buttons.EditButton(editable)
        self.exit_button = buttons.ExitButton(exitable)

        self.test_result: FAStringResult = FAStringResult(fa)

        self = (
            self.add_item(self.test_button)
            .add_item(self.convert_button)
            .add_item(self.minimize_button)
            .add_item(self.save_button)
            .add_item(self.edit_button)
            .add_item(self.exit_button)
        )

        super().__init__(timeout=timeout, autodefer=autodefer)

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

    def update_buttons(self, disable: bool = False) -> None:
        if disable:
            for item in self.children:
                item.disabled = True
            return

        self.test_button.disabled = False
        self.convert_button.disabled = True if self.fa.is_dfa else False
        try:
            self.minimize_button.disabled = True if self.fa.is_minimized else False
        except error.InvalidDFAError:
            self.minimize_button.disabled = True

    async def response(self, mode: int | ActionOptions | None = None) -> None:
        self.mode = mode if not mode else self.mode

        embeds: list[hikari.Embed] = []

        match self.mode:
            case ActionOptions.DESIGN:
                embeds.append(self.get_fa_embed())
            case ActionOptions.TEST_FA:
                result = "Determined" if self.fa.is_dfa else "Non-Determined"
                embed = hikari.Embed(
                    title="This is a",
                    description=f"**{result}** Finite Automation."
                )
                embeds.append(embed)
                embeds.append(self.get_fa_embed())
            case ActionOptions.TEST_STRING:
                color = Color.GREEN if self.test_result.is_accepted else Color.RED
                embed = hikari.Embed(
                    title="String Test",
                    color=color
                )
                status = "Accepted." if self.test_result.is_accepted else "Not accepted."
                embed.add_field("Status", status)
                string = self.test_result.string
                string = "ε" if string == "" else string
                embed.add_field("String", string)
                note = "Send messages to enter. (-{num} to backspace)"
                embeds.append(embed)
                embeds.append(self.get_fa_embed("16/9", note))
            case ActionOptions.CONVERT_TO_DFA:
                raise NotImplementedError
            case ActionOptions.MINIMIZE_DFA:
                raise NotImplementedError
            case _:
                raise error.AutomataError

        self.update_buttons()
        try:
            await self.inter.interaction.create_initial_response(
                hikari.ResponseType.MESSAGE_CREATE,
                embeds=embeds,
                components=self
            )
        except hikari.errors.NotFoundError:
            await self.inter.interaction.edit_initial_response(embeds=embeds, components=self)

    async def view_check(self, ctx: miru.ViewContext) -> bool:
        return ctx.author.id == self.inter.author.id

    async def get_user_response(self) -> hikari.MessageCreateEvent:
        def check(event: hikari.MessageCreateEvent) -> bool:
            is_author = event.author_id == self.inter.author.id
            in_channel = event.channel_id == self.inter.channel_id
            if not is_author or not in_channel:
                return False

            content = event.content
            has_valid_symbols = set(content).issubset(self.fa.alphabets)
            if '-' not in self.fa.alphabets:
                is_deleting = self.BACKSPACE_PATTERN.match(content)
            else:
                is_deleting = False

            return has_valid_symbols or is_deleting

        user_input = await self.inter.bot.wait_for(
            hikari.MessageCreateEvent, predicate=check, timeout=300
        )
        return user_input

    async def test_string_callback(self) -> None:
        ...

    async def test_fa_callback(self) -> None:
        ...

    async def convert_to_dfa_callback(self) -> None:
        ...

    async def minimize_dfa_callback(self) -> None:
        ...

    async def save_fa_callback(self) -> None:
        ...

    async def edit_fa_callback(self) -> None:
        ...

    async def cancel_callback(self) -> None:
        await self.inter.interaction.edit_initial_response(
            self.get_fa_embed(),
            components=[]
        )
        self.stop()

    async def on_timeout(self) -> None:
        await self.inter.interaction.edit_initial_response(
            self.get_fa_embed(),
            components=[]
        )
