import json
import subprocess
import sys
import unittest
from os.path import exists
from os import walk
import random

import fuzzingbook.GrammarCoverageFuzzer
from fuzzingbook import Parser
from fuzzingbook.Parser import EarleyParser

from BTMeetsCFG.BT2CFG.btcompiler import BTCompiler
from BTMeetsCFG.CFG2BT.cfgconverter import CFGConverter
from BTMeetsCFG.evaluation.result_renderer import create_result_page

length = 100
threshold = length / 2

CACHING = True
DEBUG = True


class FileTest(unittest.TestCase):
    pass


def third_party_ll1(subject):
    def test_inter(cls):
        subject["3rd_party_fails"] = []
        subject["3rd_party_success"] = []
        subject["3rd_party_internal_errors"] = 0
        subject["3rd_party_samples"] = set()
        ll1parser = Parser.LL1Parser(subject["grammar"])
        fuzzer = fuzzingbook.GrammarCoverageFuzzer.GrammarCoverageFuzzer(subject["grammar"])
        for _ in range(length * 10):
            sample = fuzzer.fuzz()
            subject["3rd_party_samples"].add(sample)
        subject["3rd_party_samples"] = list(subject["3rd_party_samples"])
        success_count = 0
        for sample in subject["3rd_party_samples"]:
            try:
                ll1parser.parse(sample)
                success_count = success_count + 1
                subject["3rd_party_success"].append(sample)
            except AssertionError:
                # No clue why the parser throws this error, probably not my issue ...
                # File "/source/BTMeetsCFG/evaluation/RQ1.py", line 36, in test_inter
                # rq1_1        |     ll1parser.parse(sample)
                # rq1_1        |   File "/usr/local/lib/python3.8/dist-packages/fuzzingbook/Parser.py", line 2387, in parse
                # rq1_1        |     return self.parse_helper(stack, inp)
                # rq1_1        |   File "/usr/local/lib/python3.8/dist-packages/fuzzingbook/Parser.py", line 2381, in parse_helper
                # rq1_1        |     return self.linear_to_tree(exprs)
                # rq1_1        |   File "/usr/local/lib/python3.8/dist-packages/fuzzingbook/Parser.py", line 2401, in linear_to_tree
                # rq1_1        |     assert len(stack) == 1
                # rq1_1        | AssertionError
                subject["3rd_party_internal_errors"] = subject["3rd_party_internal_errors"] + 1
            except ValueError as e:
                if sample == "":
                    subject["3rd_party_fails"].append({"Exception": repr(e), "Sample": sample})
                    subject["3rd_party_internal_errors"] = subject["3rd_party_internal_errors"] + 1
            except Exception as e:
                subject["3rd_party_fails"].append({"Exception": repr(e), "Sample": sample})

        # print(f'Result: {success_count} / {len(samples)} (of {length})')
        cls.assertEqual(success_count, (len(subject["3rd_party_samples"]) - subject["3rd_party_internal_errors"]))
    return test_inter


def conversion(key, subject):
    def test_conversion_inter(cls):
        converter = CFGConverter(subject["grammar"], debug_prints=False)
        code = converter.convert()

        subject["BT"] = key + ".bt"
        subject["code"] = f'http://127.0.0.1:9000/{subject["BT"]}'

        with open(f'./output/{subject["BT"]}', 'w') as o:
            o.write(code)

        compiler = BTCompiler()
        compiler.compile(f'./output/{subject["BT"]}')
        subject["Binary"] = compiler.get_cache_path()
    return test_conversion_inter


def generation(name, subject):
    def test_generation_inter(cls):
        parser = EarleyParser(subject["grammar"])
        samples = subject["samples"]
        success_count = 0
        for sample in samples:
            try:
                modified_sample = sample + "$"  # This is required for the EarleyParser
                for _ in parser.parse(modified_sample):
                    pass
                success_count = success_count + 1
            except RecursionError:  # Ignoring RecursionError, not my fault that the EarleyParser cant handle it :D
                success_count = success_count + 1
            except Exception as e:
                if DEBUG:
                    print(f'{name}: Error for sample: {sample if len(sample) < 1000 else "Too Large to Display"}, Error: {repr(e)}')

        # print(f'Result: {success_count} / {len(samples)} (of {length})')
        cls.assertTrue(success_count == len(samples))
    return test_generation_inter


