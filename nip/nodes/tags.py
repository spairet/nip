from __future__ import annotations

import nip
import nip.constructor
import nip.dumper
import nip.parser
import nip.stream
import nip.tokens as tokens

from .base import Node
from .reader import read_node
from .scalar import Nothing


class Tag(Node):
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser):
        read_tokens = stream.peek(tokens.Operator("!"), tokens.Name)
        if read_tokens is None:
            return None
        name = read_tokens[1]._value
        line, pos = stream.step()

        value = read_node(stream, parser)
        return Tag(name, value, line=line, pos=pos)

    @nip.constructor.construct_method
    def _construct(self, constructor: nip.constructor.Constructor):
        from .args import Args

        if isinstance(self._value, Args):
            args, kwargs = self._value._construct(constructor, always_pair=True)
        else:
            value = self._value._construct(constructor)
            if isinstance(value, Nothing):
                args, kwargs = [], {}
            else:
                args, kwargs = [value], {}
        return nip.constructor.construct_with_args(
            self._name, args, kwargs, constructor, self
        )

    def _dump(self, dumper: nip.dumper.Dumper):
        return f"!{self._name} " + self._value._dump(dumper)


class Class(Node):
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser):
        read_tokens = stream.peek(tokens.Operator("!&"), tokens.Name)
        if read_tokens is None:
            return None
        name = read_tokens[1]._value
        line, pos = stream.step()

        value = read_node(stream, parser)
        if not isinstance(value, Nothing):
            raise nip.parser.ParserError(
                stream, "Class should be created with nothing to the right."
            )

        return Class(name, value, line=line, pos=pos)

    @nip.constructor.construct_method
    def _construct(self, constructor: nip.constructor.Constructor):
        value = self._value._construct(constructor)
        assert isinstance(
            value, Nothing
        ), "Unexpected right value while constructing Class"
        return constructor.builders[self._name]

    def _dump(self, dumper: nip.dumper.Dumper):
        return f"!&{self._name} " + self._value._dump(dumper)
