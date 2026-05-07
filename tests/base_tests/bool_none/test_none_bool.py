from utils.test_utils import deep_conditioned_compare


def test_bool_none():
    from nip import load

    result = load("base_tests/bool_none/configs/bool_none_config.nip")
    expected = {
        "this_is_none": None,
        "also_none": None,
        "booleans": [True, True, True],
        "other_booleans": [False, False, False],
    }

    assert expected == result
    assert deep_conditioned_compare(expected, result)


def test_bool_none_dump(tmp_path):
    import nip

    obj = {
        "this_is_none": None,
        "also_none": None,
        "booleans": [True, True, True],
        "other_booleans": [False, False, False],
    }
    dump_path = tmp_path / "bool_none.nip"
    nip.dump(str(dump_path), obj)
    result = nip.load(str(dump_path))
    assert obj == result
    assert deep_conditioned_compare(obj, result)
