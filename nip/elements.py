"""Contains all the elements of nip config files"""
# from __future__ import annotations

import logging

from .stream import Stream
from .constructor import Constructor, ConstructorError, check_typing
from .convertor import Convertor
from .directives import call_directive
from .dumper import Dumper, DumpError
from .non_seq_constructor import preload_vars
from .parser import Parser, ParserError
from . import tokens
from .utils import flatten, iterate_items


from abc import abstractmethod, ABC
from typing import Any, Union, Tuple, Dict

_LOGGER = logging.getLogger(__name__)


class Element(ABC):
    """Base token for nip file"""
    def __init__(self, name: str = '', value: Any = None):
        self.name = name
        self.value = value

    @classmethod
    @abstractmethod
    def read(cls, stream: Stream, parser: "Parser") -> Union["Element", None]:
        pass

    def __str__(self):
        return f"{self.__class__.__name__}('{self.name}', {self.value})"

    def __getitem__(self, item):
        return self.value[item]

    def __setitem__(self, key, value):
        self.value[key] = value

    def to_python(self):
        return self.value.to_python()

    def construct(self, constructor: Constructor):
        return self.value.construct(constructor)

    def dump(self, dumper: Dumper):
        return self.value.dump(dumper)

    def __eq__(self, other):
        return self.name == other.name and self.value == other.value

    def flatten(self, delimiter='.') -> Dict:
        return flatten(self.to_python(), delimiter)


class Document(Element):  # ToDo: add multi document support
    @classmethod
    def read(cls, stream: Stream, parser: "Parser") -> "Document":
        doc_name = cls._read_name(stream)
        content = RightValue.read(stream, parser)
        return Document(doc_name, content)

    @classmethod
    def _read_name(cls, stream: Stream):
        read_tokens = stream.peek(tokens.Operator('---'), tokens.Name) or \
                      stream.peek(tokens.Operator('---'))
        if read_tokens is not None:
            stream.step()
            if len(read_tokens) == 2:
                return read_tokens[1].value
        return ''

    def dump(self, dumper: Dumper):
        string = "---"
        if self.name:
            string += " " + self.name + " "
        return string + self.value.dump(dumper)


class RightValue(Element):
    @classmethod
    def read(cls, stream: Stream, parser: "Parser") -> Element:
        value = Directive.read(stream, parser) or \
                LinkCreation.read(stream, parser) or \
                Link.read(stream, parser) or \
                Class.read(stream, parser) or \
                Tag.read(stream, parser) or \
                Iter.read(stream, parser) or \
                Args.read(stream, parser) or \
                FString.read(stream, parser) or \
                Nothing.read(stream, parser) or \
                InlinePython.read(stream, parser) or \
                Value.read(stream, parser)

        if value is None:
            raise ParserError(stream, "Wrong right value")

        return value


class Value(Element):
    @classmethod
    def read(cls, stream: Stream, parser: "Parser") -> Union[None, "Value"]:
        tokens_list = [
            tokens.Number,
            tokens.Bool,
            tokens.String,
            tokens.List,
            tokens.TupleToken,
            tokens.Dict
        ]
        for token in tokens_list:
            read_tokens = stream.peek(token)
            if read_tokens is not None:
                stream.step()
                return Value(read_tokens[0].name, read_tokens[0].value)

        return None

    def to_python(self):
        return self.value

    def construct(self, constructor: Constructor):
        return self.value

    def dump(self, dumper: Dumper):
        if isinstance(self.value, str):
            return f'"{self.value}"'
        return str(self.value)

    def __len__(self):
        return len(self.value)


