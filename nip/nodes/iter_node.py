from __future__ import annotations

from typing import TYPE_CHECKING, Any

import nip
from .. import tokens

from .base import Node
from .reader import read_node
from .scalar import Value

if TYPE_CHECKING:
    from ..constructor import Constructor
    from ..dumper import Dumper
    from ..parser.parser import Parser
    from ..stream import Stream


class Iter(Node):
    def __init__(self, name: str = "", value: Any = None, line: int = None, pos: int = None):
        super(Iter, self).__init__(name, value)
        self._return_index = -1
        self._line = line
        self._pos = pos

    @classmethod
    def read(cls, stream: Stream, parser: Parser):
        from .args import Args

        read_tokens = stream.peek(tokens.Operator("@"), tokens.Name) or stream.peek(tokens.Operator("@"))
        if read_tokens is None:
            return None
        line, pos = stream.step()
        value = read_node(stream, parser)
        if isinstance(value, Value) and isinstance(value._value, list):
            value = value._value
        elif isinstance(value, Args) and value._is_list():
            value = value
        else:
            raise nip.parser.ParserError(stream, "List is expected as a value for Iterable node")
        if len(read_tokens) == 1:
            iterator = Iter("", value, line=line, pos=pos)
        else:
            iterator = Iter(read_tokens[1]._value, value, line=line, pos=pos)

        parser.iterators.append(iterator)
        return iterator

    def to_python(self):
        if self._return_index == -1:
            raise iter(self._value)
        if isinstance(self._value[self._return_index], Node):
            return self._value[self._return_index].to_python()
        return self._value[self._return_index]

    @nip.constructor.construct_method
    def _construct(self, constructor: Constructor):
        from .args import Args

        if self._return_index == -1:
            raise Exception("Iterator index was not specified by IterParser")
        if isinstance(self._value, list):
            return self._value[self._return_index]
        elif isinstance(self._value, Args):
            return self._value[self._return_index]._construct(constructor)
        else:
            raise nip.constructor.ConstructorError(self, (), {}, "Unexpected iter value type")

    def _dump(self, dumper: Dumper):
        from .args import Args

        if self._return_index == -1:
            raise nip.dumper.DumpError("Dumping an iterator but index was not specified by IterParser")
        if isinstance(self._value, list):
            return str(self._value[self._return_index])
        elif isinstance(self._value, Args):
            return self._value[self._return_index]._dump(dumper)
        else:
            raise nip.dumper.DumpError("Unable to dump Iterable node: unexpected value type")
