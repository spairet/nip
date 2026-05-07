"""Contains all the elements of nip config files"""

from __future__ import annotations

import logging
import re
from abc import abstractmethod, ABC
from pathlib import Path
from typing import Any, Union, Tuple, Dict

import nip.constructor  # This import pattern because of cycle imports
import nip.directives
import nip.dumper
import nip.non_seq_constructor as nsc
import nip.parser
import nip.stream
import nip.tokens as tokens
import nip.utils
import nip.dict

_LOGGER = logging.getLogger(__name__)


class Node(ABC, object):
    def __init__(self, name: str = "", value: Any = None, line: int = None, pos: int = 0):
        self._name = name
        self._value = value
        self._parent = None
        self._line = line
        self._pos = pos

    @classmethod
    @abstractmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[Node, None]:
        pass

    def __str__(self):
        return f"{self.__class__.__name__}('{self._name}', {self._value})"

    def __getitem__(self, item):
        if not isinstance(item, (str, int)):
            raise TypeError(f"Unexpected item type: {type(item)}. str or int are expected.")
        if isinstance(item, str) and len(item) == 0:
            return self
        if self._value is None:
            raise KeyError(f"'{item}' is not a part of the Node.")
        return self._value[item]

    def __getattr__(self, item):  # unable to access names like `construct` and 'dump` via this method
        return self.__getitem__(item)

    def __setitem__(self, key, value):
        self._value[key] = value
        self._value._parent = self

    def __contains__(self, item):
        if not isinstance(self._value, Node):
            return False
        return item in self._value

    def __setattr__(self, key, value):
        if key.startswith("_"):  # mb: ensure not user's node name?
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
        return nip.construct(self, strict_typing=strict_typing, nonsequential=True, as_dictobj=as_dictobj)

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


Element = Node  # backward compatibility until 1.* version


class Document(Node):  # ToDo: add multi document support
    def __init__(self, name: str = "", value: Union[Node, Any] = None, line: int = None, pos: int = 0):
        super().__init__(name, value)
        self._path = None
        self._line = line
        self._pos = pos

    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Document:
        line, pos = stream.line, stream.pos
        doc_name = cls._read_name(stream)
        content = read_node(stream, parser)
        return Document(doc_name, content, line, pos)

    @classmethod
    def _read_name(cls, stream: nip.stream.Stream):
        read_tokens = stream.peek(tokens.Operator("---"), tokens.Name) or stream.peek(tokens.Operator("---"))
        if read_tokens is not None:
            line, pos = stream.step()
            if len(read_tokens) == 2:
                return read_tokens[1]._value
        return ""

    def _dump(self, dumper: nip.dumper.Dumper):
        string = "---"
        if self._name:
            string += " " + self._name + " "
        return string + self._value._dump(dumper)

    def update(self):
        self.dump(self._path)


class Value(Node):
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[None, Value]:
        tokens_list = [
            tokens.Number,
            tokens.NoneToken,
            tokens.Bool,
            tokens.String,
            tokens.List,
            tokens.TupleToken,
            tokens.Dict,
        ]
        for token in tokens_list:
            read_tokens = stream.peek(token)
            if read_tokens is not None:
                line, pos = stream.step()
                return Value(read_tokens[0]._name, read_tokens[0]._value, line=line, pos=pos)

        return None

    def to_python(self):
        return self._value

    @nip.constructor.construct_method
    def _construct(self, constructor: nip.constructor.Constructor = None):
        constructor[self] = self._value
        return self._value

    def _dump(self, dumper: nip.dumper.Dumper):
        if isinstance(self._value, str):
            return f'"{self._value}"'
        return str(self._value)

    def __len__(self):
        return len(self._value)


class LinkCreation(Node):
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[Node, None]:
        read_tokens = stream.peek(tokens.Operator("&"), tokens.Name)
        if read_tokens is None:
            # if stream.peek(tokens.Operator('&')):  # mb: do it more certainly: peak operator
            #     raise nip.parser.ParserError(      # mb: firstly and then choose class to read)
            #         stream, "Found variable creation operator '&' but name is not specified")
            return None

        name = read_tokens[1]._value
        line, pos = line, pos = stream.step()

        value = read_node(stream, parser)
        if name in parser.links:
            raise nip.parser.ParserError(stream, f"Redefining of link '{name}'")
        parser.links.append(name)

        return LinkCreation(name, value, line, pos)

    @nip.constructor.construct_method
    def _construct(self, constructor: nip.constructor.Constructor):
        constructor[self._name] = self
        return self._value._construct(constructor)

    def _dump(self, dumper: nip.dumper.Dumper):
        return f"&{self._name} {self._value._dump(dumper)}"


