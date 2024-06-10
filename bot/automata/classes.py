from __future__ import annotations

import re
import re
import time
from abc import ABC, abstractmethod
from datetime import datetime

import graphviz
import hikari
import lightbulb
import miru
import miru.modal

from .extensions import error_handler as error


NFATransitions = dict[tuple[str, str], set[str]]
DFATransitions = dict[tuple[str, str], str]


class FA(ABC):

    """
    Abstract base class representing a Finite Automaton (FA).

    This class provides a common interface for NFA and DFA.
    """

    @abstractmethod
    def __init__(
        self,
        states: set[str] = set(),
        alphabets: set[str] = set(),
        start_state: str = "",
        final_states: set[str] = set(),
        transition_functions: NFATransitions | DFATransitions = {},
        ctx: lightbulb.Context | None = None,
    ) -> None:
        """
        Initialize a new FA instance.

        Args:
            states (set[str]): The set of states in the FA.
            alphabets (set[str]): The set of input symbols in the FA.
            start_state (str): The start state in the FA.
            final_states (set[str]): The set of accepted states in the FA.
            transition_functions (NFATransitions | DFATransitions): The transition function in the FA.
            ctx (lightbulb.Context | None): The context of the command used. Defaults to None.

        Raises:
            error.InvalidFAError: If the provided FA data is invalid.
        """
        if not self.check_valid(
            states,
            alphabets,
            start_state,
            final_states,
            transition_functions,
        ):
            raise error.InvalidFAError("Invalid FA data provided.")

        self.states = states
        self.alphabets = alphabets
        self.start_state = start_state
        self.final_states = final_states
        self.transition_functions = transition_functions
        self.ctx = ctx

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
        A string representation of the set of states in the FA.
        """
        states = list(self.states)
        states.sort()
        return f"{{`{', '.join(states)}`}}"

    @property
    def alphabets_str(self) -> str:
        """
        A string representation of the set of alphabets in the FA.
        """
        alphabets = list(self.alphabets)
        alphabets.sort()
        return f"{{`{'`, `'.join(alphabets)}`}}"

    @property
    def start_state_str(self) -> str:
        """
        A string representation of the start state in the FA.
        """
        return f"`{self.start_state}`"

    @property
    def final_states_str(self) -> str:
        """
        A string representation of the set of final states in the FA.
        """
        final_states = list(self.final_states)
        final_states.sort()
        return f"{{`{'`, `'.join(final_states)}`}}"

    @abstractmethod
    @property
    def transition_functions_str(self) -> str:
        """
        A string representation of the transition functions in the FA.
        """
        ...

    @abstractmethod
    def nfa_to_dfa(self) -> DFA:
        """
        Convert the NFA to a DFA.

        Returns:
            DFA: The new DFA.

        Raises:
            error.InvalidFAError: If the FA is not an NFA.
        """
        ...

    @abstractmethod
    def minimize(self) -> DFA:
        """
        Minimize the DFA.

        returns:
            DFA: The minimized DFA as a new object.

        Raises:
            error.InvalidFAError: If the FA is not an DFA.
            error.NotMinimizableError: If the DFA can not be minimized.
        """
        ...

    @abstractmethod
    def is_dfa(self) -> bool: ...

    @abstractmethod
    def is_nfa(self) -> bool: ...

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
            timestamp=time_stamp
        )

        name = "State" if len(self.states) == 1 else "States"
        embed.add_field(name=name, value=self.states_str, inline=field_inline)

        name = "Alphabet" if len(self.alphabets) == 1 else "Alphabets"
        embed.add_field(name=name, value=self.alphabets_str,
                        inline=field_inline)

        embed.add_field(name="Initial State",
                        value=self.start_state_str, inline=field_inline)

        name = "Final State" if len(self.final_states) == 1 else "Final States"
        embed.add_field(name=name, value=self.final_states_str,
                        inline=field_inline)

        name = "Transition Function" if len(
            self.transition_functions) == 1 else "Transition Functions"
        embed.add_field(
            name=name, value=self.transition_functions_str, inline=field_inline)

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

    def get_diagram(self) -> hikari.File:
        """
        Get the diagram for the FA.

        Returns:
            hikari.File: The diagram for the FA.
        """
        path = self.draw_diagram()
        return hikari.File(path, filename="automata.png")

    def draw_diagram(self) -> str:
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
        start_state: str,
        final_states: set[str],
        transition_functions: DFATransitions | NFATransitions,
    ) -> bool:
        """
        Determine if a given FA is valid.

        Returns:
            bool: True if the FA is valid, else False.
        """

        # Check the start and end states if they're in the set of all states"""
        if start_state not in states:
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


class NFA(FA):
    """
    A subclass of FA that represents an NFA.
    """

    def __init__(
        self,
        states: set[str] = set(),
        alphabets: set[str] = set(),
        start_state: str = "",
        final_states: set[str] = set(),
        transition_functions: NFATransitions = {},
        ctx: lightbulb.Context | None = None,
    ) -> None:
        super().__init__(states, alphabets, start_state,
                         final_states, transition_functions, ctx)

    @property
    def is_dfa(self) -> bool:
        return True

    @property
    def is_nfa(self) -> bool:
        return False

    @property
    def is_minimized(self) -> bool:
        raise error.InvalidDFAError("The FA is not a DFA.")

    @property
    def transition_functions_str(self) -> str:
        tf = ""
        for (from_state, symbol), to_states in self.transition_functions.items():
            symbol = "ε" if symbol == "" else symbol
            tf += f"(`{from_state}`, `{symbol}`) -> {{`{'`, `'.join(to_states)}`}}\n"
        return tf

    def nfa_to_dfa(self) -> DFA:
        raise NotImplementedError

    def minimize(self) -> DFA:
        raise error.InvalidDFAError("The FA is not a DFA.")


class DFA(FA):
    """
    A subclass of FA that represents a DFA.
    """

    def __init__(
        self,
        states: set[str] = set(),
        alphabets: set[str] = set(),
        start_state: str = "",
        final_states: set[str] = set(),
        transition_functions: DFATransitions = {},
        ctx: lightbulb.Context | None = None,
    ) -> None:
        super().__init__(states, alphabets, start_state,
                         final_states, transition_functions, ctx)

    @property
    def is_dfa(self) -> bool:
        return True

    @property
    def is_nfa(self) -> bool:
        return False

    @property
    def is_minimized(self) -> bool:
        raise NotImplementedError

    @property
    def transition_functions_str(self) -> str:
        tf = ""
        for (from_state, symbol), to_state in self.transition_functions.items():
            symbol = "ε" if symbol == "" else symbol
            tf += f"(`{from_state}`, `{symbol}`) -> `{to_state}`\n"
        return tf

    def nfa_to_dfa(self) -> DFA:
        raise error.InvalidNFAError("The FA is already a DFA.")

    def minimize(self) -> DFA:
        raise NotImplementedError


class FAStringResult:
    def __init__(self, fa: FA, string: str, passed: bool, last_state: str) -> None:
        self.string = string
        self.fa = fa
        self.passed = passed
        self.last_state = last_state

    @property
    def is_accepted(self) -> bool:
        return self.passed
