from abc import abstractmethod, ABC

from .stream import Stream
from typing import Tuple, Any, Union


class Token(ABC):
    """Abstract of token reader"""
    def __init__(self, value):
        self.value = value

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
        is_float = False
        pos = 0
        while stream[pos].isnumeric() or stream[pos] == '.':
            if stream[pos] == '.':
                if is_float:
                    raise TokenError(stream, "Wrong number expression")
                is_float = True
            pos += 1
        if pos == 0:
            return 0, 0
        if is_float:
            return pos, float(stream[:pos])
        return pos, int(stream[:pos])


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

        if stream[pos] not in Operator.symbols and not stream[pos].isspace():
            string = stream[pos:]
            return len(string), string
        return 0, ""


class Name(Token):
    @staticmethod
    def read(stream: Stream) -> Tuple[int, str]:
        pos = 0
        if not stream[pos].isalpha():
            return 0, ''

        while stream[pos].isalnum() or stream[pos] == '_':
            pos += 1

        return pos, stream[:pos]


class Operator(Token):
    symbols = "@#&!-:*[]{}"

    @staticmethod
    def read(stream: Stream) -> Tuple[int, str]:
        pos = 0
        while stream[pos] and stream[pos] in Operator.symbols:
            pos += 1

        return pos, stream[:pos]


class Indent(Token):  # ToDo: not needed now?
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