class LinkCreation(Element):
    @classmethod
    def read(cls, stream: Stream, parser: "Parser") -> Union[Element, None]:
        read_tokens = stream.peek(tokens.Operator('&'), tokens.Name)
        if read_tokens is None:
            # if stream.peek(tokens.Operator('&')):  # mb: do it more certainly: peak operator
            #     raise "Parser"Error(      # mb: firstly and then choose class to read)
            #         stream, "Found variable creation operator '&' but name is not specified")
            return None

        name = read_tokens[1].value
        stream.step()

        value = RightValue.read(stream, parser)
        if name in parser.link_names:
            raise ParserError(stream, f"Redefining of link '{name}'")
        parser.link_names.append(name)

        return LinkCreation(name, value)

    def construct(self, constructor: Constructor):
        constructor.vars[self.name] = self.value.construct(constructor)
        return constructor.vars[self.name]

    def dump(self, dumper: Dumper):
        return f"&{self.name} {self.value.dump(dumper)}"


class Link(Element):
    @classmethod
    def read(cls, stream: Stream, parser: "Parser") -> Union[Element, None]:
        read_tokens = stream.peek(tokens.Operator('*'), tokens.Name)
        if read_tokens is None:
            return None

        name = read_tokens[1].value
        stream.step()

        if name in parser.link_replacements:
            return parser.link_replacements[name]

        if parser.sequential_links and name not in parser.link_names:
            ParserError(stream, "Link usage before assignment")

        return Link(name)

    def to_python(self):
        return "nil"  # something that means that object is not constructed yet.

    def construct(self, constructor: Constructor):
        return constructor.vars[self.name]

    def dump(self, dumper: Dumper):
        return f"*{self.name}"


class Tag(Element):
    @classmethod
    def read(cls, stream: Stream, parser: "Parser") -> Union["Tag", None]:
        read_tokens = stream.peek(tokens.Operator('!'), tokens.Name)
        if read_tokens is None:
            return None
        name = read_tokens[1].value
        stream.step()

        value = RightValue.read(stream, parser)

        return Tag(name, value)

    def construct(self, constructor: Constructor):
        if isinstance(self.value, Args):
            args, kwargs = self.value.construct(constructor, always_pair=True)
        else:
            value = self.value.construct(constructor)
            if isinstance(value,  Nothing):  # mb: Add IS_NOTHING method
                return constructor.builders[self.name]()
            else:
                args, kwargs = [value], {}

        if self.name not in constructor.builders:
            raise ConstructorError(
                self, args, kwargs, f"Constructor for Tag '{self.name}' is not registered.")

        messages = check_typing(constructor.builders[self.name], args, kwargs)
        if len(messages) > 0:
            if constructor.strict_typing:
                raise ConstructorError(self, args, kwargs, "\n".join(messages))
            else:
                _LOGGER.warning(f"Typing mismatch while constructing {self.name}:\n" +
                                "\n".join(messages))

        try:  # Try to construct
            return constructor.builders[self.name](*args, **kwargs)
        except Exception as e:
            raise ConstructorError(self, args, kwargs, e)

    def dump(self, dumper: Dumper):
        return f"!{self.name} " + self.value.dump(dumper)


class Class(Element):
    @classmethod
    def read(cls, stream: Stream, parser: "Parser") -> Union["Class", None]:
        read_tokens = stream.peek(tokens.Operator('!&'), tokens.Name)
        if read_tokens is None:
            return None
        name = read_tokens[1].value
        stream.step()

        value = RightValue.read(stream, parser)
        if not isinstance(value, Nothing):
            raise ParserError(stream, "Class should be created with nothing to the right.")

        return Class(name, value)

    def construct(self, constructor: Constructor):
        value = self.value.construct(constructor)
        assert isinstance(value, Nothing), "Unexpected right value while constructing Class"

        return constructor.builders[self.name]

    def dump(self, dumper: Dumper):
        return f"!&{self.name} " + self.value.dump(dumper)


