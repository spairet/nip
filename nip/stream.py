import nip.tokens as tokens

from copy import copy
from typing import Union

from nip.utils import get_subclasses


class Stream:
    def __init__(self, sstream: str):
        self.lines = self._tokenize(sstream)

    @staticmethod
    def _tokenize(sstream: str):
        lines = []
        for i, line in enumerate(sstream.split("\n")):
            lines.append(list())
            if line.isspace():
                continue
            pos = 0
            while pos < len(line):
                while line[pos].isspace():
                    pos += 1
                try:
                    length, token = Stream._read_token(line[pos:])
                except tokens.TokenError as e:
                    raise StreamError(i, pos, str(e))
                if token is None:
                    raise StreamError(i, pos, "Unable to read any token")
                lines[-1].append((i, pos, token))
                pos += length
        return lines

    @staticmethod
    def _read_token(string):
        classes = [
            tokens.InlinePython,
            tokens.List,
            tokens.Dict,
            tokens.Operator,
            tokens.Number,
            tokens.String
        ]

        for cls in classes:
            read_symbols, token = cls.read(string)
            if token:
                return read_symbols, token
        return 0, None


class StreamError(Exception):
    def __init__(self, line, position, msg: str):
        self.line = line
        self.pos = position
        self.msg = msg

    def __str__(self):
        return f"{self.line}:{self.pos}: {self.msg}"
