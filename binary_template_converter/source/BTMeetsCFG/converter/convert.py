import json
from os import walk, path
from typing import Optional, TextIO

from BTMeetsCFG.BT2CFG.btconverter import BTConverter
from BTMeetsCFG.CFG2BT.cfgconverter import CFGConverter


def print_config(input_file: str, output_file: str, universal: bool) -> None:
    print(f"Inputfile: {input_file}\nOutputfile: {output_file}\nTo Universal: {universal}")


def convert_from_universal(input_file: Optional[TextIO]) -> str:
    input_grammar = json.load(input_file)
    cfgc = CFGConverter(input_grammar)
    return cfgc.convert()


def convert_to_universal(input_file_path: str) -> str:
    btc = BTConverter(input_file_path)
    return btc.convert()


def handle_file(input_file_path: str, output_file_path: str = None, universal: bool = None) -> None:
    if universal is None:
        if path.splitext(input_file_path)[1] == ".json":
            universal = False
        else:
            universal = True

    if not output_file_path:
        output_file_path = "output/" + path.splitext(input_file_path)[0].split("/")[-1] \
                           + (".json" if universal else ".bt")

    print_config(input_file_path, output_file_path, universal)

    if not universal:
        # We need the file content for the following steps
        # Hence we open the file, read its content and pass it to the converter.
        input_file = None
        try:
            input_file = open(input_file_path, 'r')
        except FileNotFoundError:
            print("Input file was not found!")
            exit(1)
        result = convert_from_universal(input_file)
    else:
        # Here we only need the path. The file will be processed by FormatFuzzer
        result = convert_to_universal(input_file_path)

    print(result, file=open(output_file_path, "w"))


def main(pargs) -> None:
    if pargs.input:
        print("Single file mode!")
        handle_file(pargs.input, pargs.output, pargs.universal)
    else:
        print("Directory mode!")
        filenames = []
        try:
            _, _, filenames = next(walk("./input"))
        except StopIteration:
            pass

        for filename in filenames:
            handle_file("input/" + filename)
