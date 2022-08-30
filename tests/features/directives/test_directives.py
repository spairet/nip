import nip


def test_simple_load_directive():
    result = nip.parse("features/directives/configs/directive_config.nip")
    expected_result = nip.parse("features/directives/configs/expected_config.nip")
    assert nip.construct(result) == nip.construct(expected_result)
    # mb: not true comparison
