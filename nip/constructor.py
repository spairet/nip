# Constuctor of tagged objects
import importlib
import importlib.util

from typing import Callable, Optional, Union
from types import FunctionType, ModuleType, BuiltinFunctionType
from multipledispatch import dispatch

from .utils import get_sub_dict


global_builders = {}  # builders shared between Constructors
global_calls = {}  # history of object creations


class Constructor:
    def __init__(self, ignore_rewriting=False, load_builders=True):
        self.builders = {}
        self.ignore_rewriting = ignore_rewriting
        if load_builders:
            self.load_builders()
        self.vars = {}

    def construct(self, element):
        return element.construct(self)

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
        assert self.ignore_rewriting or tag not in self.builders, \
            f"Builder for tag '{tag}' already registered"
        self.builders[tag] = func

    def load_builders(self):
        self.builders.update(global_builders)
        self.builders.update(get_sub_dict(NIPBuilder))


class ConstructorError(Exception):
    def __init__(self, element, args, kwargs):
        self.cls = type(element).__name__
        self.name = element.name
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        return f"Unable to construct {self.cls} '{self.name}' with args:{self.args} and " \
               f"kwargs:{self.kwargs}"


# mb: add meta for auto detecting this class as YAP-builder
# ToDo: Add init wrapper for auto detection init args for convenient object dumping
class NIPBuilder:
    pass


def nip_decorator(name=None, wrap_call=False):
    assert name is None or len(name) > 0, "name should be nonempty"

    def _(item):
        if wrap_call:
            assert isinstance(item, type), "Call wrapping supported only for class type"
            item = call_wrapper(item)
        local_name = name or item.__name__
        global_builders[local_name] = item
        return item

    return _


@dispatch(str)
def nip(name: str, wrap_call: bool = False):
    return nip_decorator(name, wrap_call)


@dispatch()
def nip(wrap_call=False):
    return nip_decorator(wrap_call=wrap_call)


@dispatch([(type, FunctionType, BuiltinFunctionType)])
def nip(item: Union[type, FunctionType]):
    return nip_decorator()(item)


@dispatch(ModuleType)
def nip(module, wrap_builtins=False):
    wrap_module(module, wrap_builtins)


def call_wrapper(item: Union[type, FunctionType]):  # wraps call for convenient object dump
    print("wrapping")
    # ToDo: only for classes !!

    def call_dumper(*args, **kwargs):
        print(args, kwargs)
        value = item(*args, **kwargs)
        global_calls[value] = (args, kwargs)  # Todo: how to do this correctly?
        return value

    call_dumper.__doc__ = item.__doc__  # mimic to original function
    call_dumper.__name__ = item.__name__

    return call_dumper


def wrap_module(module: Union[str, ModuleType], wrap_builtins=False):
    """Wraps everything declared in module with @nip

    Parameters
    ----------
    module: str or ModuleType
        Module name (e.g. "numpy.random") or module itself
    """
    if isinstance(module, str):
        module = importlib.import_module(module)

    for value in module.__dict__.values():
        if isinstance(value, (type, FunctionType)) or \
                wrap_builtins and isinstance(value, BuiltinFunctionType):
            nip(value)
