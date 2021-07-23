from __future__ import annotations

from abc import abstractmethod, ABC
from typing import Tuple, Any, Union

import nip.parser as parser


class Token(ABC):
    """Abstract of token reader"""
    def __init__(self, value: Any = None):
        self.value = value
        
    @staticmethod
    @abstractmethod
    def read(stream: str) -> Tuple[int, Any]:
        pass


class TokenError(Exception):
    def __init__(self, msg: str):
        self.msg = msg

    def __str__(self):
        return f"{self.msg}"


class Number(Token):
    @staticmethod
    def read(stream: str) -> Tuple[int, Union[None, Number]]:
        string = stream[:].strip()
        value = None
        for t in (int, float):
            try:
                value = t(string)
                break
            except:
                pass
        if value is not None:
            return len(string), Number(value)
        else:
            return 0, None


class Bool(Token):
    @staticmethod
    def read(stream: str) -> Tuple[int, Union[None, Bool]]:
        string = stream[:].strip()
        if string in ['true', 'True', 'yes']:
            return len(string), Bool(True)
        if string in ["false", 'False', 'no']:
            return len(string), Bool(False)
        return 0, None


# class NoneType(Token):
#     @staticmethod
#     def read(stream: str) -> Tuple[int, Any]:
#         string = stream[:strip]

class String(Token):
    stop_operators = [': ']  # mb: all operators should stop string?

    @staticmethod
    def read(stream: str) -> Tuple[int, Union[None, String]]:
        for op in Operator.operators:
            if stream.startswith(op):
                return 0, String("")
        pos = 0
        if stream[pos] in "\'\"":
            start_char = stream[pos]
            pos += 1
            while stream[pos] and stream[pos] != start_char:
                pos += 1
            if stream[pos] != start_char:
                raise TokenError("Not closed string expression")
            pos += 1
            return pos, String(stream[1:pos - 1])

        pos = len(stream)
        for op in String.stop_operators:
            found_pos = stream.find(op)
            if found_pos >= 0:
                pos = min(pos, found_pos)

        if pos == 0:
            return 0, None
        return pos, String(stream[:pos].strip())


# class Name(Token):
#     @staticmethod
#     def read(stream: str) -> Tuple[int, str]:
#         pos = 0
#         if not stream[pos].isalpha():
#             return 0, ''
#
#         while stream[pos].isalnum() or stream[pos] == '_' or \
#                 stream[pos] == '.':
#             pos += 1
#
#         return pos, stream[:pos]


class Operator(Token):
    operators = ['@', '#', '&', '!', '- ', ': ', '*', '---']

    @staticmethod
    def read(stream: str) -> Tuple[int, Union[None, Operator]]:
        for op in Operator.operators:
            if stream.startswith(op):
                return len(op), Operator(op)
        return 0, None


class Indent(Token):
    @staticmethod
    def read(stream: str) -> Tuple[int, Union[None, Indent]]:
        indent = 0
        pos = 0
        while stream[pos].isspace():
            if stream[pos] == ' ':
                indent += 1
            elif stream[pos] == '\t':
                indent += 4
            else:
                raise TokenError("Unknown indent symbol")
            pos += 1

        return pos, Indent(indent)


class List(Token):
    @staticmethod
    def read(stream: str) -> Tuple[int, Union[None, List]]:
        pos = 0
        if stream[pos] != '[':
            return pos, None
        while stream and stream[pos] != ']':
            pos += 1
        if stream[pos] != ']':
            raise TokenError('List was not closed')
        pos += 1
        read_list = eval(stream[:pos])
        return pos, List(read_list)


class Dict(Token):
    @staticmethod
    def read(stream: str) -> Tuple[int, Union[None, Dict]]:
        pos = 0
        if stream[pos] != '{':
            return pos, None
        while stream and stream[pos] != '}':
            pos += 1
        if stream[pos] != '}':
            raise TokenError('Dict was not closed')
        pos += 1
        read_dict = eval(stream[:pos])
        return pos, Dict(read_dict)


class InlinePython(Token):
    @staticmethod
    def read(stream: str) -> Tuple[int, Union[None, InlinePython]]:
        pos = 0
        if stream[pos] != '`':
            return pos, None
        pos += 1
        while stream and stream[pos] != '`':
            pos += 1
        if stream[pos] != '`':
            raise TokenError('Inline python string was not clothed')
        pos += 1
        return pos, InlinePython(stream[1:pos - 1])


class PythonString(Token):
    @classmethod
    def read(cls, stream: str, implicit_fstrings=False) -> \
            Tuple[int, Union[None, PythonString]]:
        string = stream[:].strip()
        if implicit_fstrings and string[0] in "\"\'":
            if string[-1] != string[0]:
                raise TokenError("Not closed f-string")
            return len(string), PythonString((string, 'f'))
        if string[0] == 'f' and string[1] in "\"\'":
            if string[-1] != string[1]:
                raise TokenError("Not closed f-string")
            return len(string), PythonString((string[1:], 'f'))
        if string[0] == 'r' and string[1] in "\"\'":
            if string[-1] != string[1]:
                raise TokenError("Not closed r-string")
            return len(string), PythonString((string[1:], 'r'))
        return 0, PythonString(("", ''))
