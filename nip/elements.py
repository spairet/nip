"""Contains all the elements of nip config files"""

from __future__ import annotations

import logging
from abc import abstractmethod, ABC
from pathlib import Path
from typing import Any, Union, Tuple, Dict

import nip.constructor  # This import pattern because of cycle imports
import nip.directives
import nip.dumper
import nip.non_seq_constructor as nsc
import nip.parser
import nip.stream
import nip.tokens as tokens
import nip.utils

_LOGGER = logging.getLogger(__name__)


class Node(ABC, object):
    """Base token for nip file"""

    def __init__(self, name: str = "", value: Union[Node, Any] = None):
        self._name = name
        self._value = value
        self._parent = None

    @classmethod
    @abstractmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[Node, None]:
        pass

    def __str__(self):
        return f"{self.__class__.__name__}('{self._name}', {self._value})"

    def __getitem__(self, item):
        if not isinstance(item, (str, int)):
            raise KeyError(f"Unexpected item type: {type(item)}")
        if isinstance(item, str) and len(item) == 0:
            return self
        return self._value[item]

    def __getattr__(self, item):  # unable to access names like `construct` and 'dump` via this method
        return self.__getitem__(item)

    def __setitem__(self, key, value):
        self._value[key] = value
        self._value._parent = self

    def __setattr__(self, key, value):
        if key.startswith("_"):  # mb: ensure not user's node name?
            self.__dict__[key] = value
        else:
            self.__setitem__(key, value)

    def to_python(self):
        return self._value.to_python()

    def _construct(self, constructor: nip.constructor.Constructor):
        return self._value._construct(constructor)

    def construct(self, base_config: Node = None, strict_typing: bool = False, nonsequential: bool = True):
        return nip.construct(self, base_config=base_config, strict_typing=strict_typing, nonsequential=nonsequential)

    def _dump(self, dumper: nip.dumper.Dumper):
        return self._value._dump(dumper)

    def dump(self, path: Union[str, Path]):
        nip.dump(path, self)

    def dump_string(self):
        return nip.dump_string(self)

    def __eq__(self, other):
        return self._name == other._name and self._value == other._value

    def flatten(self, delimiter=".") -> Dict:
        return nip.utils.flatten(self.to_python(), delimiter)

    def _update_parents(self):
        if isinstance(self._value, Node):
            self._value._parent = self
            self._value._update_parents()

    def _get_root(self):
        if self._parent is None:
            return self
        return self._parent._get_root()

    def update(self):
        self._get_root().update()


Element = Node  # backward compatibility until 1.* version


class Document(Node):  # ToDo: add multi document support
    def __init__(self, name: str = "", value: Union[Node, Any] = None):
        super().__init__(name, value)
        self._path = None

    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Document:
        doc_name = cls._read_name(stream)
        content = read_node(stream, parser)
        return Document(doc_name, content)

    @classmethod
    def _read_name(cls, stream: nip.stream.Stream):
        read_tokens = stream.peek(tokens.Operator("---"), tokens.Name) or stream.peek(tokens.Operator("---"))
        if read_tokens is not None:
            stream.step()
            if len(read_tokens) == 2:
                return read_tokens[1]._value
        return ""

    def _dump(self, dumper: nip.dumper.Dumper):
        string = "---"
        if self._name:
            string += " " + self._name + " "
        return string + self._value._dump(dumper)

    def update(self):
        self.dump(self._path)


class Value(Node):
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[None, Value]:
        tokens_list = [
            tokens.Number,
            tokens.Bool,
            tokens.String,
            tokens.List,
            tokens.TupleToken,
            tokens.Dict,
        ]
        for token in tokens_list:
            read_tokens = stream.peek(token)
            if read_tokens is not None:
                stream.step()
                return Value(read_tokens[0]._name, read_tokens[0]._value)

        return None

    def to_python(self):
        return self._value

    def _construct(self, constructor: nip.constructor.Constructor = None):
        return self._value

    def _dump(self, dumper: nip.dumper.Dumper):
        if isinstance(self._value, str):
            return f'"{self._value}"'
        return str(self._value)

    def __len__(self):
        return len(self._value)


