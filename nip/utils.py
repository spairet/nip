import ast
import inspect
import typeguard

from typing import List, Dict, Union, Any


def get_subclasses(cls):
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in get_subclasses(c)])


def get_sub_dict(base_cls):
    return {cls.__name__: cls for cls in get_subclasses(base_cls)}


def deep_equals(first: Union[Dict, List, Any], second: Union[Dict, List, Any]):
    if type(first) != type(second):
        return False
    if isinstance(first, dict):
        for key in first:
            if key not in second:
                return False
            if not deep_equals(first[key], second[key]):
                return False
    elif isinstance(first, list):
        if len(first) != len(second):
            return False
        for i, j in zip(first, second):
            if not deep_equals(i, j):
                return False
    else:
        return first == second
    return True


def iterate_items(obj):
    if isinstance(obj, (list, tuple)):
        for i, value in enumerate(obj):
            yield i, value
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield key, value


def flatten(obj, delimiter='.', keys=()):
    if not isinstance(obj, (list, tuple, dict)):
        return {delimiter.join(keys): obj}

    result = {}
    for key, value in iterate_items(obj):
        result.update(
            flatten(value, delimiter, keys=keys + (str(key),)))
    return result

