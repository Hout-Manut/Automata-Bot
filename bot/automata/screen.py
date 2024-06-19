from __future__ import annotations

import asyncio
from datetime import timedelta

import hikari
import lightbulb
import miru
from miru.abc.item import InteractiveViewItem
from miru.ext import menu

from .classes import (
    FA,
    InputStringModal,
    EditFAModal,
    Color,
    ActionOptions,
    RegexPatterns,
    FAStringResult
)

from .buttons import (
    ConvertButton,
    MinimizeButton,
)


class AutomataMenu(menu.Menu):

    def __init__(
        self,
        *,
        timeout: float | int | timedelta | None = 300,
        autodefer: bool | miru.AutodeferOptions = True,
    ) -> None:
        super().__init__(timeout=timeout, autodefer=autodefer)

    async def on_timeout(self) -> None:
        self.clear_items()
        return await super().on_timeout()

    async def on_error(
        self,
        error: Exception,
        item: InteractiveViewItem | None = None,
        context: miru.ViewContext | None = None
    ) -> None:
        if context:
            await context.respond(
                "Something went wrong, please try again later.",
                flags=hikari.MessageFlag.EPHEMERAL
            )
        for item in self.children:
            item.disabled = True
        await self.update_message()


class MainScreen(menu.Screen):

    @menu.button(label="Test a String")
    async def test_string_callback(self, ctx: miru.ViewContext, btn: menu.ScreenButton) -> None:
        await self.menu.push(TestStringScreen(self.menu, self))

    # @menu.button(label="Convert to DFA")
    # async def convert_callback(self, ctx: miru.ViewContext, btn: menu.ScreenButton) -> None:
    #     await self.menu.push(TestStringScreen(self.menu, self))
    #     ...

    # @menu.button(label="Minimize DFA", custom_id="minimize")
    # async def minimize_callback(self, ctx: miru.ViewContext, btn: menu.ScreenButton) -> None:
    #     await self.menu.push(TestStringScreen(self.menu, self))
    #     ...


    def __init__(
        self,
        menu: menu.Menu,
        fa: FA | str,
        recent: str | None = None,
        inter: lightbulb.SlashContext | None = None
    ) -> None:
        if isinstance(fa, str):
            fa = self.get_fa_from_string()

        self.fa = fa
        self.recent = recent
        self.inter = inter



        super().__init__(menu)

        print("opahdolikahd")
        if fa.is_dfa:
            self.extra = MinimizeButton(fa)
            self.add_item(self.extra)
        elif fa.is_nfa:
            self.extra = ConvertButton(fa)
            self.add_item(self.extra)
        # match inter.invoked.name:
        #     case "string":
        #         asyncio.create_task(self.menu.push(TestStringScreen(self.menu, self)))
        #         self.menu.update_message()

    def get_fa_from_string(self) -> FA:
        ...

    async def build_content(self) -> menu.ScreenContent:
        return menu.ScreenContent(
            embed=self.get_fa_embed()
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

        embed.add_field("Initial State", fa.initial_state_str)

        name = "State" if len(fa.final_states) == 1 else "States"
        embed.add_field(f"Final {name}", fa.final_states_str)

        name = "Function" if len(fa.t_func) == 1 else "Functions"
        embed.add_field(f"Transition {name}", fa.t_func_str)

        embed.set_image(fa.get_diagram(image_ratio))
        if author_name or author_icon:
            embed.set_author(name=author_name, icon=author_icon)

        return embed

    async def invoke_test_string(self) -> None:
        await self.menu.push(TestStringScreen(self.menu, self))
        await self.menu.update_message()


    @menu.button(label="Edit", style=hikari.ButtonStyle.SECONDARY, row=1)
    async def edit_fa_callback(self, ctx: miru.ViewContext, btn: menu.ScreenButton) -> None:
        modal = EditFAModal(self.fa)
        await ctx.respond_with_modal(modal)
        await modal.wait()
        if not modal.ctx:
            await ctx.respond("timed out.", flags=hikari.MessageFlag.EPHEMERAL)
            return
        await modal.ctx.interaction.create_initial_response(
            hikari.ResponseType.DEFERRED_MESSAGE_CREATE
        )
        self.fa = modal.fa
        await self.menu.update_message(await self.build_content())
        await modal.ctx.interaction.delete_initial_response()


class TestStringScreen(menu.Screen):

    def __init__(self, menu: menu.Menu, main: MainScreen) -> None:
        self.main = main
        self.result = FAStringResult()
        super().__init__(menu)

    @property
    def color(self) -> Color:
        if self.result.is_accepted:
            return Color.GREEN
        else:
            return Color.RED

    async def get_user_response(self) -> hikari.MessageCreateEvent:
        def check(event: hikari.MessageCreateEvent) -> bool:
            is_author = event.author_id == self.menu.inter.author.id
            in_channel = event.channel_id == self.menu.inter.channel_id
            if not is_author or not in_channel:
                return False

            content = event.content
            has_valid_symbols = set(content).issubset(self.menu.fa.alphabets)
            if '-' not in self.menu.fa.alphabets:
                is_deleting = RegexPatterns.BACKSPACE.match(content)
            else:
                is_deleting = False

            return has_valid_symbols or is_deleting

        user_input = await self.menu.inter.bot.wait_for(
            hikari.MessageCreateEvent, predicate=check, timeout=300
        )
        return user_input

    async def build_content(self) -> menu.ScreenContent:
        embeds = [self.main.get_fa_embed("0.28125"), self.get_embed()]
        return menu.ScreenContent(
            embeds=embeds
        )

    def get_embed(self) -> hikari.Embed:
        embed = hikari.Embed(
            title="Test String",
            color=self.color
        )
        string = "ε" if self.result.string == "" else self.result.string
        embed.add_field("String", f"`{string}`")

        is_passed = "✅" if self.result.is_accepted else "❌"
        embed.add_field("Result", is_passed)
        return embed

    @menu.button(label="Edit String")
    async def edit_callback(self, ctx: miru.ViewContext, btn: menu.ScreenButton) -> None:
        modal = InputStringModal(self.main.fa, self.result.string)
        await ctx.respond_with_modal(modal)
        await modal.wait()
        await modal.ctx.interaction.create_initial_response(
            hikari.ResponseType.DEFERRED_MESSAGE_CREATE
        )
        self.result = modal.result
        await self.menu.update_message(await self.build_content())
        await modal.ctx.interaction.delete_initial_response()

    @menu.button(label="Back", style=hikari.ButtonStyle.SECONDARY)
    async def back_callback(self, ctx: miru.ViewContext, btn: menu.ScreenButton) -> None:
        await self.menu.pop()
