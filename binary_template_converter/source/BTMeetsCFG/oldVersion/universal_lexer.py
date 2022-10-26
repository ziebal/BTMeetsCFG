import json
import re
from global_defines import GlobalDefines
RE_NONTERMINAL = re.compile(r'(<[^<> ]*>)')


class UniversalLexer:

    def __init__(self, input_grammar):
        self.__found_longest_token = False
        self.__longest_token = 0
        self.__input_grammar = input_grammar
        self.__terminals = []
        self.__token_lst = self.__analyse()

    def __str__(self):
        return json.dumps({"tokens": self.__token_lst, "padding": self.__longest_token}, indent=2)

    def __repr__(self):
        return json.dumps({"tokens": self.__token_lst, "padding": self.__longest_token}, indent=2)

    def get_tokens(self):
        return self.__token_lst

    def get_token_length(self):
        return self.__longest_token

    def get_terminals(self):
        return self.__terminals

    def __analyse(self):
        for i in range(2):
            self.__terminals = []
            has_start_token = 0
            token_lst = {}
            for key in self.__input_grammar:
                if key == "<start>":
                    has_start_token = has_start_token + 1
                token_lst[key] = self.__get_tokens_by_key(key)

            if has_start_token != 1:
                raise Exception(f'Wrong amount of start tokens. Found {has_start_token}')

            self.__found_longest_token = True

        return token_lst

    def __get_tokens_by_key(self, key):
        if not self.__is_key(key):
            raise Exception(f'Key "{key}" is not in the required format. Keys have to fit following regex: <[^<> ]*>)')
        tokens = []
        for raw_token in self.__input_grammar[key]:
            sub_tokens = self.__split_expression(raw_token)
            labeled_sub_tokens = self.__label_sub_tokens(sub_tokens)
            tokens.append(labeled_sub_tokens)
        return tokens

    def __label_sub_tokens(self, sub_tokens):
        labeled_sub_tokens = []
        for sub_token in sub_tokens:
            if self.__is_key(sub_token):
                labeled_sub_tokens.append({"token": sub_token,
                                           "label": GlobalDefines.NON_TERMINAL,
                                           "uid": GlobalDefines.normalize(sub_token, GlobalDefines.NON_TERMINAL)})
            else:
                t = {"token": sub_token, "label": GlobalDefines.TERMINAL, "uid": GlobalDefines.normalize(sub_token, GlobalDefines.TERMINAL)}
                labeled_sub_tokens.append(t)
                self.__terminals.append(t)
        return labeled_sub_tokens

    @staticmethod
    def __is_key(string):
        return re.match(RE_NONTERMINAL, string)

    @staticmethod
    def __is_not_key(string):
        return not re.match(RE_NONTERMINAL, string)

    def __pad_terminals(self, token_list):
        new_list = []
        for entry in token_list:
            if not re.match(RE_NONTERMINAL, entry):
                new_list.append(entry.ljust(self.__longest_token))
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
        return token_list

