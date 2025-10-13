from typing import List, Any, Union

from .utils import iterate_items


class DictObject(dict):
    def __getattr__(self, item):
        return self[item]

    def add_item(self, key, value):
        prefix = key.split(".")[0]
        suffix = ".".join(key.split(".")[1:])
        if len(suffix) == 0:
            setattr(self, prefix, value)
        else:
            getattr(self, prefix)[suffix] = value
