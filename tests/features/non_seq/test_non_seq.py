import pytest
import nip.non_seq_constructor

from nip import load
from nip.non_seq_constructor import NonSequentialConstructorError


def test_simple_non_seq():
    output = load("features/non_seq/configs/simple_non_seq.nip", nonsequential=True)
    expected = {
        'main': {
            'just': 'some',
            'values': 123
        },
        'other_main': {
            'just': 'some',
            'values': 123
        },
    }
    assert output == expected


def test_harder_non_seq():
    output = load("features/non_seq/configs/harder_non_seq.nip", nonsequential=True)
    expected = {
        'main': [
            'some',
            123,
            {
                'items': [4, 5, 6, 7]
            }
        ],
        'other_main': {
            'interesting': [4, 5, 6, 7],
            'here_is_the_ll': 6
        }
    }
    assert output == expected


def test_part_harder_non_seq():
    config = nip.parse("features/non_seq/configs/harder_non_seq.nip")
    constructor = nip.non_seq_constructor.NonSequentialConstructor(config)
    expected = {
        'interesting': [4, 5, 6, 7],
        'here_is_the_ll': 6
    }
    output = constructor.construct(config['other_main'])
    assert output == expected

    output = config['other_main']._construct(constructor)
    assert output == expected

    output = nip.construct(config['other_main'])
    assert output == expected


def test_recursive_non_seq():
    with pytest.raises(NonSequentialConstructorError, match="Recursive construction"):
        load("features/non_seq/configs/recursive_non_seq.nip", nonsequential=True)


def test_inline_non_seq():
    output = nip.load("features/non_seq/configs/inline_non_seq.nip", nonsequential=True)
    expected = {
        'main': [
            "some f string with var 12",
            123,
            {
                'items': [4, 5, 6, 12]
            }
        ],
        'other_main': {
            'iteresting': [4, 5, 6, 12],
            'here_is_the_ll': 6
        },
        'inline_python': 2.5,
        't': 5
    }
    assert output == expected
