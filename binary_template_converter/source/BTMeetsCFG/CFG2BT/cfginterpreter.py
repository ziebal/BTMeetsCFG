from typing import List, Tuple, Set

from .cfgfirstset import FirstSet
from .cfgfollowset import FollowSet
from .cfglabel import Label
from .cfgtransitiontable import TransitionTable, TableEntry, Symbol
from .dataclasses import Rule, Token
from .globaldefines import GlobalDefines
from ..converter.logger import Log

ENABLE_READ_GUARD = False


def configure_insert_fn(self, indent: int):
    def insert_code_line__(new_line: str):
        self.code += "\t" * indent + new_line + "\n"
    return insert_code_line__


def eof_check(lst: Set[Token]):
    eof = 0
    remove = None

    for x in lst:
        if x.name.rstrip("@") == "$":
            eof = 1
            remove = x
            break

    if remove:
        lst.remove(remove)
    return eof


def helper_to_array(tokens: Set[Token]):
    sorted_ = sorted(x.name for x in tokens)
    return ", ".join(f'"{x}"' for x in sorted_)


class Switch:
    def __init__(self, key: str, symbols: List[Symbol], follow_set: FollowSet, first_set: FirstSet, length: int, enable_debug_print):
        self.__enable_debug_print = enable_debug_print
        self.blocks: List[Tuple[str, Rule]] = []
        self.__follow_set: FollowSet = follow_set
        self.__first_set: FirstSet = first_set
        self.__length = length
        self.__generate(symbols)
        self.__key: str = key
        self.code = ""
        self.__insert_code_line = None

    def __generate(self, symbols: List[Symbol]):
        for symbol in symbols:
            if symbol.get_rule() is None:
                continue
            if symbol.name.rstrip("@") == "$":
                continue
            self.blocks.append((symbol.name, symbol.get_rule()))

    @staticmethod
    def __helper_token_to_printable(tokens: Set[Token]):
        if len(tokens) == 0:
            return "Empty"
        return ", ".join((x.name if x.name != "" else 'epsi') for x in tokens)

    @staticmethod
    def __helper_to_array(tokens: Set[Token]):
        return helper_to_array(tokens)

    def __possible_values(self, uid, index, tokens): # UID is not needed just for debug display
        first: Set[Token] = self.__first_set.get(tokens[index:])
        # TODO cfginterpreter.Switch.__possible_values: there might be a bug with $ in FIRST, check sample3.json
        # It contains: local string new_first[] = {"$", "(", "i"};

        # 2. If there is a production A --> aBb, then everything in FIRST(b), except for e, is placed in FOLLOW(B).
        follow: Set[Token] = self.__first_set.get(tokens[(index + 1):])

        lines = []
        if self.__enable_debug_print:
            lines = [
                "// ######################################################################################################",
                "//",
                f"// {uid}",
                "//",
                f"// first: Set[Token] = self.__first_set.get(tokens[index:]) => {self.__helper_token_to_printable(tokens[index:])}",
                f"// follow: Set[Token] = self.__first_set.get(tokens[(index + 1):]) => {self.__helper_token_to_printable(tokens[(index + 1):])}",
                "//",
                "// FIRST: " + self.__helper_token_to_printable(first),
                "// FOLLOW: " + self.__helper_token_to_printable(follow),
                "// FOLLOW IS_EOF? " + ("YES" if "$" in self.__helper_token_to_printable(follow) else "NO")
            ]

            # 3. If there is a production A --> aB, or a production A --> aBb where FIRST(b) contains e (i.e., b --> e),
            # then everything in FOLLOW(A) is in FOLLOW(B).
            #  production A --> aB
            if len(follow) == 0:
                lines.append("// FOLLOW is EMPTY: we need to include the CALLEE follow information")
            # production A --> aBb where FIRST(b) contains e
            if GlobalDefines.set_has_epsilon(follow):
                lines.append("// FOLLOW contains epsi: we need to include the CALLEE follow information")

            # If FIRST contains epsilon we need to know what can this means, what comes after the epsilon?
            # For this we need the FOLLOW information from the CALLEE
            # -> This means the struct is "Nullable"
            if GlobalDefines.set_has_epsilon(first):
                lines.append("// FIRST contains epsi: we need FOLLOW information")

            lines.append("//")

            lines.append("// new_first = " + self.__helper_token_to_printable(first))
            lines.append("// new_follow = " + self.__helper_token_to_printable(follow))

            if len(follow) == 0:
                lines.append("// new_follow += follow")

            if GlobalDefines.set_has_epsilon(follow):
                lines.append("// new_follow += follow")

            if GlobalDefines.set_has_epsilon(first):
                lines.append("// new_first += new_follow")

            lines.append("//")
            lines.append("// ######################################################################################################")

        tmp_follow = GlobalDefines.get_set_without_epsilon(follow)
        tmp_first = GlobalDefines.get_set_without_epsilon(first)
        new_follow_is_eof = eof_check(tmp_follow)
        new_first_is_eof = eof_check(tmp_first)

        lines.append(f"local int new_first_is_eof = {new_first_is_eof};")
        lines.append(f"local int new_follow_is_eof = {new_follow_is_eof};")

        if len(tmp_first) == 0:
            lines.append("local string new_first[0];")
        else:
            lines.append("local string new_first[] = {" + self.__helper_to_array(tmp_first) + "};")

        if len(tmp_follow) == 0:
            lines.append("local string new_follow[0];")
        else:
            lines.append("local string new_follow[] = {" + self.__helper_to_array(tmp_follow) + "};")

        lines.append(f"local int temp_new_follow_size = {len(tmp_follow)};")
        new_follow_updated = False

        if len(follow) == 0:
            lines.append(f"local int new_follow_size = temp_new_follow_size + follow_size;")
            lines.append("local string new_follow[new_follow_size];")
            lines.append(f"local int i;")
            lines.append("for (i = temp_new_follow_size; i < new_follow_size; i++) {")
            lines.append("\tnew_follow[i] = follow[i - temp_new_follow_size];")
            lines.append("}")
            new_follow_updated = True

        if GlobalDefines.set_has_epsilon(follow):
            lines.append(f"local int new_follow_size = temp_new_follow_size + follow_size;")
            lines.append("local string new_follow[new_follow_size];")
            lines.append(f"local int i;")
            lines.append("for (i = temp_new_follow_size; i < new_follow_size; i++) {")
            lines.append("\tnew_follow[i] = follow[i - temp_new_follow_size];")
            lines.append("}")
            new_follow_updated = True

        if not new_follow_updated:
            lines.append("local int new_follow_size = temp_new_follow_size;")

        if new_follow_updated:
            lines.append("")
            lines.append("new_follow_is_eof |= follow_is_eof;")
            # lines.append(
            #    f'Printf("{self.__key}: new_follow_is_eof: %d, follow_is_eof: %d\\n", new_follow_is_eof, follow_is_eof);')

        if GlobalDefines.set_has_epsilon(first):
            lines.append(f"local int org_size_first = {len(tmp_first)};")
            lines.append(f"local int new_first_size = org_size_first + new_follow_size;")
            # lines.append('Printf("new_first loop: 1\\n");')
            lines.append("local string new_first[new_first_size];")
            lines.append("local int j;")
            lines.append("for (j = org_size_first; j < new_first_size; j++) {")
            lines.append("\tnew_first[j] = new_follow[j - org_size_first];")
            lines.append("}")
            lines.append("")
            lines.append("new_first_is_eof |= follow_is_eof;")
            # lines.append(f'Printf("{self.__key}: new_first_is_eof: %d, follow_is_eof: %d\\n", new_first_is_eof, follow_is_eof);')

        return lines

    def __follow_debug(self, index, tokens):
        try:
            first: Set[Token] = self.__first_set.get(tokens[(index - 1):])
            follow: Set[Token] = set()
            if GlobalDefines.set_has_epsilon(first):
                follow = self.__follow_set.get_specific_follow(self.__key, tokens[index:])
                first = GlobalDefines.get_set_without_epsilon(first)

            possible_values: Set[Token] = set()
            possible_values.update(first)
            possible_values.update(follow)

            names = []
            for a in possible_values:
                names.append(a.name)
            names.append(f'({", ".join([x.name for x in tokens[index:]])})')
            return names
        except:
            return "Not found!"

    def get_code(self) -> str:
        self.__insert_code_line = configure_insert_fn(self, 1)
        # self.__insert_code_line(f'Printf("{self.__key} - SELECTION CODE\\n");')
        self.__insert_code_line(f"local char selection[{self.__length}];")
        self.__insert_code_line(f"ReadBytes(selection, FTell(), {self.__length}, first, first);")
        # self.__insert_code_line(f'Printf("{self.__key} - SWITCH CODE\\n");')

        self.__insert_code_line("switch (selection) {")
        for block in self.blocks:
            self.__insert_code_line(f"\tcase \"{block[0]}\":")

            rule: Rule = block[1]
            index = 0
            for token in rule.tokens:
                if token.label == Label.NON_TERMINAL:
                    lines = self.__possible_values(token.uid, index, rule.tokens)
                    for line in lines:
                        self.__insert_code_line("\t\t" + line)
                    self.__insert_code_line(f"\t\t{token.uid} {token.uid.lower()}(new_first, new_follow, new_follow_size, new_first_is_eof, new_follow_is_eof);\n")
                else:
                    if token.name == "":
                        self.__insert_code_line("")
                    else:
                        if token.name.rstrip("@") == "$":
                            pass
                        else:
                            self.__insert_code_line(f"\t\tchar {token.uid}[{self.__length}] = " + "{ \"" + token.name + "\" };\n")
                            if ENABLE_READ_GUARD:
                                self.__insert_code_line(f"\t\tif ({token.uid} != \"{token.name}\")" + " {")
                                self.__insert_code_line(f"\t\t\treturn -1;")
                                self.__insert_code_line("\t\t}")
                index += 1
            self.__insert_code_line("\t\tbreak;")

        self.__insert_code_line(f"\tdefault:")
        self.__insert_code_line(f"\t\treturn -1;")
        self.__insert_code_line("}")
        return self.code


