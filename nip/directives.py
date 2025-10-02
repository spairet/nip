"""Contains nip directives."""

import nip.elements
from nip.parser import Parser, ParserError, parse
from .stream import Stream
from .update import update


def insert_directive(node, stream: Stream):  # mb: class; mb: just a Node, not a directive
    if isinstance(node, nip.elements.Value):
        path = node.to_python()
        assert isinstance(path, str), "Load directive expects path as an argument."
        parser = Parser()
        config = parser.parse(path)  # Document
        return config._value

    elif isinstance(node, nip.elements.Args):
        assert len(node._args) == 1, "only single positional argument will be treated as config path."
        path = node[0].to_python()
        assert isinstance(path, str), "Load directive expects path as first argument."
        parser = Parser()
        parser.link_replacements = node._kwargs
        config = parser.parse(path)  # Document
        return config._value

    else:
        raise ParserError(
            stream,
            "string or combination of arg and **kwargs are expected as value of !!insert directive",
        )


def update_directive(node, stream: Stream):  # mb: skip directive operator
    if not isinstance(node, nip.elements.Args) or "_update_" not in node:
        raise ParserError(stream, "!!update directive expects dict node with __update__ key.")
    update_config_path = node["_update_"].to_python()
    del node._kwargs["_update_"]
    return update(node, update_config_path)


def base_directive(node, stream: Stream):  # mb: parent
    if not isinstance(node, nip.elements.Args) or "_base_" not in node:
        raise ParserError(stream, "!!base directive expects dict node with __base__ key.")
    base_config_path = node["_base_"].to_python()
    base_config = parse(base_config_path)
    del node._kwargs["_base_"]
    return update(base_config, node)


_directives = {"insert": insert_directive, "update": update_directive, "base": base_directive}


def call_directive(name, right_value, stream: Stream):
    if name not in _directives:
        raise ParserError(stream, f"Unknown parser directive '{name}'.")
    return _directives[name](right_value, stream)
