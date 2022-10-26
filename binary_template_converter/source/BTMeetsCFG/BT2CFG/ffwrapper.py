import subprocess
from typing import List, Any, Union
from BTMeetsCFG.converter.logger import Log
from .dataclasses import DTreeEntry, IntermRep


class FormatFuzzerError(Exception):
    """Base class for exceptions"""
    pass


class FFWrapper:
    def __init__(self, path_to_binary: str):
        self.path = path_to_binary
        self.log = Log('FFWrapper')

    @staticmethod
    def __format_item(item) -> Union[DTreeEntry, None]:
        s = item.split(",")

        # FormatFuzzer Stack contains always 3 or 4 elements.
        # Everything else is related to prints.
        if len(s) not in [3, 4]:
            return None
        # return {"start": s[0], "end": s[1], "stack": s[2], "state": s[3] if len(s) == 4 else "Required"}
        return DTreeEntry(s[0], s[1], s[2], s[3] if len(s) == 4 else "Required")

    def __clean_output(self, output: Any) -> List[DTreeEntry]:
        raw_lines = output.split("\n")
        dtree_entries = [self.__format_item(item) for item in raw_lines]
        return list(filter(lambda entry: entry is not None, dtree_entries))

    def execute(self, enable_hex=True) -> IntermRep:
        proc = subprocess.Popen([self.path, "fuzz", "-p", "/dev/shm/result.txt"],
                                stdout=subprocess.PIPE,
                                )
        stdout_value = proc.communicate()[0]
        if proc.returncode != 0:
            raise FormatFuzzerError(
                f"FormatFuzzer Return Code != 0:\n\t{proc.returncode}\n\t{proc.stdout}\n\t{proc.stderr}")

        if enable_hex:
            res_file = open("/dev/shm/result.txt", "rb")
            inp = res_file.read().hex()
        else:
            res_file = open("/dev/shm/result.txt", "rb")
            inp = res_file.read().decode('UTF-8')
        res_file.close()

        dtree = self.__clean_output(stdout_value.decode('UTF-8'))

        return IntermRep(inp, dtree)
