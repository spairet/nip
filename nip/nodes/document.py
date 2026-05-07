from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from .. import tokens

from .base import Node
from .reader import read_node

if TYPE_CHECKING:
    from ..dumper import Dumper
    from ..parser.parser import Parser
    from ..stream import Stream


class Document(Node):
    def __init__(
        self,
        name: str = "",
        value: Union[Node, Any] = None,
        line: int = None,
        pos: int = 0,
    ):
        super().__init__(name, value)
        self._path = None
        self._line = line
        self._pos = pos

    @classmethod
    def read(cls, stream: Stream, parser: Parser) -> "Document":
        line, pos = stream.line, stream.pos
        doc_name = cls._read_name(stream)
        content = read_node(stream, parser)
        return Document(doc_name, content, line, pos)

    @classmethod
    def _read_name(cls, stream: Stream):
        read_tokens = stream.peek(tokens.Operator("---"), tokens.Name) or stream.peek(
            tokens.Operator("---")
        )
        if read_tokens is not None:
            stream.step()
            if len(read_tokens) == 2:
                return read_tokens[1]._value
        return ""

    def _dump(self, dumper: Dumper):
        string = "---"
        if self._name:
            string += " " + self._name + " "
        return string + self._value._dump(dumper)

    def update(self):
        self.dump(self._path)
