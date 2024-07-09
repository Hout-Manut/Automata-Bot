from __future__ import annotations

import re
from datetime import datetime, timedelta

import graphviz
import hikari
import lightbulb
import miru
import mysql.connector
import mysql.connector.cursor
from mysql.connector import Error as SQLError

from .extensions import error_handler as error


TransitionT = dict[tuple[str, str], set[str]]
"""
Type alias that represents the transition function type.
"""


class Color(int):
    """A class to store default colors."""

    RED = 0xFF6459
    GREEN = 0xA2E57B
    LIGHT_BLUE = 0x55C7F1
    YELLOW = 0xF2EE78


class RegexPatterns:
    """A class that contains regex patterns to use for parsing user inputs"""

    STATES = re.compile(r"\b[\w'‘]+\b")
    """Matches word (`a-zA-z0-9_'‘`)"""

    ALPHABETS = re.compile(r"\w")
    """Matches single letter (`a-zA-z0-9_`)"""

    INITIAL_STATE = re.compile(r"\b[\w'‘]+\b")
    """Matches word (`a-zA-z0-9_'‘`)"""

    FINAL_STATES = re.compile(r"\b[\w'‘]+\b")
    """Matches word (`a-zA-z0-9_'‘`)"""

    TF = re.compile(
        r"\b([\w'‘]+)\s*[,\s+]\s*([\w'‘]*)\s*(=|>|->)\s*([\w'‘]+)\b")
    """
    Matches word, followed by `,` or `space`, a word or nothing,
    then any of these [`=`, `>`, `->`] and another word.
    """

    DFA_OR_NFA = re.compile(r"\b(dfa|nfa)\b")

    STATE_NUM_QUERY = re.compile(r"\bstates?(=|>|<|>=|<=)(\d+)\b")

    ALPHABET_NUM_QUERY = re.compile(
        r"\b(inpu?t?|alpha?b?e?t?|symb?o?l?s?|chara?c?t?e?r?)s?\b(=|>|<|>=|<=)(\d+)\b")

    ALPHABETS_QUERY = re.compile(
        r"\b(inpu?t?|alpha?b?e?t?|symb?o?l?s?|chara?c?t?e?r?)s?\b=(\w+)\b")


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
        self._is_minimized = False

    def save_to_db(self, ctx: lightbulb.SlashContext | None = None) -> None:
        """
        Saves this FA object to the database. Only updates the date if this already exists in the database.

        Args:
            ctx (Context): the context of an interaction to get the user id.
        """
        if not ctx:
            ctx = self.ctx

        template = "{fa} with {num_states} states, {num_alphabets} inputs. Starts at {initial_state}."
        """Default FA name to be saved."""

        values = self.get_values()

        user_id = ctx.user.id
        states = values["states"]
        alphabets = values["alphabets"]
        initial_state = values["initial_state"]
        final_states = values["final_states"]
        tf = values["tf"]  # Transition functions

        fa_type = "An NFA" if self.is_nfa else "A DFA"
        num_states = len(self.states)
        num_alphabets = len(self.alphabets)

        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        fa_name = template.format(
            fa=fa_type,
            num_states=num_states,
            num_alphabets=num_alphabets,
            initial_state=initial_state,
        )

        try:
            cursor: mysql.connector.cursor.MySQLCursor = ctx.app.d.cursor

            # Check if the record already exists
            check_query = """
            SELECT id
            FROM Recent
            WHERE
                user_id = %s AND
                states = %s AND
                alphabets = %s AND
                initial_state = %s AND
                final_states = %s AND
                transitions = %s
            """
            data = (user_id, states, alphabets,
                    initial_state, final_states, tf)
            cursor.execute(check_query, data)
            result = cursor.fetchall()

            if result:
                for fa_id in result:
                    # Records exist, update them all
                    update_query = """
                    UPDATE Recent
                    SET
                        updated_at = %s
                    WHERE
                        id = %s
                    """
                    data_update = (
                        date,
                        fa_id[0],
                    )
                    cursor.execute(update_query, data_update)
            else:
                # Record does not exist, insert new one
                insert_query = """
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
                data_insert = (
                    user_id,
                    fa_name,
                    states,
                    alphabets,
                    initial_state,
                    final_states,
                    tf,
                    date,
                )
                cursor.execute(insert_query, data_insert)
            ctx.app.d.db.commit()

        except SQLError as e:
            print(f"Inserting data unsucessfully: {e}")

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
        sorted_dict = dict(
            sorted(self.t_func.items(), key=lambda item: (
                item[0][0], item[0][1]))
        )
        if self.is_dfa:
            for (from_state, symbol), to_state in sorted_dict.items():
                symbol = "ε" if symbol == "" else symbol
                tf += f"(`{from_state}`, `{symbol}`) -> `{next(iter(to_state))}`\n"
        else:
            for (from_state, symbol), to_states in sorted_dict.items():
                symbol = "ε" if symbol == "" else symbol
                tf += (
                    f"(`{from_state}`, `{symbol}`) -> {{`{'`, `'.join(to_states)}`}}\n"
                )
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

        Raises:
            error.InvalidFAError: If the FA is not an DFA.
        """
        if self.is_nfa:
            raise error.InvalidFAError("The FA is not a DFA.")

        return self._is_minimized

    def epsilon_closure(self, state: str) -> set[str]:
        """Epsilon closure of a state"""
        stack = [state]
        closure = {state}

        while stack:
            current_state = stack.pop()
            if (current_state, "") in self.t_func:
                for next_state in self.t_func[(current_state, "")]:
                    if next_state not in closure:
                        closure.add(next_state)
                        stack.append(next_state)

        return closure

    def epsilon_closure_set(self, states: set[str]) -> set[str]:
        """Epsilon closure of a set of states"""
        closure = set()
        for state in states:
            closure |= self.epsilon_closure(state)
        return closure

    def move(self, states: set[str], symbol: str) -> set[str]:
        """Gets a state return all next states it can moves to."""
        new_states = set()
        for state in states:
            if (state, symbol) in self.t_func:
                new_states |= set(self.t_func[(state, symbol)])

        return new_states

    def nfa_to_dfa(self) -> tuple[FA, FAConversionResult]:
        """
        Generate a DFA from an NfA.

        Returns:
            FA: the new DFA.
            FAConversionResult: A result object that contains informations of the conversion.
        """
        initial_closure = self.epsilon_closure(self.initial_state)
        # Custom prime state names
        dfa_states = {frozenset(initial_closure): "q'0"}
        dfa_states_list = [initial_closure]
        dfa_transition_functions: TransitionT = {}
        dfa_final_states = set()

        # States to be marked, starts from the initial state.
        unmarked_states = [initial_closure]
        # For tracking custom names.
        state_counter = 1

        while unmarked_states:
            current_state = unmarked_states.pop()
            current_state_name = dfa_states[frozenset(current_state)]

            for symbol in self.alphabets:
                next_state = self.move(current_state, symbol)
                next_closure = self.epsilon_closure_set(next_state)

                if frozenset(next_closure) not in dfa_states:
                    new_state_name = f"q'{state_counter}"
                    dfa_states[frozenset(next_closure)] = new_state_name
                    dfa_states_list.append(next_closure)
                    unmarked_states.append(next_closure)
                    state_counter += 1

                dfa_transition_functions[(current_state_name, symbol)] = {
                    dfa_states[frozenset(next_closure)]
                }
            if any(state in self.final_states for state in current_state):
                dfa_final_states.add(current_state_name)

        new_state_set = set(dfa_states.values())
        new_alphabets = self.alphabets
        new_initial_state = dfa_states[frozenset(initial_closure)]
        new_final_states = dfa_final_states
        new_transition_functions = {
            (current, symbol): to
            for (current, symbol), to in dfa_transition_functions.items()
        }
        new_fa = FA(
            new_state_set,
            new_alphabets,
            new_initial_state,
            new_final_states,
            new_transition_functions,
            self.ctx,
        )
        result = FAConversionResult(dfa_states)
        return new_fa, result

    def convert(self) -> tuple[FA, FAConversionResult]:
        """
        Convert the NFA to a DFA.

        Returns:
            DFA: The new DFA.

        Raises:
            error.InvalidFAError: If the FA is not an NFA.
        """
        if self.is_dfa:
            raise error.InvalidFAError("The FA is already a DFA.")

        return self.nfa_to_dfa()

    def get_unreachable_states(self) -> set[str]:
        """
        Find any unreacble states by going through the states from the start using the transition functions.
        If by the end there are states that have not been reached, those are the unreachable states.
        """
        reachable_states: set[str] = set()
        stack: list[str] = [self.initial_state]

        while stack:
            current_state = stack.pop()
            if current_state not in reachable_states:
                reachable_states.add(current_state)
                for alphabet in self.alphabets:
                    if (current_state, alphabet) in self.t_func:
                        next_states = self.t_func[(current_state, alphabet)]
                        for next_state in next_states:
                            if next_state not in reachable_states:
                                stack.append(next_state)

        return self.states - reachable_states

    def get_equivalent_states(
        self,
        reachable_states: set[str],
        reachable_t_func: TransitionT,
    ) -> list[set[str]]:
        partitions = [self.final_states, reachable_states - self.final_states]
        worklist = [self.final_states, reachable_states - self.final_states]

        while worklist:
            current = worklist.pop()
            for symbol in self.alphabets:
                state_transitions = set(
                    state
                    for state in self.states
                    if (state, symbol) in reachable_t_func
                    and reachable_t_func[(state, symbol)] & current
                )
                for partition in partitions[:]:
                    intersection = partition & state_transitions
                    difference = partition - state_transitions

                    if intersection and difference:
                        partitions.remove(partition)
                        partitions.extend([intersection, difference])
                        if partition in worklist:
                            worklist.remove(partition)
                            worklist.extend([intersection, difference])
                        else:
                            worklist.append(
                                intersection
                                if len(intersection) <= len(difference)
                                else difference
                            )

        return partitions

    def get_minimized_dfa(self) -> tuple[FA, FAMinimizationResult]:
        """
        Minimize the current DFA object.

        Returns:
            FA: a new DFA object.
            FAMinimizationResult: a result object containing the details of the minimization.
        """
        unreachable_states = self.get_unreachable_states()
        reachable_states = self.states - unreachable_states

        reachable_transition_functions = {
            (state, symbol): next_states
            for (state, symbol), next_states in self.t_func.items()
            if state in reachable_states
        }

        partitions = self.get_equivalent_states(
            reachable_states, reachable_transition_functions
        )
        old_states = list(self.states)
        old_states.sort()
        state_map = {
            frozenset(part): old_states[i] for i, part in enumerate(partitions)
        }

        new_states = set(state_map[frozenset(part)] for part in partitions)
        new_initial_state = state_map[
            next(frozenset(part)
                 for part in partitions if self.initial_state in part)
        ]
        new_final_states = set(
            state_map[frozenset(part)]
            for part in partitions
            if part & self.final_states
        )
        new_transition_functions: TransitionT = {}

        for part in partitions:
            current = next(iter(part))
            for symbol in self.alphabets:
                if (current, symbol) in reachable_transition_functions:
                    next_states = reachable_transition_functions[(
                        current, symbol)]
                    for next_state in next_states:
                        new_part = next(
                            frozenset(part) for part in partitions if next_state in part
                        )
                        if (
                            state_map[frozenset(part)],
                            symbol,
                        ) not in new_transition_functions:
                            new_transition_functions[
                                (state_map[frozenset(part)], symbol)
                            ] = set()
                        new_transition_functions[
                            (state_map[frozenset(part)], symbol)
                        ].add(state_map[new_part])

        new_dfa = FA(
            new_states,
            self.alphabets,
            new_initial_state,
            new_final_states,
            new_transition_functions,
            self.ctx,
        )
        lost_states = self.states - new_dfa.states
        result = FAMinimizationResult(unreachable_states, lost_states)
        return new_dfa, result

    def minimize(self) -> tuple[FA, FAMinimizationResult]:
        """
        Minimize the DFA.

        returns:
            DFA: The minimized DFA as a new object.

        Raises:
            InvalidFAError: If the FA is not an DFA.
        """
        if self.is_nfa:
            raise error.InvalidFAError("The FA is not a DFA.")

        minimized_dfa, result = self.get_minimized_dfa()

        self._is_minimized = True
        return minimized_dfa, result

    @property
    def is_minimizable(self) -> bool:
        """Checks if this fa is minimizable. True if it is, else False."""
        if self.is_nfa:
            raise error.InvalidFAError("The FA is not a DFA.")

        # Try to minimize the DFA
        minimized_dfa, _ = self.get_minimized_dfa()

        # Check if the minimized DFA is the same as the old DFA
        is_same = len(self.states) == len(minimized_dfa.states)
        return not is_same

    def get_values(self) -> dict[str, str]:
        """
        Converts all of the FA data into string representations.
        Mainly used to store into the database.
        """
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
        color: hikari.Colorish = Color.LIGHT_BLUE,
        author_name: str | None = None,
        author_icon: hikari.Resourceish | None = None,
        with_diagram: bool = True,
    ) -> hikari.Embed:
        """
        Generate an embed with the information of the FA.

        Embeds are those cool Discord message blocks that you can add accent colors to.
        """

        title = "Deterministic" if self.is_dfa else "Non-deterministic"
        title += " Finite Automaton"
        embed = hikari.Embed(title=title, description=None, color=color)

        name = "State" if len(self.states) == 1 else "States"
        embed.add_field(name, self.states_str)

        name = "Alphabet" if len(self.alphabets) == 1 else "Alphabets"
        embed.add_field(name, self.alphabets_str)

        embed.add_field("Initial State", self.initial_state_str)

        name = "State" if len(self.final_states) == 1 else "States"
        embed.add_field(f"Final {name}", self.final_states_str)

        name = "Function" if len(self.t_func) == 1 else "Functions"
        embed.add_field(f"Transition {name}", self.t_func_str)

        if author_name or author_icon:
            embed.set_author(name=author_name, icon=author_icon)

        if with_diagram:
            embed.set_image(self.get_diagram(image_ratio))

        return embed

    def get_diagram(self, ratio: str = "1") -> hikari.File:
        """
        Get the diagram for the FA.

        Args:
            ratio (str): How wide the diagram image will be.

        Returns:
            hikari.File: The diagram for the FA.
        """
        path = self.draw_diagram(ratio=ratio)
        return hikari.File(path, filename="automata.png")

    def draw_diagram(self, ratio: str = "1") -> str:
        """
        Draw the FA as a diagram.

        Args:
            ratio (str): How wide the diagram image will be.

        Returns:
            str: The path to the diagram.
        """
        file_name = self.author_name
        if len(self.states) >= 4 and ratio == "1":
            ratio = "0.5625"
        # margin = "0" if ratio == "1" else "5,0"
        graph = graphviz.Digraph(
            format="png",
            graph_attr={
                "bgcolor": "#383a40",
                "color": "transparent",
                "fillcolor": "#383a40",
                "size": "10,10",
                "ratio": ratio,
                "dpi": "200",
                "center": "true",
                "beautify": "true",
                "smoothing": "avg_dist",
                "orientation": "90",
                "rankdir": "LR",
            },
        )
        with graph.subgraph(name="cluster_0") as c:
            c.attr = {
                "ratio": "1",
                "size": "10,10",
                "bgcolor": "#3a4348",
                "center": "true",
            }
            c.node_attr.update(
                color="#ffffff", fillcolor="transparent", fontcolor="#ffffff"
            )
            c.edge_attr.update(color="#ffffff", fontcolor="#ffffff", len="1")
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
            FAStringResult: A result object that contains the informations of the test.
        """

        def dfs(current_state: str, remaining_str: str) -> bool:
            """
            Search through the string with a depth-first search algorithm.

            Returns:
                bool: True if any of the end of the search branches lands on a final state.
            """
            if not remaining_str:
                # Check if the current state is a final state or if any epsilon transitions lead to a final state
                if current_state in self.final_states:
                    return True
                if (current_state, "") in self.t_func:
                    for next_state in self.t_func[(current_state, "")]:
                        if dfs(next_state, remaining_str):
                            return True
                return False

            # Process epsilon transitions first
            if (current_state, "") in self.t_func:
                for next_state in self.t_func[(current_state, "")]:
                    if dfs(next_state, remaining_str):
                        return True

            # Process transitions for the current symbol
            symbol = remaining_str[0]
            remaining_str = remaining_str[1:]

            if (current_state, symbol) in self.t_func:
                for next_state in self.t_func[(current_state, symbol)]:
                    if dfs(next_state, remaining_str):
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
    def get_db_fa_data(ctx: lightbulb.SlashContext) -> tuple[FA, dict[str, str]]:
        """
        A static method that returns the full FA data from the database.

        Args:
            ctx (lightbulb.SlashContext): The context of the command used, must have a recent option.

        Returns:
            tuple[FA, dict[str, str]]: A tuple containing the FA and the FA data.
        """
        try:
            fa_id = int(ctx.options.recent)
            if fa_id == 0:
                raise error.UserError
        except ValueError:
            raise error.UserError

        try:
            cursor: mysql.connector.cursor.MySQLCursor = ctx.app.d.cursor

            query = """
                SELECT
                    id,
                    fa_name,
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
                raise error.InvalidDBQuery

            states_str = str(result[2])
            alphabets_str = str(result[3])
            initial_state = str(result[4])
            final_states_str = str(result[5])
            transitions_str = str(result[6])

            fa = FA.parse_db_data(
                state_str=states_str,
                alphabets_str=alphabets_str,
                initial_state=initial_state,
                final_states_str=final_states_str,
                transitions_str=transitions_str,
                ctx=ctx,
            )

            data = {
                "id": str(result[0]),
                "fa_name": str(result[1]),
            }

            return fa, data

        except error.InvalidDBQuery:
            raise

    @staticmethod
    def get_fa_from_db(fa_id: int, ctx: lightbulb.SlashContext) -> FA:
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
                raise error.InvalidDBQuery

            states_str = str(result[0])
            alphabets_str = str(result[1])
            initial_state = str(result[2])
            final_states_str = str(result[3])
            transitions_str = str(result[4])

            return FA.parse_db_data(
                state_str=states_str,
                alphabets_str=alphabets_str,
                initial_state=initial_state,
                final_states_str=final_states_str,
                transitions_str=transitions_str,
                ctx=ctx,
            )
        except SQLError as e:
            raise error.AutomataError(
                "Something went wrong while fetching the FA from the database.: "
                + e.args[1]
            )

    @staticmethod
    def parse_db_data(
        state_str: str,
        alphabets_str: str,
        initial_state: str,
        final_states_str: str,
        transitions_str: str,
        ctx: lightbulb.SlashContext,
    ) -> FA:
        states = RegexPatterns.STATES.findall(state_str)
        alphabets = RegexPatterns.ALPHABETS.findall(alphabets_str)
        final_states = RegexPatterns.STATES.findall(final_states_str)

        transitions: TransitionT = {}
        values = transitions_str.split("|")

        for value in values:
            match = RegexPatterns.TF.match(value.strip())
            if match:
                k0, k1, _, v = match.groups()
                if (k0, k1) in transitions:
                    transitions[(k0, k1)].add(v)
                else:
                    transitions[(k0, k1)] = {v}
        return FA(
            states=set(states),
            alphabets=set(alphabets),
            initial_state=initial_state,
            final_states=set(final_states),
            transition_functions=transitions,
            ctx=ctx,
        )

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

            fa = FA.get_fa_from_db(fa_id, ctx)
            fa.save_to_db(ctx)
            return fa
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
        fa.save_to_db(ctx)
        return fa

    def __str__(self) -> str:
        return f"FA({self.states}, {self.alphabets}, {self.initial_state}, {self.final_states}, {self.transition_functions})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, FA):
            return False

        self_normalized = self._normalized()
        other_normalized = other._normalized()
        return self_normalized == other_normalized

    def _normalized(self) -> tuple:
        state_list = sorted(self.states)
        state_map = {state: f"s{i}" for i, state in enumerate(state_list)}

        # Normalize transition functions
        normalized_transitions = {}
        for (state, symbol), next_states in self.transition_functions.items():
            normalized_transitions[(state_map[state], symbol)] = {
                state_map[next_state] for next_state in next_states
            }

        # Normalize initial and final states
        normalized_initial_state = state_map[self.initial_state]
        normalized_final_states = {state_map[state]
                                   for state in self.final_states}

        # Return normalized DFA representation
        return (
            set(state_map.values()),
            self.alphabets,
            normalized_initial_state,
            normalized_final_states,
            normalized_transitions,
        )