class Struct:
    def __init__(self, key: str, table_entry: TableEntry, follow_set: FollowSet, first_set: FirstSet, length: int, enable_debug_print):
        self.name: str = table_entry.name
        self.args: List[Tuple[str, str]] = []
        self.switch: Switch = Switch(key, table_entry.symbols, follow_set, first_set, length, enable_debug_print)

    def get_code(self) -> str:
        code = f"struct {self.name}(string first[], string follow[], int follow_size, int first_is_eof, int follow_is_eof)" + " {\n"

        # code += "\tif (eof) {\n"
        # code += "\t\treturn;\n"
        # code += "\t}\n"

        code += "\n"

        code += "\tif (first_is_eof) {\n"
        code += "\t\tif (FEof(0.25)) {\n"
        code += f'\t\t\tPrintf("{self.name} - EOF\\n");\n'
        code += "\t\t\treturn;\n"
        code += "\t\t}\n"
        code += "\t}\n"

        code += "\n"

        # code += f'\tPrintf("{self.name} - SELECTION CODE\\n");\n'
        # code += "\t#cpp for (auto i: first)\n"
        # code += "\t#cpp \tstd::cout << i << ' ';\n"
        code += self.switch.get_code() + "\n"
        code += "};"
        return code


class CFGInterpreter:
    def __init__(self, first_set: FirstSet, follow_set: FollowSet, transition_table: TransitionTable, length: int, enable_debug_print=True):
        self.__logger = Log(class_name="CFGInterpreter")
        self.__enable_debug_print = enable_debug_print
        self.__firstSet: FirstSet = first_set
        self.__followSet = follow_set
        self.__transitionTable = transition_table
        self.__start_symbols = []
        self.__length = length
        self.structs = []

    def debug_print(self):
        self.__logger.debug(self.structs)

    def interpret(self):
        table = self.__transitionTable.get()
        for name, tableEntry in table.items():
            if name == "<start>":
                self.__start_symbols = tableEntry.symbols
            self.structs.append(Struct(name, tableEntry, self.__followSet, self.__firstSet, self.__length, self.__enable_debug_print))

    def get_code(self, start_symbols: Set[Token]):
        code = "// Global Defines\n"
        for struct in self.structs:
            code += "struct " + struct.name + "(string first[], string follow[], int follow_size, int first_is_eof, int follow_is_eof) {};" + "\n"
        code += "\n"

        code += "// Code Section\n"
        for struct in self.structs:
            code += struct.get_code() + "\n\n"

        code += "SetEvilBit(false);\n"

        eof = eof_check(start_symbols)


        start_args = helper_to_array(start_symbols)
        code += "local string possible_values[] = {" + start_args + "};\n"
        code += "local string required_follows[0];\n"
        code += f'START_NONTERMINAL_9A43E7 start(possible_values, required_follows, 0, {eof}, 1);'
        return code
