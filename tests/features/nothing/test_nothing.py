from nip.elements import Nothing
from typing import List, Callable

# mb: depending on config
# mb: make Nothing a singleton
# NOTHING = None
# IS_NOTHING = lambda obj, None: obj is None

NOTHING = Nothing()
IS_NOTHING = lambda obj: isinstance(obj, Nothing)


def nothing_comparison(first, second):
    return IS_NOTHING(first) and IS_NOTHING(second)


def deep_conditioned_compare(first: object, second: object, conditions: List[Callable] = ()):
    if first.__class__ != second.__class__:  # mb: let them be subclasses of one super class
        return False
    if isinstance(first, (list, tuple)) and isinstance(second, (list, tuple)):
        if len(first) != len(second):
            return False
        return all([deep_conditioned_compare(first_item, second_item, conditions)
                    for first_item, second_item
                    in zip(first, second)])
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


def test_nothing():
    from nip import load
    result = load("features/nothing/configs/nothing.nip")
    expected_result = (
        [
            2,
            213,
            {
                'qwe': [
                    3,
                    NOTHING,
                    NOTHING,
                    {
                        'fgh': (
                            [NOTHING],
                            {'fgr': NOTHING}
                        )
                    }
                ]
            }
        ],
        {
            'qwe': {
                'asd': {
                    'dfg': NOTHING
                }
            },
            'zxc': NOTHING,
            'fff': NOTHING
        }
    )
    assert deep_conditioned_compare(result, expected_result, [nothing_comparison])
