from __future__ import annotations

from datetime import timedelta

import hikari
import lightbulb
import miru
from miru.abc.item import InteractiveViewItem
from miru.ext import menu as miru_menu

from .extensions.error_handler import InvalidDBQuery, NotMinimizeable
from .buttons import ConvertButton, MinimizeButton
from .classes import (
    Color,
    EditFAModal,
    FA,
    FAStringResult,
    InputStringModal,
    RegexPatterns,
)


class AutomataMenu(miru_menu.Menu):

    def __init__(
        self,
        fa: FA,
        ctx: lightbulb.SlashContext,
        *,
        timeout: float | int | timedelta | None = 300,
    ) -> None:
        self._fa = fa
        self.ctx = ctx
        super().__init__(timeout=timeout)

    @property
    def fa(self) -> FA:
        return self._fa

    @fa.setter
    def fa(self, value: FA) -> None:
        self._fa = value

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
            if isinstance(error, NotMinimizeable):
                await context.respond(
                    "Something went wrong, please try again later.",
                    flags=hikari.MessageFlag.EPHEMERAL
                )
                return
            elif isinstance(error, InvalidDBQuery):
                error_embed = hikari.Embed(
                    title="Error",
                    description="Invalid FA id provided.",
                    color=Color.RED
                )
                await context.respond(error_embed, flags=hikari.MessageFlag.EPHEMERAL)
                return
        for item in self.children:
            item.disabled = True
        await self.update_message()

    async def view_check(self, context: miru.ViewContext) -> bool:
        return context.user.id == self.ctx.author.id


class MainScreen(miru_menu.Screen):

    @miru_menu.button(label="Test a String")
    async def test_string_callback(self, ctx: miru.ViewContext, btn: miru_menu.ScreenButton) -> None:
        await self.menu.push(TestStringScreen(self.menu, self))

    # @miru_menu.button(label="Convert to DFA")
    # async def convert_callback(self, ctx: miru.ViewContext, btn: menu.ScreenButton) -> None:
    #     await self.menu.push(TestStringScreen(self.menu, self))
    #     ...

    # @miru_menu.button(label="Minimize DFA", custom_id="minimize")
    # async def minimize_callback(self, ctx: miru.ViewContext, btn: menu.ScreenButton) -> None:
    #     await self.menu.push(TestStringScreen(self.menu, self))
    #     ...

    def __init__(
        self,
        menu: AutomataMenu,
    ) -> None:
        super().__init__(menu)

        self.conversion_result = None
        self.minimization_result = None

        if self.menu.ctx.invoked.name == "nfa_to_dfa":
            if self.menu.fa.is_nfa:
                new_fa, result = self.menu.fa.convert()
                self.conversion_result = result
                self.menu.fa = new_fa

        if self.menu.ctx.invoked.name == "dfa":
            if self.menu.fa.is_dfa:
                self.minimizeable = self.menu.fa.is_minimizable
                if self.minimizeable:
                    new_fa, result = self.menu.fa.minimize()
                    self.minimization_result = result
                    self.menu.fa = new_fa

        if self.menu.fa.is_dfa:
            self.extra = MinimizeButton(self.menu.fa)
        else:
            self.extra = ConvertButton()
        self.add_item(self.extra)

    @property
    def menu(self) -> AutomataMenu:
        return super().menu

    def change_button(self) -> None:
        self.remove_item(self.extra)
        self.extra = MinimizeButton(self.menu.fa)
        self.add_item(self.extra)

    async def build_content(self, extra_embeds: hikari.Embed | None = None) -> miru_menu.ScreenContent:
        embeds = [self.menu.fa.get_embed()]
        if extra_embeds:
            embeds.append(extra_embeds)

        if self.menu.ctx.invoked.name == "fa":
            result = "Deterministic" if self.menu.fa.is_dfa else "Non-Deterministic"
            embed = hikari.Embed(
                title="Finite Automation Test",
                color=Color.LIGHT_BLUE
            ).add_field(
                "Result",
                f"**{result}**"
            )
            embeds.append(embed)
        elif self.menu.ctx.invoked.name == "dfa":
            if self.menu.fa.is_nfa:
                embed = hikari.Embed(
                    title="Automata Minimization",
                    description="Can't minimize a non-deterministic automata.",
                    color=Color.RED
                )
                embeds.append(embed)
            elif self.minimization_result:
                embeds.append(self.minimization_result.get_embed())
            else:
                embed = hikari.Embed(
                    title="Automata Minimization",
                    description="This DFA is not minimizable.",
                    color=Color.RED
                )
                embeds.append(embed)

        elif self.menu.ctx.invoked.name == "nfa_to_dfa":
            if self.menu.fa.is_dfa:
                embed = hikari.Embed(
                    title="Automata Conversion",
                    description="Cannot convert an already deterministic automata.",
                    color=Color.RED
                )
                embeds.append(embed)
            elif self.conversion_result:
                embeds.append(self.conversion_result.get_embed())

        return miru_menu.ScreenContent(
            embeds=embeds
        )

    @miru_menu.button(label="Edit", style=hikari.ButtonStyle.SECONDARY, row=1)
    async def edit_fa_callback(self, ctx: miru.ViewContext, btn: miru_menu.ScreenButton) -> None:
        modal = EditFAModal(self.menu.fa)
        await ctx.respond_with_modal(modal)
        await modal.wait()
        if not modal.ctx:
            await ctx.respond("timed out.", flags=hikari.MessageFlag.EPHEMERAL)
            return
        await modal.ctx.interaction.create_initial_response(
            hikari.ResponseType.DEFERRED_MESSAGE_CREATE
        )
        self.menu.fa = modal.fa
        await self.menu.update_message(await self.build_content())
        await modal.ctx.interaction.delete_initial_response()

    async def minimize_callback(self, ctx: miru.ViewContext, btn: miru_menu.ScreenButton) -> None:
        self.menu.fa.minimize()
        self.extra.disabled = True
        await self.menu.update_message(await self.build_content())


class TestStringScreen(miru_menu.Screen):

    def __init__(self, menu: AutomataMenu, main: MainScreen | None = None) -> None:
        self.main = main
        self.result = FAStringResult()
        super().__init__(menu)

    @property
    def menu(self) -> AutomataMenu:
        return super().menu

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

    async def build_content(self) -> miru_menu.ScreenContent:
        embeds = [self.menu.fa.get_embed("0.28125"), self.get_embed()]
        return miru_menu.ScreenContent(
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

    @miru_menu.button(label="Edit String")
    async def edit_callback(self, ctx: miru.ViewContext, btn: miru_menu.ScreenButton) -> None:
        modal = InputStringModal(self.menu.fa, self.result.string)
        await ctx.respond_with_modal(modal)
        await modal.wait()
        await modal.ctx.interaction.create_initial_response(
            hikari.ResponseType.DEFERRED_MESSAGE_CREATE
        )
        self.result = modal.result
        await self.menu.update_message(await self.build_content())
        await modal.ctx.interaction.delete_initial_response()

    @miru_menu.button(label="Back", style=hikari.ButtonStyle.SECONDARY)
    async def back_callback(self, ctx: miru.ViewContext, btn: miru_menu.ScreenButton) -> None:
        if self.main:
            await self.menu.pop()
        else:
            await self.menu.push(MainScreen(self.menu))
