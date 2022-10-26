import json
import re


RE_NONTERMINAL = re.compile(r'(<[^<> ]*>)')


def is_key(string):
    return re.match(RE_NONTERMINAL, string)

def split_expression(string):
    if string == "":
        return ["ϵ"]
    tokens = re.split(RE_NONTERMINAL, string)
    token_list = list(filter(None, tokens))
    return token_list

def main():
    with open("./grammar.json", "r") as f:
        grammar = json.load(f)
    for k, v in grammar.items():
        values = []
        for entry in v:
            s = ""
            tokens = split_expression(entry)
            for token in tokens:
                if not is_key(token):
                    s += ' '.join(token) + " "
                else:
                    s += token + " "
            values.append(s)

        print(f"{k} -> {'| '.join(values)}")
    

if __name__ == "__main__":
    main()