class LinkCreation(Node):
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[Node, None]:
        read_tokens = stream.peek(tokens.Operator("&"), tokens.Name)
        if read_tokens is None:
            # if stream.peek(tokens.Operator('&')):  # mb: do it more certainly: peak operator
            #     raise nip.parser.ParserError(      # mb: firstly and then choose class to read)
            #         stream, "Found variable creation operator '&' but name is not specified")
            return None

        name = read_tokens[1]._value
        stream.step()

        value = read_node(stream, parser)
        if name in parser.links:
            raise nip.parser.ParserError(stream, f"Redefining of link '{name}'")
        parser.links.append(name)

        return LinkCreation(name, value)

    def _construct(self, constructor: nip.constructor.Constructor):
        if nsc.should_construct(self._name, constructor):
            constructor.vars[self._name] = self._value._construct(constructor)
        return constructor.vars[self._name]

    def _dump(self, dumper: nip.dumper.Dumper):
        return f"&{self._name} {self._value._dump(dumper)}"


class Link(Node):
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[Node, None]:
        read_tokens = stream.peek(tokens.Operator("*"), tokens.Name)
        if read_tokens is None:
            return None

        name = read_tokens[1]._value
        stream.step()

        if name in parser.link_replacements:
            return parser.link_replacements[name]

        if parser.sequential_links and name not in parser.links:
            nip.parser.ParserError(stream, "Link usage before assignment")

        return Link(name)

    def to_python(self):
        return "nil"  # something that means that object is not constructed yet.

    def _construct(self, constructor: nip.constructor.Constructor):
        return constructor.vars[self._name]

    def _dump(self, dumper: nip.dumper.Dumper):
        return f"*{self._name}"


class Tag(Node):
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[Tag, None]:
        read_tokens = stream.peek(tokens.Operator("!"), tokens.Name)
        if read_tokens is None:
            return None
        name = read_tokens[1]._value
        stream.step()

        value = read_node(stream, parser)

        return Tag(name, value)

    def _construct(self, constructor: nip.constructor.Constructor):
        if isinstance(self._value, Args):
            args, kwargs = self._value._construct(constructor, always_pair=True)
        else:
            value = self._value._construct(constructor)
            if isinstance(value, Nothing):  # mb: Add IS_NOTHING method
                return constructor.builders[self._name]()
            else:
                args, kwargs = [value], {}

        if self._name not in constructor.builders:
            raise nip.constructor.ConstructorError(
                self,
                args,
                kwargs,
                f"Constructor for Tag '{self._name}' is not registered.",
            )

        messages = nip.utils.check_typing(constructor.builders[self._name], args, kwargs)
        if len(messages) > 0:
            if constructor.strict_typing:
                raise nip.constructor.ConstructorError(self, args, kwargs, "\n".join(messages))
            else:
                _LOGGER.warning(f"Typing mismatch while constructing {self._name}:\n" + "\n".join(messages))

        try:  # Try to construct
            return constructor.builders[self._name](*args, **kwargs)
        except Exception as e:
            raise nip.constructor.ConstructorError(self, args, kwargs, e)

    def _dump(self, dumper: nip.dumper.Dumper):
        return f"!{self._name} " + self._value._dump(dumper)


class Class(Node):
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[Class, None]:
        read_tokens = stream.peek(tokens.Operator("!&"), tokens.Name)
        if read_tokens is None:
            return None
        name = read_tokens[1]._value
        stream.step()

        value = read_node(stream, parser)
        if not isinstance(value, Nothing):
            raise nip.parser.ParserError(stream, "Class should be created with nothing to the right.")

        return Class(name, value)

    def _construct(self, constructor: nip.constructor.Constructor):
        value = self._value._construct(constructor)
        assert isinstance(value, Nothing), "Unexpected right value while constructing Class"

        return constructor.builders[self._name]

    def _dump(self, dumper: nip.dumper.Dumper):
        return f"!&{self._name} " + self._value._dump(dumper)


