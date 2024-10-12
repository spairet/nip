from pathlib import Path
from typing import Union

import nip.elements as elements
from .stream import Stream


class Parser:
    def __init__(
        self,
        implicit_fstrings: bool = True,
        strict: bool = False,
        sequential_links: bool = False,
    ):
        self.links = []
        self.iterators = []
        self.link_replacements = {}  # used with !!insert directive
        self.implicit_fstrings = implicit_fstrings
        self.strict = strict
        self.sequential_links = sequential_links
        self.last_indent = -1
        self.stack = []

    def parse(self, path: Union[str, Path]):
        path = Path(path)
        with path.open() as f_stream:
            string_representation = f_stream.read()

        tree = self.parse_string(string_representation)
        tree._path = path
        return tree

    def __call__(self, path: Union[str, Path]):
        return self.parse(path)

    def parse_string(self, string):
        stream = Stream(string)  # mb: add stream to parser and log errors more convenient
        tree = elements.Document.read(stream, self)
        if stream:
            raise ParserError(stream, "Wrong statement.")
        tree._update_parents()
        return tree

    def has_iterators(self) -> bool:
        return len(self.iterators) > 0


class ParserError(Exception):
    def __init__(self, stream: Stream, msg: str):
        self.line = stream.n
        self.pos = stream.pos
        self.msg = msg

    def __str__(self):
        return f"{self.line + 1}:{self.pos + 1}: {self.msg}"
