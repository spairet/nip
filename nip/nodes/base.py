from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Union

import nip
import nip.constructor
import nip.dict
import nip.dumper
import nip.parser
import nip.stream
import nip.utils


class Node(ABC, object):
    def __init__(
        self, name: str = "", value: Any = None, line: int = None, pos: int = 0
    ):
        self._name = name
        self._value = value
        self._parent = None
        self._line = line
        self._pos = pos

    @classmethod
    @abstractmethod
    def read(
        cls, stream: nip.stream.Stream, parser: nip.parser.Parser
    ) -> Union["Node", None]:
        pass

    def __str__(self):
        return f"{self.__class__.__name__}('{self._name}', {self._value})"

    def __getitem__(self, item):
        if not isinstance(item, (str, int)):
            raise TypeError(
                f"Unexpected item type: {type(item)}. str or int are expected."
            )
        if isinstance(item, str) and len(item) == 0:
            return self
        if self._value is None:
            raise KeyError(f"'{item}' is not a part of the Node.")
        return self._value[item]

    def __getattr__(self, item):
        return self.__getitem__(item)

    def __setitem__(self, key, value):
        self._value[key] = value
        self._value._parent = self

    def __contains__(self, item):
        if not isinstance(self._value, Node):
            return False
        return item in self._value

    def __setattr__(self, key, value):
        if key.startswith("_"):
            self.__dict__[key] = value
        else:
            self.__setitem__(key, value)

    def to_python(self):
        return self._value.to_python()

    def to_dictobject(self):
        data = self.construct()
        if isinstance(data, (tuple, list, dict)):
            return nip.dict.DictObject(data)
        return data

    @nip.constructor.construct_method
    def _construct(self, constructor: nip.constructor.Constructor):
        return self._value._construct(constructor)

    def construct(self, strict_typing: bool = False, as_dictobj: bool = False):
        return nip.construct(
            self, strict_typing=strict_typing, nonsequential=True, as_dictobj=as_dictobj
        )

    def _dump(self, dumper: nip.dumper.Dumper):
        return self._value._dump(dumper)

    def dump(self, path: Union[str, Path]):
        nip.dump(path, self)

    def dump_string(self):
        return nip.dump_string(self)

    def __eq__(self, other):
        return self._name == other._name and self._value == other._value

    def flatten(self, delimiter=".") -> Dict:
        return nip.utils.flatten(self.to_python(), delimiter)

    def _update_parents(self):
        if isinstance(self._value, Node):
            self._value._parent = self
            self._value._update_parents()

    def _get_root(self):
        if self._parent is None:
            return self
        return self._parent._get_root()

    def update(self):
        self._get_root().update()


Element = Node