class Args(Element):
    @classmethod
    def read(cls, stream: Stream, parser: "Parser") -> Union["Args", None]:
        start_indent = stream.pos
        if start_indent <= parser.last_indent:
            return None

        args = []
        kwargs = {}  # mb: just dict with integer and string keys
        read_kwarg = False
        while stream and stream.pos == start_indent:
            parser.last_indent = start_indent

            item = cls._read_list_item(stream, parser)
            if item is not None:
                if parser.strict and read_kwarg:
                    raise ParserError(stream,
                                                 "Positional argument after keyword argument "
                                                 "is forbiddent in `strict` mode.")
                args.append(item)
                continue

            key, value = cls._read_dict_pair(stream, parser, kwargs.keys())
            if key is not None:
                read_kwarg = True
                kwargs[key] = value
                continue

            break

        if stream.pos > start_indent:
            raise ParserError(stream, "Unexpected indent")

        if not args and not kwargs:
            return None
        return Args("args", (args, kwargs))

    @classmethod
    def _read_list_item(cls, stream: Stream, parser: "Parser") \
            -> Union[Element, None]:
        read_tokens = stream.peek(tokens.Operator('- '))
        if read_tokens is None:
            return None
        stream.step()

        value = RightValue.read(stream, parser)

        return value

    @classmethod
    def _read_dict_pair(cls, stream: Stream, parser: "Parser", kwargs_keys) \
            -> Union[Tuple[str, Element], Tuple[None, None]]:
        # mb: read String instead of Name for keys with spaces,
        # mb: but this leads to the case that
        read_tokens = stream.peek(tokens.Name, tokens.Operator(': '))
        if read_tokens is None:
            return None, None

        key = read_tokens[0].value
        if parser.strict and key in kwargs_keys:
            raise ParserError(stream,
                                         f"Dict key overwriting is forbidden in `strict` "
                                         f"mode. Overwritten key: '{key}'.")
        stream.step()

        value = RightValue.read(stream, parser)

        return key, value

    def __str__(self):
        args_repr = "[" + ", ".join([str(item) for item in self.value[0]]) + "]"
        kwargs_repr = \
            "{" + ", ".join([f"{key}: {str(value)}" for key, value in self.value[1].items()]) + "}"

        return f"{self.__class__.__name__}('{self.name}', {args_repr}, {kwargs_repr})"

    def __bool__(self):
        return bool(self.value[0]) or bool(self.value[1])

    def __getitem__(self, item):
        try:
            return self.value[0][item]
        except TypeError:
            return self.value[1][item]

    def __setitem__(self, key, value):
        convertor = Convertor()
        if isinstance(key, int):
            self.value[0][key] = convertor.convert(value)
        else:
            self.value[1][key] = convertor.convert(value)

    def append(self, value):
        convertor = Convertor()
        self.value[0].append(convertor.convert(value))

    def __len__(self):
        return len(self.value[0]) + len(self.value[1])

    def __iter__(self):
        for item in self.value[0]:
            yield item
        for key, item in self.value[1].items():
            yield item

    def to_python(self):
        args = list(item.to_python() for item in self.value[0])
        kwargs = {key: value.to_python() for key, value in self.value[1].items()}
        assert args or kwargs, "Error converting Args node to python"  # This should never happen
        if args and kwargs:
            result = {}
            result.update(iterate_items(args))
            result.update(iterate_items(kwargs))
            return result
        return args or kwargs

    def construct(self, constructor: Constructor, always_pair=False):
        args = list(item.construct(constructor) for item in self.value[0])
        kwargs = {key: value.construct(constructor) for key, value in self.value[1].items()}
        assert args or kwargs, "Error converting Args node to python"  # This should never happen
        if args and kwargs or always_pair:
            return args, kwargs
        return args or kwargs

    def dump(self, dumper: Dumper):
        dumped_args = '\n'.join([
            " "*dumper.indent + f"- {item.dump(dumper + dumper.default_shift)}"
            for item in self.value[0]
        ])
        string = ('\n' if dumped_args else '') + dumped_args

        dumped_kwargs = '\n'.join([
            " "*dumper.indent + f"{key}: {value.dump(dumper + dumper.default_shift)}"
            for key, value in self.value[1].items()
        ])
        string += ('\n' if dumped_kwargs else '') + dumped_kwargs

        return string