class Args(Node):
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[Args, None]:
        start_indent = stream.pos
        if start_indent <= parser.last_indent:
            return None

        args = []
        kwargs = {}  # mb: just dict with integer and string keys !
        read_kwarg = False
        while stream and stream.pos == start_indent:
            parser.last_indent = start_indent

            item = cls._read_list_item(stream, parser)
            if item is not None:
                if parser.strict and read_kwarg:
                    raise nip.parser.ParserError(
                        stream,
                        "Positional argument after keyword argument is forbidden in `strict` mode.",
                    )
                args.append(item)
                continue

            key, value = cls._read_dict_pair(stream, parser, kwargs.keys())
            if key is not None:
                read_kwarg = True
                kwargs[key] = value
                continue

            break

        if stream.pos > start_indent:
            raise nip.parser.ParserError(stream, "Unexpected indent")

        if not args and not kwargs:
            return None
        return Args("args", (args, kwargs))

    @classmethod
    def _read_list_item(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[Node, None]:
        read_tokens = stream.peek(tokens.Operator("- "))
        if read_tokens is None:
            return None
        stream.step()

        value = read_node(stream, parser)

        return value

    @classmethod
    def _read_dict_pair(
        cls, stream: nip.stream.Stream, parser: nip.parser.Parser, kwargs_keys
    ) -> Union[Tuple[str, Node], Tuple[None, None]]:
        # mb: read String instead of Name for keys with spaces,
        # mb: but this leads to the case that
        read_tokens = stream.peek(tokens.Name, tokens.Operator(": "))
        if read_tokens is None:
            return None, None

        key = read_tokens[0]._value
        if parser.strict and key in kwargs_keys:
            raise nip.parser.ParserError(
                stream,
                f"Dict key overwriting is forbidden in `strict` " f"mode. Overwritten key: '{key}'.",
            )
        stream.step()

        value = read_node(stream, parser)

        return key, value

    def __str__(self):
        args_repr = "[" + ", ".join([str(item) for item in self._value[0]]) + "]"
        kwargs_repr = "{" + ", ".join([f"{key}: {str(value)}" for key, value in self._value[1].items()]) + "}"

        return f"{self.__class__.__name__}('{self._name}', {args_repr}, {kwargs_repr})"

    def __bool__(self):
        return bool(self._value[0]) or bool(self._value[1])

    def __getitem__(self, item):
        if not isinstance(item, (str, int)):
            raise KeyError(f"Unexpected item type: {type(item)}")
        if isinstance(item, str) and len(item) == 0:
            return self
        if isinstance(item, int):
            return self._value[0][item]
        key = None
        for key in self._value[1]:
            if item.startswith(key):
                break
        if not item.startswith(key):
            raise KeyError(f"'{item}' is not a part of the Node.")
        if len(item) == len(key):
            return self._value[1][key]
        if item[len(key)] != ".":
            raise KeyError(f"items should be separated by a dot '.'.")

        item = item[len(key) + 1 :]
        return self._value[1][key][item]

    def __setitem__(self, key, value):
        value = nip.convert(value)
        if isinstance(key, int):
            self._value[0][key] = value
        else:
            self._value[1][key] = value

    def append(self, value):
        self._value[0].append(nip.convert(value))

    def __len__(self):
        return len(self._value[0]) + len(self._value[1])

    def __iter__(self):
        for item in self._value[0]:
            yield item
        for key, item in self._value[1].items():
            yield item

    def to_python(self):
        args = list(item.to_python() for item in self._value[0])
        kwargs = {key: value.to_python() for key, value in self._value[1].items()}
        assert args or kwargs, "Error converting Args node to python"  # This should never happen
        if args and kwargs:
            result = {}
            result.update(nip.utils.iterate_items(args))
            result.update(nip.utils.iterate_items(kwargs))
            return result
        return args or kwargs

    def _construct(self, constructor: nip.constructor.Constructor, always_pair=False):
        args = list(item._construct(constructor) for item in self._value[0])
        kwargs = {key: value._construct(constructor) for key, value in self._value[1].items()}
        assert args or kwargs, "Error converting Args node to python"  # This should never happen
        if args and kwargs or always_pair:
            return args, kwargs
        return args or kwargs

    def _dump(self, dumper: nip.dumper.Dumper):
        dumped_args = "\n".join(
            [" " * dumper.indent + f"- {item._dump(dumper + dumper.default_shift)}" for item in self._value[0]]
        )
        string = ("\n" if dumped_args else "") + dumped_args

        dumped_kwargs = "\n".join(
            [
                " " * dumper.indent + f"{key}: {value._dump(dumper + dumper.default_shift)}"
                for key, value in self._value[1].items()
            ]
        )
        string += ("\n" if dumped_kwargs else "") + dumped_kwargs

        return string

    def _update_parents(self):
        self.__dict__.update(self._value[1])
        for item in self:
            item._parent = self
            item._update_parents()


class Iter(Node):  # mark all parents as Iterable and allow construct specific instance
    def __init__(self, name: str = "", value: Any = None):
        super(Iter, self).__init__(name, value)
        self._return_index = -1
        # mb: name all the iterators and get the value from constructor rather then use this index

    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[Iter, None]:
        read_tokens = stream.peek(tokens.Operator("@"), tokens.Name) or stream.peek(tokens.Operator("@"))
        if read_tokens is None:
            return None
        stream.step()
        value = read_node(stream, parser)
        if isinstance(value, Value) and isinstance(value._value, list):
            value = value._value
        elif isinstance(value, Args) and len(value._value[1]) == 0:
            value = value
        else:
            raise nip.parser.ParserError(stream, "List is expected as a value for Iterable node")
        if len(read_tokens) == 1:
            iterator = Iter("", value)
        else:
            iterator = Iter(read_tokens[1]._value, value)

        parser.iterators.append(iterator)
        return iterator

    def to_python(self):
        if self._return_index == -1:
            raise iter(self._value)
        if isinstance(self._value[self._return_index], Node):
            return self._value[self._return_index].to_python()
        return self._value[self._return_index]

    def _construct(self, constructor: nip.constructor.Constructor):
        if self._return_index == -1:
            raise Exception("Iterator index was not specified by IterParser")
        if isinstance(self._value, list):
            return self._value[self._return_index]
        elif isinstance(self._value, Args):
            return self._value[self._return_index]._construct(constructor)
        else:
            raise nip.constructor.ConstructorError(self, (), {}, "Unexpected iter value type")

    def _dump(self, dumper: nip.dumper.Dumper):
        if self._return_index == -1:
            raise nip.dumper.DumpError("Dumping an iterator but index was not specified by IterParser")
        if isinstance(self._value, list):
            return str(self._value[self._return_index])
        elif isinstance(self._value, Args):
            return self._value[self._return_index]._dump(dumper)
        else:
            raise nip.dumper.DumpError("Unable to dump Iterable node: unexpected value type")


class InlinePython(Node):
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[InlinePython, None]:
        read_tokens = stream.peek(tokens.InlinePython)
        if read_tokens is None:
            return None
        stream.step()
        exec_string = read_tokens[0]._value
        return InlinePython(value=exec_string)

    def _construct(self, constructor: nip.constructor.Constructor):
        nsc.preload_vars(self._value, constructor)
        locals().update(constructor.vars)
        return eval(self._value)

    def _dump(self, dumper: nip.dumper.Dumper):
        return f"`{self._value}`"

    def to_python(self):
        return f"`{self._value}`"


class Nothing(Node):
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[Nothing, None]:
        if not stream:
            return Nothing()

        indent = stream.pos
        if stream.pos == 0 or (stream.lines[stream.n][: stream.pos].isspace() and indent <= parser.last_indent):
            return Nothing()

    def _construct(self, constructor: nip.constructor.Constructor):
        return self

    def _dump(self, dumper: nip.dumper.Dumper):
        return ""

    def to_python(self):
        return None


class FString(Node):  # Includes f-string and r-string
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[FString, None]:
        read_tokens = stream.peek(tokens.PythonString)
        if read_tokens is None:
            return None
        stream.step()
        string, t = read_tokens[0]._value
        if t == "r":
            print(
                "Warning: all strings in NIP are already python r-string. " "You don't have to explicitly specify it."
            )
        return FString(value=string)

    def _construct(self, constructor: nip.constructor.Constructor):
        nsc.preload_vars(f"f{self._value}", constructor)
        locals().update(constructor.vars)
        return eval(f"f{self._value}")

    def _dump(self, dumper: nip.dumper.Dumper):
        return f"f{self._value}"

    def to_python(self):
        return f"f{self._value}"


class Directive(Node):
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[FString, None]:
        read_tokens = stream.peek(tokens.Operator("!!"), tokens.Name)
        if read_tokens is None:
            return None
        name = read_tokens[1]._value
        stream.step()

        value = read_node(stream, parser)

        return nip.directives.call_directive(name, value, stream)


def read_node(stream: nip.stream.Stream, parser: nip.parser.Parser) -> Node:
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
