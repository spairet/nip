# Constructor of tagged objects
import importlib
import importlib.util
import inspect
import typeguard

from typing import Callable, Optional, Union, List, Tuple
from types import FunctionType, ModuleType, BuiltinFunctionType
from multipledispatch import dispatch

from .utils import get_sub_dict


global_builders = {}  # builders shared between Constructors
global_calls = {}  # history of object creations


class Constructor:
    def __init__(self, ignore_rewriting=False, load_builders=True,
                 strict_typing=False):
        self.builders = {}
        self.ignore_rewriting = ignore_rewriting
        if load_builders:
            self.load_builders()
        self.vars = {}
        self.strict_typing = strict_typing

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
    def __init__(self, element, args, kwargs, e):
        self.cls = type(element).__name__
        self.name = element.name
        self.args = args
        self.kwargs = kwargs
        self.e = e

    def __str__(self):
        return f"Unable to construct {self.cls} '{self.name}' with args:{self.args} and " \
               f"kwargs:{self.kwargs}.\nFollowing exception occurred:\n" \
               f"{self.e.__class__.__name__}: {self.e}"


# mb: add meta for auto detecting this class as NIP-builder
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
        if isinstance(local_name, (list, tuple)):
            for n in local_name:
                global_builders[n] = item
        else:
            global_builders[local_name] = item
        return item

    return _


@dispatch(str)
def nip(name: str, wrap_call: bool = False):
    """Wrapper to register function or class with specified name."""
    return nip_decorator(name, wrap_call)


@dispatch([(list, tuple)])
def nip(names: Union[List[str], Tuple[str]], wrap_call: bool = False):
    """Wrapper to register function or class with specified name."""
    assert len(names) > 0, "Tag list should be nonempty"
    for name in names:
        assert isinstance(name, str), "Every specified Tag should be string."
    return nip_decorator(names, wrap_call)


@dispatch()
def nip(wrap_call=False):
    return nip_decorator(wrap_call=wrap_call)


@dispatch([(type, FunctionType, BuiltinFunctionType)])
def nip(item: Union[type, FunctionType]):
    """Wrapper to register function or class with default name."""
    return nip_decorator()(item)


@dispatch(ModuleType)
def nip(module, wrap_builtins=False):
    """Wraps everything specified under module."""
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
    wrap_builtins
        Whether to wrap builtin functions or not.
        (Useful when wrapping whole module like `numpy`)
    """
    if isinstance(module, str):
        module = importlib.import_module(module)

    for value in module.__dict__.values():
        if isinstance(value, (type, FunctionType)) or \
                wrap_builtins and isinstance(value, BuiltinFunctionType):
            nip(value)


def check_typing(func, args, kwargs) -> List[str]:
    try:
        signature = inspect.signature(func)
    except ValueError:  # unable to load function signature (common case for builtin functions)
        return []
    messages = []
    for arg, param in zip(args, signature.parameters.values()):
        if param.annotation is inspect.Parameter.empty:
            continue
        try:
            typeguard.check_type(param.name, arg, param.annotation)
        except TypeError as e:
            messages.append("- " + str(e))

    for name, value in kwargs.items():
        if name not in signature.parameters:
            continue  # handled by python
        annotation = signature.parameters[name].annotation
        if annotation is inspect.Parameter.empty:
            continue
        try:
            typeguard.check_type(name, value, annotation)
        except TypeError as e:
            messages.append("- " + str(e))

    return messages
