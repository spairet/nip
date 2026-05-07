from __future__ import annotations

from typing import TYPE_CHECKING

import nip
from .. import tokens

from .base import Node
from .reader import read_node

if TYPE_CHECKING:
    from ..constructor import Constructor
    from ..dumper import Dumper
    from ..non_seq_constructor import NonSequentialConstructor
    from ..parser.parser import Parser
    from ..stream import Stream


class LinkCreation(Node):
    @classmethod
    def read(cls, stream: Stream, parser: Parser):
        read_tokens = stream.peek(tokens.Operator("&"), tokens.Name)
        if read_tokens is None:
            return None

        name = read_tokens[1]._value
        line, pos = stream.step()
        value = read_node(stream, parser)
        if name in parser.links:
            raise nip.parser.ParserError(stream, f"Redefining of link '{name}'")
        parser.links.append(name)
        return LinkCreation(name, value, line, pos)

    @nip.constructor.construct_method
    def _construct(self, constructor: Constructor):
        constructor[self._name] = self
        return self._value._construct(constructor)

    def _dump(self, dumper: Dumper):
        return f"&{self._name} {self._value._dump(dumper)}"


class Link(Node):
    @classmethod
    def read(cls, stream: Stream, parser: Parser):
        read_tokens = stream.peek(tokens.Operator("*"), tokens.Name)
        if read_tokens is None:
            return None

        name = read_tokens[1]._value
        line, pos = stream.step()

        if name in parser.link_replacements:
            return parser.link_replacements[name]

        if parser.sequential_links and name not in parser.links:
            nip.parser.ParserError(stream, "Link usage before assignment")

        return Link(name, line=line, pos=pos)

    def to_python(self):
        return "nil"

    @nip.constructor.construct_method
    def _construct(self, constructor: NonSequentialConstructor):
        root = self._get_root()
        if self._name in constructor.links:
            value = constructor[self._name]
        elif self._name in root:
            value = root[self._name]._construct(constructor)
        else:
            raise NameError(f"Unable to resolve link '{self._name}'.")
        return value

    def _dump(self, dumper: Dumper):
        return f"*{self._name}"

    def __getitem__(self, item):
        raise NotImplementedError("'__getitem__' is not implemented for Link node.")

    def __contains__(self, item):
        raise NotImplementedError("'in' operator if not implemented for Link node.")
