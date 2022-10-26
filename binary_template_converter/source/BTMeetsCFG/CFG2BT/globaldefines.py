import hashlib
import json
from typing import Dict, Set

from .cfglabel import Label
from .dataclasses import Token, RuleSet


class GlobalDefines:
    @staticmethod
    def token_in_grammar(token: Token, grammar: Dict[str, RuleSet]) -> bool:
        for key in grammar:
            if token.name == key:
                return True
        return False

    @staticmethod
    def set_has_epsilon(token_set: Set[Token]) -> bool:
        for token in token_set:
            if token.name == "":
                return True
        return False

    @staticmethod
    def get_set_without_epsilon(token_set: Set[Token]) -> Set[Token]:
        new_set: Set[Token] = set()
        for token in token_set:
            if token.name == "":
                continue
            new_set.add(token)
        return new_set

    @staticmethod
    def normalize(token: str, label: Label):
        # creates a unique identifier for a labeled token.
        token_alnum = filter(str.isalpha, token)
        label_alnum = filter(str.isalpha, label.value)
        alnum_filter = "".join(token_alnum) + "_" + "".join(label_alnum)
        h = hashlib.sha256()
        h.update((token + label.value).encode("utf-8"))
        return f'{"".join(alnum_filter).upper()}_{h.hexdigest()[0:6].upper()}'

    @staticmethod
    def contained_in_set(uid, s):
        for e in s["data"]:
            if e["uid"] == uid:
                return True
        return False

    @staticmethod
    def hash_rule(rule):
        string = json.dumps(rule)
        h = hashlib.sha256()
        h.update(string.encode("utf-8"))
        return f'rule_{h.hexdigest()[0:24].upper()}'
