from typing import Dict, List, Set

from .cfgfirstset import FirstSet
from .cfglabel import Label
from .dataclasses import RuleSet, Token
from BTMeetsCFG.converter.logger import Log
from .globaldefines import GlobalDefines


class FollowSet:
    def __init__(self, grammar: Dict[str, RuleSet], first_set: FirstSet, symbols: Set[Token]):
        self.__logger = Log(class_name="FollowSet")
        self.__grammar: Dict[str, RuleSet] = grammar
        self.__first_set: FirstSet = first_set
        self.__symbols: Set[Token] = symbols
        self.__changed = True
        self.__follow_set: Dict[str, Set[Token]] = self.__init()
        self.__follow_set_by_rule: Dict[str, Set[Token]] = {}
        self.__DEBUG_TOKEN = Token(
            name="UNKNOWN",
            label=Label.TERMINAL,
            uid=GlobalDefines.normalize("UNKNOWN", Label.TERMINAL)
        )

    def __init(self) -> Dict[str, Set[Token]]:
        # make sure everything is already initialized with an empty set.
        # this prevents annoying "does the key exist, if not create it" code snippets.
        fs: Dict[str, Set[Token]] = {}
        for symbol in self.__symbols:
            fs[symbol.name] = set()
        return fs

    def debug_print(self):
        self.__logger.debug(self.__follow_set)

    def debug_print_by_rule(self):
        self.__logger.debug(self.__follow_set_by_rule)

    def to_printable(self):
        ret_str = "// Follow Table Table:\n"
        for key, value in self.__follow_set.items():
            flt = list(filter(lambda x: x.name != "", value))
            ret_str += f'// {key:30s} {(", ".join(x.name for x in flt)):30s}\n'
        return ret_str

    def get(self, key: str) -> Set[Token]:
        return self.__follow_set[key]

    def get_specific_follow(self, rule_name: str, partial_rule: List[Token]):
        return self.__follow_set_by_rule[f'{rule_name}#{"-".join(x.name for x in partial_rule)}']

    def __get_follow_by_rule(self, rule_name: str, token: str):
        ret = []
        for k, v in self.__follow_set_by_rule.items():
            if k.startswith(rule_name + "#" + token):
                ret.append(k)
        return ret

    def debug_get_specific(self):
        return self.__follow_set_by_rule

    def __follow_set_update(self, rule_name: str, partial_rule: List[Token], key: str, tokens: List[Token]):
        if f'{rule_name}#{"-".join(x.name for x in partial_rule)}' not in self.__follow_set_by_rule.keys():
            self.__follow_set_by_rule[f'{rule_name}#{"-".join(x.name for x in partial_rule)}'] = set()
        self.__follow_set_by_rule[f'{rule_name}#{"-".join(x.name for x in partial_rule)}'].update(tokens)


        # this function is required because the algorithm has to run until no more changes occur.
        # this function tracks changes to any set.
        current = len(self.__follow_set[key])
        self.__follow_set[key].update(tokens)
        new = len(self.__follow_set[key])
        if new - current != 0:
            self.__changed = True

    def __follow(self, rule_set: RuleSet):
        # TODO this step is probably useless because the lexer already alters the grammar with endmarker "$"
        # 1. Place $ in FOLLOW(S), where S is the start symbol and $ is the input right endmarker.
        self.__follow_set_update("<start>", [], "<start>", [Token(
            name="$",
            label=Label.TERMINAL,
            uid=GlobalDefines.normalize("$", Label.TERMINAL)
        )])

        for rule_org in rule_set.rules:

            # Weird python stuff for reversing a list without altering the original list ....
            # #deepcopy #justpythonthings
            tokens = rule_org.tokens[:]

            # we proceed back to front
            tokens.reverse()

            # 2. If there is a production A --> aBb, then everything in FIRST(b), except for e, is placed in FOLLOW(B).
            prev_list = []
            for token in tokens:
                first_prev = self.__first_set.get(prev_list)
                # self.__logger.debug((prev_list, first_prev))
                self.__follow_set_update(
                    rule_set.symbol.name, prev_list,
                    token.name, list(GlobalDefines.get_set_without_epsilon(first_prev)))

                # insert at the start cause we iterate backwards over the list of tokens.
                # in order to maintain the original string eg we iterate over:
                # b<Y><H><G>
                # -> reverse: <G><H><Y>b
                #
                # APPEND VS INSERT 0
                # -> append into list:
                # 1. <G>
                # 2. <H>
                # 3. <Y>
                # --> Results into <G><H><Y> but this is not the correct substring of b<Y><H><G>
                #
                # -> insert at beginning:
                # 1. <G>
                # 2. <H>
                # 3. <Y>
                # --> Results into <Y><H><G> which is the correct substring b<Y><H><G>
                prev_list.insert(0, token)

            # 3. If there is a production A --> aB, or a production A --> aBb where FIRST(b) contains e (i.e., b --> e),
            # then everything in FOLLOW(A) is in FOLLOW(B).
            prev_list = []
            for token in tokens:
                follow_A = self.__follow_set[rule_set.symbol.name]

                if len(prev_list) == 0 or GlobalDefines.set_has_epsilon(self.__first_set.get(prev_list)):
                    self.__follow_set_update(
                        rule_set.symbol.name, prev_list,
                        token.name, list(follow_A))

                # insert at the start cause we iterate backwards over the list of tokens.
                # see comment above
                prev_list.insert(0, token)

    # Source: https://www.cs.uaf.edu/~cs331/notes/FirstFollow.pdf
    #
    # FOLLOW(A)
    #
    # Define FOLLOW(A), for nonterminal A, to be the set of terminals a that can appear immediately to the right
    # of A in some sentential form, that is, the set of terminals a such that there exists a derivation of the form
    # SÞaAab for some a and b. Note that there may, at some time during the derivation, have been symbols
    # between A and a, but if so, they derived e and disappeared. If A can be the rightmost symbol in some
    # sentential form, then $, representing the input right endmarker, is in FOLLOW(A).
    #
    # To compute FOLLOW(A) for all nonterminals A, apply the following rules until nothing can be added to any
    # FOLLOW set:
    # 1. Place $ in FOLLOW(S), where S is the start symbol and $ is the input right endmarker.
    # 2. If there is a production A Þ aBb, then everything in FIRST(b), except for e, is placed in FOLLOW(B).
    # 3. If there is a production A Þ aB, or a production A Þ aBb where FIRST(b) contains e (i.e., b Þe),
    # then everything in FOLLOW(A) is in FOLLOW(B).
    def generate(self):
        while self.__changed:
            self.__changed = False
            for _, value in self.__grammar.items():
                self.__follow(value)
