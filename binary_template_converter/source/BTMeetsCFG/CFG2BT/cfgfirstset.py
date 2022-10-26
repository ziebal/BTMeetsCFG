from typing import Dict, List, Set

from .cfglabel import Label
from .cfglexer import CFGLexer
from .dataclasses import RuleSet, Token
from BTMeetsCFG.converter.logger import Log
from .globaldefines import GlobalDefines


class FirstSet:
    def __init__(self, grammar: Dict[str, RuleSet], symbols: Set[Token]):
        self.__logger = Log(class_name="FirstSet")
        self.__grammar: Dict[str, RuleSet] = grammar
        self.__symbols: Set[Token] = symbols
        self.__first_set: Dict[str, Set[Token]] = self.__init()

    def to_printable(self):
        ret_str = "// First Table:\n"
        for key, value in self.__first_set.items():
            flt = list(filter(lambda x: x.name != "", value))
            if CFGLexer.is_key(key):
                ret_str += f'// {key:30s} {(", ".join(x.name for x in flt)):30s}\n'
        return ret_str

    def get(self, grammar_string: List[Token]) -> Set[Token]:
        if len(grammar_string) == 0:
            return set()

        # Now, we can compute FIRST for any string X1 X2 ... Xn
        first_set: Set[Token] = set()
        epsilon_counter = 0

        for token in grammar_string:
            first_set_of_token: Set[Token] = self.__first_set[token.name]

            first_set.update(GlobalDefines.get_set_without_epsilon(first_set_of_token))

            # if epsilon is in FIRST(X1) and FIRST(X2) then we add FIRST(X3)
            # --> as long as the loop runs every previous FIRST did contain an epsilon.
            if not GlobalDefines.set_has_epsilon(first_set_of_token):
                # FIRST(Xj) did not contain an epsilon, hence no other Xk need to checked.
                break

            epsilon_counter += 1

        # Every FIRST(X1) till FIRST(Xn) contained an epsilon -> add epsilon to first set.
        if epsilon_counter == len(grammar_string):
            first_set.add(
                Token(
                        name="",
                        label=Label.TERMINAL,
                        uid=GlobalDefines.normalize("", Label.TERMINAL)
                    )
            )

        return first_set

    def __init(self) -> Dict[str, Set[Token]]:
        # make sure everything is already initialized with an empty set.
        # this prevents annoying "does the key exist, if not create it" cases.
        fs: Dict[str, Set[Token]] = {}
        for symbol in self.__symbols:
            fs[symbol.name] = set()
        return fs

    def debug_print(self):
        self.__logger.debug(self.__first_set)

    def __first(self, symbol: Token) -> Set[Token]:
        # If X is terminal, then FIRST(X) is {X}.
        if not GlobalDefines.token_in_grammar(symbol, self.__grammar):
            return {symbol}

        first_set: Set[Token] = set()
        rule_set: RuleSet = self.__grammar[symbol.name]
        for rule in rule_set.rules:
            # If X --> e is a production, then add e to FIRST(X).
            if len(rule.tokens) == 1 and rule.tokens[0].name == "":
                first_set.add(rule.tokens[0])

            # If X is nonterminal and X --> Y1 Y2 ... Yk is a production ...
            did_break = False
            for t in rule.tokens:
                t_first_set: Set[Token] = self.__first_set[t.name]
                if GlobalDefines.set_has_epsilon(t_first_set):
                    first_set.update(GlobalDefines.get_set_without_epsilon(t_first_set))
                else:
                    first_set.update(t_first_set)
                    did_break = True
                    break
            if not did_break:
                first_set.add(
                    Token(
                        name="",
                        label=Label.TERMINAL,
                        uid=GlobalDefines.normalize("", Label.TERMINAL)
                    )
                )
        return first_set

    # Source: https://www.cs.uaf.edu/~cs331/notes/FirstFollow.pdf
    #
    # FIRST(a)
    #
    # If a is any string of grammar symbols, let FIRST(a) be the set of terminals that begin the strings derived
    # from a. If a Þ e then e is also in FIRST(a).
    # To compute FIRST(X) for all grammar symbols X, apply the following rules until no more terminals or e can
    # be added to any FIRST set:
    # 1. If X is terminal, then FIRST(X) is {X}.
    # 2. If X => e is a production, then add e to FIRST(X).
    # 3. If X is nonterminal and X => Y1 Y2 ... Yk. is a production, then place a in FIRST(X) if for some i, a is in
    # FIRST(Yi), and e is in all of FIRST(Y1), ... , FIRST(Yi-1); that is, Y1, ... ,Yi-1 Þ e. If e is in FIRST(Yj) for
    # all j = 1, 2, ... , k, then add e to FIRST(X). For example, everything in FIRST(Y1) is surely in
    # FIRST(X). If Y1 does not derive e, then we add nothing more to FIRST(X), but if Y1Þ e, then we add
    # FIRST(Y2) and so on.
    #
    # Now, we can compute FIRST for any string X1X2 . . . Xn as follows. Add to FIRST(X1X2 ... Xn) all the non-e symbols
    # of FIRST(X1). Also add the non-e symbols of FIRST(X2) if e is in FIRST(X1), the non-e symbols
    # of FIRST(X3) if e is in both FIRST(X1) and FIRST(X2), and so on. Finally, add e to FIRST(X1X2 ... Xn) if,
    # for all i, FIRST(Xi) contains e.
    def generate(self) -> None:
        did_change = True
        while did_change:
            did_change = False
            for symbol in self.__symbols:
                current = len(self.__first_set[symbol.name])
                self.__first_set[symbol.name] = self.__first(symbol)
                new = len(self.__first_set[symbol.name])

                if new - current != 0:
                    did_change = True
