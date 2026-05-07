from typing import Union, Iterable

import nip.elements
from .parser import parse


def update_flatten(
    base_config: "nip.elements.Node", updating_config: Union[str, "nip.elements.Node"]
) -> "nip.elements.Node":
    """Updates base_config with flatten params described in other_config. Inplace.

    Notes
    -----
    updating_config is expected to be flat dict and deep nodes of base_config are accessed via dots in keys.
    (e.g. `some.deep.node: new_value`)

    Parameters
    ----------
    base_config : str or Node
        Basic config Node to be updated.
        If str, will be treated as a path to config.
    updating_config : Node
        Config that will be used to update the basic one.

    Returns
    -------
    updated_config : Node
        Updated config Node.
    """
    if isinstance(updating_config, str):
        updating_config = parse(updating_config)
    if isinstance(updating_config, Iterable):
        raise TypeError(
            "Only non iterable configs are supported as updating_config."
        )  # mb: add IterableConfig, instead of handling this by Parser.
    if isinstance(updating_config, nip.elements.Document):
        updating_config = updating_config._value
    if (
        not isinstance(updating_config, nip.elements.Args)
        or not updating_config._is_dict()
    ):
        raise TypeError("Flatten updating config should be just a dict.")
    for key, value in updating_config:
        base_config[key] = value
    base_config._get_root()._update_parents()
    return base_config


def _update(base_config: "nip.elements.Node", updating_config: "nip.elements.Node"):
    if isinstance(
        base_config,
        (
            nip.elements.Document,
            nip.elements.Link,
            nip.elements.LinkCreation,
            nip.elements.Tag,
        ),
    ):  # step into
        base_config._value = _update(base_config._value, updating_config)
        return base_config
    if not isinstance(base_config, nip.elements.Args) or not isinstance(
        updating_config, nip.elements.Args
    ):  # leaf in any conf
        return updating_config
    for key, value in updating_config:  # both args and kwargs
        if key in base_config:
            base_config[key] = _update(base_config[key], value)
        else:
            base_config[key] = value  # adding args via next index
    return base_config


def update(
    base_config: "nip.elements.Node", updating_config: "nip.elements.Node"
) -> "nip.elements.Node":  # mb: merge
    """Updates base_config with other_config recursively traversing both trees. Inplace.

    Notes
    -----
    Any leaf Node of base_config will be overwritten by corresponding Node of updating_config.
    Any Node of updating_config that is not dict or list will overwrite corresponding Node of base_config.
    It is not possible to overwrite dict nodes atm, since they will be simply updated.

    Parameters
    ----------
    base_config : Node
        Basic config Node to be updated.
    updating_config : Node
        Config that will be used to update the basic one.

    Returns
    -------
    updated_config : Node
        Updated config Node.
    """
    if isinstance(updating_config, str):
        updating_config = parse(updating_config)
    if isinstance(updating_config, nip.elements.Document):
        updating_config = updating_config._value
    base_config = _update(base_config, updating_config)
    base_config._get_root()._update_parents()
    return base_config
