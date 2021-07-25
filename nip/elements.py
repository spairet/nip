"""Contains all the elements of nip config files"""
from __future__ import annotations

import nip.parser  # This import pattern because of cycle imports
import nip.dumper
import nip.constructor
import nip.stream
import nip.tokens as tokens

from abc import abstractmethod, ABC
from collections import OrderedDict
from typing import Any, Type, Union, Tuple


class Element(ABC):
    """Base token for nip file"""
    def __init__(self, name: str = '', value: Any = None):
        self.name = name
        self.value = value

    @classmethod
    @abstractmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[Element, None]:
        pass

    def __str__(self):
        return f"{self.__class__.__name__}('{self.name}', {self.value})"

    def __getitem__(self, item):
        return self.value[item]

    def to_python(self):
        return self.value.to_python()

    def construct(self, constructor: nip.constructor.Constructor):
        return self.value.construct(constructor)

    def dump(self, dumper: nip.dumper.Dumper):
        return self.value.dump(dumper)


class Document(Element):  # ToDo: add multi document support
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Document:
        doc_name = cls._read_name(stream)
        content = RightValue.read(stream, parser)
        return Document(doc_name, content)

    @classmethod
    def _read_name(cls, stream: nip.stream.Stream):
        read_tokens = stream.peek(tokens.Operator('---'), tokens.String) or \
                      stream.peek(tokens.Operator('---'))
        if read_tokens is not None:
            stream.step()
            if len(read_tokens) == 2:
                return read_tokens[1].value
        return ''

    def dump(self, dumper: nip.dumper.Dumper):
        return "--- " + self.value.dump(dumper)


class RightValue(Element):
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Element:
        value = LinkCreation.read(stream, parser) or \
                Link.read(stream, parser) or \
                Tag.read(stream, parser) or \
                Iter.read(stream, parser) or \
                Args.read(stream, parser) or \
                FString.read(stream, parser) or \
                Nothing.read(stream, parser) or \
                InlinePython.read(stream, parser) or \
                Value.read(stream, parser)

        if not value:
            raise nip.parser.ParserError(stream, "Wrong right value")

        return value


