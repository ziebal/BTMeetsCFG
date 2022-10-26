import json
import re

file_name = "token_test"

file_path = "D:/projects/bachelor-proposal/input_requires_padding/"
outp_path = "D:/projects/bachelor-proposal/padded_grammar/"
RE_NONTERMINAL = re.compile(r'(<[^<> ]*>)')


def load_grammar():
    file = open(file_path + file_name + ".json", "r")
    g = json.load(file)
    file.close()
    return g


def is_key(string):
    return re.match(RE_NONTERMINAL, string)


def is_not_key(string):
    return not re.match(RE_NONTERMINAL, string)


def get_tokens(str_lst, f=False):
    token_lst = []
    for val in str_lst:
        if val == "":
            token_lst.append([""])
            continue
        tokens = re.split(RE_NONTERMINAL, val)
        token_lst_all = list(filter(None, tokens))
        if f:
            token_lst.append(list(filter(is_not_key, token_lst_all)))
        else:
            token_lst.append(token_lst_all)
    return token_lst


def search_pad_length(g):
    longest_string = 0
    for _, val in g.items():
        for t_lst in get_tokens(val, True):
            for t in t_lst:
                if len(t) > longest_string:
                    longest_string = len(t)
    return longest_string


def add_padding(rule, l):
    for i in range(len(rule)):
        if is_not_key(rule[i]):
            rule[i] = rule[i].ljust(l)
    return rule


def pad_grammar(g, l):
    new_grammar = {}
    for key, val in g.items():
        new_grammar[key] = []
        split_rules = get_tokens(val)
        print(split_rules)
        for rule in split_rules:
            new_grammar[key].append("".join(add_padding(rule, l)))
    return new_grammar


if __name__ == '__main__':
    grammar = load_grammar()
    pad_length = search_pad_length(grammar)
    p_grammar = pad_grammar(grammar, pad_length)
    file = open(outp_path + file_name + "_padded.json", 'w')
    file.write(json.dumps(p_grammar, indent=2))
    file.close()
