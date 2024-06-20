from __future__ import annotations

import os
import re
import time
from datetime import datetime, timedelta

import graphviz
import hikari
import lightbulb
import miru
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import mysql.connector.cursor

from .extensions import error_handler as error


transitionT = dict[tuple[str, str], set[str]]


class Color(int):
    RED = 0xff6459
    GREEN = 0xa2e57b
    LIGHT_BLUE = 0x55c7f1
    YELLOW = 0xf2ee78


class ActionOptions(int):
    DESIGN = 0
    TEST_FA = 1
    TEST_STRING = 2
    CONVERT_TO_DFA = 3
    MINIMIZE_DFA = 4


class RegexPatterns:
    BACKSPACE = re.compile(r"-(\d+)\s*$")

    STATES = re.compile(r"\b\w+\b")
    ALPHABETS = re.compile(r"\w+")
    INITIAL_STATE = re.compile(r"\b\w+\b")
    FINAL_STATES = re.compile(r"\b\w+\b")
    TF = re.compile(r"\b(\w+)\s*[,\s]\s*(\w+)\s*(=|>|->)\s*(\w+)\b")


class FA:
    """
    Class representing a Finite Automaton (FA).
    """

    def __init__(
        self,
        states: set[str] = set(),
        alphabets: set[str] = set(),
        initial_state: str = "",
        final_states: set[str] = set(),
        transition_functions: dict[tuple[str, str], set[str]] = {},
        ctx: lightbulb.SlashContext | None = None,
    ) -> None:
        """
        Initialize a new FA instance.

        Args:
            states (set[str]): The set of states in the FA.
            alphabets (set[str]): The set of input symbols in the FA.
            initial_state (str): The start state in the FA.
            final_states (set[str]): The set of accepted states in the FA.
            transition_functions (dict[tuple[str, str], set[str]]): The transition function in the FA.
            ctx (lightbulb.Context | None): The context of the command used. Defaults to None.

        Raises:
            error.InvalidFAError: If the provided FA data is invalid.
        """
        if not self.check_valid(
            states,
            alphabets,
            initial_state,
            final_states,
            transition_functions,
        ):
            raise error.InvalidFAError("Invalid FA data provided.")

        if self.check_dfa(
            states, alphabets, initial_state, final_states, transition_functions
        ):
            self.is_dfa = True
        else:
            self.is_dfa = False

        self.states = states
        self.alphabets = alphabets
        self.initial_state = initial_state
        self.final_states = final_states
        self.transition_functions = transition_functions
        self.ctx = ctx

    def save_to_db(self, ctx: lightbulb.SlashContext | None = None) -> None:
        if not ctx:
            ctx = self.ctx

        template = "{fa} with {num_states} states, {num_alphabets} inputs. Starts at {initial_state}."

        values = self.get_values()

        user_id = ctx.user.id
        states = values["states"]
        alphabets = values["alphabets"]
        initial_state = values["initial_state"]
        final_states = values["final_states"]
        tf = values["tf"]

        fa_type = "An NFA" if self.is_nfa else "A DFA"
        num_states = len(self.states)
        num_alphabets = len(self.alphabets)

        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        fa_name = template.format(
            fa=fa_type,
            num_states=num_states,
            num_alphabets=num_alphabets,
            initial_state=initial_state,
        )

        try:
            cursor: mysql.connector.cursor.MySQLCursor = ctx.app.d.cursor

            sql_query = """
            INSERT INTO Recent (
                user_id,
                fa_name,
                states,
                alphabets,
                initial_state,
                final_states,
                transitions,
                updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            # sql_query = 'SELECT * FROM History;'

            data = (user_id, fa_name, states, alphabets,
                    initial_state, final_states, tf, date)
            cursor.execute(sql_query, data)

            ctx.app.d.db.commit()

            # for row in cursor:
            #     print(row)

        except Error as e:
            print(f'Inserting data unsucessfully: {e}')

    @property
    def is_nfa(self) -> bool:
        return not self.is_dfa

    @property
    def author_id(self) -> int:
        """The id of the user who created the FA"""
        if self.ctx:
            return self.ctx.author.id
        return 0

    @property
    def author_name(self) -> str:
        """The name of the user who created the FA"""
        if self.ctx:
            return self.ctx.author.username
        return "Unknown"

    @property
    def states_str(self) -> str:
        """
        A string representation of the set of states of the FA.
        """
        states = list(self.states)
        states.sort()
        return f"{{`{'`, `'.join(states)}`}}"

    @property
    def alphabets_str(self) -> str:
        """
        A string representation of the set of alphabets of the FA.
        """
        alphabets = list(self.alphabets)
        alphabets.sort()
        return f"{{`{'`, `'.join(alphabets)}`}}"

    @property
    def initial_state_str(self) -> str:
        """
        A string representation of the initial state of the FA.
        """
        return f"`{self.initial_state}`"

    @property
    def final_states_str(self) -> str:
        """
        A string representation of the set of final stsates of the FA.
        """
        final_states = list(self.final_states)
        final_states.sort()
        return f"{{`{'`, `'.join(final_states)}`}}"

    @property
    def transition_functions_str(self) -> str:
        """
        A string representation of the transition functions of the FA.
        """
        tf = ""
        if self.is_dfa:
            for (from_state, symbol), to_state in self.transition_functions.items():
                symbol = "ε" if symbol == "" else symbol
                tf += f"(`{from_state}`, `{symbol}`) -> `{to_state.pop()}`\n"
        else:
            for (from_state, symbol), to_states in self.transition_functions.items():
                symbol = "ε" if symbol == "" else symbol
                tf += f"(`{from_state}`, `{symbol}`) -> {{`{'`, `'.join(to_states)}`}}\n"
        return tf

    @property
    def t_func(self) -> dict[tuple[str, str], set[str]]:
        """
        An alias for `transition_functions`.
        """
        return self.transition_functions

    @property
    def t_func_str(self) -> str:
        """
        An alias for `transition_functions_str`.
        """
        return self.transition_functions_str

    @property
    def is_minimized(self) -> bool:
        """
        Returns True if the FA has been minimized once already.
        """
        if self.is_nfa:
            raise error.InvalidFAError("The FA is not a DFA.")

        raise NotImplementedError

    def nfa_to_dfa(self) -> FA:
        """
        Convert the NFA to a DFA.

        Returns:
            DFA: The new DFA.

        Raises:
            error.InvalidFAError: If the FA is not an NFA.
        """
        if self.is_dfa:
            raise error.InvalidFAError("The FA is already a DFA.")

        raise NotImplementedError

    def minimize(self) -> FA:
        """
        Minimize the DFA.

        returns:
            DFA: The minimized DFA as a new object.

        Raises:
            error.InvalidFAError: If the FA is not an DFA.
            error.NotMinimizableError: If the DFA can not be minimized.
        """
        if self.is_nfa:
            raise error.InvalidFAError("The FA is not a DFA.")

        raise NotImplementedError

    def get_values(self) -> dict[str, str]:
        states = list(self.states)
        states.sort()
        states_str = " ".join(states)

        alphabets = list(self.alphabets)
        alphabets.sort()
        alphabets_str = " ".join(alphabets)

        final_states = list(self.final_states)
        final_states.sort()
        final_states_str = " ".join(final_states)

        buffer = []
        for (s_state, symbol), n_states in self.transition_functions.items():
            for n_state in n_states:
                buffer.append(f"{s_state},{symbol}={n_state}")

        tf = "|".join(buffer)

        return {
            "states": states_str,
            "alphabets": alphabets_str,
            "initial_state": self.initial_state,
            "final_states": final_states_str,
            "tf": tf,
        }


    def get_embed(
        self,
        image_ratio: str = "1",
        author_name: str | None = None,
        author_icon: hikari.Resourceish | None = None
    ) -> hikari.Embed:

        title = "Deterministic" if self.is_dfa else "Non-deterministic"
        title += " Finite Automation"
        embed = hikari.Embed(
            title=title,
            description=None,
            color=Color.LIGHT_BLUE
        )

        name = "State" if len(self.states) == 1 else "States"
        embed.add_field(name, self.states_str)

        name = "Alphabet" if len(self.alphabets) == 1 else "Alphabets"
        embed.add_field(name, self.alphabets_str)

        embed.add_field("Initial State", self.initial_state_str)

        name = "State" if len(self.final_states) == 1 else "States"
        embed.add_field(f"Final {name}", self.final_states_str)

        name = "Function" if len(self.t_func) == 1 else "Functions"
        embed.add_field(f"Transition {name}", self.t_func_str)

        embed.set_image(self.get_diagram(image_ratio))
        if author_name or author_icon:
            embed.set_author(name=author_name, icon=author_icon)

        return embed

    def get_diagram(self, ratio: str = "1") -> hikari.File:
        """
        Get the diagram for the FA.

        Returns:
            hikari.File: The diagram for the FA.
        """
        path = self.draw_diagram(ratio=ratio)
        return hikari.File(path, filename="automata.png")

    def draw_diagram(self, ratio: str = "1") -> str:
        """
        Draw the FA as a diagram.

        Returns:
            str: The path to the diagram.
        """
        file_name = self.author_name
        margin = "0" if ratio == "1" else "5"
        graph = graphviz.Digraph(
            format="png",
            graph_attr={
                "bgcolor": "#383a40",
                # "color": "transparent",
                "fillcolor": "#383a40",
                "size": "10,10",
                "ratio": ratio,
                "dpi": "200",
                "center": "true",
                "beautify": "true",
                "smoothing": "avg_dist",
                "orientation": "90",
            },
        )
        with graph.subgraph(name="cluster_0") as c:
            c.attr = {
                "shape": "square",
                "bgcolor": "#3a4348",
            }
            c.node_attr = {
                "color": "#ffffff",
                "fillcolor": "transparent",
                "fontcolor": "#ffffff"
            }
            c.edge_attr = {
                "color": "#ffffff",
                "fontcolor": "#ffffff",
                "len": "1"
            }
            for state in self.states:
                if state in self.final_states:
                    c.node(state, shape="doublecircle")
                else:
                    c.node(state, shape="circle")
            c.node("", shape="point")
            c.edge("", self.initial_state)
            for (state, symbol), next_states in self.transition_functions.items():
                symbol = "ε" if symbol == "" else symbol
                for next_state in next_states:
                    c.edge(state, next_state, symbol)

        graph.render(f"storage/graph_cache/{file_name}")
        return f"storage/graph_cache/{file_name}.png"

    def check_string(self, string: str) -> FAStringResult:
        """
        Check if a string is accepted by the FA.

        Args:
            string (str): The string to check.

        Returns:
            bool: True if the string is accepted, else False.
        """

        def dfs(current_state: str, remaining_str: str) -> bool:
            if not remaining_str:
                return current_state in self.final_states

            if (current_state, "") in self.t_func:
                next_states = self.transitions[(current_state, "")]
                for next_state in next_states:
                    accepted = dfs(next_state, remaining_str)
                    if accepted:
                        return True

            symbol = remaining_str[0]
            remaining_str = remaining_str[1:]

            if (current_state, symbol) in self.t_func:
                next_states = self.t_func[(current_state, symbol)]
                for next_state in next_states:
                    accepted = dfs(next_state, remaining_str)
                    if accepted:
                        return True

            return False

        passed = dfs(self.initial_state, string)
        return FAStringResult(self, string, passed)

    @staticmethod
    def check_valid(
        states: set[str],
        alphabets: set[str],
        initial_state: str,
        final_states: set[str],
        transition_functions: dict[tuple[str, str], set[str]],
    ) -> bool:
        """
        Determine if a given FA is valid.

        Returns:
            bool: True if the FA is valid, else False.
        """

        # Check the initial and end states if they're in the set of all states"""
        if initial_state not in states:
            return False
        if not final_states.issubset(states):
            return False

        for (from_state, symbol), to_states in transition_functions.items():
            if from_state not in states:
                return False
            if symbol != "" and symbol not in alphabets:  # ε
                return False
            if not to_states.issubset(states):
                return False

        return True

    @staticmethod
    def check_dfa(
        states: set[str],
        inputs: set[str],
        initial: str,
        finals: set[str],
        transitions: dict[tuple[str, str], set[str]],
    ) -> bool:
        """
        Determine if a given FA is an NFA or a DFA.

        Args:
            states (set): The set of states.
            inputs (set): The set of imput symbols.
            initial (str): The start state.
            finals (set): The set of accept states.
            transitions (dict): The transition functions as a dictionary where the keys are (state, symbol) and values are set of next states

        Returns:
            bool: True if the FA is DFA, False if it is an NFA.
        """
        for state in states:
            for symbol in inputs:
                if (state, symbol) not in transitions:
                    return False  # Missing transitions: NFA
                next_states = transitions[(state, symbol)]
                if len(next_states) != 1:
                    return False  # Transition of a state and symbol leads to 0 or more than 1 states: NFA

        return True

    @staticmethod
    def get_fa_from_db(fa_id : int,ctx: lightbulb.SlashContext) -> FA:
        try:
            cursor: mysql.connector.cursor.MySQLCursor = ctx.app.d.cursor
            query = """
                SELECT
                    states,
                    alphabets,
                    initial_state,
                    final_states,
                    transitions
                FROM Recent
                WHERE
                    id=%s
                AND
                    user_id=%s;
            """
            cursor.execute(query, (str(fa_id), ctx.user.id))
            result = cursor.fetchone()
            if result is None:
                raise error.UserError

            states_str = str(result[0])
            alphabets_str = str(result[1])
            initial_state = str(result[2])
            final_states_str = str(result[3])
            transitions_str = str(result[4])

            states = RegexPatterns.STATES.findall(states_str)
            alphabets = RegexPatterns.ALPHABETS.findall(alphabets_str)
            final_states = RegexPatterns.STATES.findall(final_states_str)

            transitions: transitionT = {}
            values =  transitions_str.split("|")
            for value in values:
                match = RegexPatterns.TF.match(value.strip())
                if match:
                    k0, k1, _, v = match.groups()
                    if (k0, k1) in transitions:
                        transitions[(k0, k1)].add(v)
                    else:
                        transitions[(k0, k1)] = {v}

            fa = FA(
                states=set(states),
                alphabets=set(alphabets),
                initial_state=initial_state,
                final_states=set(final_states),
                transition_functions=transitions,
                ctx=ctx,
            )
            return fa
        except Error as e:
            raise error.AutomataError("Something went wrong while fetching the FA from the database.: " + e.args[1])

    @staticmethod
    async def ask_or_get_fa(ctx: lightbulb.SlashContext) -> FA:
        """
        Get the FA from the context depends on the command usage.

        Either ask the user with a modal or retrieve the data from the database.

        Args:
            ctx (SlashContext): The context of the command.

        Returns:
            FA: The FA instance.
        """
        try:
            recent: str = ctx.options.recent
            if recent == "":
                raise AttributeError
            try:
                fa_id = int(recent)
            except ValueError:
                await ctx.respond("Invalid input.", flags=hikari.MessageFlag.EPHEMERAL)
                raise error.UserError
            if fa_id == 0:
                await ctx.respond("Funny.", flags=hikari.MessageFlag.EPHEMERAL)
                raise error.UserError

            return FA.get_fa_from_db(fa_id, ctx)
        except AttributeError:
            pass  # No recent data given, asking the user instead

        modal = InputFAModal()
        builder = modal.build_response(ctx.app.d.miru)
        await builder.create_modal_response(ctx.interaction)
        ctx.app.d.miru.start_modal(modal)
        await modal.wait()
        await modal.ctx.interaction.create_initial_response(
            hikari.ResponseType.DEFERRED_MESSAGE_CREATE,
        )
        await modal.ctx.interaction.delete_initial_response()
        fa = modal.fa
        return fa

    def __str__(self) -> str:
        return f"FA({self.states}, {self.alphabets}, {self.initial_state}, {self.final_states}, {self.transition_functions})"


