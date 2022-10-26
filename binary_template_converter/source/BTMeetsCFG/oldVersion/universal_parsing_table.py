import json
from binary_template_converter.source.BTMeetsCFG.oldVersion.global_defines import GlobalDefines


class ParsingTable:
    def __init__(self, first_set, follow_set, lexer, IGNORE_DUPLICATES = False):
        self.__first_set = first_set
        self.__follow_set = follow_set
        self.__lexer = lexer
        self.__IGNORE_DUPLICATES = IGNORE_DUPLICATES
        self.__parsing_table = self.__generate()

    def __str__(self):
        return json.dumps(self.__parsing_table, indent=2)

    def __repr__(self):
        return json.dumps(self.__parsing_table, indent=2)

    @staticmethod
    def __pretty_rule(data):
        if data is None:
            return ""
        rule = ""
        for val in data:
            if val["token"] == "":
                rule += "epsilon"
            else:
                rule += val["token"]
        return rule

    def print(self):
        x_values = set()
        y_axis = {}
        for key, entry in self.__parsing_table.items():
            if entry["__debug_y_axis"] not in y_axis.keys():
                y_axis[entry["__debug_y_axis"]] = {}
            y_axis[entry["__debug_y_axis"]][entry["__debug_x_axis"]] = entry["rule"]
            x_values.add(entry["__debug_x_axis"])

        x_values = list(x_values)
        x_values.sort()
        print(json.dumps(y_axis, indent=2))
        print(x_values)

        e = ""
        x_line = f"{e:<15}"
        for x_v in x_values:
            cell = f"| {x_v}"
            x_line += f"{cell:<15}"
        print(x_line)
        for y_key, y_val in y_axis.items():
            s = f"{y_key}"
            s = f"{s:<15}"
            for x_h in x_values:
                cell = f"| {self.__pretty_rule(y_val[x_h])}"
                s += f"{cell:<15}"
            print(s)


    def get_table(self):
        return self.__parsing_table

    def get_distinct_keys(self):
        distinct_keys = set()
        for _, value in self.__parsing_table.items():
            distinct_keys.add(value['key'])
        return distinct_keys

    #def get_distinct_symbols_for_key(self, key):
    #    distinct_symbols = set()
    #    for _, value in self.__parsing_table.items():
    #        if value['key'] != key:
    #            continue
    #        distinct_symbols.add(value['data'])
    #    return [entry for entry in distinct_symbols]

    def get_rule(self, key):
        rules = []
        for _, value in self.__parsing_table.items():
            if value['key'] == key and value["rule"]:
                rules.append({"rule": value["rule"], "symbol": value["data"]})
        return rules

    def __generate(self):
        terminals = self.__lexer.get_terminals()
        production_rules = self.__lexer.get_grammar()

        # init table
        parsing_table = {}
        for key in production_rules:
            for terminal in terminals:
                if terminal["token"] == "":
                    continue
                pt_key = GlobalDefines.normalize(terminal["uid"], key)
                parsing_table[pt_key] = {
                    "readable": f'{terminal["token"]}-{key}',
                    "data": terminal["token"],
                    "rule_hash": None,
                    "rule": None,
                    "key": key,
                    "x_axis": terminal["uid"],
                    "y_axis": key,
                    "__debug_x_axis": terminal["token"],
                    "__debug_y_axis": key
                }
            pt_key = GlobalDefines.normalize('None', key)
            parsing_table[pt_key] = {
                "readable": f'$-{key}',
                "data": "$",
                "rule_hash": None,
                "rule": None,
                "key": key,
                "x_axis": "$",
                "y_axis": key,
                "__debug_x_axis": "$",
                "__debug_y_axis": key
             }

        for key in production_rules:
            for rule in production_rules[key]:
                # print(key, rule)
                rule_hash = key + GlobalDefines.hash_rule(rule)

                # Find First(α) and for each terminal in First(α), make entry A –> α in the table.
                first_set_pt = self.__first_set.get_first_pt(rule_hash)
                # print(first_set_pt["data"])
                # print("##########################################")
                for entry in first_set_pt["data"]:
                    if entry["token"] == "":
                        continue

                    if entry["label"] == "terminal":
                        pt_key = GlobalDefines.normalize(entry["uid"], key)
                        parsing_table[pt_key]["rule_hash"] = rule_hash
                        parsing_table[pt_key]["rule"] = rule
                        print("PT_KEY", pt_key)

                # If First(α) contains ε (epsilon) as terminal than,
                # find the Follow(A) and for each terminal in Follow(A), make entry A –> α in the table.
                if first_set_pt["epsilon"]:
                    follow_set = self.__follow_set.get_follow(key)
                    # print("Follow Set", follow_set)
                    for follow_entry in follow_set["data"]:
                        if follow_entry["label"] == "terminal":
                            follow_pt_key = GlobalDefines.normalize(follow_entry["uid"], key)
                            parsing_table[follow_pt_key]["rule_hash"] = rule_hash
                            if parsing_table[follow_pt_key]["rule"] is not None:
                                if not self.__IGNORE_DUPLICATES:
                                    raise Exception(f"Not LL1, duplicate rule found! \nCurrent Table: {parsing_table[follow_pt_key]['rule']}\nAttempted Insert: {rule}\nRelated Key: {key}")
                            parsing_table[follow_pt_key]["rule"] = rule
                            # print("FOLLOW_PT_KEY", follow_pt_key)
                # print("---------------------------------------------")

        return parsing_table