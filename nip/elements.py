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
        # possible document starts: "--- {name} {!tag}"
        pos, operator = tokens.Operator.read(stream)
        if pos > 0 and operator == '---':
            stream.move(pos)
        else:
            return None

        pos, indent = tokens.Indent.read(stream)
        if indent is not None:  # new string means start of right value
            return None

        pos, doc_name = tokens.Name.read(stream)
        if not pos:
            return None
        stream.move(pos)
        return doc_name

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
                Value.read(stream, parser) or \
                InlinePython.read(stream, parser) or \
                Nothing.read(stream, parser)

        if not value:
            raise nip.parser.ParserError(stream, "Wrong right value")

        return value


class Value(Element):
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Value:
        return cls._read_token(tokens.Number, stream) or \
               cls._read_token(tokens.Bool, stream) or \
               cls._read_token(tokens.String, stream) or \
               cls._read_token(tokens.List, stream) or \
               cls._read_token(tokens.Dict, stream)

    @staticmethod
    def _read_token(cls: Type[tokens.Token], stream: nip.stream.Stream) -> Union[Value, None]:
        pos, value = cls.read(stream)
        if pos > 0:
            stream.move(pos)
            return Value(cls.__name__, value)

        return None

    def to_python(self):
        return self.value

    def construct(self, constructor: nip.constructor.Constructor, always_pair=False):
        if always_pair:
            return [self.value], {}
        return self.value

    def dump(self, dumper: nip.dumper.Dumper):
        if isinstance(self.value, str):
            return f'"{self.value}"'
        return str(self.value)


class LinkCreation(Element):
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[Element, None]:
        pos, op = tokens.Operator.read(stream)
        if pos > 0 and op == '&':
            stream.move(pos)
        else:
            return None

        pos, name = tokens.Name.read(stream)
        if not pos:
            raise nip.parser.ParserError(stream, "Wrong link creation")
        stream.move(pos)

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
        pos, op = tokens.Operator.read(stream)
        if pos > 0 and (op == '*'):
            stream.move(pos)
        else:
            return None

        pos, name = tokens.Name.read(stream)
        if not pos:
            raise nip.parser.ParserError(stream, "Wrong link usage")
        if name not in parser.links:
            nip.parser.ParserError(stream, "Link usage before assignment")
        stream.move(pos)

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
        pos, op = tokens.Operator.read(stream)
        if pos > 0 and op == '!':
            stream.move(pos)
        else:
            return None

        pos, name = tokens.Name.read(stream)
        if not pos:
            raise nip.parser.ParserError(stream, "Wrong tag creation")
        stream.move(pos)

        value = RightValue.read(stream, parser)
        #assert isinstance(value, (Args, Value)), "Tag should be created with List or Dict or Args"

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
        pos, indent = tokens.Indent.read(stream)
        if indent is None or indent <= stream.last_indent:
            return None

        args: list = cls._read_list(stream, parser, indent)
        stream.pos = 0
        kwargs: dict = cls._read_dict(stream, parser, indent)

        if not args and not kwargs:
            raise nip.parser.ParserError(stream, "Error reading indented element")
        return Args("args", (args, kwargs))

    @classmethod
    def _read_list(cls, stream: nip.stream.Stream, parser: nip.parser.Parser,
                   start_indent: int) -> list:
        pos, indent = tokens.Indent.read(stream)
        current_list = []
        while stream and indent == start_indent:
            stream.move(pos)
            stream.last_indent = indent
            item = cls._read_list_item(stream, parser)
            if not item:
                break
            current_list.append(item)

            if not stream:
                break

            pos, indent = tokens.Indent.read(stream)

        return current_list

    @classmethod
    def _read_list_item(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) \
            -> Union[Element, None]:
        pos, op = tokens.Operator.read(stream)
        if not pos or op != '-':
            return None
        stream.move(pos)

        value = RightValue.read(stream, parser)

        return value

    @classmethod
    def _read_dict(cls, stream: nip.stream.Stream, parser: nip.parser.Parser,
                   start_indent: int) -> dict:
        pos, indent = tokens.Indent.read(stream)

        current_dict = OrderedDict()
        while stream and indent == start_indent:
            stream.move(pos)
            stream.last_indent = indent
            key, value = cls._read_dict_pair(stream, parser)
            if not key:
                break
            current_dict[key] = value

            if not stream:
                break

            pos, indent = tokens.Indent.read(stream)

        return current_dict

    @classmethod
    def _read_dict_pair(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) \
            -> Union[Tuple[str, Element], Tuple[None, None]]:
        pos, key = tokens.Name.read(stream)
        if not pos:
            return None, None
        stream.move(pos)

        pos, op = tokens.Operator.read(stream)
        if not pos or op != ':':
            raise nip.parser.ParserError(stream, "Wrong dict pair assertion")
        stream.move(pos)

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

        dumped_kwargs = '\n'.join([
            " "*dumper.indent + f"{key}: {value.dump(dumper + dumper.default_shift)}"
            for key, value in self.value[1].items()
        ])

        return '\n' + dumped_args + dumped_kwargs


