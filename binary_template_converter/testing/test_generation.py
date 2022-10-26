import json

import fuzzingbook.GrammarCoverageFuzzer
from fuzzingbook import Parser
import subprocess
import unittest
import logging
import argparse

import sys
sys.path.insert(1, '../source/BTMeetsCFG/converter')
from universal_lexer import UniversalLexer

length = 100
threshold = length / 2


class FileTest(unittest.TestCase):
    pass


def test_3rd_party_ll1(subject):
    def test_inter(cls):
        ll1parser = Parser.LL1Parser(subject["grammar"])
        fuzzer = fuzzingbook.GrammarCoverageFuzzer.GrammarCoverageFuzzer(subject["grammar"])
        samples = []
        for i in range(100):
            samples.append(fuzzer.fuzz())
        success_count = 0
        for sample in samples:
            try:
                ll1parser.parse(sample)
                success_count = success_count + 1
            except:
                print(f'Error for sample: {sample}')

        # print(f'Result: {success_count} / {len(samples)} (of {length})')
        cls.assertTrue(success_count == len(samples))
    return test_inter


def test(name, subject):
    def test_inter(cls):
        ll1parser = Parser.LL1Parser(subject["grammar"])
        samples = subject["samples"]
        success_count = 0
        for sample in samples:
            try:
                ll1parser.parse(sample["data"])
                success_count = success_count + 1
            except:
                print(f'{name}: Error for sample: {sample["name"]} > {sample["data"]}, Length: {len(sample["data"])}')

        # print(f'Result: {success_count} / {len(samples)} (of {length})')
        cls.assertTrue(success_count == len(samples))
    return test_inter


def coverage(name, subject):
    def coverage_inter(cls):
        log = logging.getLogger("coverage")
        log.debug("key=%s", name)
        for sample in subject["samples"]:
            symbols = list(sample["data"])
            for s in symbols:
                subject["tokens"][s] = subject["tokens"][s] + 1
        log.debug(subject["tokens"])
        for _, item in subject["tokens"].items():
            cls.assertTrue(item > 0)
    return coverage_inter


def test_parsing(key, subject):
    def parsing_inter(cls):
        fuzzer = fuzzingbook.GrammarCoverageFuzzer.GrammarCoverageFuzzer(subject["grammar"])
        for _ in range(length * 10):
            f = open(f"parser_input_{key}.tmp", "w")
            gen_data = fuzzer.fuzz()
            f.write(gen_data)
            f.close()
            result = subprocess.run(
                [f"/home/lxnorm/tools/FormatFuzzer/build/{key}.bt-fuzzer", "parse", f"parser_input_{key}.tmp"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                text=True
            )
            cls.assertTrue(result.returncode == 0)
    return parsing_inter


def pprint(string):
    print(json.dumps(string, indent=2))


def gather_seeded_samples(subjects):
    pass


def gather_samples(subjects):
    pass


def gather_samples_slow(key, subject):
    def gather_sample_slow_inter(cls):
        log = logging.getLogger("gather_sample_slow")
        log.debug("key=%s", key)
        subject["samples"] = []
        subject["fails"] = 0
        existing_inputs = []
        i = 0
        t = 0
        while i < length:
            subprocess.run(
                [f"/home/lxnorm/tools/FormatFuzzer/build/{key}.bt-fuzzer", "fuzz", f"inputs/{key}_{i}.input"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
            try:
                f = open(f"inputs/{key}_{i}.input", "r")
                input_ = f.read()
                log.debug("input=%s", input_)
                f.close()
                if t > threshold:
                    t = 0
                    i = i + 1
                    continue
                if input_ not in existing_inputs:
                    existing_inputs.append(input_)
                    subject["samples"].append({"name": f"{key}_{i}.input", "data": input_})
                    i = i + 1
                    t = 0
                else:
                    t = t + 1
            except:
                subject["fails"] = subject["fails"] + 1
                if subject["fails"] > threshold:
                    break
        cls.assertTrue(len(subject["samples"]) > 0)
    return gather_sample_slow_inter


def gather_symbols(subjects):
    for key, subject in subjects.items():
        subject["tokens"] = {}
        lexer = UniversalLexer(subject["grammar"])
        for e in lexer.get_terminals():
            # ignoring epsilon
            if e["token"] != '':
                subject["tokens"][e["token"]] = 0


def find_test_files():
    # We only test the currently build files.
    # Find all the files in the build folder
    result = subprocess.run(
        ["find", "/home/lxnorm/tools/FormatFuzzer/build", "-printf", "%f\n"],
        stdout=subprocess.PIPE, text=True)
    subjects = {}
    for entry in result.stdout.split("\n"):
        if entry.endswith(".bt-fuzzer"):
            subjects[(entry[:-10])] = {}

    # Search the corresponding grammars
    folders = ["input" , "input_working", "input_tmp", "other_inputs"]
    for folder in folders:
        for entry in subjects.keys():
            try:
                f = open(f'/mnt/d/projects/bachelor-proposal/{folder}/{entry}.json', "r")
                if "grammar" in subjects[entry].keys():
                    raise Exception(f"{folder}/{entry} is a duplicate!")
                subjects[entry]["grammar"] = json.load(f)
            except FileNotFoundError:
                pass
    return subjects


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stderr)
    # logging.getLogger("gather_sample_slow").setLevel(logging.DEBUG)
    # logging.getLogger("coverage").setLevel(logging.DEBUG)

    subjects = find_test_files()
    # gather_samples(subjects)
    gather_seeded_samples(subjects)
    gather_symbols(subjects)
    pprint(subjects)
    for key, subject in subjects.items():
        # Hacky solution to ensure correct order
        # "Note that the order in which the various test cases will be run is determined by sorting
        # the test function names with respect to the built-in ordering for strings" - DOCS
        setattr(FileTest, f"test_a_3rd_party_{key}", test_3rd_party_ll1(subject))
        setattr(FileTest, f"test_b_gather_{key}", gather_samples_slow(key, subject))
        setattr(FileTest, f"test_c_sample_{key}", test(key, subject))
        setattr(FileTest, f"test_d_coverage_{key}", coverage(key, subject))
        setattr(FileTest, f"test_e_parsing_{key}", test_parsing(key, subject))

    unittest.main()

    # g++ --coverage -c -I . -std=c++17 -g -O3 -Wall gif.cpp
    # g++ --coverage -c -I . -std=c++17 -g -O3 -Wall fuzzer.cpp
    # g++ --coverage -O3 gif.o fuzzer.o -o gif-fuzzer -lz
