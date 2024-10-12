# Constructor of tagged objects
import importlib
import importlib.util
from types import FunctionType, ModuleType, BuiltinFunctionType
from typing import Callable, Optional, Union

from .utils import get_sub_dict

global_builders = {}  # builders shared between Constructors
global_calls = {}  # history of object creations


class Constructor:
    def __init__(self, ignore_rewriting=False, load_builders=True, strict_typing=False):
        self.builders = {}
        self.ignore_rewriting = ignore_rewriting
        if load_builders:
            self.load_builders()
        self.vars = {}
        self.strict_typing = strict_typing

    def construct(self, element):
        return element._construct(self)

    def register(self, func: Callable, tag: Optional[str] = None):
        """Registers builder function for tag
        Parameters
        ----------
        func:
            Function or class to build the python object.
            In case of class its __init__ method will be called to construct object.
        tag: str, optional
            Tag in yaml/nip file. func.__name__ will be used if not specified.
        """
        if tag is None:
            tag = func.__name__
        assert self.ignore_rewriting or tag not in self.builders, f"Builder for tag '{tag}' already registered"
        self.builders[tag] = func

    def load_builders(self):
        self.builders.update(global_builders)
        self.builders.update(get_sub_dict(NIPBuilder))


class ConstructorError(Exception):
    def __init__(self, element, args, kwargs, e):
        self.cls = type(element).__name__
        self.name = element._name
        self.args = args
        self.kwargs = kwargs
        self.e = e

    def __str__(self):
        return (
            f"Unable to construct {self.cls} '{self.name}' with args:{self.args} and "
            f"kwargs:{self.kwargs}.\nFollowing exception occurred:\n"
            f"{self.e.__class__.__name__}: {self.e}"
        )


# mb: add meta for auto detecting this class as NIP-builder
# ToDo: Add init wrapper for auto detection init args for convenient object dumping
class NIPBuilder:
    pass


def nip_decorator(name=None, convertable=False):
    assert name is None or len(name) > 0, "name should be nonempty"

    def _(item):
        if convertable:
            assert isinstance(item, type), "Call wrapping supported only for class type"
            make_convertable(item)
        local_name = name or item.__name__
        if isinstance(local_name, (list, tuple)):
            for n in local_name:
                global_builders[n] = item
        else:
            global_builders[local_name] = item
        return item

    return _


# instead of multipledispatch
def nip(item=None, *, wrap_builtins=False, convertable=False):
    if isinstance(item, str):  # single name is passed
        return nip_decorator(item, convertable)
    if isinstance(item, (list, tuple)):
        for name in item:
            if not isinstance(name, str):
                raise ValueError("Every specified Tag should be a string.")
        return nip_decorator(item, convertable)
    if isinstance(item, (type, FunctionType, BuiltinFunctionType)):
        return nip_decorator(convertable=convertable)(item)
    if isinstance(item, ModuleType):
        return wrap_module(item, wrap_builtins=wrap_builtins, convertable=convertable)
    if item is not None:
        raise ValueError("Unexpected type passed to @nip decorator.")
    return nip_decorator(convertable=convertable)


def wrap_module(module: Union[str, ModuleType], wrap_builtins=False, convertable=False):
    """Wraps everything declared in module with @nip

    Parameters
    ----------
    module: str or ModuleType
        Module name (e.g. "numpy.random") or module itself
    wrap_builtins
        Whether to wrap builtin functions or not.
        (Useful when wrapping whole module like `numpy`)
    """
    if isinstance(module, str):
        module = importlib.import_module(module)

    for value in module.__dict__.values():
        if isinstance(value, (type, FunctionType)) or wrap_builtins and isinstance(value, BuiltinFunctionType):
            nip(value, convertable=convertable and isinstance(value, type))

    return module


class ArgsKwargs:
    def __init__(self, args, kwargs):
        self.args = args
        self.kwargs = kwargs


def _wrap_init_call(self, *args, **kwargs):
    self.__init_args = ArgsKwargs(args, kwargs)
    self.__origin_init__(*args, **kwargs)


def _converter(self):
    return self.__init_args


def make_convertable(cls):
    if hasattr(cls, "__nip__"):
        return
    cls.__origin_init__ = cls.__init__
    cls.__init__ = _wrap_init_call
    cls.__nip__ = _converter
