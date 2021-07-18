from abc import abstractmethod, ABC
import nip.parser as parser

from .stream import Stream
from typing import Tuple, Any, Union


# mb: tokens takes parser
class Token(ABC):
    """Abstract of token reader"""
    @staticmethod
    @abstractmethod
    def read(stream: Stream) -> Tuple[int, Any]:
        pass


class TokenError(Exception):
    def __init__(self, stream: Stream, msg: str):
        self.line = stream.n
        self.pos = stream.pos
        self.msg = msg

    def __str__(self):
        return f"{self.line}:{self.pos}: {self.msg}"


class Number(Token):
    @staticmethod
    def read(stream: Stream) -> Tuple[int, Union[int, float]]:
        string = stream[:].strip()
        value = None
        for t in (int, float):
            try:
                value = t(string)
                break
            except:
                pass
        if value is not None:
            return len(string), value
        else:
            return 0, 0


class Bool(Token):
    @staticmethod
    def read(stream: Stream) -> Tuple[int, bool]:
        string = stream[:].strip()
        if string in ['true', 'True', 'yes']:
            return len(string), True
        if string in ["false", 'False', 'no']:
            return len(string), False
        return 0, False


# class NoneType(Token):
#     @staticmethod
#     def read(stream: Stream) -> Tuple[int, Any]:
#         string = stream[:strip]

class String(Token):
    @staticmethod
    def read(stream: Stream) -> Tuple[int, str]:
        pos = 0
        if stream[pos] in "\'\"":
            start_char = stream[pos]
            pos += 1
            while stream[pos] and stream[pos] != start_char:
                pos += 1
            if stream[pos] != start_char:
                raise TokenError(stream, "Not closed string expression")
            pos += 1
            return pos, stream[1:pos - 1]

        if stream[pos].isspace() or stream[pos] in Operator.symbols:
            return 0, ""

        while stream[pos] and stream[pos] != '#':
            pos += 1

        return pos, stream[:pos]


class Name(Token):
    @staticmethod
    def read(stream: Stream) -> Tuple[int, str]:
        pos = 0
        if not stream[pos].isalpha():
            return 0, ''

        while stream[pos].isalnum() or stream[pos] == '_' or \
                stream[pos] == '.':
            pos += 1

        return pos, stream[:pos]


class Operator(Token):
    symbols = "@#&!-:*[]{}`"

    @staticmethod
    def read(stream: Stream) -> Tuple[int, str]:
        pos = 0
        while stream[pos] and stream[pos] in Operator.symbols:
            pos += 1

        return pos, stream[:pos]


class Indent(Token):
    @staticmethod
    def read(stream: Stream) -> Tuple[int, Union[int, None]]:
        if not stream or stream.pos != 0:
            return 0, None
        indent = 0
        pos = 0
        while stream[pos].isspace():
            if stream[pos] == ' ':
                indent += 1
            elif stream[pos] == '\t':
                indent += 4
            else:
                raise TokenError(stream, "Unknown indent symbol")
            pos += 1

        return pos, indent


class List(Token):
    @staticmethod
    def read(stream: Stream) -> Tuple[int, list]:
        pos = 0
        if stream[pos] != '[':
            return pos, []
        while stream and stream[pos] != ']':
            pos += 1
        if stream[pos] != ']':
            raise TokenError(stream, 'List was not closed')
        pos += 1
        read_list = eval(stream[:pos])
        return pos, read_list


class Dict(Token):
    @staticmethod
    def read(stream: Stream) -> Tuple[int, list]:
        pos = 0
        if stream[pos] != '{':
            return pos, []
        while stream and stream[pos] != '}':
            pos += 1
        if stream[pos] != '}':
            raise TokenError(stream, 'Dict was not closed')
        pos += 1
        read_dict = eval(stream[:pos])
        return pos, read_dict


class InlinePython(Token):
    @staticmethod
    def read(stream: Stream) -> Tuple[int, Any]:
        pos = 0
        if stream[pos] != '`':
            return pos, []
        pos += 1
        while stream and stream[pos] != '`':
            pos += 1
        if stream[pos] != '`':
            raise TokenError(stream, 'Inline python string was not clothed')
        pos += 1
        return pos, stream[1:pos - 1]


class PythonString(Token):
    @classmethod
    def read(cls, stream: Stream) -> Tuple[int, str, str]:
        string = stream[:].strip()
        if string[0] == 'f' and string[1] in "\"\'":
            if string[-1] != string[1]:
                raise TokenError(stream, "Not closed f-string")
            return len(string), string[1:], 'f'
        if string[0] == 'r' and string[1] in "\"\'":
            if string[-1] != string[1]:
                raise TokenError(stream, "Not closed r-string")
            return len(string), string[1:], 'r'
        return 0, "", ''
