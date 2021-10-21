import parser
from typing import Union, Any, Iterable
from pathlib import Path

from .parser import Parser
from .constructor import Constructor, ConstructorError
from .iter_parser import IterParser
from .dumper import Dumper
from . import elements


def parse(path: Union[str, Path], always_iter: bool = False,
          implicit_fstrings: bool = True,
          strict: bool = False) -> \
        Union[elements.Element, Iterable[elements.Element]]:
    """Parses config providing Element tree

    Parameters
    ----------
    path: str or Path
        path to config file
    always_iter: bool
        If True will always return iterator over configs.
    implicit_fstrings: boot, default: True
        If True, all quoted strings will be treated as python f-strings.
    strict:
        It True, checks overwriting dict keys and positioning (`args` before `kwargs`).

    Returns
    -------
    tree: Element or Iterable[Element]
    """
    parser = Parser(implicit_fstrings=implicit_fstrings, strict=strict)
    tree = parser.parse(path)
    if parser.has_iterators() or always_iter:
        return IterParser(parser).iter_configs(tree)
    return tree


def construct(tree: elements.Element,
              strict_typing: bool = False) -> Any:
    """Constructs python object based on config and known nip-objects

    Parameters
    ----------
    tree: Element
        Read config tree.
    strict_typing:
        If True, raises Exception when typing mismatch.

    Returns
    -------
    obj: Any
    """
    constructor = Constructor(strict_typing=strict_typing)
    return constructor.construct(tree)


def _iter_load(configs, strict_typing):  # Otherwise load() will always be an iterator
    for config in configs:
        yield construct(config, strict_typing)


def load(path: Union[str, Path],
         always_iter: bool = False,
         strict: bool = False) -> Union[Any, Iterable[Any]]:
    """Parses config and constructs python object
    Parameters
    ----------
    path: str or Path
        Path to config file
    always_iter: bool
        If True will always return iterator over configs.
    strict:
        If True, raises Exception when typing mismatch or overwriting dict key.

    Returns
    -------
    obj: Any or Iterable[Any]
    """
    config = parse(path, always_iter, strict=strict)

    if isinstance(config, Iterable):
        return _iter_load(config, strict)

    return construct(config, strict)


def dump(path: Union[str, Path], tree: elements.Element):
    """Dumps config tree to file
    Parameters
    ----------
    path: str or Path
        Path to save the config
    tree: Element
        Read or generated config tree
    """
    dumper = Dumper()
    dumper.dump(path, tree)


def dumps(tree: elements.Element):
    """Dumps config tree to file
    Parameters
    ----------
    tree: Element
        Read or generated config tree

    Returns
    -------
    string: str
        Dumped element as a string
    """
    dumper = Dumper()
    return dumper.dumps(tree)


def _run_return(value, config, return_values, return_configs):
    if return_values or return_configs:
        if not return_values and return_configs:
            return value if return_values else dumps(config)
        else:
            return value, dumps(config)


def _single_run(config, verbose, return_values, return_configs, config_parameter,
                strict):
    if verbose:
        print("=" * 20)
        print("Running config:")
        print(dumps(config))
        print("----")

    if config_parameter:
        assert isinstance(config.value, elements.Tag)

        def tag_construct(tag, constructor):  # copy of a tag construction code =(
            if isinstance(tag.value, elements.Args):
                args, kwargs = tag.value.construct(constructor, always_pair=True)
            else:
                value = tag.value.construct(constructor)
                if value is elements.Nothing:
                    args, kwargs = [], {}
                else:
                    args, kwargs = [value], {}
            if config_parameter in kwargs:
                raise RuntimeWarning(
                    f"nip.run() was asked to add config parameter '{config_parameter}', "
                    f"but it is already specified by the config. It will be overwritten.")
            kwargs[config_parameter] = config  # adding the config
            try:
                return constructor.builders[tag.name](*args, **kwargs)
            except Exception as e:
                raise ConstructorError(tag, args, kwargs, e)
        constructor = Constructor(strict_typing=strict)
        value = tag_construct(config.value, constructor)
    else:
        value = construct(config, strict_typing=strict)

    if verbose:
        print("----")
        print("Run value:")
        print(value)

    return _run_return(value, config, return_values, return_configs)


def _iter_run(configs, verbose, return_values, return_configs, config_parameter, strict):
    for config in configs:
        run_return = _single_run(config, verbose, return_values, return_configs,
                                 config_parameter, strict)
        if run_return:
            yield run_return


def run(path: Union[str, Path],
        verbose: bool = True,
        strict: bool = False,
        return_values: bool = True,
        return_configs: bool = True,
        always_iter: bool = False,
        config_parameter: Union[str, None] = None):
    """Runs config. Config should be declared with function to run as a tag for the Document.
    In case of iterable configs we will iterate over and run each of them.

    Parameters
    ----------
    path: str or Path
        path to config to run.
    verbose: bool, optional
        Whether to print information about currently running experiment or not.
    strict:
        If True, raises Exception when typing mismatch or overwriting dict key.
    return_values: bool, optional
        Whether to return values of ran functions or not.
    return_configs: bool, optional
        Whether to return config for ran function or not.
    always_iter: bool, optional
        Result will always be iterable.
    config_parameter: str, optional
        If specified, parsed config will be passed to called function as a parameter with this name.

    Returns
    -------
    Iterator or single value depending on whether the config is iterable
    value or config or (value, config): Any or str or (Any, str)
        returned values and configs of runs
    """
    config = parse(path, always_iter=always_iter, strict=strict)
    if isinstance(config, Iterable):
        return list(_iter_run(config, verbose, return_values, return_configs,
                              config_parameter, strict))  # mb iter?

    return _single_run(config, verbose, return_values, return_configs, config_parameter, strict)
