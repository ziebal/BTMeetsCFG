from os import walk
import json
import time
from fuzzingbook.Parser import EarleyParser
import fuzzingbook.GrammarCoverageFuzzer


PATH = "/mnt/d/projects/BTMeetsCFG/samples"

def main():
    filenames = []
    try:
        _, _, filenames = next(walk(PATH))
    except StopIteration:
        pass

    for filename in filenames:
        with open(f'{PATH}/{filename}', "r") as f:
            # print(f"Running benchmark for {filename}")
            grammar = json.load(f)

            fuzzer = fuzzingbook.GrammarCoverageFuzzer.GrammarCoverageFuzzer(grammar)
            st = time.time()
            for i in range(10000):
                fuzzer.fuzz()
            elapsed_time = time.time() - st
            fuzzTime = 10000 / elapsed_time

            samples = []
            for i in range(10000):
                samples.append(fuzzer.fuzz())
            parser = EarleyParser(grammar)
            st = time.time()
            result = 0
            for sample in samples:
                for res in parser.parse(sample):
                    if res:
                        result += 1
            elapsed_time = time.time() - st
            parseTime = 10000 / elapsed_time

            # print(f"{filename}: Done")
            print(f"Fuzzing: {fuzzTime}, Parsing: {parseTime}")


if __name__ == "__main__":
    main()