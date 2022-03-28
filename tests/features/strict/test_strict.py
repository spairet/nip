import pytest

from nip.constructor import ConstructorError
from nip.parser import ParserError


def test_correct_strict():
    import builders
    from nip import load
    result = load("features/strict/configs/strict_func_types_correct.nip", strict=True)
    assert isinstance(result['simple'], builders.SimpleClass) and result['f'] == 5


def test_strict_1():
    import builders
    from nip import load
    with pytest.raises(ConstructorError,
                       match="type of c must be int; got str instead"):
        load("features/strict/configs/strict_func_types_1.nip", strict=True)


def test_strict_2():
    import builders
    from nip import load
    with pytest.raises(ConstructorError,
                       match="type of a must be int; got builders.SimpleClass instead"):
        load("features/strict/configs/strict_func_types_2.nip", strict=True)


def test_strict_3():
    import builders
    from nip import load
    with pytest.raises(ConstructorError,
                       match="type of name must be str; got int instead"):
        load("features/strict/configs/strict_func_types_3.nip", strict=True)


def test_strict_names():
    import builders
    from nip import load
    with pytest.raises(ParserError,
                       match="4:3: Dict key overwriting is forbidden "
                             "in `strict` mode. Overwritten key: 'some_name'."):
        load("features/strict/configs/double_names.nip", strict=True)


# def test_wrong_args():
#     with pytest.warns(warnings.WarningMessage,
#                       math="Typing mismatch while constructing {self.name}"):
