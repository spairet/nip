from __future__ import annotations

from typing import TYPE_CHECKING

import nip
from .. import tokens

from .base import Node

if TYPE_CHECKING:
    from ..constructor import Constructor
    from ..dumper import Dumper
    from ..parser.parser import Parser
    from ..stream import Stream


class Value(Node):
    @classmethod
    def read(cls, stream: Stream, parser: Parser):
        tokens_list = [
            tokens.Number,
            tokens.NoneToken,
            tokens.Bool,
            tokens.String,
            tokens.List,
            tokens.TupleToken,
            tokens.Dict,
        ]
        for token in tokens_list:
            read_tokens = stream.peek(token)
            if read_tokens is not None:
                line, pos = stream.step()
                return Value(
                    read_tokens[0]._name, read_tokens[0]._value, line=line, pos=pos
                )
        return None

    def to_python(self):
        return self._value

    @nip.constructor.construct_method
    def _construct(self, constructor: Constructor = None):
        constructor[self] = self._value
        return self._value

    def _dump(self, dumper: Dumper):
        if isinstance(self._value, str):
            return f'"{self._value}"'
        return str(self._value)

    def __len__(self):
        return len(self._value)


class InlinePython(Node):
    @classmethod
    def read(cls, stream: Stream, parser: Parser):
        read_tokens = stream.peek(tokens.InlinePython)
        if read_tokens is None:
            return None
        line, pos = stream.step()
        exec_string = read_tokens[0]._value
        return InlinePython(value=exec_string, line=line, pos=pos)

    @nip.constructor.construct_method
    def _construct(self, constructor: Constructor):
        symbols, attributes_access = nip.utils.extract_symbols_from_code(self._value)
        namespace = nip.utils.Namespace()
        root = self._get_root()
        for item in attributes_access:
            if item in root:
                namespace[item] = constructor[root[item]]
        for symbol in symbols:
            if symbol in constructor:
                namespace[symbol] = constructor[symbol]
        locals().update(namespace.__dict__)
        return eval(self._value)

    def _dump(self, dumper: Dumper):
        return f"`{self._value}`"

    def to_python(self):
        return f"`{self._value}`"


class Nothing(Node):
    @classmethod
    def read(cls, stream: Stream, parser: Parser):
        line, pos = stream.line, stream.pos
        if not stream:
            return Nothing(line=line, pos=pos)

        indent = stream.pos
        if stream.pos == 0 or (
            stream.lines[stream.line][: stream.pos].isspace()
            and indent <= parser.last_indent
        ):
            return Nothing(line=line, pos=pos)

    @nip.constructor.construct_method
    def _construct(self, constructor: Constructor):
        return self

    def _dump(self, dumper: Dumper):
        return ""

    def to_python(self):
        return None


class FString(Node):
    @classmethod
    def read(cls, stream: Stream, parser: Parser):
        read_tokens = stream.peek(tokens.PythonString)
        if read_tokens is None:
            return None
        line, pos = stream.step()
        string, token_type = read_tokens[0]._value
        if token_type == "r":
            print(
                "Warning: all strings in NIP are already python r-string. You don't have to explicitly specify it."
            )
        return FString(value=string, line=line, pos=pos)

    @nip.constructor.construct_method
    def _construct(self, constructor: Constructor):
        symbols, attributes_access = nip.utils.extract_symbols_from_code(
            f"f{self._value}"
        )
        namespace = nip.utils.Namespace()
        root = self._get_root()
        for item in attributes_access:
            if item in root:
                namespace[item] = constructor[root[item]]
        for symbol in symbols:
            if symbol in constructor:
                namespace[symbol] = constructor[symbol]
        locals().update(namespace.__dict__)
        return eval(f"f{self._value}")

    def _dump(self, dumper: Dumper):
        return f"f{self._value}"

    def to_python(self):
        return f"f{self._value}"
