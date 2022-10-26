from universal_first_set import FirstSet
from universal_follow_set import FollowSet
from universal_parsing_table import ParsingTable
from universal_parser_generator import ParserGenerator
from universal_follow_set_specific import FollowSetSpecific
from universal_bt_template_generator import BinaryTemplateGenerator
from universal_bt_template_generator_specific import BinaryTemplateGeneratorSpecific

class UniversalParser:
    def __init__(self, lexer):
        self.__lexer = lexer

    def __generate_first_follow_sets(self):
        tokens = self.__lexer.get_grammar()
        first_set = FirstSet(tokens)
        follow_set = FollowSet(tokens, first_set)

        print("First Set:", first_set)
        print("Follow Set:", follow_set)

        return first_set, follow_set

    def __generate_parsing_table(self, first_set, follow_set):
        parsing_table = ParsingTable(first_set, follow_set, self.__lexer) #, IGNORE_DUPLICATES=True)

        #print("Parsing Table:", parsing_table)
        #parsing_table.print()

        return parsing_table

    def __generate_follow_set_specific(self, first_set, follow_set, parsing_table):
        tokens = self.__lexer.get_grammar()
        follow_set_specific = FollowSetSpecific(tokens, first_set, follow_set, parsing_table)

        return follow_set_specific

    def parse(self):
        first_set, follow_set = self.__generate_first_follow_sets()
        parsing_table = self.__generate_parsing_table(first_set, follow_set)
        follow_set_specific = self.__generate_follow_set_specific(first_set, follow_set, parsing_table)
        # template_generator = BinaryTemplateGenerator(self.__lexer.get_token_length())
        # parsing_generator = ParserGenerator(parsing_table, first_set, follow_set, template_generator)
        # print("Internal Parser Representation:", parsing_generator)
        # code = parsing_generator.code()
        bt_gen_specific = BinaryTemplateGeneratorSpecific(parsing_table, self.__lexer.get_token_length())
        code = bt_gen_specific.generate_code(follow_set_specific)
        # print("Parser Code:\n", code)
        return code
