from typing import List, Dict
from .globaldefines import Label


class Token:
    def __init__(self, name: str, label: Label, uid: str):
        self.name: str = name
        self.label: Label = label
        self.uid: str = uid

    def __hash__(self):
        return hash(self.uid)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.uid == other.uid


class Rule:
    def __init__(self, tokens: List[Token]):
        self.tokens: List[Token] = tokens

    def __str__(self):
        return ",".join(x.name for x in self.tokens)


class RuleSet:
    def __init__(self, symbol: Token, rules=None):
        if rules is None:
            rules = []
        self.symbol: Token = symbol
        self.rules: List[Rule] = rules

    def append(self, rule):
        self.rules.append(rule)
