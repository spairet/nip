import nip
import builders


def test_class_const():
    result = nip.parse("features/class_construction/configs/class_const_config.nip")
    expected_result = nip.parse("features/class_construction/configs/class_const_config.nip")
    assert nip.construct(result) == nip.construct(expected_result)


test_class_const()