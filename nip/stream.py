import nip.tokens as tokens

from typing import Union


class Stream:
    def __init__(self, sstream: str):
        self.lines = self._tokenize(sstream)
        self.n = 0
        self.pos = 0

    @staticmethod
    def _tokenize(sstream):
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
                token.set_position(i, pos)
                lines[-1].append(token)
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
            tokens.PythonString,  # ToDo: implicit fstrings?
            tokens.String
        ]

        for cls in classes:
            read_symbols, token = cls.read(string)
            if token:
                return read_symbols, token
        return 0, None

    def __getitem__(self, item: int) -> Union[None, tokens.Token]:
        if self.pos + item < len(self.lines[self.n]):
            return self.lines[self.n][self.pos + item]
        else:
            return None

    def move(self, n_tokens: int):  # move only in the line
        self.pos += n_tokens
        if self.pos >= len(self.lines[self.n]):
            self.n += 1
            self.pos = 0

    def __bool__(self):
        return self.n < len(self.lines)


class StreamError(Exception):
    def __init__(self, line, position, msg: str):
        self.line = line
        self.pos = position
        self.msg = msg

    def __str__(self):
        return f"{self.line}:{self.pos}: {self.msg}"
