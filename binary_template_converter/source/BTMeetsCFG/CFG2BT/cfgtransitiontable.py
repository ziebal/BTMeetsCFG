from typing import List, Dict, Set, Optional

from BTMeetsCFG.CFG2BT.cfgfirstset import FirstSet
from BTMeetsCFG.CFG2BT.cfgfollowset import FollowSet
from BTMeetsCFG.CFG2BT.cfglabel import Label
from BTMeetsCFG.CFG2BT.dataclasses import RuleSet, Token, Rule
from BTMeetsCFG.CFG2BT.globaldefines import GlobalDefines
from BTMeetsCFG.converter.logger import Log


class Symbol:
    def __init__(self, name: str):
        self.__rule: Optional[Rule] = None
        self.name: str = name

    def get_rule(self) -> Rule:
        return self.__rule

    def set_rule(self, rule: Rule) -> None:
        if self.__rule is not None:
            raise Exception(f'Grammar not LL1. Duplicate Rule for Symbol found! (Symbol: {self.name}, New Rule: {",".join(x.name for x in rule.tokens)}, Current Rule: {",".join(x.name for x in self.__rule.tokens)})')
        self.__rule = rule


class TableEntry:
    def __init__(self, name: str):
        self.name: str = name
        self.symbols: List[Symbol] = []

    def find_symbol(self, key: str):
        for symbol in self.symbols:
            if symbol.name == key:
                return symbol
        raise Exception(f"Symbol not found! (Was looking for {key} in TableEntry {self.name})")


class TransitionTable:
    def __init__(self, grammar: Dict[str, RuleSet], terminals: List[Token], first_set: FirstSet, follow_set: FollowSet):
        self.__logger = Log(class_name="TransitionTable")
        self.__table: Dict[str, TableEntry] = self.__init(grammar, terminals, first_set, follow_set)

    def debug_print(self):
        self.__logger.debug(self.__table)

    def get(self) -> Dict[str, TableEntry]:
        return self.__table

    def __init(self, grammar: Dict[str, RuleSet], terminals: List[Token], first_set: FirstSet, follow_set: FollowSet) -> Dict[str, TableEntry]:
        table: Dict[str, TableEntry] = {}

        # init table
        for _, rule_set in grammar.items():
            tableEntry = TableEntry(name=GlobalDefines.normalize(rule_set.symbol.name, Label.NON_TERMINAL))
            for terminal in terminals:

                if terminal.name == "":
                    continue  # Skip epsilon

                tableEntry.symbols.append(Symbol(terminal.name))

            table[rule_set.symbol.name] = tableEntry

        # fill table
        for _, rule_set in grammar.items():

            for rule in rule_set.rules:
                gamma: Set[Token] = first_set.get(rule.tokens)
                tableEntry = table[rule_set.symbol.name]

                for a in gamma:
                    if a.name == "":
                        continue  # Skip epsilon

                    symbol: Symbol = tableEntry.find_symbol(a.name)
                    symbol.set_rule(rule)

                if GlobalDefines.set_has_epsilon(gamma):
                    for a in follow_set.get(rule_set.symbol.name):
                        if a.name == "":
                            continue  # Skip epsilon

                        symbol: Symbol = tableEntry.find_symbol(a.name)
                        symbol.set_rule(rule)

        return table