class Iter(Element):
    def __init__(self, name: str = '', value: Any = None):
        super(Iter, self).__init__(name, value)
        self.return_index = -1
        # mb: name all the iterators and get the value from constructor rather then use this index

    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[Iter, None]:
        pos, op = tokens.Operator.read(stream)
        if pos > 0 and (op == '@'):
            stream.move(pos)
        else:
            return None

        pos, name = tokens.Name.read(stream)
        stream.move(pos)
        # mb: read full RightValue here? what with nested cases?
        pos, iter_list = tokens.List.read(stream)  # mb: or tuple
        if not pos:
            nip.parser.ParserError(stream, "Wrong iter creation")
        stream.move(pos)
        iterator = Iter(name, iter_list)
        parser.iterators.append(iterator)
        return iterator

    def to_python(self):
        if self.return_index == -1:
            raise iter(self.value)
        return self.value[self.return_index]

    def construct(self, constructor: nip.constructor.Constructor):
        if self.return_index == -1:
            raise nip.constructor.ConstructorError("Iterator index was not specified by IterParser")
        return self.value[self.return_index]

    def dump(self, dumper: nip.dumper.Dumper):
        if self.return_index == -1:
            raise nip.dumper.DumpError(
                "Dumping an iterator but index was not specified by IterParser"
            )
        return str(self.value[self.return_index])


class InlinePython(Element):
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[InlinePython, None]:
        pos, exec_string = tokens.InlinePython.read(stream)
        if pos > 0:
            stream.move(pos)
            return InlinePython(value=exec_string)
        else:
            return None

    def construct(self, constructor: nip.constructor.Constructor):
        locals().update(constructor.vars)
        return eval(self.value)

    def dump(self, dumper: nip.dumper.Dumper):
        return f"`{self.value}`"


class Nothing(Element):
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[Nothing, None]:
        pos, indent = tokens.Indent.read(stream)
        if indent is None:
            return None
        if indent <= stream.last_indent:
            return Nothing()

    def construct(self, constructor: nip.constructor.Constructor):
        return Nothing

    def dump(self, dumper: nip.dumper.Dumper):
        return ""


class FString(Element):  # Includes f-string and r-string
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> \
            Union[FString, None]:
        pos, string, t = tokens.PythonString.read(stream)
        if t == 'r':
            print("Warning: all strings in NIP are already python r-string. "
                  "You don't have to explicitly specify it.")
        if pos > 0:
            stream.move(pos)
            return FString(value=string)
        return None

    def construct(self, constructor: nip.constructor.Constructor):
        locals().update(constructor.vars)
        string: str = self.value
        for name, value in constructor.vars.items():
            string = string.replace(f'{{{name}}}', str(value))
        return string[1:-1]  # because we store quotes as well

    def dump(self, dumper: nip.dumper.Dumper):
        return f"f{self.value}"

    def to_python(self):
        return f"f{self.value}"