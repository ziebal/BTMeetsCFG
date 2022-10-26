import json
import re
import shutil
import subprocess
import time
from os import walk

from fuzzingbook.Parser import EarleyParser

from BTMeetsCFG.BT2CFG.btcompiler import BTCompiler
from BTMeetsCFG.CFG2BT.cfgconverter import CFGConverter
import fuzzingbook.GrammarCoverageFuzzer

from BTMeetsCFG.evaluation.result_renderer import create_result_page


def build_bt_fuzzer(filename, grammar):
    converter = CFGConverter(grammar, debug_prints=False)
    code = converter.convert()

    with open(f'./output/{filename}.bt', 'w') as o:
        o.write(code)

    compiler = BTCompiler()
    compiler.compile(f'./output/{filename}.bt')
    return compiler.get_cache_path()


def main():
    filenames = []
    try:
        _, _, filenames = next(walk("./rq4_input"))
    except StopIteration:
        pass

    results = {}
    for filename in filenames:
        results[filename] = (-1, -1, -1)
        with open(f'./rq4_input/{filename}', "r") as f:
            print(f"Running benchmark for {filename}")
            grammar = json.load(f)
            binary = build_bt_fuzzer(filename, grammar)

            proc = subprocess.run([binary, "benchmark"], stdout=subprocess.PIPE)
            stdout = proc.stdout.decode("utf-8").split("\n")
            result = re.search(r"[0-9]+[.[0-9]+]?", stdout[2])[0]
            results[filename] = (float(result), results[filename][1], results[filename][2])

            fuzzer = fuzzingbook.GrammarCoverageFuzzer.GrammarCoverageFuzzer(grammar)
            st = time.time()
            for i in range(10000):
                fuzzer.fuzz()
            elapsed_time = time.time() - st
            results[filename] = (results[filename][0], 10000 / elapsed_time, results[filename][2])

            samples = []
            for i in range(10000):
                samples.append(fuzzer.fuzz())
            parser = EarleyParser(grammar)
            st = time.time()
            for sample in samples:
                for _ in parser.parse(sample):
                    pass
            elapsed_time = time.time() - st
            results[filename] = (results[filename][0], results[filename][1], 10000 / elapsed_time)

            print(f"{filename}: Done")

    create_result_page(results)



