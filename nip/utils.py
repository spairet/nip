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


def check_typing(func, args, kwargs):
    signature = inspect.signature(func)
    for arg, param in zip(args, signature.parameters.values()):
        if param.annotation is inspect.Parameter.empty:
            continue
        typeguard.check_type(param.name, arg, param.annotation)

    for name, value in kwargs.items():
        if name not in signature.parameters:
            continue  # handled by python
        annotation = signature.parameters[name].annotation
        if annotation is inspect.Parameter.empty:
            continue
        typeguard.check_type(name, value, annotation)
