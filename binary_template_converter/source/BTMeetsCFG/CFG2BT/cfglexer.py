import json
import re
from typing import List, Dict, Set

from BTMeetsCFG.converter.logger import Log
from .cfglabel import Label
from .globaldefines import GlobalDefines
from .dataclasses import Token, Rule, RuleSet


RE_NONTERMINAL = re.compile(r'(<[^<> ]*>)')
PADDING = False
SPLITTING = True


class CFGLexer:

    def __init__(self, input_grammar: Dict[str, List[str]]):
        self.__logger = Log(class_name="CFGLexer")
        self.__found_longest_token = False
        self.__longest_token: int = 0
        self.__input_grammar: Dict[str, List[str]] = self.__modify_input_grammar(input_grammar)
        self.__terminals: List[Token] = []
        self.__symbols: Set[Token] = set()
        self.__grammar: Dict[str, RuleSet] = self.__analyse()

    def convert_string(self, s: str) -> List[Token]:
        tokens_raw: List[str] = self.__split_expression(s)
        tokens: List[Token] = []
        for tr in tokens_raw:
            for t in self.__symbols:
                if t.name == tr:
                    tokens.append(t)
                    break

        return tokens

    def debug_print(self):
        self.__logger.debug({"tokens": self.__grammar, "symbols": self.__symbols, "padding": self.__longest_token})

    def get_grammar(self) -> Dict[str, RuleSet]:
        return self.__grammar

    def get_grammar_as_cfg(self):
        cfg = {}
        grammar = self.__grammar
        for _, ruleSet in grammar.items():
            rulesCfg = []
            for rule in ruleSet.rules:
                r = ""
                for token in rule.tokens:
                    r += token.name
                rulesCfg.append(r)
            cfg[ruleSet.symbol.name] = rulesCfg
        return json.dumps(cfg, indent=4)

    def get_symbols(self) -> Set[Token]:
        return self.__symbols

    def get_token_length(self) -> int:
        return self.__longest_token

    def get_terminals(self) -> List[Token]:
        return self.__terminals

    def get_input_grammar(self) -> Dict[str, List[str]]:
        return self.__input_grammar

    def __generate_token(self, name: str, label: Label) -> Token:
        t: Token = Token(
            name=name,
            label=label,
            uid=GlobalDefines.normalize(name, label)
        )
        self.__symbols.add(t)
        return t

    @staticmethod
    def __modify_input_grammar(input_grammar):
        # first check that the input grammar does not contain EoF marker.
        for key, value in input_grammar.items():
            if "$" in ''.join(value):
                raise Exception(f"Grammar can not contain the reserved symbol '$'!\nKey: {key}\nRules: {value}")
            #if "@" in ''.join(value):
            #    raise Exception(f"Grammar can not contain the reserved symbol '@'!\nKey: {key}\nRules: {value}")

        # alert <start> entry to add additional information
        # insert intermediate start section
        input_grammar["<__start_internal>"] = input_grammar["<start>"]

        # replace original start section
        input_grammar["<start>"] = []
        input_grammar["<start>"].append("<__start_internal>$")

        return input_grammar

    def __analyse(self) -> Dict[str, RuleSet]:
        grammar: Dict[str, RuleSet] = {}
        for i in range(2):
            self.__terminals = []
            has_start_token = 0
            grammar: Dict[str, RuleSet] = {}
            for key in self.__input_grammar:
                if key == "<start>":
                    has_start_token = has_start_token + 1
                grammar[key] = self.__get_rule_set(key)

            if has_start_token != 1:
                raise Exception(f'Wrong amount of start tokens. Found {has_start_token}')

            self.__found_longest_token = True

        return grammar

    def __get_rule_set(self, key: str) -> RuleSet:
        if not self.is_key(key):
            raise Exception(f'Key "{key}" is not in the required format. Keys have to fit following regex: <[^<> ]*>)')
        token_key: Token = self.__generate_token(key, Label.NON_TERMINAL)
        self.__symbols.add(token_key)
        ruleSet: RuleSet = RuleSet(token_key)
        for raw_token in self.__input_grammar[key]:
            sub_tokens = self.__split_expression(raw_token)
            rule: Rule = self.__get_rule(sub_tokens)
            ruleSet.append(rule)
        return ruleSet

    def __get_rule(self, sub_tokens) -> Rule:
        labeled_sub_tokens: List[Token] = []
        for sub_token in sub_tokens:
            if self.is_key(sub_token):
                t: Token = self.__generate_token(sub_token, Label.NON_TERMINAL)
                labeled_sub_tokens.append(t)
            else:
                t: Token = self.__generate_token(sub_token, Label.TERMINAL)
                labeled_sub_tokens.append(t)
                self.__terminals.append(t)
        return Rule(labeled_sub_tokens)

    @staticmethod
    def is_key(string):
        return re.match(RE_NONTERMINAL, string)

    @staticmethod
    def __is_not_key(string):
        return not re.match(RE_NONTERMINAL, string)

    def __pad_terminals(self, token_list):
        new_list = []
        for entry in token_list:
            if PADDING and not re.match(RE_NONTERMINAL, entry):
                new_list.append(entry.ljust(self.__longest_token, "@"))
            else:
                new_list.append(entry)
        return new_list

    @staticmethod
    def __get_max_str(lst, fallback=''):
        return max(lst, key=len) if lst else fallback

    def __split_expression(self, string):
        if string == "":
            return [""]
        tokens = re.split(RE_NONTERMINAL, string)
        token_list = list(filter(None, tokens))
        if self.__found_longest_token:
            token_list = self.__pad_terminals(token_list)
        else:
            token_len = len(self.__get_max_str(list(filter(self.__is_not_key, token_list))))
            if token_len > self.__longest_token:
                self.__longest_token = token_len
        if SPLITTING:
            new_token_list = []
            for token in token_list:
                if self.is_key(token):
                    new_token_list.append(token)
                else:
                    new_token_list.extend(list(token))
                    token_list = new_token_list
                    # print(token_list)
        return token_list