class Link(Node):
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[Node, None]:
        read_tokens = stream.peek(tokens.Operator("*"), tokens.Name)
        if read_tokens is None:
            return None

        name = read_tokens[1]._value  # mb: use LinkCreation node as value. fixes `in` operator.
        line, pos = stream.step()

        if name in parser.link_replacements:
            return parser.link_replacements[name]

        if parser.sequential_links and name not in parser.links:
            nip.parser.ParserError(stream, "Link usage before assignment")

        return Link(name, line=line, pos=pos)

    def to_python(self):
        return "nil"  # something that means that object is not constructed yet.

    @nip.constructor.construct_method
    def _construct(self, constructor: nip.non_seq_constructor.NonSequentialConstructor):
        # if self._construction_in_progress:
        #     raise nip.non_seq_constructor.NonSequentialConstructorError(f"Recursive construction of {self._name}")
        # self._construction_in_progress = True
        root = self._get_root()
        if self._name in constructor.links:  # was constructed or can be constructed
            value = constructor[self._name]
        elif self._name in root:
            value = root[self._name]._construct(constructor)
        else:
            raise NameError(f"Unable to resolve link '{self._name}'.")
        # self._construction_in_progress = False
        return value

    def _dump(self, dumper: nip.dumper.Dumper):
        return f"*{self._name}"

    def __getitem__(self, item):
        raise NotImplementedError("'__getitem__' is not implemented for Link node.")

    def __contains__(self, item):
        raise NotImplementedError("'in' operator if not implemented for Link node.")


class Tag(Node):
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[Tag, None]:
        read_tokens = stream.peek(tokens.Operator("!"), tokens.Name)
        if read_tokens is None:
            return None
        name = read_tokens[1]._value
        line, pos = stream.step()

        value = read_node(stream, parser)

        return Tag(name, value, line=line, pos=pos)

    @nip.constructor.construct_method
    def _construct(self, constructor: nip.constructor.Constructor):
        if isinstance(self._value, Args):
            args, kwargs = self._value._construct(constructor, always_pair=True)
        else:
            value = self._value._construct(constructor)
            if isinstance(value, Nothing):  # mb: Add IS_NOTHING method
                args, kwargs = [], {}
            else:
                args, kwargs = [value], {}

        return nip.constructor.construct_with_args(self._name, args, kwargs, constructor, self)

    def _dump(self, dumper: nip.dumper.Dumper):
        return f"!{self._name} " + self._value._dump(dumper)


class Class(Node):
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[Class, None]:
        read_tokens = stream.peek(tokens.Operator("!&"), tokens.Name)
        if read_tokens is None:
            return None
        name = read_tokens[1]._value
        line, pos = stream.step()

        value = read_node(stream, parser)
        if not isinstance(value, Nothing):
            raise nip.parser.ParserError(stream, "Class should be created with nothing to the right.")

        return Class(name, value, line=line, pos=pos)

    @nip.constructor.construct_method
    def _construct(self, constructor: nip.constructor.Constructor):
        value = self._value._construct(constructor)
        assert isinstance(value, Nothing), "Unexpected right value while constructing Class"

        return constructor.builders[self._name]

    def _dump(self, dumper: nip.dumper.Dumper):
        return f"!&{self._name} " + self._value._dump(dumper)


