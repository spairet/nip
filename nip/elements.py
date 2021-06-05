"""Contains all the elements of nip config files"""
from __future__ import annotations

import nip.parser  # This import pattern because of cycle imports
import nip.dumper
import nip.constructor
import nip.stream
import nip.tokens as tokens

from abc import abstractmethod, ABC
from typing import Any, Type, Union


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


class DictPair(Element):
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[DictPair, None]:
        pos, key = tokens.Name.read(stream)
        if not pos:
            return None
        stream.move(pos)

        pos, op = tokens.Operator.read(stream)
        if not pos or op != ':':
            raise nip.parser.ParserError(stream, "Wrong dict pair assertion")
        stream.move(pos)

        value = RightValue.read(stream, parser)

        return DictPair(key, value)

    def dump(self, dumper: nip.dumper.Dumper):
        return " "*dumper.indent + \
               self.name + ': ' + \
               self.value.dump(dumper + dumper.default_shift)


class Dict(Element):
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[Dict, None]:
        pos, indent = tokens.Indent.read(stream)
        if indent is None:
            return None
        start_indent = indent

        current_dict = []
        while stream and indent == start_indent:
            stream.move(pos)
            pair = DictPair.read(stream, parser)
            if not pair:
                break
            current_dict.append(pair)

            if not stream:
                break

            pos, indent = tokens.Indent.read(stream)
            if stream and indent is None:
                raise nip.parser.ParserError(stream, "Unexpected dict value")
            if stream and indent > start_indent:
                raise nip.parser.ParserError(stream, "Error reading dict indent")

        if len(current_dict) == 0:  # Unable to read dict pair
            stream.pos = 0
            return None

        return Dict('name', current_dict)

    def __str__(self):
        values_string = "[" + ", ".join([str(item) for item in self.value]) + "]"
        return f"{self.__class__.__name__}('{self.name}', {values_string})"

    def __bool__(self):
        return bool(self.value)

    def __getitem__(self, item):
        for pair in self.value:
            if item == pair.name:
                return pair.value
        raise KeyError(f"Undefined key '{item}'")

    def to_python(self):
        return {
            pair.name: pair.value.to_python()
            for pair in self.value
        }

    def construct(self, constructor: nip.constructor.Constructor):
        return {
            pair.name: pair.value.construct(constructor)
            for pair in self.value
        }

    def dump(self, dumper: nip.dumper.Dumper):
        string = ""
        for pair in self.value:
            string += "\n" + pair.dump(dumper)
        return string


class ListItem(Element):
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[ListItem, None]:
        pos, op = tokens.Operator.read(stream)
        if not pos or op != '-':
            return None
        stream.move(pos)

        value = RightValue.read(stream, parser)

        return ListItem('ListItem', value=value)

    def dump(self, dumper: nip.dumper.Dumper):
        return " "*dumper.indent + '- ' + self.value.dump(dumper + dumper.default_shift)


class List(Element):
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[List, None]:
        pos, indent = tokens.Indent.read(stream)
        if indent is None:
            return None
        start_indent = indent
        current_list = []
        while stream and indent == start_indent:
            stream.move(pos)
            item = ListItem.read(stream, parser)
            if not item:
                break
            current_list.append(item)

            if not stream:
                break

            pos, indent = tokens.Indent.read(stream)
            if stream and indent is None:
                raise nip.parser.ParserError(stream, "Unexpected list value")
            if stream and indent > start_indent:
                raise nip.parser.ParserError(stream, "Error reading list indent")

        if len(current_list) == 0:  # Unable to read list item
            stream.pos = 0
            return None

        return List('name', current_list)

    def __str__(self):
        values_string = "[" + ", ".join([str(item) for item in self.value]) + "]"
        return f"{self.__class__.__name__}('{self.name}', {values_string})"

    def __bool__(self):
        return bool(self.value)

    def to_python(self):
        return [item.to_python() for item in self.value]

    def construct(self, constructor: nip.constructor.Constructor):
        return [item.construct(constructor) for item in self.value]

    def dump(self, dumper: nip.dumper.Dumper):
        string = ""
        for item in self.value:
            string += "\n" + item.dump(dumper)
        return string


class RightValue(Element):
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Element:
        value = LinkCreation.read(stream, parser) or \
                Link.read(stream, parser) or \
                Tag.read(stream, parser) or \
                Iter.read(stream, parser) or \
                Dict.read(stream, parser) or \
                List.read(stream, parser) or \
                Value.read(stream, parser)

        if not value:
            raise nip.parser.ParserError(stream, "Wrong right value")

        return value


class Value(Element):
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Value:
        return cls._read_token(tokens.Number, stream) or \
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

    def construct(self, constructor: nip.constructor.Constructor):
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
        parser.links[name] = value

        return value


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

        return parser.links[name]

    # mb: construct the same object for every link? optionally?


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
        parser.tags[name] = value
        return Tag(name, value)

    def construct(self, constructor: nip.constructor.Constructor):
        args = self.value.construct(constructor)  # ToDo: dict or list as well?
        return constructor.builders[self.name](**args)

    def dump(self, dumper: nip.dumper.Dumper):
        return f"!{self.name} " + self.value.dump(dumper)


class Args(Element):  # ToDo: Append to lib
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Args:
        args = List.read(stream, parser)
        kwargs = Dict.read(stream, parser)
        return Args("args", (args, kwargs))

    def __str__(self):
        values_string = "[" + ", ".join([str(item) for item in self.value]) + "]"
        return f"{self.__class__.__name__}('{self.name}', {values_string})"

    def __bool__(self):
        return bool(self.value[0]) or bool(self.value[1])

    def __getitem__(self, item):
        try:
            return self.value[0][item]
        except KeyError:
            return self.value[1][item]

    def to_python(self):
        return self.value[0].to_python(), self.value[1].to_python()

    def construct(self, constructor: nip.constructor.Constructor):
        return self.value[0].construt(constructor), self.value[1].construct(constructor)


class Iter(Element):
    def __init__(self, name: str = '', value: Any = None):
        super(Iter, self).__init__(name, value)
        self.return_index = -1
        # mb: name all the iterators and get the value from constructor rather then use this index

    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[Iter, None]:
        pos, op = tokens.Operator.read(stream)
        if pos > 0 and (op == '@'):  # mb: other operator? mb: read full RightValue here?
            stream.move(pos)
        else:
            return None

        pos, name = tokens.Name.read(stream)
        stream.move(pos)
        pos, iter_list = tokens.List.read(stream)  # Mb: or tuple
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
