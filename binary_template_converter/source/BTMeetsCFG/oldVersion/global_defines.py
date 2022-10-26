import hashlib
import json


class GlobalDefines:
    TERMINAL = "terminal"
    NON_TERMINAL = "non_terminal"

    @staticmethod
    def normalize(token, label):
        # creates a unique identifier for a labeled token.
        token_alnum = filter(str.isalpha, token)
        label_alnum = filter(str.isalpha, label)
        alnum_filter = "".join(token_alnum) + "_" + "".join(label_alnum)
        h = hashlib.sha256()
        h.update((token + label).encode("utf-8"))
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