class Args(Node):
    def __init__(self, args, kwargs, name: str = "", line=None, pos=None):
        self._name = name
        self._args = args
        self._kwargs = kwargs
        self._value = None  # to prevent step into
        self._parent = None
        self._line = line
        self._pos = pos

    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[Args, None]:
        start_indent = stream.pos
        if start_indent <= parser.last_indent:
            return None

        args = []
        kwargs = {}  # mb: just dict with integer and string keys !
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
    def _read_list_item(
        cls, stream: nip.stream.Stream, parser: nip.parser.Parser
    ) -> Union[Tuple[Node, Tuple[int, int]], Tuple[None, None]]:
        read_tokens = stream.peek(tokens.Operator("- "))
        if read_tokens is None:
            return None, None
        line, pos = stream.step()

        value = read_node(stream, parser)

        return value, (line, pos)

    @classmethod
    def _read_dict_pair(
        cls, stream: nip.stream.Stream, parser: nip.parser.Parser, kwargs_keys
    ) -> Union[Tuple[str, Node, Tuple[int, int]], Tuple[None, None, None]]:
        # mb: read String instead of Name for keys with spaces,
        # mb: but this leads to the case that
        read_tokens = stream.peek(tokens.Name, tokens.Operator(": "))
        if read_tokens is None:
            return None, None, None

        key = read_tokens[0]._value
        if parser.strict and key in kwargs_keys:
            raise nip.parser.ParserError(
                stream,
                f"Dict key overwriting is forbidden in `strict` " f"mode. Overwritten key: '{key}'.",
            )
        line, pos = stream.step()

        value = read_node(stream, parser)

        return key, value, (line, pos)

    def __str__(self):
        args_repr = "[" + ", ".join([str(item) for item in self._args]) + "]"
        kwargs_repr = "{" + ", ".join([f"{key}: {str(value)}" for key, value in self._kwargs.items()]) + "}"

        return f"{self.__class__.__name__}('{self._name}', {args_repr}, {kwargs_repr})"

    def __bool__(self):  # mb: should always be True.
        return bool(self._args) or bool(self._kwargs)

    def _is_list(self):
        return len(self._args) > 0 and len(self._kwargs) == 0

    def _is_dict(self):
        return len(self._args) == 0 and len(self._kwargs) > 0

    def _is_args(self):
        return len(self._args) > 0 and len(self._kwargs) > 0

    def _get_sub_item(self, item):
        # some.deep.0.parameter -> [some.deep][0][parameter] / [some][deep][0][parameter]
        if not isinstance(item, (str, int)):
            raise TypeError(f"Unexpected item type: {type(item)}. str or int are expected.")

        if isinstance(item, int) or item.isnumeric():
            item = int(item)
            if 0 <= item < len(self._args):
                return None, self._args[item]
            return None, None
        key = item.split(".")[0]
        if key.isnumeric():
            # left_key = None if len(key) == len(item) else item[len(key) + 1 :]
            return item[len(key) + 1 :], self._args[int(key)]
        for key in self._kwargs:
            if item.startswith(key):
                if len(item) == len(key):
                    return None, self._kwargs[key]
                if item[len(key)] != ".":
                    continue
                return item[len(key) + 1 :], self._kwargs[key]
        return None, None

    def _set_sub_item(self, key, value):
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

    def __getitem__(self, item) -> Node:
        left_key, node = self._get_sub_item(item)
        if node is None:
            raise KeyError(f"'{item}' is not a part of the Node.")
        if left_key:  # step deeper
            return node[left_key]
        return node

    def __contains__(self, item):
        left_key, node = self._get_sub_item(item)
        if node is None:
            return False
        if left_key:  # step deeper
            return left_key in node
        return True

    def __setitem__(self, key, value):
        if not isinstance(value, Node):
            value = nip.convert(value)
        if isinstance(value, Document):  # this convenient for user. but do not insert Document node inside the tree.
            value = value._value

        left_key, node = self._get_sub_item(key)
        if node is None:  # new sub
            self._set_sub_item(key, value)
            return
        if left_key:  # step deeper
            node[left_key] = value
        else:  # update sub
            self._set_sub_item(key, value)

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
        assert args or kwargs, "Error converting Args node to python."  # This should never happen
        if args and kwargs:
            result = {}
            result.update(nip.utils.iterate_items(args))
            result.update(nip.utils.iterate_items(kwargs))
            return result
        return args or kwargs

    @nip.constructor.construct_method
    def _construct(self, constructor: nip.constructor.Constructor, always_pair=False):
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
        assert args or kwargs, "Error constructing Args node."  # This should never happen
        if args and kwargs or always_pair:
            return args, kwargs
        # return args or kwargs
        return args or (nip.dict.DictObject(kwargs) if constructor.as_dictobj else kwargs)

    def _dump(self, dumper: nip.dumper.Dumper):
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


class Iter(Node):  # mark all parents as Iterable and allow construct specific instance
    def __init__(self, name: str = "", value: Any = None, line: int = None, pos: int = None):
        super(Iter, self).__init__(name, value)
        self._return_index = -1
        # mb: name all the iterators and get the value from constructor rather then use this index
        self._line = line
        self._pos = pos

    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[Iter, None]:
        read_tokens = stream.peek(tokens.Operator("@"), tokens.Name) or stream.peek(tokens.Operator("@"))
        if read_tokens is None:
            return None
        line, pos = stream.step()
        value = read_node(stream, parser)
        if isinstance(value, Value) and isinstance(value._value, list):  # mb: replace inline list with Node
            value = value._value
        elif isinstance(value, Args) and value._is_list():
            value = value
        else:
            raise nip.parser.ParserError(stream, "List is expected as a value for Iterable node")
        if len(read_tokens) == 1:
            iterator = Iter("", value, line=line, pos=pos)
        else:
            iterator = Iter(read_tokens[1]._value, value, line=line, pos=pos)

        parser.iterators.append(iterator)
        return iterator

    def to_python(self):
        if self._return_index == -1:
            raise iter(self._value)
        if isinstance(self._value[self._return_index], Node):
            return self._value[self._return_index].to_python()
        return self._value[self._return_index]

    @nip.constructor.construct_method
    def _construct(self, constructor: nip.constructor.Constructor):
        if self._return_index == -1:
            raise Exception("Iterator index was not specified by IterParser")
        if isinstance(self._value, list):
            return self._value[self._return_index]
        elif isinstance(self._value, Args):
            return self._value[self._return_index]._construct(constructor)
        else:
            raise nip.constructor.ConstructorError(self, (), {}, "Unexpected iter value type")

    def _dump(self, dumper: nip.dumper.Dumper):
        if self._return_index == -1:
            raise nip.dumper.DumpError("Dumping an iterator but index was not specified by IterParser")
        if isinstance(self._value, list):
            return str(self._value[self._return_index])
        elif isinstance(self._value, Args):
            return self._value[self._return_index]._dump(dumper)
        else:
            raise nip.dumper.DumpError("Unable to dump Iterable node: unexpected value type")


