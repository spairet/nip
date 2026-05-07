from typing import List, Callable

from nip.elements import Nothing

# mb: depending on config
# mb: make Nothing a singleton
# NOTHING = None
# IS_NOTHING = lambda obj, None: obj is None

NOTHING = Nothing()


def IS_NOTHING(obj):
    return isinstance(obj, Nothing)


def nothing_comparison(first, second):
    return IS_NOTHING(first) and IS_NOTHING(second)


def deep_conditioned_compare(first: object, second: object, conditions: List[Callable] = ()):
    if not (isinstance(second, first.__class__) or isinstance(first, second.__class__)):
        return False
    if isinstance(first, (list, tuple)) and isinstance(second, (list, tuple)):
        if len(first) != len(second):
            return False
        return all(
            [
                deep_conditioned_compare(first_item, second_item, conditions)
                for first_item, second_item in zip(first, second)
            ]
        )
    if isinstance(first, dict) and isinstance(second, dict):
        if len(first) != len(second):
            return False
        for key in first:
            if key not in second:
                return False
            if not deep_conditioned_compare(first[key], second[key], conditions):
                return False
    for cond in conditions:
        if cond(first, second):
            return True
    return first == second
