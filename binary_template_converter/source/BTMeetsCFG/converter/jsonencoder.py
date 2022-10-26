import json
from BTMeetsCFG.CFG2BT.globaldefines import Label


class JSONEncoder:
    @staticmethod
    def __default(obj):
        if type(obj) is Label:
            return obj.value
        if type(obj) is set:
            return list(obj)
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')

    @staticmethod
    def dumps(obj):
        return json.dumps(obj, default=JSONEncoder.__default, indent=4)
