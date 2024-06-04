from __future__ import annotations

import re
from typing import Sequence

import hikari
import lightbulb
import miru

from .extensions import error_handler as error


class FA:

    def __init__(
        self,
        states: set[str],
        inputs: set[str],
        initial: str,
        finals: set[str],
        transitions: dict[tuple[str, str], set[str]],
    ) -> None:
        if not self.check_valid(states, inputs, initial, finals, transitions):
            raise error.InvalidFAError("The provided values are invalid.")
        self.states = states
        self.inputs = inputs
        self.initial = initial
        self.finals = finals
        self.transitions = transitions

    @property
    def is_dfa(self) -> bool:
        return self.check_dfa(
            self.states, self.inputs, self.initial, self.finals, self.transitions
        )

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


class NFA(FA):
    pass


class DFA(FA):
    pass


class FormView(miru.View):

    def __init__(self, ctx: lightbulb.SlashContext, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ctx = ctx
        self.modal = FormModal(title="Enter FA data.")

    @miru.button(label="Click here", style=hikari.ButtonStyle.SUCCESS)
    async def form_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        print("hi")
        # if ctx.author.id != self.ctx.author.id:
        #     return
        await ctx.respond_with_modal(self.modal)

    @miru.button(label="Cancel", style=hikari.ButtonStyle.PRIMARY)
    async def cancel_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        if ctx.author.id != self.ctx.author.id:
            return
        self.stop()


class FormModal(miru.Modal):

    states = miru.TextInput(
        label="States", placeholder="q0 q1 q2...", required=True)
    inputs = miru.TextInput(
        label="Inputs", placeholder="a b...", required=True)
    initial = miru.TextInput(label="Initial state",
                             placeholder="q0", required=True)
    finals = miru.TextInput(
        label="Final state(s)", placeholder="q2 q3...", required=True
    )
    transitions = miru.TextInput(
        label="Transition Functions",
        placeholder='state,symbol(None for epsilon)=state\nq0,a=q1\nq0,=q2...',
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
        pattern = re.compile(r"\b\w+\b")
        values = pattern.findall(self._states)
        return set(values)

    @property
    def inputs_value(self) -> set[str]:
        pattern = re.compile(r"\b\w+\b")
        values = pattern.findall(self._inputs)
        return set(values)

    @property
    def initial_value(self) -> str:
        pattern = re.compile(r"\b\w+\b")
        match = pattern.search(self._initial)
        return match.group(0) if match else ""

    @property
    def finals_value(self) -> set[str]:
        pattern = re.compile(r'\b\w+\b')
        values = pattern.findall(self._finals)
        return set(values)

    @property
    def transitions_value(self) -> dict[tuple[str, str], set[str]]:
        transition_dict = {}
        pattern = re.compile(r"(\w+),(\w?)=(\w+)")

        values = self._transitions.split("\n")
        for value in values:
            match = pattern.match(value.strip())
            if match:
                k0, k1, v = match.groups()
                if (k0, k1) in transition_dict:
                    transition_dict[(k0, k1)].add(v)
                else:
                    transition_dict[(k0, k1)] = {v}

        return transition_dict

    async def modal_check(
            self, ctx: miru.ModalContext) -> bool:

        self._states = ctx.values.get(self.states)
        self._inputs = ctx.values.get(self.inputs)
        self._initial = ctx.values.get(self.initial)
        self._finals = ctx.values.get(self.finals)
        self._transitions = ctx.values.get(self.transitions)

        return FA.check_valid(self.states_value, self.inputs_value, self.initial_value, self.finals_value, self.transitions_value)

    async def callback(self, ctx: miru.ModalContext) -> None:
        self.fa = FA(
            self.states_value,
            self.inputs_value,
            self.initial_value,
            self.finals_value,
            self.transitions_value,
        )
        self._ctx = ctx
        self.stop()
