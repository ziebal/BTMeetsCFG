from .jsonencoder import JSONEncoder
from typing import Union


class Log:
    def __init__(self, class_name: str):
        self.class_name = class_name

    def __internal_print(self, message: Union[str, object]) -> None:
        if type(message) is str:
            print(f'{self.class_name}: {message}')
        else:
            print(f'{self.class_name}: {JSONEncoder.dumps(message)}')

    def debug(self, message: Union[str, object]) -> None:
        self.__internal_print(message)



