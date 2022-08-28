"""Contains nip directives."""


import nip.parser  # This import pattern because of cycle imports
import nip.elements
import nip.constructor
import nip.stream


def insert_directive(path: str):
    assert isinstance(path, str), "Load directive expects path as an argument."
    parser = nip.parser.Parser()
    config = parser.parse(path)  # nip.elements.Document
    return config.value


_directives = {
    'insert': insert_directive
}


def call_directive(name, right_value, stream: nip.stream.Stream):
    if name not in _directives:
        raise nip.parser.ParserError(stream, f"Unknown parser directive '{name}'.")
    constructor = nip.constructor.Constructor()
    args = constructor.construct(right_value)
    if isinstance(args, dict):  # mb: check what constructed dict? Args or any dict?
        return _directives[name](**args)
    if isinstance(args, (list, tuple)):
        return _directives[name](*args)
    if args is None:  # mb: check Nothing. (copy paste all the stuff from !Tag)
        return _directives[name]()
    return _directives[name](args)
