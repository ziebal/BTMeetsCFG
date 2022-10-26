import hashlib
import os
import subprocess
from BTMeetsCFG.converter.logger import Log
from .ffwrapper import FFWrapper


class BTCompiler:
    def __init__(self):
        self.log = Log("BTCompiler")
        self.__cache_path = None

    @staticmethod
    def __hash_file(target):
        BUF_SIZE = 65536

        sha256 = hashlib.sha256()

        with open(target, 'rb') as f:
            while True:
                data = f.read(BUF_SIZE)
                if not data:
                    break
                sha256.update(data)

        return sha256.hexdigest()

    def get_cache_path(self):
        return self.__cache_path

    def compile(self, input_file_path: str) -> FFWrapper:
        file_name = input_file_path.split("/")[-1]
        tmp_binary_path = f'/FormatFuzzer/build/{file_name}-fuzzer'
        self.__cache_path = f'/FormatFuzzer/build/{self.__hash_file(input_file_path)}'

        if not os.path.exists(self.__cache_path):
            # Build Fuzzers from template files.
            subprocess.call(['bash', '/source/BTMeetsCFG/BT2CFG/template_builder.sh', input_file_path])
            # self.log.debug(f'Binary Path: {fuzzer_binary_path}')
            os.rename(tmp_binary_path, self.__cache_path)

        return FFWrapper(self.__cache_path)
