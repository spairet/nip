import pytest


def test_args():
    from nip import load, wrap_module
    wrap_module("builders")

    result = load("features/args/configs/args_config.nip")
    expected_result = {
        'main': (
            ['arg1', 321],
            {'one': 1,
             'two': 2,
             'three': 'three'}),
        'other': {
            'four': 4,
            'ff': 'five'
        },
        'func': None
    }

    assert result == expected_result