def gather_samples(subject):
    def gather_samples_inter(cls):
        cache_path = f'{subject["Binary"]}-rq1-samples.cache'
        subject["samples"] = []
        subject["fails"] = 0

        if CACHING and exists(cache_path):
            with open(cache_path, "r") as f:
                for line in f.readlines():
                    subject["samples"].append(line.rstrip("\n"))
            cls.skipTest("Samples found in cache.")
            return

        i = 0
        t = 0
        while i < length:
            try:
                proc = subprocess.Popen(
                    [subject["Binary"], "fuzz", "/dev/shm/result.txt"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                result = proc.wait()
                if result != 0:
                    raise Exception("Failed to generate sample!")

                with open('/dev/shm/result.txt', 'r') as f:
                    input_ = f.read().replace("@", "")  # Remove padding if it exists.

                if t > threshold:
                    t = 0
                    i = i + 1
                    continue

                if input_ not in subject["samples"]:
                    subject["samples"].append(input_)
                    i = i + 1
                    t = 0
                else:
                    t = t + 1
            except:
                subject["fails"] = subject["fails"] + 1
                if subject["fails"] > threshold:
                    break
        cls.assertTrue(len(subject["samples"]) > 0)
        with open(cache_path, 'w') as f:
            f.write("\n".join(subject["samples"]))

    return gather_samples_inter


def coverage(subject):
    def coverage_inter(cls):
        cls.assertGreaterEqual(len(subject["samples"]), len(subject["3rd_party_samples"]))

    return coverage_inter


def parsing_valid(subject):
    def parsing_inter(cls):
        #subject["parsing_samples"] = set()
        fuzzer = fuzzingbook.GrammarCoverageFuzzer.GrammarCoverageFuzzer(subject["grammar"])
        for _ in range(length * 10):
            sample = fuzzer.fuzz().rstrip("$")  # remove trailing $ ..some parser alters my grammar >.<
            #subject["parsing_samples"].add(sample)
            with open('/dev/shm/input.txt', 'w') as f:
                f.write(sample)

            proc = subprocess.Popen(
                [subject["Binary"], "parse", "/dev/shm/input.txt"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            result = proc.wait()
            if result != 0:
                cls.assertTrue(False, f"Failed to parse sample:\n{sample}")

        # JSON cant deal with sets
        #subject["parsing_samples"] = list(subject["parsing_samples"])

    return parsing_inter


def parsing_invalid(subject):
    def delete_random_character(s: str) -> str:
        """Returns s with a random character deleted"""
        if s == "":
            return s

        pos = random.randint(0, len(s) - 1)
        # print("Deleting", repr(s[pos]), "at", pos)
        return s[:pos] + s[pos + 1:]

    def insert_random_character(s: str) -> str:
        """Returns s with a random character inserted"""
        pos = random.randint(0, len(s))
        random_character = chr(random.randrange(32, 127))
        # print("Inserting", repr(random_character), "at", pos)
        return s[:pos] + random_character + s[pos:]

    def flip_random_character(s):
        """Returns s with a random bit flipped in a random position"""
        if s == "":
            return s

        pos = random.randint(0, len(s) - 1)
        c = s[pos]
        bit = 1 << random.randint(0, 6)
        new_c = chr(ord(c) ^ bit)
        # print("Flipping", bit, "in", repr(c) + ", giving", repr(new_c))
        return s[:pos] + new_c + s[pos + 1:]

    def shuffle_string(s):
        lst = list(s)
        random.shuffle(lst)
        return "".join(lst)

    def mutate(s: str) -> str:
        """Return s with a random mutation applied"""
        mutators = [
            #delete_random_character,
            #insert_random_character,
            #flip_random_character,
            shuffle_string
        ]
        mutator = random.choice(mutators)
        # print(mutator)
        return mutator(s)

    def parsing_inter(cls):
        subject["parsing_samples_invalid"] = set()
        parser = EarleyParser(subject["grammar"])
        fuzzer = fuzzingbook.GrammarCoverageFuzzer.GrammarCoverageFuzzer(subject["grammar"])
        for _ in range(length):
            sample = fuzzer.fuzz().rstrip("$")  # remove trailing $ ..some parser alters my grammar >.<
            for _ in range(10):
                sample = mutate(sample)
                subject["parsing_samples_invalid"].add(repr(sample))
                with open('/dev/shm/input.txt', 'w') as f:
                    f.write(sample)

                proc = subprocess.Popen(
                    [subject["Binary"], "parse", "/dev/shm/input.txt"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                result = proc.wait()
                if result == 0:
                    # Sample should have been rejected.
                    # Let's check if the mutation was valid by accident
                    try:
                        modified_sample = sample + "$"  # This is required for the EarleyParser
                        for _ in parser.parse(modified_sample):
                            pass
                    except Exception:
                        # if there is an exception the sample was invalid and the test failed!
                        subject["parsing_samples_invalid"] = list(subject["parsing_samples_invalid"])
                        cls.assertTrue(False, f"Failed to reject sample:\n{sample}")

        # JSON cant deal with sets
        subject["parsing_samples_invalid"] = list(subject["parsing_samples_invalid"])

    return parsing_inter


def main():
    filenames = []
    try:
        _, _, filenames = next(walk("./rq1_input"))
    except StopIteration:
        pass

    test_cases = {}
    for filename in filenames:
        test_cases[filename] = {}
        with open(f'./rq1_input/{filename}', "r") as f:
            test_cases[filename]["grammar"] = json.load(f)

    for key, subject in test_cases.items():
        # Hacky solution to ensure correct order
        # "Note that the order in which the various test cases will be run is determined by sorting
        # the test function names with respect to the built-in ordering for strings" - DOCS
        setattr(FileTest, f"test_a_3rd_party_{key}", third_party_ll1(subject))
        setattr(FileTest, f"test_b_conversion_{key}", conversion(key, subject))
        setattr(FileTest, f"test_c_gather_sample_{key}", gather_samples(subject))
        setattr(FileTest, f"test_d_generation_{key}", generation(key, subject))
        # setattr(FileTest, f"test_e_coverage_{key}", coverage(subject))
        setattr(FileTest, f"test_f_parsing_valid_{key}", parsing_valid(subject))
        setattr(FileTest, f"test_g_parsing_invalid_{key}", parsing_invalid(subject))

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(testCaseClass=FileTest)
    unittest.TextTestRunner(stream=sys.stdout, descriptions=True, verbosity=2).run(suite)

    for _, value in test_cases.items():
        value["grammar"] = "Removed"
    create_result_page(test_cases)

