from __future__ import annotations

import re
from typing import Coroutine, Optional, Any
import time

import hikari
import lightbulb
import miru
import graphviz
import miru.modal

from .extensions import error_handler as error


class FA:

    def __init__(
        self,
        states: set[str],
        inputs: set[str],
        initial: str,
        finals: set[str],
        transitions: dict[tuple[str, str], set[str]],
        ctx: Optional[lightbulb.Context] = None,
    ) -> None:
        if not self.check_valid(states, inputs, initial, finals, transitions):
            raise error.InvalidFAError("The provided values are invalid.")
        self.states = states
        self.inputs = inputs
        self.initial = initial
        self.finals = finals
        self.transitions = transitions
        self.ctx = ctx

    @property
    def is_dfa(self) -> bool:
        return self.check_dfa(
            self.states, self.inputs, self.initial, self.finals, self.transitions
        )

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

    def draw_graph(self) -> str:
        """
        Draw the FA as a graph.

        Args:
            None
        Returns:
            str: The path to the graph.
        """
        file_name = self.author_name
        graph = graphviz.Digraph(
            format="png",
            graph_attr={
                "size": "10,10",
                "ratio": "1",
                "dpi": "200",
                "center": "true",
                "beautify": "true",
            },
        )
        for state in self.states:
            if state in self.finals:
                graph.node(state, shape="doublecircle")
            else:
                graph.node(state, shape="circle")
        graph.node("", shape="point")
        graph.edge("", self.initial)
        for (state, symbol), next_states in self.transitions.items():
            symbol = "ε" if symbol == "" else symbol
            for next_state in next_states:
                graph.edge(state, next_state, symbol)

        graph.render(f"storage/graph_cache/{file_name}")
        return f"storage/graph_cache/{file_name}.png"

    def check_string(self, string: str) -> FAStringTest:
        """
        Check the string with a depth-first-search algorithm.

        Args:
            string (str): The input string.

        Returns:
            FAStringTest: An object containing the result data from the test.
        """

        def dfs(current_state: str, remaining_str: str) -> tuple[bool, str]:
            if not remaining_str:
                return current_state in self.finals, current_state

            if (current_state, "") in self.transitions:
                next_state = self.transitions[(current_state, "")]

                for next_state in next_states:
                    if dfs(next_state, remaining_str):
                        return True, current_state

            symbol = remaining_str[0]
            remaining_str = remaining_str[1:]

            if (current_state, symbol) in self.transitions:
                next_states = self.transitions[(current_state, symbol)]

                for next_state in next_states:
                    if dfs(next_state, remaining_str):
                        return True, current_state
            return False, current_state

        passed, last_state = dfs(self.initial, string)
        return FAStringTest(self, string, passed, last_state)

    @staticmethod
    def check_valid(
        states: set[str],
        inputs: set[str],
        initial: str,
        finals: set[str],
        transitions: dict[tuple[str, str], set[str]],
    ) -> bool:
        """
        Determine if a given FA is valid.

        Args:
            states (set): The set of states.
            inputs (set): The set of imput symbols.
            initial (str): The start state.
            finals (set): The set of accept states.
            transitions (dict): The transition functions as a dictionary where the keys are (state, symbol) and values are set of next states

        Returns:
            bool: True if the FA is valid, else False.
        """

        # Check the start and end states if they're in the set of all states
        if initial not in states:
            return False
        if not finals.issubset(states):
            return False

        for (state, symbol), next in transitions.items():
            if state not in states:
                return False
            if symbol != "" and symbol not in inputs:
                return False
            if not next.issubset(states):
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


class FAStringTest:

    def __init__(self, fa: FA, string: str, passed: bool, last_state: str) -> None:
        self.string = string
        self.fa = fa
        self.passed = passed
        self.last_state = last_state
        
    @property
    def is_accepted(self) -> bool:
        return self.passed


class SaveView(miru.View):

    def __init__(self, ctx: lightbulb.SlashContext, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ctx = ctx
        self.modal = FormModal(title="Enter FA data.")

    @miru.button(label="Click here", style=hikari.ButtonStyle.PRIMARY)
    async def form_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        await ctx.respond_with_modal(self.modal)

    @miru.button(label="Cancel", style=hikari.ButtonStyle.SECONDARY)
    async def cancel_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        self.stop()

    def view_check(self, context: miru.ViewContext) -> bool:
        return self.ctx.author.id == context.author.id


class SaveFAModal(miru.Modal):
    pass


class FormModal(miru.Modal):
    STATES_PATTERN = re.compile(r"\b\w+\b")
    INPUTS_PATTERN = re.compile(r"\b\w+\b")
    INITIAL_PATTERN = re.compile(r"\b\w+\b")
    FINALS_PATTERN = re.compile(r"\b\w+\b")
    TF_PATTERN = re.compile(r"(\w+),(\w?)=(\w+)")

    states = miru.TextInput(label="States", placeholder="q0 q1 q2...", required=True)
    inputs = miru.TextInput(label="Inputs", placeholder="a b c...", required=True)
    initial = miru.TextInput(label="Initial state", placeholder="q0", required=True)
    finals = miru.TextInput(label="Final state(s)", placeholder="q2...", required=True)
    transitions = miru.TextInput(
        label="Transition Functions",
        placeholder="state,symbol(None for ε)=state\nq0,a=q1\nq0,=q2\n...",
        style=hikari.TextInputStyle.PARAGRAPH,
        required=True,
    )

    @property
    def ctx(self) -> miru.ModalContext:
        if not self._ctx:
            raise error.UserError("No context available.")
        return self._ctx

    @property
    def is_dfa(self) -> bool:
        if not self.fa:
            raise error.InvalidFAError("No FA data provided.")
        return self.fa.is_dfa

    @property
    def states_value(self) -> set[str]:
        values = self.STATES_PATTERN.findall(self._states)
        return set(values)

    @property
    def inputs_value(self) -> set[str]:
        values = self.INPUTS_PATTERN.findall(self._inputs)
        return set(values)

    @property
    def initial_value(self) -> str:
        match = self.INITIAL_PATTERN.search(self._initial)
        return match.group(0) if match else ""

    @property
    def finals_value(self) -> set[str]:
        values = self.FINALS_PATTERN.findall(self._finals)
        return set(values)

    @property
    def transitions_value(self) -> dict[tuple[str, str], set[str]]:
        transition_dict = {}

        values = self._transitions.split("\n")
        for value in values:
            match = self.TF_PATTERN.match(value.strip())
            if match:
                k0, k1, v = match.groups()
                if (k0, k1) in transition_dict:
                    transition_dict[(k0, k1)].add(v)
                else:
                    transition_dict[(k0, k1)] = {v}

        return transition_dict

    async def modal_check(self, ctx: miru.ModalContext) -> bool:

        self._states = ctx.values.get(self.states)
        self._inputs = ctx.values.get(self.inputs)
        self._initial = ctx.values.get(self.initial)
        self._finals = ctx.values.get(self.finals)
        self._transitions = ctx.values.get(self.transitions)

        return FA.check_valid(
            self.states_value,
            self.inputs_value,
            self.initial_value,
            self.finals_value,
            self.transitions_value,
        )

    async def callback(self, ctx: miru.ModalContext) -> None:
        self.fa = FA(
            self.states_value,
            self.inputs_value,
            self.initial_value,
            self.finals_value,
            self.transitions_value,
            ctx,
        )
        self._ctx = ctx
        self.stop()
