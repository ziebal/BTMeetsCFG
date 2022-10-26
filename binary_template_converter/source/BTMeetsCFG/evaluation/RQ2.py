import json
import subprocess
from os import walk
import binascii
import re
from pprint import pprint

from fuzzingbook.GrammarFuzzer import GrammarFuzzer, tree_to_string
from fuzzingbook.Parser import EarleyParser
from BTMeetsCFG.BT2CFG.btconverter import BTConverter
from .result_renderer import create_result_page

ATTEMPTS = 10


def test_earley():
    A3_GRAMMAR = {
        "<start>": ["<bexpr>", "<aexpr>"], # RESULTS IN AN ERROR
        # This works: "<start>": ["<bexpr>"], dont ask why...
        "<bexpr>": [
            "<aexpr><gt><aexpr>", "<aexpr><lt><aexpr>", "<aexpr>=<aexpr>",
            "<bexpr>=<bexpr>", "<bexpr>&<bexpr>", "<bexpr>|<bexpr>", "(<bexrp>)"
        ],
        "<aexpr>":
            ["<aexpr>+<aexpr>", "<aexpr>-<aexpr>", "(<aexpr>)", "<integer>"],
        "<integer>": ["<digit><integer>", "<digit>"],
        "<digit>": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
        "<lt>": ['<'],
        "<gt>": ['>']
    }
    mystring = '(1+24)=33'
    parser = EarleyParser(A3_GRAMMAR)
    print(A3_GRAMMAR)
    for tree in parser.parse(mystring):
        print(tree)
        print(tree_to_string(tree))


def eval_generate(grammar, binary_path):
    # For some reason the EarleyParser expects only one argument at the start ...
    # Inserting a intermediate key as a workaround!
    grammar["<__intermediate_start>"] = grammar["<start>"]
    grammar["<start>"] = ["<__intermediate_start>"]

    result = []
    success = 0
    fail = 0
    for _ in range(ATTEMPTS):
        # generate inputs
        proc = subprocess.Popen([binary_path, "fuzz", "-"],
                                stdout=subprocess.PIPE,
                                )

        stdout_value = proc.communicate()[0]
        if proc.returncode != 0:
            pprint(
                f"FormatFuzzer Return Code != 0:\n\t{proc.returncode}\n\t{proc.stdout}\n\t{proc.stderr}")

        inp = stdout_value.hex()

        # attempt to parse the generated input from the original BT
        parser = EarleyParser(grammar)
        try:
            for tree in parser.parse(inp):
                result.append(tree_to_string(tree))
            success += 1
        except SyntaxError:
            fail += 1

    return success, fail, result


def eval_parse(grammar, binary_path):
    f = GrammarFuzzer(grammar)
    fail = 0
    success = 0
    error_rate = []
    for i in range(ATTEMPTS):
        fuzz = f.fuzz()
        with open(f'/dev/shm/test_{i}', 'wb') as fout:
            fout.write(
                binascii.unhexlify(fuzz)
            )

        proc = subprocess.Popen([binary_path, "parse", f"/dev/shm/test_{i}"],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE
                                )

        stdout_value = proc.communicate()[1].decode('UTF-8')

        if "failed" in stdout_value:
            fail += 1
            if "-nan" in stdout_value:
                error_rate.append(-1)
            else:
                error = re.search("error [0-9]+[.[0-9]+]?", stdout_value)
                error_rate.append(error[0])
        else:
            success += 1

    return success, fail, error_rate


def main():
    filenames = []
    try:
        _, _, filenames = next(walk("./rq2_input"))
    except StopIteration:
        pass

    test_data = []
    for filename in filenames:
        btc = BTConverter(f"./rq2_input/{filename}")
        grammar_str = btc.convert()
        binary_path = btc.get_cache_path()
        grammar = json.loads(grammar_str)
        test_data.append((grammar, binary_path, filename))

    results = {}
    for data in test_data:
        try:
            results[data[2]] = {"mined-grammar": data[0]}
            results[data[2]]["parse"] = eval_parse(data[0], data[1])
            results[data[2]]["generate"] = eval_generate(data[0], data[1])
        except Exception as e:
            print(f'Error for {data[2]}: {repr(e)}')

    #pprint(test_data)
    #print("#" * 40)
    #pprint(results)
    with open("./output/result.json", 'w') as result_file:
        result_file.write(json.dumps(results))
    create_result_page(results)


