from __future__ import annotations

import nip.parser
import nip.stream

from .base import Node


def read_node(stream: nip.stream.Stream, parser: nip.parser.Parser) -> Node:
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
        raise nip.parser.ParserError(stream, "Wrong right value")
    return value
