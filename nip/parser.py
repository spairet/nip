import nip.elements as elements

from pathlib import Path
from typing import Union

from .stream import Stream


class Parser:  # mb: we don't need Parser itself. its just storage for links and tags. Hm...
    def __init__(self, implicit_fstrings: bool = True):
        self.links = []
        self.iterators = []
        self.implicit_fstrings = implicit_fstrings
        self.last_indent = -1

    def parse(self, path: Union[str, Path]):
        path = Path(path)
        with path.open() as f_stream:
            string_representation = f_stream.read()

        return self.parse_string(string_representation)

    def __call__(self, path: Union[str, Path]):
        return self.parse(path)

    def parse_string(self, string):
        stream = Stream(string)  # mb: add stream to parser and log errors more convenient
        return elements.Document.read(stream, self)

    def has_iterators(self) -> bool:
        return len(self.iterators) > 0


class ParserError(Exception):  # ToDo: currently blank lines skipped thus printed line mb wrong
    def __init__(self, stream: Stream, msg: str):
        self.line = stream[0].line
        self.pos = stream[0].pos
        self.msg = msg

    def __str__(self):
        return f"{self.line}:{self.pos}: {self.msg}"
