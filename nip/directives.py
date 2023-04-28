"""Contains nip directives."""


import nip.parser  # This import pattern because of cycle imports
import nip.constructor
import nip.stream


def insert_directive(right_value, stream: nip.stream.Stream):
    from nip.elements import Value, Args
    if isinstance(right_value, Value):
        constructor = nip.constructor.Constructor()
        path = constructor.construct(right_value)
        assert isinstance(path, str), "Load directive expects path as an argument."
        parser = nip.parser.Parser()
        config = parser.parse(path)  # nip.elements.Document
        return config.value

    elif isinstance(right_value, Args):
        assert len(right_value.value[0]) == 1, "only single positional argument will be treated as config path."
        constructor = nip.constructor.Constructor()
        path = constructor.construct(right_value.value[0][0])
        assert isinstance(path, str), "Load directive expects path as first argument."
        parser = nip.parser.Parser()
        parser.link_replacements = right_value.value[1]
        config = parser.parse(path)  # nip.elements.Document
        return config.value

    else:
        raise nip.parser.ParserError(
            stream, "string or combination of arg and **kwargs are expected as value of !!insert directive")


_directives = {
    'insert': insert_directive
}


def call_directive(name, right_value, stream: nip.stream.Stream):
    if name not in _directives:
        raise nip.parser.ParserError(stream, f"Unknown parser directive '{name}'.")
    return _directives[name](right_value, stream)
