from typing import Dict, List
from binary_template_converter.source.BTMeetsCFG.oldVersion.universal_lexer import UniversalLexer
from universal_parser import UniversalParser


class FromUniversal:
    def __init__(self, input_grammar: Dict[str, List[str]]):
        self.input_grammar = input_grammar

    def convert(self):
        # 1. Step: Run the lexer and get all tokens in a usable format.
        lexer = UniversalLexer(self.input_grammar)
        print("Lexer result:", lexer)

        # 2. Step: Run the parser with the tokens generated by the lexer.
        parser = UniversalParser(lexer)
        return parser.parse()
