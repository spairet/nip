from copy import copy
from typing import Union


class Stream:
    # mb: do move in token reading if it is performed.
    # mb: add read_token method to stream
    # mb: add read_name, read_string, etc. methods to stream
    def __init__(self, sstream: str, start_pos: int = 0):
        self.lines = sstream.split("\n")
        self.lines = [line for line in self.lines if len(line) > 0]
        self.pos = start_pos
        self.n = 0
        self.last_indent = -1

    def __getitem__(self, item) -> Union[str, None]:
        if isinstance(item, int):
            if self.pos + item >= len(self.lines[self.n]):
                return ''
            return self.lines[self.n][self.pos + item]
        elif isinstance(item, slice):
            start = (item.start or 0) + self.pos
            stop = None if item.stop is None else item.stop + self.pos
            item = slice(start, stop, item.step)
            return self.lines[self.n][item]
        else:
            raise IndexError("Unexpected index")

    def move(self, shift=0):
        self.pos += shift

        # read out spaces
        while self.pos < len(self.lines[self.n]) and \
                self.lines[self.n][self.pos].isspace():
            self.pos += 1

        if self.pos == len(self.lines[self.n]) or \
                self.lines[self.n][self.pos] == '#':
            self.n += 1
            self.pos = 0

        if not self:
            return
        # skip empty lines
        while self and (self.lines[self.n].isspace() or self.lines[self.n].strip()[0]) == '#':
            self.n += 1

    def __bool__(self):
        return self.n < len(self.lines)

    def __add__(self, shift: int):  # ToDo: do we even need this?
        new_stream = copy(self)  # ToDo: check how does ot work
        new_stream.move(shift)
        return new_stream
