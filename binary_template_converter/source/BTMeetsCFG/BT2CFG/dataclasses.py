from typing import List, Callable, Dict, Any, Set, Tuple
from hashlib import sha256
import re

COMBINE_SUBSEQUENT_CALLS = False

class DTreeEntry:
    def __init__(self, start: str, end: str, stack_raw: str, state: str):
        # {"start": s[0], "end": s[1], "stack": s[2], "state": s[3] if len(s) == 4 else "Required"}
        self.start: int = int(start) * 2
        self.end: int = int(end) * 2
        self.stack: List[Tuple[int, str]] = self.__update_stack(stack_raw)
        self.state: str = state

    @staticmethod
    def __update_stack(raw) -> List[Tuple[int, str]]:
        new_entry = []
        c = 0
        for name in raw.split("~"):
            if COMBINE_SUBSEQUENT_CALLS:
                # modify the name of the entry, because FF appends _<number> to multiple calls
                pattern = r'_\d*$'
                # Replace all occurrences of characters with an empty string
                modified_name = re.sub(pattern, '', name)
                new_entry.append((c, modified_name))
            else:
                new_entry.append((c, name))
            c += 1
        return new_entry


class PartialGrammar:
    def __init__(self, tree):
        self.tree: Dict[Any] = tree


class MinedGrammar:
    def __init__(self):
        self.tree: Dict[Set[str]] = {}
        self.partial_grammars = []

    def enhance(self, partial_grammar: PartialGrammar):
        self.partial_grammars.append(partial_grammar)
        for k, v in partial_grammar.tree.items():
            if k not in self.tree:
                self.tree[k] = set()
            self.tree[k].update(v)


class IntermRep:
    def __init__(self, input_: str, dtree: List[DTreeEntry]):
        self.dtree: List[DTreeEntry] = dtree
        self.input = input_
        self.dtree_req: List[DTreeEntry] = self.__get_only_required(dtree)

    def uid(self) -> str:
        return sha256(self.input.encode('utf-8')).hexdigest()

    @staticmethod
    def __get_only_required(dt_entries: List[DTreeEntry]) -> List[DTreeEntry]:
        filter_func: Callable[[DTreeEntry], bool] = lambda x: (x.state == "Required")
        return list(filter(filter_func, dt_entries))