class FAStringResult:
    def __init__(
        self,
        fa: FA | None = None,
        string: str | None = None,
        passed: bool = False,
    ) -> None:
        self._string = string
        self.fa = fa
        self.passed = passed

    @property
    def string(self) -> str:
        return "" if self._string is None else self._string

    @string.setter
    def string(self, string: str) -> None:
        self._string = string

    @property
    def is_accepted(self) -> bool:
        return self.passed


class FAConversionResult:
    def __init__(
        self,
        state_names: dict[frozenset[str], str],
    ) -> None:
        self.state_names = state_names

    @property
    def state_names_str(self) -> str:
        string = ""
        for states, name in self.state_names.items():
            string += f"`{self.get_str_from_frozenset(states)}` -> `{name}`\n"
        return string

    def get_embed(self) -> hikari.Embed:
        embed = hikari.Embed(title="Automaton Conversion", color=Color.YELLOW)
        name = "Closure" if len(self.state_names) == 1 else "Closures"
        embed.add_field(f"State {name}", self.state_names_str)
        return embed

    @staticmethod
    def get_str_from_frozenset(states: frozenset[str]) -> str:
        if len(states) == 0:
            return "Trap State"

        buffer = []
        for state in states:
            state = "Trap State" if state == "" else state
            buffer.append(f"`{state}`")
        return f"{{{', '.join(buffer)}}}"


