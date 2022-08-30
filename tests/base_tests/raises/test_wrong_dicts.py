import pytest

from nip import load
from nip.parser import ParserError


def test_wrong_indent():
    with pytest.raises(ParserError, match="2:3: Unexpected indent"):
        load("base_tests/raises/configs/wrong_dict_indent.nip")


def test_wrong_item():
    with pytest.raises(ParserError, match="Wrong statement"):
        load("base_tests/raises/configs/wrong_item.nip")
