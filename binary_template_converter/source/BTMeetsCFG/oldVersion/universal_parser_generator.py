import json
from binary_template_converter.source.BTMeetsCFG.oldVersion.global_defines import GlobalDefines


class ParserGenerator:
    def __init__(self, parsing_table, first_set, follow_set, template_generator):
        self.__parsing_table = parsing_table
        self.__follow_set = follow_set
        self.__first_set = first_set
        self.__code = ""
        self.__code_generator = template_generator
        self.__internal_parser = self.__generate()

    def __str__(self):
        return json.dumps(self.__internal_parser, indent=2)

    def __repr__(self):
        return json.dumps(self.__internal_parser, indent=2)

    def code(self):
        return self.__code_generator.generate_code(
            globals_=self.__internal_parser["globals"],
            evilbit=False,
            start_key=self.__internal_parser["start_key"],
            structs=self.__internal_parser["structs"],
            nullables=self.__internal_parser["nullables"]
        )

    def __generate(self):
        internal_parser = {"globals": [], "structs": [], "start_key": None, "stack_symbols": [], "nullables": []}

        #distinct_first_set_symbols = self.__first_set.get_distinct_symbols()
        #distinct_follow_set_symbols = self.__follow_set.get_distinct_symbols()

        #for symbol in distinct_follow_set_symbols:
        #    if symbol not in distinct_first_set_symbols:
        #        internal_parser["stack_symbols"].append(symbol)

        for el in self.__first_set.get_nullable():
            follow_entry = self.__follow_set.get_follow(el)
            for entry in follow_entry["data"]:
                internal_parser["stack_symbols"].append(entry["token"])


        distinct_keys = self.__parsing_table.get_distinct_keys()
        for key in distinct_keys:
            normalized_name = GlobalDefines.normalize(key, "non_terminal")
            if key != "<start>":
                internal_parser["globals"].append(normalized_name)
            else:
                internal_parser["start_key"] = GlobalDefines.normalize(key, "non_terminal")
            rule_mapping = []
            eof_rule = None
            pref_values_0 = []
            for rule in self.__parsing_table.get_rule(key):
                if rule["symbol"] != "$":
                    rule_mapping.append(rule)
                    pref_values_0.append(f'"{rule["symbol"]}"')
                else:
                    eof_rule = rule
            pref_values_1 = pref_values_0[:] # copy by value

            has_stack_symbol = False
            first_entries = self.__first_set.get_first(key)["data"]
            for entry in internal_parser["stack_symbols"]:
                in_first = False
                for fen in first_entries:
                    if fen["token"] == entry:
                        in_first = True
                        break
                if in_first:
                    continue
                try:
                    pref_values_1.remove(f'"{entry}"')
                    pref_values_0.remove(f'"{entry}"')
                    has_stack_symbol = True
                except:
                    pass
            if has_stack_symbol:
                pref_values_1.append("stack[top - 1]")

            updated_rule_mapping = []
            nullable = False
            for entry in rule_mapping:
                rule = entry["rule"]
                prev_symbol = {"label": "terminal"}
                symbol_lst = []
                index = 0
                for symbol in rule:
                    if prev_symbol["label"] == "non_terminal" and symbol["token"] in internal_parser["stack_symbols"]:
                        symbol_lst.append({
                            "token": "actually it would be stack[--top], but we dont need the value.",
                            "label": "instruction",
                            "uid": "--top"
                        })
                        symbol_lst.insert(index - 1, {
                            "token": "push the required symbol onto the stack",
                            "label": "instruction",
                            "uid": f'stack[top++] = "{symbol["token"]}"'
                        })
                    symbol_lst.append(symbol)
                    if symbol["token"] == '' and symbol["label"] == 'terminal' and not nullable:
                        internal_parser["nullables"].append(GlobalDefines.normalize(key, "non_terminal"))
                        nullable = True
                    prev_symbol = symbol
                    index = index + 1
                updated_rule_mapping.append({"rule": symbol_lst, "symbol": entry["symbol"]})
            rule_mapping = updated_rule_mapping

            internal_parser["structs"].append(
                {
                    "uid": GlobalDefines.normalize(key, "non_terminal"),
                    "key": key,
                    "nullable": nullable,
                    "name": normalized_name,
                    "rule_mapping": rule_mapping,
                    "eof_rule": eof_rule,
                    "pref_values_0": pref_values_0,
                    "pref_values_1": pref_values_1
                }
            )
        return internal_parser

    #def __find_key(self, key):
    #    rules = []
    #    table = self.__parsing_table.get_table()
    #    for objkey in table:
    #        entry = table[objkey]
    #        if entry["key"] == key and entry["rule_hash"]:
    #            rules.append(entry)
    #    return rules
