from pathlib import Path
from typing import Union, Iterable

from nip import elements
from nip.parser.iter_parser import IterParser
from nip.parser.parser import Parser


def parse(
    path: Union[str, Path],
    always_iter: bool = False,
    implicit_fstrings: bool = True,
    strict: bool = False,
) -> Union["elements.Node", "Iterable[elements.Node]"]:
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


def parse_string(
    config_string: str,
    always_iter: bool = False,
    implicit_fstrings: bool = True,
    strict: bool = False,
) -> Union["elements.Node", "Iterable[elements.Node]"]:
    """Parses config providing Element tree

    Parameters
    ----------
    config_string: str
        Config as a string.
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
    tree = parser.parse_string(config_string)
    if parser.has_iterators() or always_iter:
        return IterParser(parser).iter_configs(tree)
    return tree
