from __future__ import annotations

from typing import TYPE_CHECKING

import nip.directives
from .. import tokens

from .base import Node
from .reader import read_node

if TYPE_CHECKING:
    from ..parser.parser import Parser
    from ..stream import Stream


class Directive(Node):
    @classmethod
    def read(cls, stream: Stream, parser: Parser):
        read_tokens = stream.peek(tokens.Operator("!!"), tokens.Name)
        if read_tokens is None:
            return None
        name = read_tokens[1]._value
        stream.step()
        value = read_node(stream, parser)
        return nip.directives.call_directive(name, value, stream)
