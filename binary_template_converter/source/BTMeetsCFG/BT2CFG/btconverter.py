import json
from hashlib import sha256
from typing import List, Tuple
import networkx as nx

from BTMeetsCFG.converter.logger import Log
from BTMeetsCFG.converter.jsonencoder import JSONEncoder
from .btcompiler import BTCompiler
from .dataclasses import IntermRep, PartialGrammar, MinedGrammar
from .ffwrapper import FFWrapper, FormatFuzzerError

DRAW_GRAPH_IMAGE = False


class BTConverter:
    def __init__(self, input_file_path: str, enable_hex=True):
        self.__enable_hex = enable_hex
        self.file_path = input_file_path
        self.file_name = input_file_path.split("/")[-1]
        self.SAMPLE_SIZE = 200
        self.THRESHOLD = 10
        self.FF_FAIL_THRESHOLD = 10
        self.btc = BTCompiler()
        self.log = self.log = Log("BTConverter")

    def __gather_samples(self, ff_binary: FFWrapper) -> List[IntermRep]:
        interm_reps: List[IntermRep] = []
        generated_inputs = []
        counter_distinct_samples = 0
        counter_attempts = 0
        counter_ff_fail = 0

        while (counter_distinct_samples < self.SAMPLE_SIZE and
               counter_attempts < self.SAMPLE_SIZE * self.THRESHOLD):

            if counter_ff_fail >= self.FF_FAIL_THRESHOLD:
                if counter_distinct_samples == 0:
                    raise Exception("Failed to produce samples!")
                self.log.debug(
                    f"WARNING: FF_FAIL_THRESHOLD reached, continuing with only {counter_distinct_samples} samples...")
                break

            try:
                ff_res = ff_binary.execute(enable_hex=self.__enable_hex)
            except FormatFuzzerError:
                counter_ff_fail += 1
                continue

            if ff_res.input in generated_inputs:
                counter_attempts += 1
                continue

            generated_inputs.append(ff_res.input)
            interm_reps.append(ff_res)
            counter_distinct_samples += 1
        return interm_reps

    @staticmethod
    def __combine_minded_trees(grammars: List[PartialGrammar]) -> MinedGrammar:
        final_grammar: MinedGrammar = MinedGrammar()
        for grammar in grammars:
            final_grammar.enhance(grammar)
        return final_grammar

    @staticmethod
    def __get_sub_string(inp: str, start: int, end: int) -> str:
        return inp[start:end + 2]

    @staticmethod
    def __hash_call_tree(s: List[str]) -> Tuple[str, str, str, str]:
        ss = '->'.join(s)
        result_hash = sha256(ss.encode('utf-8')).hexdigest()

        ss_p = '->'.join(s[:-1])
        hash_p = sha256(ss_p.encode('utf-8')).hexdigest()
        return ss, result_hash[:10], ss_p, hash_p[:10]

    @staticmethod
    def __children_info(tree, nodes):
        ret = {}
        lst = list(nodes)
        for e in lst:
            ret[e] = {"name": tree.nodes[e]["label"]}
        return ret

    def __process_sample(self, sample: IntermRep) -> PartialGrammar:
        graph = nx.DiGraph()
        inp = sample.input
        dtree = sample.dtree

        # TODO workaround
        if len(dtree) == 0:
            substring_map = {"3b9c358f36": ""}
        else:
            substring_map = {}

        start_node = '3b9c358f36'  # TODO what is this? Probably the hash of "<file>"
        graph.add_node(start_node, label="file")
        for entry in dtree:
            # print(get_string(input, entry["start"], entry["end"]))
            for i in range(len(entry.stack)):
                c = i + 1
                if i == 0:
                    continue
                res = self.__hash_call_tree([x[1] for x in entry.stack[:c]])
                tmp = entry.stack[i][1]

                #print("Res:", res)
                # print("Stack:", entry.stack[:c])
                # print("Substring:", self.__get_sub_string(inp, entry.start, entry.end))
                substring_map[res[1]] = self.__get_sub_string(inp, entry.start, entry.end)

                # Graph stuff
                graph.add_node(res[1], label=tmp)
                graph.add_edge(res[3], res[1])

        leaves = [v for v, d in graph.out_degree() if d == 0]
        for leaf in leaves:
            # print("Leaf:", leaf)
            # print(substring_map[leaf])
            terminal = f'{leaf}-leaf'
            graph.add_node(terminal, label=substring_map[leaf])
            graph.add_edge(leaf, terminal)

        if DRAW_GRAPH_IMAGE:
            vizgraph = nx.drawing.nx_agraph.to_agraph(graph)
            vizgraph.layout('dot')
            vizgraph.draw(f'/source/output/{self.file_name}-debug-{sample.uid()}.jpeg')

        grammar_raw = {}
        for node in graph.nodes:
            grammar_raw[node] = {
                "name": graph.nodes[node]["label"],
                "type": "leaf" if "leaf" in node else "node",
                "children": self.__children_info(graph, graph[node])
            }
        # self.log.debug(grammar_raw)

        grammar = {}
        for entry in grammar_raw.items():
            children = []
            for child in entry[1]["children"]:
                if "leaf" in child:
                    children.append(f'{entry[1]["children"][child]["name"]}')
                else:
                    children.append(f'<{entry[1]["children"][child]["name"]}>')
            if len(children) > 0:
                if entry[1]["name"] not in grammar:
                    grammar[entry[1]["name"]] = []
                s = ''.join(children)
                if s not in grammar[entry[1]["name"]]:
                    grammar[entry[1]["name"]].append(''.join(children))

        # self.log.debug(grammar)
        return PartialGrammar(grammar)

    def __format_grammar(self, mined: MinedGrammar) -> str:
        formatted_grammar = {}
        for key, value in mined.tree.items():
            # self.log.debug(f'{key}: {value}')
            # we replace entry 'file' with 'start'
            # every BT Tree starts with 'file' and every CFG starts with 'start'
            # hence its interchangeable
            if key == "file":
                formatted_grammar["<start>"] = value
            else:
                formatted_grammar[f'<{key}>'] = value
        # self.log.debug(formatted_grammar)
        return JSONEncoder.dumps(formatted_grammar)

    def get_cache_path(self):
        return self.btc.get_cache_path()

    def convert(self) -> str:
        try:
            ff_binary = self.btc.compile(self.file_path)
            self.log.debug("Compile step done!")

            samples: List[IntermRep] = self.__gather_samples(ff_binary)
            self.log.debug("Sample step done!")

            mined_trees: List[PartialGrammar] = [self.__process_sample(s) for s in samples]
            self.log.debug("Tree step done!")

            mined_grammar: MinedGrammar = self.__combine_minded_trees(mined_trees)
            self.log.debug("Mining step done!")

            return self.__format_grammar(mined_grammar)
        except Exception as e:
            return json.dumps({"Status": "Failed", "Error": repr(e)})
