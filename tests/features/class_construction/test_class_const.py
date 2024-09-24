import nip
from utils import builders


def test_class_const():
    result = nip.load("features/class_construction/configs/class_const_config.nip")
    expected_result = {
        "var": 123,
        "main": {"just": "some_stuff", "simple_class": builders.SimpleClass, "def_class": builders.ClassWithDefaults},
    }
    assert result == expected_result
