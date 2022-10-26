import re
import json
from hashlib import sha256

RE_NONTERMINAL = re.compile(r'(<[^<> ]*>\'{1,})')

def hash(string):
    return sha256(string.encode('utf-8')).hexdigest()[:8]

def fix_non_terminal(s):
    found = re.findall(RE_NONTERMINAL, s)
    for f in found:
        print(f)
        s = s.replace(f, f"<{hash(f)}>")
    return s

def remove_epsilon(array):
    ret = []
    for a in array:
        if a == 'ϵ':
            ret.append("")
        else:
            ret.append(a)
    return ret

def main():
    grammar = []
    with open("./grammar.txt", "r") as f:
        for line in f.readlines():
            line = fix_non_terminal(line)
            if "->" in line:
                grammar.append(tuple(line.strip("\n").lstrip().split(" -> ")))
            else:
                tp = grammar[-1]
                l = line.strip("\n").lstrip()
                tp = (tp[0], tp[1] + l)
                grammar[-1] = tp
    new_grammar = {}
    for entry in grammar:
        value = entry[1].replace(" ", "")
        value = value.split("|")
        value = remove_epsilon(value)
        new_grammar[entry[0]] = value

    print(json.dumps(new_grammar, indent=4))
    

if __name__ == "__main__":
    main()