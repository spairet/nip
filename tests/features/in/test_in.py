import nip
import pytest


def test_in():
    config = nip.parse("features/in/configs/include.nip")
    assert "some_parameter" in config
    assert "some_param" not in config
    assert "some_parameter.deep_param" in config
    assert "some_parameter.deep_parameter" not in config
    assert "deep_param" in config.some_parameter
    assert "anything" not in config.some_parameter.deep_param
    assert 0 in config.complex_node
    assert 1 in config.complex_node
    assert 2 not in config.complex_node
    assert "third" in config.complex_node
    # assert "complex_node.0" in config  # mb: combined str and index access not supported
    assert "complex_node.third" in config
    with pytest.raises(NotImplementedError):
        "other_param.deep_param" in config


def test_ambiguity():
    config = nip.parse("features/in/configs/ambiguity.nip")
    assert "a.b" in config
    assert "b" in config.a
    assert "a.c" in config
    assert "c" not in config.a
