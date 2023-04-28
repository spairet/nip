"""Contains nip directives."""


from .parser import Parser, ParserError
from .constructor import Constructor
from .stream import Stream


def insert_directive(right_value, stream: Stream):
    from nip.elements import Value, Args
    if isinstance(right_value, Value):
        constructor = Constructor()
        path = constructor.construct(right_value)
        assert isinstance(path, str), "Load directive expects path as an argument."
        parser = Parser()
        config = parser.parse(path)  # Document
        return config.value

    elif isinstance(right_value, Args):
        assert len(right_value.value[0]) == 1, "only single positional argument will be treated as config path."
        constructor = Constructor()
        path = constructor.construct(right_value.value[0][0])
        assert isinstance(path, str), "Load directive expects path as first argument."
        parser = Parser()
        parser.link_replacements = right_value.value[1]
        config = parser.parse(path)  # Document
        return config.value

    else:
        raise ParserError(
            stream, "string or combination of arg and **kwargs are expected as value of !!insert directive")


_directives = {
    'insert': insert_directive
}


def call_directive(name, right_value, stream: Stream):
    if name not in _directives:
        raise ParserError(stream, f"Unknown parser directive '{name}'.")
    return _directives[name](right_value, stream)
