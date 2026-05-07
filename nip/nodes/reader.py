from __future__ import annotations

from typing import TYPE_CHECKING

from .base import Node

if TYPE_CHECKING:
    from ..parser.parser import Parser
    from ..stream import Stream


def read_node(stream: Stream, parser: Parser) -> Node:
    from .args import Args
    from .directive import Directive
    from .iter_node import Iter
    from .references import Link, LinkCreation
    from .scalar import FString, InlinePython, Nothing, Value
    from .tags import Class, Tag

    value = (
        Directive.read(stream, parser)
        or LinkCreation.read(stream, parser)
        or Link.read(stream, parser)
        or Class.read(stream, parser)
        or Tag.read(stream, parser)
        or Iter.read(stream, parser)
        or Args.read(stream, parser)
        or FString.read(stream, parser)
        or Nothing.read(stream, parser)
        or InlinePython.read(stream, parser)
        or Value.read(stream, parser)
    )

    if value is None:
        import nip

        raise nip.parser.ParserError(stream, "Wrong right value")
    return value
