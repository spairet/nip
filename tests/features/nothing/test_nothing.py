from utils.test_utils import NOTHING, deep_conditioned_compare, nothing_comparison


def test_nothing():
    from nip import load

    result = load("features/nothing/configs/nothing.nip")
    expected_result = (
        [2, 213, {"qwe": [3, NOTHING, NOTHING, {"fgh": ([NOTHING], {"fgr": NOTHING})}]}, NOTHING],
        {"qwe": {"asd": {"dfg": NOTHING}}, "zxc": NOTHING, "fff": NOTHING},
    )
    assert deep_conditioned_compare(result, expected_result, [nothing_comparison])
