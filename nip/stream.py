import nip.tokens as tokens

from typing import Union, List, Type


class Stream:
    def __init__(self, sstream: str):
        self.lines = sstream.split("\n")
        #self.lines = self._tokenize(sstream)
        self.n = 0
        self.pos = 0

    def peek(self, *args: Union[tokens.Token, Type[tokens.Token]]):  # read several tokens from stream
        line = self.lines[self.n]
        pos = self.pos
        read_tokens = []
        for arg in args:
            if isinstance(arg, tokens.Token):
                token_type = arg.__class__
            else:
                token_type = arg

            while pos < len(line) and line[pos].isspace():
                pos += 1
            if pos >= len(line):
                return None

            try:
                length, token = token_type.read(line[pos:])
            except tokens.TokenError as e:
                raise StreamError(self.n, pos, e)
            if token is None:
                return None
            if isinstance(arg, tokens.Token) and token != arg:
                return None

            token.set_position(self.n, pos)
            read_tokens.append(token)
            pos += length

        self.last_read_pos = pos
        return read_tokens

    def step(self):
        self.pos = self.last_read_pos
        if self.pos >= len(self.lines[self.n]) or self.lines[self.n][self.pos:].isspace():
            self.n += 1
            self.pos = 0

        while self and (len(self.lines[self.n]) == 0 or self.lines[self.n].isspace()):
            self.n += 1

        if not self:
            return

        while self.lines[self.n][self.pos].isspace():
            self.pos += 1

    def move(self, n_tokens: int):  # move only in the line
        self.pos += n_tokens
        if self.pos >= len(self.lines[self.n]):
            self.n += 1
            self.pos = 0

    def __bool__(self):
        return self.n < len(self.lines)


class StreamError(Exception):
    def __init__(self, line: int, position: int, msg: Exception):
        self.line = line
        self.pos = position
        self.msg = msg

    def __str__(self):
        return f"{self.line}:{self.pos}: {self.msg}"
