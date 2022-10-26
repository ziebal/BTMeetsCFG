from binary_template_converter.source.BTMeetsCFG.oldVersion.global_defines import GlobalDefines
import json


class FollowSetSpecific:
    def __init__(self, production_rules, first_set, follow_set, parsing_table):
        self.__production_rules = production_rules
        self.__first_set = first_set
        self.__follow_set = follow_set
        self.__parsing_table = parsing_table
        self.__follow_set_specific = {}
        self.__analyse()

    def __str__(self):
        return json.dumps(self.__follow_set_specific, indent=2)

    def __repr__(self):
        return json.dumps(self.__follow_set_specific, indent=2)

    def get_iterable(self):
        return self.__follow_set_specific

    def get_follow_specific(self, key):
        return self.__follow_set_specific[key]

    def __update_rule_2(self, rule, key_of_rule):
        # Provide all the information required for the "struct" arguments.

        # Index is required to check for the follow symbol of a non terminal.
        index = 0
        for entry in rule:
            # Pre init with default values.
            entry["__debug_index"] = index
            entry["follow"] = []
            entry["follow_size"] = 0
            entry["include_parent_follow"] = False

            # No need to create follow set for terminals.
            # if entry["label"] == "terminal":
            #     index = index + 1
            #     continue

            first, epsilon = self.__first_set.get_first_without_epsilon(rule[index])
            entry["follow_contained_epsilon"] = epsilon
            # print(rule[index], json.dumps(first, indent=2), epsilon)

            # Implementation of rules depending if there is a following symbol or not.
            if index + 1 < len(rule):

                epsilon2 = True
                ic = 1
                while epsilon2:
                    if index + ic is len(rule):
                        entry["include_parent_follow"] = True
                        break

                    follow2, epsilon2 = self.__first_set.get_first_without_epsilon(rule[index + ic])
                    ic = ic + 1

                    for f in follow2["data"]:
                        entry["follow"].append(f)
                        entry["follow_size"] = entry["follow_size"] + 1

            else:
                # TODO: Implementation required.
                # If A->pB is a production, then everything in FOLLOW(A) is in FOLLOW(B)
                # assert index + 1 < len(rule), "Grammar is not supported. Missing implementation."
                entry["include_parent_follow"] = True

            index = index + 1
        return rule

    def __update_rule(self, rule, key_of_rule):
        # Provide all the information required for the "struct" arguments.

        # Index is required to check for the follow symbol of a non terminal.
        index = 0

        for entry in rule:
            # Pre init with default values.
            entry["__debug_index"] = index
            entry["follow"] = []
            entry["follow_size"] = 0
            entry["include_parent_follow"] = False

            # No need to create follow set for terminals.
            # if entry["label"] == "terminal":
            #     index = index + 1
            #     continue

            # Implementation of rules depending if there is a following symbol or not.
            if index + 1 < len(rule):
                # If A -> pBq is a production, where p, B and q are any grammar symbols,
                # ; X ;
                # then everything in FIRST(q) except Є is in FOLLOW(B).
                follow2, epsilon2 = self.__first_set.get_first_without_epsilon(rule[index + 1])
                print(rule[index+1], json.dumps(follow2, indent=2), epsilon2)

                for f in follow2["data"]:
                    entry["follow"].append(f)
                    entry["follow_size"] = entry["follow_size"] + 1

                entry["follow_contained_epsilon"] = epsilon2

                # TODO: Implementation required.
                # If A->pBq is a production and FIRST(q) contains Є,
                # then FOLLOW(B) contains { FIRST(q) – Є } U FOLLOW(A)
                # We already added FIRST(q) - Є to FOLLOW(B), now we need to add FOLLOW(A)
                # Self Note: This seems to only affect the case where "q" is the last symbol
                # TODO: update: this does NOT apply to the last symbol but all.
                # Multiple Є after another fail.
                # See sample37.json for an example
                if epsilon2 and index + 1 is len(rule) - 1:
                    # entry["follow"].append(f"FOLLOW({key_of_rule}) A->pBq")
                    entry["include_parent_follow"] = True

            else:
                # TODO: Implementation required.
                # If A->pB is a production, then everything in FOLLOW(A) is in FOLLOW(B)
                # assert index + 1 < len(rule), "Grammar is not supported. Missing implementation."
                entry["include_parent_follow"] = True

            index = index + 1
        return rule

    def __analyse(self):
        # TODO missing EOF
        for key, value in self.__parsing_table.get_table().items():
            y = value["y_axis"]
            x = value["x_axis"]
            rule = value["rule"]
            rule_hash = value["rule_hash"]
            key_ = value["key"]

            # We can ignore empty rules. We don't need those for generating the code.
            if rule_hash is None:
                continue

            # Initialize the dictionaries if not already done.
            if y not in self.__follow_set_specific.keys():
                self.__follow_set_specific[y] = {}
                self.__follow_set_specific[y]["switch"] = {}
                self.__follow_set_specific[y]["select"] = {}

            # TODO: remove debug print
            # print(key, json.dumps(value, indent=2))

            # Give the rule a unique name.
            self.__follow_set_specific[y]["name"] = GlobalDefines.normalize(y, "non_terminal")

            # Get the first symbols from the first set.
            # TODO should this be get_fist_without_epsilon ?
            # First with epsilon is probably required, see example:
            # A ::= Z ;
            # Z ::= X Y
            # X ::= ''
            # Y ::= a
            key_obj = self.__first_set.get_first(key_)
            first_set = []
            for f in key_obj["data"]:
                # TODO: remove epsilon until above is addressed
                if f["token"] == "":
                    continue
                first_set.append(f)

            self.__follow_set_specific[y]["select"] = first_set
            self.__follow_set_specific[y]["select_size"] = len(first_set)

            # Provide all the information required to build the "switch" instruction and
            # the "struct" arguments call.
            self.__follow_set_specific[y]["switch"][x] = {
                "rule": self.__update_rule_2(rule, y),
                "name": value["data"]
            }

        # TODO: remove debug print
        # print(json.dumps(self.__follow_set_specific, indent=2))