class FAStringResult:
    def __init__(
        self,
        fa: FA | None = None,
        string: str | None = None,
        passed: bool = False,
        # last_state: str | None = None,
    ) -> None:
        self._string = string
        self.fa = fa
        self.passed = passed
        # self.last_state = last_states

    @property
    def string(self) -> str:
        return "" if self._string is None else self._string

    @string.setter
    def string(self, string: str) -> None:
        self._string = string

    @property
    def is_accepted(self) -> bool:
        return self.passed


class InputFAModal(miru.Modal):

    _states = miru.TextInput(
        label="States",
        placeholder="q0 q1 q2...",
        required=True,
        value="q0 q1",
    )
    _alphabets = miru.TextInput(
        label="Alphabets",
        placeholder="a b c...",
        required=True,
        value="a b",
    )
    _initial_state = miru.TextInput(
        label="Initial State",
        placeholder="q0",
        required=True,
        value="q0",
    )
    _final_states = miru.TextInput(
        label="Final State(s)",
        placeholder="q2...",
        required=True,
        value="q1",
    )
    _transition_functions = miru.TextInput(
        label="Transition Functions",
        placeholder="state,symbol(None for ε)=state\nq0,a=q1\nq0,=q2\n...",
        required=True,
        value="q0,a=q1\nq1,b=q0",
        style=hikari.TextInputStyle.PARAGRAPH,
    )

    def __init__(
        self,
        title: str | None = "Enter FA Data",
        *,
        custom_id: str | None = None,
        timeout: float | int | timedelta | None = 300,
    ) -> None:
        self.states = ""
        self.alphabets = ""
        self.initial_state = ""
        self.final_states = ""
        self.transition_functions = ""
        super().__init__(title, custom_id=custom_id, timeout=timeout)

    @property
    def ctx(self) -> miru.ModalContext:
        return self._ctx

    @property
    def is_dfa(self) -> bool:
        if not self.fa:
            raise error.InvalidFAError("No FA data provided.")
        return self.fa.is_dfa

    @property
    def states_value(self) -> set[str]:
        values = RegexPatterns.STATES.findall(self.states)
        return set(values)

    @property
    def alphabets_value(self) -> set[str]:
        values = RegexPatterns.ALPHABETS.findall(self.alphabets)
        return set(values)

    @property
    def initial_value(self) -> str:
        match = RegexPatterns.INITIAL_STATE.search(self.initial_state)
        return match.group(0) if match else ""

    @property
    def finals_value(self) -> set[str]:
        values = RegexPatterns.FINAL_STATES.findall(self.final_states)
        return set(values)

    @property
    def transitions_value(self) -> dict[tuple[str, str], set[str]]:
        transition_dict = {}

        values = self.transition_functions.split("\n")
        for value in values:
            match = RegexPatterns.TF.match(value.strip())
            if match:
                k0, k1, _, v = match.groups()
                if (k0, k1) in transition_dict:
                    transition_dict[(k0, k1)].add(v)
                else:
                    transition_dict[(k0, k1)] = {v}

        return transition_dict

    async def modal_check(self, ctx: miru.ModalContext) -> bool:
        self.states = ctx.values.get(self._states)
        self.alphabets = ctx.values.get(self._alphabets)
        self.initial_state = ctx.values.get(self._initial_state)
        self.final_states = ctx.values.get(self._final_states)
        self.transition_functions = ctx.values.get(self._transition_functions)

        return FA.check_valid(
            self.states_value,
            self.alphabets_value,
            self.initial_value,
            self.finals_value,
            self.transitions_value,
        )

    async def callback(self, ctx: miru.ModalContext) -> None:
        self.fa = FA(
            self.states_value,
            self.alphabets_value,
            self.initial_value,
            self.finals_value,
            self.transitions_value,
            ctx,
        )
        self._ctx = ctx
        self.stop()