class Iter(Element):
    def __init__(self, name: str = '', value: Any = None):
        super(Iter, self).__init__(name, value)
        self.return_index = -1
        # mb: name all the iterators and get the value from constructor rather then use this index

    @classmethod
    def read(cls, stream: Stream, parser: "Parser") -> Union["Iter", None]:
        read_tokens = stream.peek(tokens.Operator('@'), tokens.Name) or \
                      stream.peek(tokens.Operator('@'))
        if read_tokens is None:
            return None
        stream.step()
        value = RightValue.read(stream, parser)
        if isinstance(value, Value) and isinstance(value.value, list):
            value = value.value
        elif isinstance(value, Args) and len(value.value[1]) == 0:
            value = value
        else:
            raise ParserError(stream, "List is expected as a value for Iterable node")
        if len(read_tokens) == 1:
            iterator = Iter('', value)
        else:
            iterator = Iter(read_tokens[1].value, value)

        parser.iterators.append(iterator)
        return iterator

    def to_python(self):
        if self.return_index == -1:
            raise iter(self.value)
        if isinstance(self.value[self.return_index], Element):
            return self.value[self.return_index].to_python()
        return self.value[self.return_index]

    def construct(self, constructor: Constructor):
        if self.return_index == -1:
            raise Exception("Iterator index was not specified by IterParser")
        if isinstance(self.value, list):
            return self.value[self.return_index]
        elif isinstance(self.value, Args):
            return self.value[self.return_index].construct(constructor)
        else:
            raise ConstructorError(self, (), {}, "Unexpected iter value type")

    def dump(self, dumper: Dumper):
        if self.return_index == -1:
            raise DumpError(
                "Dumping an iterator but index was not specified by IterParser"
            )
        if isinstance(self.value, list):
            return str(self.value[self.return_index])
        elif isinstance(self.value, Args):
            return self.value[self.return_index].dump(dumper)
        else:
            raise DumpError("Unable to dump Iterable node: unexpected value type")


class InlinePython(Element):
    @classmethod
    def read(cls, stream: Stream, parser: "Parser") -> \
            Union["InlinePython", None]:
        read_tokens = stream.peek(tokens.InlinePython)
        if read_tokens is None:
            return None
        stream.step()
        exec_string = read_tokens[0].value
        return InlinePython(value=exec_string)

    def construct(self, constructor: Constructor):
        preload_vars(self.value, constructor)
        locals().update(constructor.vars)
        return eval(self.value)

    def dump(self, dumper: Dumper):
        return f"`{self.value}`"

    def to_python(self):
        return f"`{self.value}`"


class Nothing(Element):
    @classmethod
    def read(cls, stream: Stream, parser: "Parser") -> Union["Nothing", None]:
        if not stream:
            return Nothing()

        indent = stream.pos
        if stream.pos == 0 or (
                stream.lines[stream.n][:stream.pos].isspace()
                and indent <= parser.last_indent):
            return Nothing()

    def construct(self, constructor: Constructor):
        return self

    def dump(self, dumper: Dumper):
        return ""

    def to_python(self):
        return None


class FString(Element):  # Includes f-string and r-string
    @classmethod
    def read(cls, stream: Stream, parser: "Parser") -> \
            Union["FString", None]:
        read_tokens = stream.peek(tokens.PythonString)
        if read_tokens is None:
            return None
        stream.step()
        string, t = read_tokens[0].value
        if t == 'r':
            print("Warning: all strings in NIP are already python r-string. "
                  "You don't have to explicitly specify it.")
        return FString(value=string)

    def construct(self, constructor: Constructor):
        preload_vars(f"f{self.value}", constructor)
        locals().update(constructor.vars)
        return eval(f"f{self.value}")

    def dump(self, dumper: Dumper):
        return f"f{self.value}"

    def to_python(self):
        return f"f{self.value}"


class Directive(Element):
    @classmethod
    def read(cls, stream: Stream, parser: "Parser") -> \
            Union["FString", None]:
        read_tokens = stream.peek(tokens.Operator('!!'), tokens.Name)
        if read_tokens is None:
            return None
        name = read_tokens[1].value
        stream.step()

        value = RightValue.read(stream, parser)

        return call_directive(name, value, stream)
