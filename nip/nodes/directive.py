from __future__ import annotations

import nip.directives
import nip.parser
import nip.stream
import nip.tokens as tokens

from .base import Node
from .reader import read_node


class Directive(Node):
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser):
        read_tokens = stream.peek(tokens.Operator("!!"), tokens.Name)
        if read_tokens is None:
            return None
        name = read_tokens[1]._value
        stream.step()
        value = read_node(stream, parser)
        return nip.directives.call_directive(name, value, stream)