class InlinePython(Node):
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[InlinePython, None]:
        read_tokens = stream.peek(tokens.InlinePython)
        if read_tokens is None:
            return None
        line, pos = stream.step()
        exec_string = read_tokens[0]._value
        return InlinePython(value=exec_string, line=line, pos=pos)

    @nip.constructor.construct_method
    def _construct(self, constructor: nip.constructor.Constructor):
        symbols, attributes_access = nip.utils.extract_symbols_from_code(self._value)
        namespace = nip.utils.Namespace()
        root = self._get_root()
        for item in attributes_access:
            if item in root:
                namespace[item] = constructor[root[item]]  # != root[item]._construct(constructor) for Constructor
        for symbol in symbols:
            if symbol in constructor:
                namespace[symbol] = constructor[symbol]
        # mb: check we didn't find attributes. default exception is fine?
        # but we need to do this for symbols that are not links
        locals().update(namespace.__dict__)
        return eval(self._value)

    def _dump(self, dumper: nip.dumper.Dumper):
        return f"`{self._value}`"

    def to_python(self):
        return f"`{self._value}`"


class Nothing(Node):
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[Nothing, None]:
        line, pos = stream.line, stream.pos
        if not stream:
            return Nothing(line=line, pos=pos)

        indent = stream.pos
        if stream.pos == 0 or (stream.lines[stream.line][: stream.pos].isspace() and indent <= parser.last_indent):
            return Nothing(line=line, pos=pos)

    @nip.constructor.construct_method
    def _construct(self, constructor: nip.constructor.Constructor):
        return self

    def _dump(self, dumper: nip.dumper.Dumper):
        return ""

    def to_python(self):
        return None


class FString(Node):  # Includes f-string and r-string
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[FString, None]:
        read_tokens = stream.peek(tokens.PythonString)
        if read_tokens is None:
            return None
        line, pos = stream.step()
        string, t = read_tokens[0]._value
        if t == "r":
            print(
                "Warning: all strings in NIP are already python r-string. " "You don't have to explicitly specify it."
            )
        return FString(value=string, line=line, pos=pos)

    @nip.constructor.construct_method
    def _construct(self, constructor: nip.constructor.Constructor):
        symbols, attributes_access = nip.utils.extract_symbols_from_code(f"f{self._value}")
        namespace = nip.utils.Namespace()
        root = self._get_root()
        for item in attributes_access:
            if item in root:
                namespace[item] = constructor[root[item]]  # != root[item]._construct(constructor) for Constructor
        for symbol in symbols:
            if symbol in constructor:
                namespace[symbol] = constructor[symbol]
        # mb: check we didn't find attributes. default exception is fine?
        # but we need to do this for symbols that are not links
        locals().update(namespace.__dict__)
        return eval(f"f{self._value}")

    def _dump(self, dumper: nip.dumper.Dumper):
        return f"f{self._value}"

    def to_python(self):
        return f"f{self._value}"


class Directive(Node):
    @classmethod
    def read(cls, stream: nip.stream.Stream, parser: nip.parser.Parser) -> Union[FString, None]:
        read_tokens = stream.peek(tokens.Operator("!!"), tokens.Name)
        if read_tokens is None:
            return None
        name = read_tokens[1]._value
        stream.step()

        value = read_node(stream, parser)

        return nip.directives.call_directive(name, value, stream)


def read_node(stream: nip.stream.Stream, parser: nip.parser.Parser) -> Node:
    value = (
        Directive.read(stream, parser)
        or LinkCreation.read(stream, parser)
        or Link.read(stream, parser)
        or Class.read(stream, parser)
        or Tag.read(stream, parser)
        or Iter.read(stream, parser)
        or Args.read(stream, parser)
        or FString.read(stream, parser)
        or Nothing.read(stream, parser)
        or InlinePython.read(stream, parser)
        or Value.read(stream, parser)
    )

    if value is None:
        raise nip.parser.ParserError(stream, "Wrong right value")

    return value