class FAMinimizationResult:
    def __init__(
        self,
        unreachable_states: set[str],
        deleted_states: set[str],
    ) -> None:
        self.unreachable_states = unreachable_states
        self.deleted_states = deleted_states

    @property
    def unreachable_states_str(self) -> str:
        buffer = []
        for state in self.unreachable_states:
            buffer.append(f"`{state}`")

        if buffer == []:
            return "None"

        return f'{{{", ".join(buffer)}}}'

    @property
    def deleted_states_str(self) -> str:
        buffer = []
        for state in self.deleted_states:
            buffer.append(f"`{state}`")

        if buffer == []:
            return "None"

        return f'{{{", ".join(buffer)}}}'

    def get_embed(self) -> hikari.Embed:
        embed = hikari.Embed(
            title="Automaton Minimization", color=Color.YELLOW)
        name = "State" if len(self.deleted_states) == 1 else "States"
        embed.add_field(f"Minimized {name}", self.deleted_states_str)
        name = "State" if len(self.deleted_states) == 1 else "States"
        embed.add_field(f"Unreachable {name}", self.unreachable_states_str)
        return embed


class InputFAModal(miru.Modal):

    _states = miru.TextInput(
        label="States",
        placeholder="q0 q1 q2...",
        required=True,
        value="",
    )
    _alphabets = miru.TextInput(
        label="Alphabets",
        placeholder="a b c...",
        required=True,
        value="",
    )
    _initial_state = miru.TextInput(
        label="Initial State",
        placeholder="q0",
        required=True,
        value="",
    )
    _final_states = miru.TextInput(
        label="Final State(s)",
        placeholder="q2...",
        required=True,
        value="",
    )
    _transition_functions = miru.TextInput(
        label="Transition Functions",
        placeholder="state,symbol(None for ε)=state\nq0,a=q1\nq0,=q2\n...",
        required=True,
        value="",
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
