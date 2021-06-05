from itertools import product
from typing import Iterable

from .parser import Parser
from .elements import Element


class IterParser:  # mb: insert this functionality into Parser (save parsed tree in Parser)
    def __init__(self, parser: Parser, element: Element = None):
        self.iterators = parser.iterators
        self.element = element

    def iter_configs(self, element: Element) -> Iterable[Element]:
        index_sets = product(*(range(len(iterator.value)) for iterator in self.iterators))
        for indexes in index_sets:
            for iterator, i in zip(self.iterators, indexes):
                iterator.return_index = i  # mb: better to get this from constructor
            yield element

    def __iter__(self):
        if self.element is None:
            raise IterParserError("config element to iterate through was not defined in __init__")
        return self.iter_configs(self.element)


class IterParserError(Exception):
    pass