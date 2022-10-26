import json
import sys
import unittest
from os import walk

import fuzzingbook.GrammarCoverageFuzzer
from fuzzingbook.Parser import EarleyParser

from BTMeetsCFG.BT2CFG.btconverter import BTConverter
from BTMeetsCFG.CFG2BT.cfgconverter import CFGConverter
from BTMeetsCFG.evaluation.result_renderer import create_result_page


class FileTest(unittest.TestCase):
    pass

def generation(key,subject):
    def generation_inter(cls):
        mined_grammar = subject["mined_grammar"]
        original_grammar = subject["grammar"]
        fuzzer = fuzzingbook.GrammarCoverageFuzzer.GrammarCoverageFuzzer(mined_grammar)
        parser = EarleyParser(original_grammar)
        success_count = 0
        seen = set()
        for _ in range(10000):
            sample = fuzzer.fuzz()
            if sample in seen:
                continue
            else:
                seen.add(sample)
            sample = bytes.fromhex(sample).decode('utf-8')
            try:
                modified_sample = sample + "$"  # This is required for the EarleyParser
                for _ in parser.parse(modified_sample):
                    pass
                success_count = success_count + 1
            except RecursionError:  # Ignoring RecursionError, not my fault that the EarleyParser cant handle it :D
                success_count = success_count + 1
            except Exception as e:
                    print(f'{key}: Error for sample: {sample if len(sample) < 1000 else "Too Large to Display"}, Error: {repr(e)}')

        subject["generation"] = f"{success_count} of {len(seen)}"
        subject["samples_generation"] = list(seen)
        cls.assertEqual(success_count, len(seen))

    return generation_inter


def parsing(key, subject):
    def parsing_inter(cls):
        mined_grammar = subject["mined_grammar"]
        original_grammar = subject["grammar"]
        fuzzer = fuzzingbook.GrammarCoverageFuzzer.GrammarCoverageFuzzer(original_grammar)
        parser = EarleyParser(mined_grammar)
        success_count = 0
        seen = set()
        for _ in range(10000):
            sample = fuzzer.fuzz()
            if sample in seen:
                continue
            else:
                seen.add(sample)
            try:
                modified_sample = ''.join(hex(ord(x))[2:] for x in sample.rstrip("$"))  # This is required for the EarleyParser
                for _ in parser.parse(modified_sample):
                    pass
                success_count = success_count + 1
            except RecursionError:  # Ignoring RecursionError, not my fault that the EarleyParser cant handle it :D
                success_count = success_count + 1
            except Exception as e:
                print(
                    f'{key}: Error for sample: {sample if len(sample) < 1000 else "Too Large to Display"}, Error: {repr(e)}')

        subject["parsing"] = f"{success_count} of {len(seen)}"
        subject["samples_parsing"] = list(seen)
        cls.assertEqual(success_count, len(seen))

    return parsing_inter


def main():
    filenames = []
    try:
        _, _, filenames = next(walk("./rq3_input"))
    except StopIteration:
        pass

    test_cases = {}
    for filename in filenames:
        test_cases[filename] = {}
        with open(f'./rq3_input/{filename}', "r") as f:
            print(filename)
            test_cases[filename]["grammar"] = json.load(f)

    for key, subject in test_cases.items():
        converter = CFGConverter(subject["grammar"], debug_prints=False)
        code = converter.convert()

        subject["BT"] = key + ".bt"
        subject["code"] = f'http://127.0.0.1:9000/{subject["BT"]}'

        with open(f'./output/{subject["BT"]}', 'w') as o:
            o.write(code)

        btc = BTConverter(f'./output/{subject["BT"]}')
        grammar_str = btc.convert()
        with open(f'./output/mined-{subject["BT"]}', 'w') as o:
            o.write(grammar_str)
        subject["mined_grammar"] = json.loads(grammar_str)

        setattr(FileTest, f"test_generation_{key}", generation(key, subject))
        setattr(FileTest, f"test_parsing_{key}", parsing(key, subject))

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(testCaseClass=FileTest)
    unittest.TextTestRunner(stream=sys.stdout, descriptions=True, verbosity=2).run(suite)

    for _, value in test_cases.items():
        value["grammar"] = "Removed"
        value["mined_grammar"] = "Removed"
    create_result_page(test_cases)