class EditFAModal(miru.Modal):

    _states = miru.TextInput(
        label="States",
        placeholder="q0 q1 q2...",
        required=True,
        value="q0 q1",
    )
    _alphabets = miru.TextInput(
        label="Alphabets",
        placeholder="a b c...",
        required=True,
        value="a b",
    )
    _initial_state = miru.TextInput(
        label="Initial State",
        placeholder="q0",
        required=True,
        value="q0",
    )
    _final_states = miru.TextInput(
        label="Final State(s)",
        placeholder="q2...",
        required=True,
        value="q1",
    )
    _transition_functions = miru.TextInput(
        label="Transition Functions",
        placeholder="state,symbol(None for ε)=state\nq0,a=q1\nq0,=q2\n...",
        required=True,
        value="q0,a=q1\nq1,b=q0",
        style=hikari.TextInputStyle.PARAGRAPH,
    )

    def __init__(
        self,
        fa: FA,
        title: str | None = "Edit FA Data",
        *,
        custom_id: str | None = None,
        timeout: float | int | timedelta | None = 300,
    ) -> None:
        self._fa = fa
        values = fa.get_values()
        self._states.value = values["states"]
        self._alphabets.value = values["alphabets"]
        self._initial_state.value = values["initial_state"]
        self._final_states.value = values["final_states"]
        tf = values["tf"].split("|")
        self._transition_functions.value = "\n".join(tf)

        self._ctx: miru.ModalContext | None = None

        self.states = ""
        self.alphabets = ""
        self.initial_state = ""
        self.final_states = ""
        self.transition_functions = ""

        super().__init__(title, custom_id=custom_id, timeout=timeout)

    @property
    def ctx(self) -> miru.ModalContext:
        return self._ctx

    @property
    def states_value(self) -> set[str]:
        values = RegexPatterns.STATES.findall(self.states)
        return set(values)

    @property
    def alphabets_value(self) -> set[str]:
        values = RegexPatterns.ALPHABETS.findall(self.alphabets)
        return set(values)

    @property
    def initial_value(self) -> str:
        match = RegexPatterns.INITIAL_STATE.search(self.initial_state)
        return match.group(0) if match else ""

    @property
    def finals_value(self) -> set[str]:
        values = RegexPatterns.FINAL_STATES.findall(self.final_states)
        return set(values)

    @property
    def transitions_value(self) -> dict[tuple[str, str], set[str]]:
        transition_dict = {}

        values = self.transition_functions.split("\n")
        for value in values:
            match = RegexPatterns.TF.match(value.strip())
            if match:
                k0, k1, _, v = match.groups()
                if (k0, k1) in transition_dict:
                    transition_dict[(k0, k1)].add(v)
                else:
                    transition_dict[(k0, k1)] = {v}

        return transition_dict

    async def modal_check(self, ctx: miru.ModalContext) -> bool:
        self.states = ctx.values.get(self._states)
        self.alphabets = ctx.values.get(self._alphabets)
        self.initial_state = ctx.values.get(self._initial_state)
        self.final_states = ctx.values.get(self._final_states)
        self.transition_functions = ctx.values.get(self._transition_functions)

        return FA.check_valid(
            self.states_value,
            self.alphabets_value,
            self.initial_value,
            self.finals_value,
            self.transitions_value,
        )

    async def callback(self, ctx: miru.ModalContext) -> None:
        self.fa = FA(
            self.states_value,
            self.alphabets_value,
            self.initial_value,
            self.finals_value,
            self.transitions_value,
            ctx,
        )
        self._ctx = ctx
        self.stop()


class InputStringModal(miru.Modal):

    _string = miru.TextInput(
        label="String",
        placeholder="Input String",
        value="",
    )

    def __init__(
        self,
        fa: FA,
        string: str = "",
        title: str | None = "Input a String to Test",
        *,
        custom_id: str | None = None,
        timeout: float | int | timedelta | None = 300,
    ) -> None:
        self.fa = fa
        self._string.placeholder = fa.get_values()["alphabets"]
        self._string.value = string

        self.string = string

        super().__init__(title, custom_id=custom_id, timeout=timeout)

    @property
    def string_value(self) -> str:
        return self._string.value

    async def modal_check(self, ctx: miru.ModalContext) -> bool:
        content = ctx.values.get(self._string)
        if content is None:
            return True

        return set(content).issubset(self.fa.alphabets)

    async def callback(self, ctx: miru.ModalContext) -> None:
        self.result = self.fa.check_string(self.string_value)
        self.ctx = ctx
        self.stop()
