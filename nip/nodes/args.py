from __future__ import annotations

from typing import TYPE_CHECKING, Tuple, Union

import nip

from .. import tokens
from .base import Node
from .reader import read_node
from .utils import STEP_INTO_NODE_TYPES, step_into_node

if TYPE_CHECKING:
    from ..constructor import Constructor
    from ..dumper import Dumper
    from ..parser.parser import Parser
    from ..stream import Stream


class Args(Node):
    def __init__(self, args, kwargs, name: str = "", line=None, pos=None):
        self._name = name
        self._args = args
        self._kwargs = kwargs
        self._value = None
        self._parent = None
        self._line = line
        self._pos = pos

    @classmethod
    def read(cls, stream: Stream, parser: Parser):
        start_indent = stream.pos
        if start_indent <= parser.last_indent:
            return None

        args = []
        kwargs = {}
        read_kwarg = False
        pos, read_pos = [None, None], None
        while stream and stream.pos == start_indent:
            pos = pos or read_pos
            parser.last_indent = start_indent

            item, read_pos = cls._read_list_item(stream, parser)
            if item is not None:
                if parser.strict and read_kwarg:
                    raise nip.parser.ParserError(
                        stream,
                        "Positional argument after keyword argument is forbidden in `strict` mode.",
                    )
                args.append(item)
                continue

            key, value, read_pos = cls._read_dict_pair(stream, parser, kwargs.keys())
            if key is not None:
                read_kwarg = True
                kwargs[key] = value
                continue

            break

        if stream.pos > start_indent:
            raise nip.parser.ParserError(stream, "Unexpected indent")

        if not args and not kwargs:
            return None
        pos = pos or (None, None)
        return Args(args, kwargs, "args", line=pos[0], pos=pos[1])

    @classmethod
    def _read_list_item(cls, stream: Stream, parser: Parser) -> Union[Tuple[Node, Tuple[int, int]], Tuple[None, None]]:
        read_tokens = stream.peek(tokens.Operator("- "))
        if read_tokens is None:
            return None, None
        line, pos = stream.step()
        value = read_node(stream, parser)
        return value, (line, pos)

    @classmethod
    def _read_dict_pair(
        cls, stream: Stream, parser: Parser, kwargs_keys
    ) -> Union[Tuple[str, Node, Tuple[int, int]], Tuple[None, None, None]]:
        read_tokens = stream.peek(tokens.Name, tokens.Operator(": "))
        if read_tokens is None:
            return None, None, None

        key = read_tokens[0]._value
        if parser.strict and key in kwargs_keys:
            raise nip.parser.ParserError(
                stream,
                f"Dict key overwriting is forbidden in `strict` mode. Overwritten key: '{key}'.",
            )
        line, pos = stream.step()
        value = read_node(stream, parser)
        return key, value, (line, pos)

    def __str__(self):
        args_repr = "[" + ", ".join([str(item) for item in self._args]) + "]"
        kwargs_repr = "{" + ", ".join([f"{key}: {str(value)}" for key, value in self._kwargs.items()]) + "}"
        return f"{self.__class__.__name__}('{self._name}', {args_repr}, {kwargs_repr})"

    def __bool__(self):
        return bool(self._args) or bool(self._kwargs)

    def _is_list(self):
        return len(self._args) > 0 and len(self._kwargs) == 0

    def _is_dict(self):
        return len(self._args) == 0 and len(self._kwargs) > 0

    def _is_args(self):
        return len(self._args) > 0 and len(self._kwargs) > 0

    def _get_sub_item(self, item):
        if not isinstance(item, (str, int)):
            raise TypeError(f"Unexpected item type: {type(item)}. str or int are expected.")

        if isinstance(item, int) or item.isnumeric():
            item = int(item)
            if 0 <= item < len(self._args):
                return None, self._args[item]
            return None, None
        key = item.split(".")[0]
        if key.isnumeric():
            return item[len(key) + 1 :], self._args[int(key)]
        for key in self._kwargs:
            if item.startswith(key):
                if len(item) == len(key):
                    return None, self._kwargs[key]
                if item[len(key)] != ".":
                    continue
                return item[len(key) + 1 :], self._kwargs[key]
        return None, None

    def _set_sub_item(self, key: Union[int, str], value: Node, node: Node = None):
        if node is value:  # fixes recursion problem with python __setitem__ call after /=
            return
        if node is not None and isinstance(node, STEP_INTO_NODE_TYPES):  # lets update values of links and tags
            parent, node = step_into_node(node)
            parent._value = value
            return
        if isinstance(key, int) or key.isnumeric():
            key = int(key)
            if 0 <= key < len(self._args):
                self._args[key] = value
            elif key == len(self._args):
                self._args.append(value)
            else:
                raise KeyError("You may only update existing arg of the Node or add one using `len(args)` as index")
        else:
            self._kwargs[key] = value
        self._update_parents()

    def _update_child(self, prev_child: Node, new_child: Node):
        updated = False
        for key, item in self:
            if item is prev_child:
                self._set_sub_item(key, new_child, None)
                updated = True
        assert updated, "did not find child upon updating node."

    def __getitem__(self, item) -> Node:
        left_key, node = self._get_sub_item(item)
        if node is None:
            raise KeyError(f"'{item}' is not a part of the Node.")
        if left_key:
            return node[left_key]
        return node

    def __contains__(self, item):
        left_key, node = self._get_sub_item(item)
        if node is None:
            return False
        if left_key:
            return left_key in node
        return True

    def __setitem__(self, key, value):
        from .document import Document

        if not isinstance(value, Node):
            value = nip.convert(value)
        if isinstance(value, Document):
            value = value._value

        left_key, node = self._get_sub_item(key)
        if node is None:  # new item set
            self._set_sub_item(key, value)
            return
        if left_key:  # some part of the key left, lets step into
            node[left_key] = value
        else:  # we should update here, ot step into link/tag to update its value.
            self._set_sub_item(key, value, node)

    def append(self, value):
        self._args.append(nip.convert(value))

    def __len__(self):
        return len(self._args) + len(self._kwargs)

    def __iter__(self):
        for i, item in enumerate(self._args):
            yield i, item
        for key, item in self._kwargs.items():
            yield key, item

    def to_python(self):
        args = list(item.to_python() for item in self._args)
        kwargs = {key: value.to_python() for key, value in self._kwargs.items()}
        assert args or kwargs, "Error converting Args node to python."
        if args and kwargs:
            result = {}
            result.update(nip.utils.iterate_items(args))
            result.update(nip.utils.iterate_items(kwargs))
            return result
        return args or kwargs

    @nip.constructor.construct_method
    def _construct(self, constructor: Constructor, always_pair=False):
        args = list(item._construct(constructor) for item in self._args)
        kwargs = {
            key: value._construct(constructor)
            for key, value in self._kwargs.items()
            if key not in ["_target_", "_args_"]
        }
        if "_target_" in self._kwargs:
            name = self._kwargs["_target_"]._construct(constructor)
            if "_args_" in self._kwargs:
                if len(args) > 0:
                    nip.constructor.ConstructorError(
                        self,
                        args,
                        kwargs,
                        "'_args_' key and usual args cant be presented in the Node at the same time.",
                        name=name,
                    )
                args = self._kwargs["_args_"]._construct(constructor)
            return nip.constructor.construct_with_args(name, args, kwargs, constructor, self)
        assert args or kwargs, "Error constructing Args node."
        if args and kwargs or always_pair:
            return args, kwargs
        return args or (nip.dict.DictObject(kwargs) if constructor.as_dictobj else kwargs)

    def _dump(self, dumper: Dumper):
        dumped_args = "\n".join(
            [" " * dumper.indent + f"- {item._dump(dumper + dumper.default_shift)}" for item in self._args]
        )
        string = ("\n" if dumped_args else "") + dumped_args

        dumped_kwargs = "\n".join(
            [
                " " * dumper.indent + f"{key}: {value._dump(dumper + dumper.default_shift)}"
                for key, value in self._kwargs.items()
            ]
        )
        string += ("\n" if dumped_kwargs else "") + dumped_kwargs
        return string

    def _update_parents(self):
        self.__dict__.update(self._kwargs)
        for key, item in self:
            item._parent = self
            item._update_parents()
