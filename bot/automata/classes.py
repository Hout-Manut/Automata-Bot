from __future__ import annotations

import re
import time
from datetime import datetime, timedelta
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
import graphviz
import hikari
import lightbulb
import miru

from .extensions import error_handler as error

class Color(int):
    RED = 0xff6459
    GREEN = 0xa2e57b
    LIGHT_BLUE = 0x55c7f1


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
        ctx: lightbulb.Context | None = None,
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

    def save_to_db(self, ctx: lightbulb.SlashContext) -> None:

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
            db_con = mysql.connector.connect(
                host=os.getenv('DB_HOST'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                database=os.getenv('DB_NAME'),
                # port=int(os.getenv('DB_PORT'))
            )

            if db_con.is_connected():
                try:
                    cursor = db_con.cursor()

                    sql_query = 'INSERT INTO Recent (user_id, fa_name, states, alphabets, initial_state, final_states, transitions, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'
                    # sql_query = 'SELECT * FROM History;'

                    data = (user_id, fa_name, states, alphabets, initial_state, final_states, tf, date)
                    cursor.execute(sql_query, data)

                    db_con.commit()

                    # for row in cursor:
                    #     print(row)

                except Error as e:
                    print(f'Inserting data unsucessfully: {e}')

        except Error as e:
            print(f'Error: {e}')
        pass

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
        return f"{{`{', '.join(states)}`}}"

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
        *,
        title: str | None = None,
        description: str | None = None,
        url: str | None = None,
        color: hikari.Colourish | None = None,
        colour: hikari.Colorish | None = None,
        time_stamp: datetime | None = None,
        field_inline: bool | None = False,
        footer_text: str | None = None,
        footer_icon: hikari.Resourceish | None = None,
        author_name: str | None = None,
        author_url: str | None = None,
        author_icon: hikari.Resourceish | None = None,
        with_diagram: bool | None = False,
        as_thumbnail: bool | None = False,
    ) -> hikari.Embed:
        if not title:
            title = "Deterministic" if self.is_dfa else "Non-deterministic"
            title += " Finite Automaton"

        embed = hikari.Embed(
            title=title,
            description=description,
            url=url,
            color=color,
            colour=colour,
            timestamp=time_stamp,
        )

        name = "State" if len(self.states) == 1 else "States"
        embed.add_field(name=name, value=self.states_str, inline=field_inline)

        name = "Alphabet" if len(self.alphabets) == 1 else "Alphabets"
        embed.add_field(name=name, value=self.alphabets_str,
                        inline=field_inline)

        embed.add_field(
            name="Initial State", value=self.initial_state_str, inline=field_inline
        )

        name = "Final State" if len(self.final_states) == 1 else "Final States"
        embed.add_field(name=name, value=self.final_states_str,
                        inline=field_inline)

        name = (
            "Transition Function"
            if len(self.transition_functions) == 1
            else "Transition Functions"
        )
        embed.add_field(
            name=name, value=self.transition_functions_str, inline=field_inline
        )

        if with_diagram:
            if as_thumbnail:
                embed.set_thumbnail(self.get_diagram())
            else:
                embed.set_image(self.get_diagram())

        if footer_text:
            embed.set_footer(text=footer_text, icon=footer_icon)

        if author_name:
            embed.set_author(name=author_name,
                             url=author_url, icon=author_icon)

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
        graph = graphviz.Digraph(
            format="png",
            graph_attr={
                "size": "10,10",
                "ratio": ratio,
                "dpi": "200",
                "center": "true",
                "beautify": "true",
            },
        )
        for state in self.states:
            if state in self.final_states:
                graph.node(state, shape="doublecircle")
            else:
                graph.node(state, shape="circle")
        graph.node("", shape="point")
        graph.edge("", self.initial_state)
        for (state, symbol), next_states in self.transition_functions.items():
            symbol = "ε" if symbol == "" else symbol
            for next_state in next_states:
                graph.edge(state, next_state, symbol)

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

        def dfs(current_state: str, remaining_str: str) -> tuple[bool, str]:
            if not remaining_str:
                return current_state in self.finals, current_state

            if (current_state, "") in self.transitions:
                next_states = self.transitions[(current_state, "")]
                for next_state in next_states:
                    accepted, last_state = dfs(next_state, remaining_str)
                    if accepted:
                        return True, last_state

            symbol = remaining_str[0]
            remaining_str = remaining_str[1:]

            if (current_state, symbol) in self.transitions:
                next_states = self.transitions[(current_state, symbol)]
                for next_state in next_states:
                    accepted, last_state = dfs(next_state, remaining_str)
                    if accepted:
                        return True, last_state

            return False, current_state if not remaining_str else last_state

        passed, last_state = dfs(self.initial, string)
        return FAStringResult(self, string, passed, last_state)

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

    def __str__(self) -> str:
        return f"FA({self.states}, {self.alphabets}, {self.initial_state}, {self.final_states}, {self.transition_functions})"



class FAStringResult:
    def __init__(
        self,
        fa: FA | None = None,
        string: str | None = None,
        passed: bool = False,
        last_state: str | None = None,
    ) -> None:
        self._string = string
        self.fa = fa
        self.passed = passed
        self.last_state = last_state

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

    async def callback(self, context: miru.ModalContext) -> None:
        self.fa = FA(
            self.states_value,
            self.alphabets_value,
            self.initial_value,
            self.finals_value,
            self.transitions_value,
            context,
        )
        self._ctx = context
        self.stop()


class InputStringModal(miru.Modal):
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
        self._string = miru.TextInput(
            label="String",
            placeholder="Input String",
            required=True,
            value=string,
        )
        self.add_item(self._string)

        self.string = string

        super().__init__(title, custom_id=custom_id, timeout=timeout)

    @property
    def string_value(self) -> str:
        return self._string.value

    async def modal_check(self, ctx: miru.ModalContext) -> bool:
        content = ctx.values.get(self._string)

        return set(content).issubset(self.fa.alphabets)

    async def callback(self, ctx: miru.ModalContext) -> None:
        self.result = self.fa.check_string(self.string_value)
        self.ctx = ctx
        self.stop()
