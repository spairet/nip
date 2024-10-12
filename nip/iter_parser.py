from collections import defaultdict
from itertools import product
from typing import Iterable

from .elements import Node
from .parser import Parser


class IterParser:  # mb: insert this functionality into Parser (save parsed tree in Parser)
    def __init__(self, parser: Parser, element: Node = None):
        self.iterators = parser.iterators
        self.element = element

    def iter_configs(self, element: Node) -> Iterable[Node]:
        iter_groups = defaultdict(list)
        for i, iterator in enumerate(self.iterators):
            name = iterator._name if iterator._name else f"_{i}"
            iter_groups[name].append(iterator)
        for group_name, group in iter_groups.items():
            iter_len = len(group[0]._value)
            for iterator in group:
                if len(iterator._value) != iter_len:
                    raise IterParserError(f"Iterators of group '{group_name}' have different lengths")

        group_names = sorted(iter_groups.keys())
        group_lengths = [len(iter_groups[name][0]._value) for name in group_names]
        index_sets = product(*(range(length) for length in group_lengths))

        for indexes in index_sets:
            for index, group_name in zip(indexes, group_names):
                for iterator in iter_groups[group_name]:
                    iterator._return_index = index
            yield element

    def __iter__(self):
        if self.element is None:
            raise IterParserError("config element to iterate through was not defined in __init__")
        return self.iter_configs(self.element)


class IterParserError(Exception):
    pass
