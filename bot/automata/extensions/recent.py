"""
This module is used to get user's recent FA datas to fill in the recent option in most commands so they can select them there.
User can manage recent FA data here.
"""

import asyncio
from datetime import datetime, timedelta

import hikari
import lightbulb
import miru
from hikari.commands import CommandChoice
from mysql.connector.cursor import MySQLCursor
from mysql.connector import Error as SQLError

import bot.automata as automata
from ._history_autocomplete import history_autocomplete


recent_plugin = lightbulb.Plugin('recent')


class RecentView(miru.View):

    def __init__(
        self,
        ctx: lightbulb.SlashContext,
        *,
        timeout: float | int | timedelta | None = 120,
        autodefer: bool | miru.AutodeferOptions = True
    ) -> None:
        self.ctx = ctx
        fa, db_data = automata.FA.get_db_fa_data(ctx)
        self.fa = fa
        self.db_data = db_data
        self.deleted = False
        super().__init__(timeout=timeout, autodefer=autodefer)

    async def update(self) -> None:
        embeds = []
        if not self.deleted:
            embed = hikari.Embed(
                title="Manage Recent Automation Data",
                color=automata.classes.Color.LIGHT_BLUE
            ).add_field(
                "Saved As",
                self.db_data['fa_name']
            )
        else:
            embed = hikari.Embed(
                title="Manage Recent Automation Data",
                description="Automation data has been deleted.",
            )
        embeds.append(embed)
        embeds.append(self.fa.get_embed(with_diagram=False))

        await self.ctx.interaction.edit_initial_response(
            embeds=embeds,
            components=self,
        )

    @miru.button(label="Rename", style=hikari.ButtonStyle.SECONDARY)
    async def rename_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        modal = RenameModal(self.db_data)
        await ctx.respond_with_modal(modal)
        await modal.wait()
        if not modal.ctx:
            return
        await modal.ctx.interaction.create_initial_response(
            hikari.ResponseType.DEFERRED_MESSAGE_CREATE
        )
        new_name = modal.new_fa_name or self.db_data['fa_name']
        self.db_data['fa_name'] = new_name
        self.rename_in_db()

        await modal.ctx.interaction.delete_initial_response()
        await self.update()

    @miru.button(label="Edit", style=hikari.ButtonStyle.SECONDARY)
    async def edit_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        modal = automata.EditFAModal(self.fa)
        await ctx.respond_with_modal(modal)
        await modal.wait()
        if not modal.ctx:
            return
        await modal.ctx.interaction.create_initial_response(
            hikari.ResponseType.DEFERRED_MESSAGE_CREATE
        )
        self.fa = modal.fa
        self.edit_in_db()

        await modal.ctx.interaction.delete_initial_response()
        await self.update()

    @miru.button(label="Delete", style=hikari.ButtonStyle.DANGER)
    async def delete_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        self.delete_from_db()
        self.deleted = True
        for item in self.children:
            item.disabled = True
        await self.update()
        await asyncio.sleep(10)

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        await self.update()

    def rename_in_db(self) -> None:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            cursor: MySQLCursor = self.ctx.app.d.cursor
            update_query = """
                UPDATE Recent
                SET
                    fa_name=%s,
                    updated_at=%s
                WHERE
                    id=%s AND
                    user_id=%s
            """
            update_data = (
                self.db_data['fa_name'], current_time, self.db_data['id'], self.ctx.user.id)
            cursor.execute(update_query, update_data)
            self.ctx.app.d.db.commit()
        except SQLError as e:
            raise automata.AutomataError(e)

    def edit_in_db(self) -> None:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        values = self.fa.get_values()

        user_id = self.ctx.user.id
        states = values["states"]
        alphabets = values["alphabets"]
        initial_state = values["initial_state"]
        final_states = values["final_states"]
        tf = values["tf"]  # Transition functions

        try:
            cursor: MySQLCursor = self.ctx.app.d.cursor
            update_query = """
                UPDATE Recent
                SET
                    states = %s,
                    alphabets = %s,
                    initial_state = %s,
                    final_states = %s,
                    transitions = %s,
                    updated_at=%s
                WHERE
                    id=%s AND
                    user_id=%s
            """
            update_data = (
                states, alphabets, initial_state, final_states, tf, current_time,
                self.db_data['id'], user_id,
            )
            cursor.execute(update_query, update_data)
            self.ctx.app.d.db.commit()
        except SQLError as e:
            raise automata.AutomataError(e)

    def delete_from_db(self) -> None:
        try:
            cursor: MySQLCursor = self.ctx.app.d.cursor
            delete_query = """
                DELETE FROM Recent
                WHERE
                    id=%s AND
                    user_id=%s
            """
            delete_data = (self.db_data['id'], self.ctx.user.id)
            cursor.execute(delete_query, delete_data)
            self.ctx.app.d.db.commit()
        except SQLError as e:
            raise automata.AutomataError(e)


class RenameModal(miru.Modal):

    _fa_name = miru.TextInput(
        label="FA Name",
        placeholder="",
        value="",
        max_length=80,  # Limit to 80 characters because Discord's limit is 100
    )                   # and we need room to add delta time too.

    def __init__(
        self,
        db: dict[str, str],
    ) -> None:
        self.db = db
        self._fa_name.placeholder = db['fa_name']
        self._fa_name.value = db['fa_name']
        self.new_fa_name = None

        super().__init__(title="Edit FA Name", timeout=300)

    async def callback(self, ctx: miru.ModalContext) -> None:
        self.new_fa_name = self._fa_name.value or self.db['fa_name']
        self.ctx = ctx
        self.stop()


@recent_plugin.command
@lightbulb.option('recent', 'Your recent FA inputs', autocomplete=True, required=True)
@lightbulb.command('recent', 'Manage your recent FAs')
@lightbulb.implements(lightbulb.SlashCommand)
async def recent_cmd(ctx: lightbulb.SlashContext) -> None:
    await ctx.interaction.create_initial_response(
        hikari.ResponseType.DEFERRED_MESSAGE_CREATE
    )

    view = RecentView(ctx, timeout=600)
    await view.update()
    ctx.app.d.miru.start_view(view)
    await view.wait()


@recent_cmd.autocomplete("recent")
async def autocomplete_history(
    opt: hikari.AutocompleteInteractionOption,
    inter: hikari.AutocompleteInteraction,
) -> list[CommandChoice]:
    return await history_autocomplete(opt, inter, recent_plugin)


def load(bot: lightbulb.BotApp):
    bot.add_plugin(recent_plugin)
