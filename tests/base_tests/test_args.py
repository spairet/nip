import pytest


def test_args():
    from nip import parse, load, wrap_module
    wrap_module("builders")
    res = parse("configs/args_config.yaml")
    print(res.to_python())

    result = load("configs/args_config.yaml")
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
