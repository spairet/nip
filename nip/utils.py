import ast
import inspect
from typing import List, Dict, Union, Any

import typeguard


def get_subclasses(cls):
    return set(cls.__subclasses__()).union([s for c in cls.__subclasses__() for s in get_subclasses(c)])


def get_sub_dict(base_cls):
    return {cls.__name__: cls for cls in get_subclasses(base_cls)}


def deep_equals(first: Union[Dict, List, Any], second: Union[Dict, List, Any]):
    if type(first) is type(second):
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


def flatten(obj, delimiter=".", keys=()):
    if not isinstance(obj, (list, tuple, dict)):
        return {delimiter.join(keys): obj}

    result = {}
    for key, value in iterate_items(obj):
        result.update(flatten(value, delimiter, keys=keys + (str(key),)))
    return result


def check_typing(func, args, kwargs) -> List[str]:
    try:
        signature = inspect.signature(func)
    except ValueError:  # unable to load function signature (common case for builtin functions)
        return []
    messages = []
    typeguard.typechecked()
    if len(args) > len(signature.parameters.values()):
        messages.append("Too many arguments")
    for arg, param in zip(args, signature.parameters.values()):
        if param.annotation is inspect.Parameter.empty:
            continue
        try:
            typeguard.check_type(arg, param.annotation)
        except typeguard.TypeCheckError as e:
            messages.append(f"{param.name}: {e}")

    for name, value in kwargs.items():
        if name not in signature.parameters:
            continue  # handled by python
        annotation = signature.parameters[name].annotation
        if annotation is inspect.Parameter.empty:
            continue
        try:
            typeguard.check_type(value, annotation)
        except typeguard.TypeCheckError as e:
            messages.append(f"{name}: {e}")

    return messages


class Namespace:
    def __getattr__(self, key: str) -> "Namespace":
        item = Namespace()
        setattr(self, key, item)
        return item

    def __setitem__(self, key, value):
        prefix = key.split(".")[0]
        suffix = ".".join(key.split(".")[1:])
        if len(suffix) == 0:
            setattr(self, prefix, value)
        else:
            getattr(self, prefix)[suffix] = value


class SymbolExtractor(ast.NodeVisitor):
    def __init__(self):
        self.symbols = set()
        self.attribute_accesses = set()

    def visit_Name(self, node):
        """Extract variable names"""
        if isinstance(node.ctx, ast.Load):  # Only interested in reads, not assignments
            self.symbols.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node):
        """Extract attribute accesses like model.backbone.name"""
        if isinstance(node.ctx, ast.Load):  # Only interested in reads
            # Build the full attribute chain
            parts = []
            current = node
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
                full_path = ".".join(reversed(parts))
                self.attribute_accesses.add(full_path)
        self.generic_visit(node)


def extract_symbols_from_code(code_string: str):
    """
    Extract all symbols and attribute accesses from Python code.
    Returns: (simple_symbols, attribute_chains)
    """
    try:
        tree = ast.parse(code_string)
        extractor = SymbolExtractor()
        extractor.visit(tree)
        return extractor.symbols, extractor.attribute_accesses
    except SyntaxError as e:
        print(f"Syntax error in code: {e}")
        return set(), set()
