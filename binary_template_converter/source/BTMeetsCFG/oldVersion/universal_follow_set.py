from binary_template_converter.source.BTMeetsCFG.oldVersion.global_defines import GlobalDefines
import json


class FollowSet:
    def __init__(self, production_rules, first_set):
        self.__production_rules = production_rules
        self.__first_set = first_set
        self.__follow_set = {}
        self.__analyse()

    def __str__(self):
        return json.dumps(self.__follow_set, indent=2)

    def __repr__(self):
        return json.dumps(self.__follow_set, indent=2)

    def get_follow(self, key):
        return self.__follow_set[key]

    def get_distinct_symbols(self):
        distinct_symbols = set()
        for _, value in self.__follow_set.items():
            for entry in value["data"]:
                if entry["token"] != "$":
                    distinct_symbols.add(entry["token"])
        return distinct_symbols

    def __find_follow(self, key):
        # FOLLOW(S) = { $ }   // where S is the starting Non-Terminal
        if key == "<start>" and key not in self.__follow_set:
            self.__follow_set[key] = { "data": [{"token": "$", "label": GlobalDefines.TERMINAL, "uid": "None"}]}
        else:
            if key not in self.__follow_set:
                self.__follow_set[key] = {"data": []}

        rule = self.__production_rules[key]
        for expr in rule:
            for i in range(len(expr)):
                token_B = expr[i]
                if token_B["label"] == GlobalDefines.NON_TERMINAL:
                    self.__create_follow_set(token_B)

                # If A->pB is a production, then everything in FOLLOW(A) is in FOLLOW(B)
                if token_B["label"] == GlobalDefines.NON_TERMINAL and i == len(expr) - 1:
                    if token_B["token"] == key:
                        continue
                    self.__append_set_to_set(self.__follow_set[token_B["token"]], self.__follow_set[key])
                else:
                    # If A -> pBq is a production, where p, B and q are any grammar symbols,
                    # then everything in FIRST(q)  except Є is in FOLLOW(B).
                    if token_B["label"] == GlobalDefines.TERMINAL:
                        continue
                    token_beta = expr[i+1]
                    beta_first_set_without_epsilon, had_epsilon = self.__first_set.get_first_without_epsilon(token_beta)
                    self.__append_set_to_set(self.__follow_set[token_B["token"]], beta_first_set_without_epsilon)

                    # If A->pBq is a production and FIRST(q) contains Є,
                    # then FOLLOW(B) contains { FIRST(q) – Є } U FOLLOW(A)
                    if had_epsilon:
                        print("Key:", key)
                        self.__append_set_to_set(self.__follow_set[token_B["token"]], self.__follow_set[key])

    def __append_set_to_set(self, target_set, src_set):
        for entry in src_set["data"]:
            if not GlobalDefines.contained_in_set(entry["uid"], target_set):
                target_set["data"].append(entry)

    def __create_follow_set(self, expr):
        key = expr["token"]
        if key not in self.__follow_set:
            self.__follow_set[key] = {"data": []}

    @staticmethod
    def __count_set_size(s):
        count = 0
        for key in s:
            count = count + len(s[key]["data"])
        return count

    def __analyse(self):
        current_count = 0
        old_count = -1
        while current_count != old_count:
            old_count = current_count
            for key in self.__production_rules:
                self.__find_follow(key)
            current_count = self.__count_set_size(self.__follow_set)