class Value(Element):
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[None, Value]:
        tokens_list = [
            tokens.Number,
            tokens.Bool,
            tokens.String,
            tokens.List,
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

    def construct(self, constructor: nip.constructor.Constructor):
        return self.value

    def dump(self, dumper: nip.dumper.Dumper):
        if isinstance(self.value, str):
            return f'"{self.value}"'
        return str(self.value)


class LinkCreation(Element):
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[Element, None]:
        read_tokens = stream.peek(tokens.Operator('&'), tokens.Name)
        if read_tokens is None:
            return None
        # if not isinstance(stream[1], tokens.Name):
        #     raise nip.parser.ParserError(stream, "Wrong var creation")  # mb: No good errors now =(

        name = read_tokens[1].value
        stream.step()

        value = RightValue.read(stream, parser)
        parser.links.append(name)

        return LinkCreation(name, value)

    def construct(self, constructor: nip.constructor.Constructor):
        constructor.vars[self.name] = self.value.construct(constructor)
        return constructor.vars[self.name]

    def dump(self, dumper: nip.dumper.Dumper):
        return f"&{self.name} {self.value.dump(dumper)}"


class Link(Element):
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[Element, None]:
        read_tokens = stream.peek(tokens.Operator('*'), tokens.Name)
        if read_tokens is None:
            return None

        name = read_tokens[1].value
        if name not in parser.links:
            nip.parser.ParserError(stream, "Link usage before assignment")
        stream.step()

        return Link(name)

    def to_python(self):
        return "nil"  # something that means that object is not constructed yet.

    def construct(self, constructor: nip.constructor.Constructor):
        return constructor.vars[self.name]

    def dump(self, dumper: nip.dumper.Dumper):
        return f"*{self.name}"


class Tag(Element):
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[Tag, None]:
        read_tokens = stream.peek(tokens.Operator('!'), tokens.Name)
        if read_tokens is None:
            return None
        name = read_tokens[1].value
        stream.step()

        value = RightValue.read(stream, parser)

        return Tag(name, value)

    def construct(self, constructor: nip.constructor.Constructor):
        if isinstance(self.value, Args):
            args, kwargs = self.value.construct(constructor, always_pair=True)
        else:
            value = self.value.construct(constructor)
            if value is Nothing:
                return constructor.builders[self.name]()
            else:
                args, kwargs = [value], {}
        try:
            return constructor.builders[self.name](*args, **kwargs)
        except Exception as e:
            raise nip.constructor.ConstructorError(self, args, kwargs, e)

    def dump(self, dumper: nip.dumper.Dumper):
        return f"!{self.name} " + self.value.dump(dumper)


class Args(Element):
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[Args, None]:
        start_indent = stream.pos
        if start_indent <= parser.last_indent:
            return None

        args = []
        kwargs = {}
        while stream and stream.pos == start_indent:
            parser.last_indent = start_indent

            item = cls._read_list_item(stream, parser)
            if item is not None:
                args.append(item)
                continue

            key, value = cls._read_dict_pair(stream, parser)
            if key is not None:
                kwargs[key] = value
                continue

            break

        if not args and not kwargs:
            return None
        return Args("args", (args, kwargs))


    @classmethod
    def _read_list_item(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) \
            -> Union[Element, None]:
        read_tokens = stream.peek(tokens.Operator('-'))
        if read_tokens is None:
            return None
        stream.step()

        value = RightValue.read(stream, parser)

        return value

    @classmethod
    def _read_dict_pair(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) \
            -> Union[Tuple[str, Element], Tuple[None, None]]:
        read_tokens = stream.peek(tokens.String, tokens.Operator(':'))
        if read_tokens is None:
            return None, None

        key = read_tokens[0].value
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

    def to_python(self):
        args = list(item.to_python() for item in self.value[0])
        kwargs = {key: value.to_python() for key, value in self.value[1].items()}
        assert args or kwargs, "Error converting Args node to python"  # This should never happen
        if args and kwargs:
            return args, kwargs
        return args or kwargs

    def construct(self, constructor: nip.constructor.Constructor, always_pair=False):
        args = list(item.construct(constructor) for item in self.value[0])
        kwargs = {key: value.construct(constructor) for key, value in self.value[1].items()}
        assert args or kwargs, "Error converting Args node to python"  # This should never happen
        if args and kwargs or always_pair:
            return args, kwargs
        return args or kwargs

    def dump(self, dumper: nip.dumper.Dumper):
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
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[Iter, None]:
        read_tokens = stream.peek(tokens.Operator('@'), tokens.Name, tokens.List) or \
                      stream.peek(tokens.Operator('@'), tokens.List)
        if read_tokens is None:
            return None
        stream.step()
        if len(read_tokens) == 2:
            iterator = Iter('', read_tokens[1].value)
        else:
            iterator = Iter(read_tokens[1].value, read_tokens[2].value)

        parser.iterators.append(iterator)
        return iterator

    def to_python(self):
        if self.return_index == -1:
            raise iter(self.value)
        return self.value[self.return_index]

    def construct(self, constructor: nip.constructor.Constructor):
        if self.return_index == -1:
            raise Exception("Iterator index was not specified by IterParser")
        return self.value[self.return_index]

    def dump(self, dumper: nip.dumper.Dumper):
        if self.return_index == -1:
            raise nip.dumper.DumpError(
                "Dumping an iterator but index was not specified by IterParser"
            )
        return str(self.value[self.return_index])


class InlinePython(Element):
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> \
            Union[InlinePython, None]:
        read_tokens = stream.peek(tokens.InlinePython)
        if read_tokens is None:
            return None
        stream.step()
        exec_string = read_tokens[0].value
        return InlinePython(value=exec_string)

    def construct(self, constructor: nip.constructor.Constructor):
        locals().update(constructor.vars)
        return eval(self.value)

    def dump(self, dumper: nip.dumper.Dumper):
        return f"`{self.value}`"


class Nothing(Element):
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[Nothing, None]:
        if not stream:
            return Nothing()
        if not stream.lines[stream.n][:stream.pos].isspace():
            return None
        indent = stream.pos
        # pos, indent = tokens.Indent.read(stream)
        # if indent is None:  # mb this should be specifically processed
        #     return None
        if indent <= parser.last_indent:
            return Nothing()

    def construct(self, constructor: nip.constructor.Constructor):
        return Nothing

    def dump(self, dumper: nip.dumper.Dumper):
        return ""

    def to_python(self):
        return None


class FString(Element):  # Includes f-string and r-string
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> \
            Union[FString, None]:
        read_tokens = stream.peek(tokens.PythonString)
        if read_tokens is None:
            return None
        stream.step()
        string, t = read_tokens[0].value
        if t == 'r':
            print("Warning: all strings in NIP are already python r-string. "
                  "You don't have to explicitly specify it.")
        return FString(value=string)

    def construct(self, constructor: nip.constructor.Constructor):
        locals().update(constructor.vars)
        return eval(f"f{self.value}")

    def dump(self, dumper: nip.dumper.Dumper):
        return f"f{self.value}"

    def to_python(self):
        return f"f{self.value}"
