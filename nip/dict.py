from typing import List, Any, Union

from .utils import iterate_items


class DictObject(dict):
    def __getattr__(self, item):
        return self[item]

    @classmethod
    def create(cls, obj):
        return convert(obj)

    def add_item(self, key, value):
        prefix = key.split(".")[0]
        suffix = ".".join(key.split(".")[1:])
        if len(suffix) == 0:
            setattr(self, prefix, value)
        else:
            getattr(self, prefix)[suffix] = value


def convert(obj) -> Union[DictObject, List, Any]:
    if isinstance(obj, (list, dict)):
        for key, value in iterate_items(obj):
            obj[key] = convert(value)  # so we preserve links
    if isinstance(obj, tuple):
        for sub_obj in obj:
            for key, value in iterate_items(sub_obj):
                sub_obj[key] = convert(value)
    return obj
