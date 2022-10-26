from binary_template_converter.source.BTMeetsCFG.oldVersion.global_defines import GlobalDefines
import json


class FirstSet:
    def __init__(self, production_rules):
        self.__production_rules = production_rules
        self.__first_set = {}
        self.__first_set_pt = {}
        self.__analyse()

    def __str__(self):
        return json.dumps([self.__first_set, self.__first_set_pt], indent=2)

    def __repr__(self):
        return json.dumps([self.__first_set, self.__first_set_pt], indent=2)

    def get_nullable(self):
        nullables = []
        for el in self.__first_set:
            if self.__first_set[el]["epsilon"]:
                nullables.append(el)
        return nullables

    def get_distinct_symbols(self):
        distinct_symbols = set()
        for _, value in self.__first_set.items():
            for entry in value["data"]:
                if entry["token"] != "":
                    distinct_symbols.add(entry["token"])
        return distinct_symbols

    def get_first_without_epsilon(self, token):
        key = token["token"]
        if key not in self.__first_set:
            return {"data": [token], "epsilon": False}, False
        first_set = self.__first_set[key]
        if not first_set["epsilon"]:
            return first_set, False
        first_set_without_epsilon = { "data": [], "epsilon": False}
        for entry in first_set["data"]:
            if not entry["token"] == "":
                first_set_without_epsilon["data"].append(entry)

        return first_set_without_epsilon, first_set["epsilon"]

    def get_first(self, key):
        return self.__first_set[key]

    def get_first_pt(self, key):
        return self.__first_set_pt[key]

    def __analyse(self):
        # generate first set
        # find all tokens and generate their first sets
        for key in self.__production_rules:
            self.__find_first(key)

    def __find_first(self, key):
        # Sources:
        # https://www.geeksforgeeks.org/first-set-in-syntax-analysis/?ref=lbp
        # https://services.informatik.hs-mannheim.de/~schramm/com/files/Kapitel03Teil1.pdf

        # <A> -> <X> | <Y> | <Z> where X, Y and Z are all different rules of A (key)
        # iterate each rule independently and add to First(A)
        self.__first_set[key] = {"data": [], "epsilon": False}
        for rule in self.__production_rules[key]:
            pt_key = key + GlobalDefines.hash_rule(rule)
            self.__first_set_pt[pt_key] = {"data": [], "epsilon": False}
            # if <A> is NON_TERMINAL and <A> -> <X1><X2><X3>...<Xk> in Production rules
            token_count = len(rule)
            epsilon_count = 0
            for token in rule:
                # 1. If x is a terminal, then FIRST(x) = { ‘x’ }
                # 2. If x-> Є, is a production rule, then add Є to FIRST(x).
                if token["label"] == GlobalDefines.TERMINAL:
                    self.__append_to_first_set(key, token, pt_key)
                    break

                # 3. If X->Y1 Y2 Y3….Yn is a production (and every non terminal is a production)
                if token["label"] == GlobalDefines.NON_TERMINAL:
                    # 3.1 FIRST(X) = FIRST(Y1)
                    self.__find_first(token["token"])
                    self.__append_first_set_to_first_set(key, self.__first_set[token["token"]], pt_key, with_epsilon=False)

                    # 3.2 If FIRST(Y1) contains Є then FIRST(X) = { FIRST(Y1) – Є } U { FIRST(Y2) }
                    if not self.__first_set[token["token"]]["epsilon"]:
                        # 3.2 not satisfied
                        break
                    else:
                        # 3.2 satisfied
                        epsilon_count = epsilon_count + 1

            # 3.3 If FIRST (Yi) contains Є for all i = 1 to n, then add Є to FIRST(X).
            if epsilon_count == token_count:
                self.__append_epsilon_to_first_set(key, pt_key)

    def __append_first_set_to_first_set(self, key, other_first_set, pt_key, with_epsilon=True):
        for entry in other_first_set["data"]:
            if not with_epsilon and entry["token"] == "":
                continue
            self.__append_to_first_set(key, entry, pt_key)

    def __append_epsilon_to_first_set(self, key, pt_key):
        epsilon = {'label': 'terminal', 'token': '', 'uid': 'TERMINAL_4E686A'}
        self.__append_to_first_set(key, epsilon, pt_key)

    def __append_to_first_set(self, key, token, pt_key):
        # if token is already added to given set then the grammar might not be LL(1)
        # todo needs to be evaluated further, not sure if this simple check is sufficient
        # todo ^ see https://www.cs.hs-rm.de/~weber/fachsem/vortraege/ll1.pdf Analyse 1
        for el in self.__first_set[key]["data"]:
            if el["uid"] == token["uid"]:
                raise Exception(f'Grammar not LL(1)! Key: {key}, Token: {token}, Current FirstSet: {json.dumps(self.__first_set, indent=2)}')
        if token["token"] == "":
            self.__first_set[key]["epsilon"] = True
        self.__first_set[key]["data"].append(token)

        for el in self.__first_set_pt[pt_key]["data"]:
            if el["uid"] == token["uid"]:
                raise Exception(f'Grammar not LL(1)! Key: {pt_key}, Token: {token}, Current FirstSetPT: {json.dumps(self.__first_set_pt, indent=2)}')
        if token["token"] == "":
            self.__first_set_pt[pt_key]["epsilon"] = True
        self.__first_set_pt[pt_key]["data"].append(token)