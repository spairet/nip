def test_basics():
    from nip import parse
    config = parse("features/flatten/configs/simple.nip")
    expected_dict = {
        'main.number': 1,
        'main.string': 'qwe',
        'something_more.float': 0.123,
        'something_more.bool': True,
        'list.0': 'some string',
        'list.1.0': 123
    }
    assert config.flatten() == expected_dict


def test_complex():
    from nip import parse
    config = parse("features/flatten/configs/complex.nip")
    expected_result = {
        'main.first.in1': '11',
        'main.first.in2': -12.5,
        'main.second.0': 1,
        'main.second.1': 2,
        'main.second.2': 3,
        'main.third.a': '123',
        'main.third.123': 'qweqwe',
        'other.main.other': 'nil',
        'other.list.0': 'f"this is float value {float}"',
        'other.list.1': True,
        'other.list.2': None,
        'other.list.sdf.0.sfds.abra': 'cadabra',
        'other.list.sdf.1.0': 'nested value',
        'other.list.sdf.1.1': 'one more',
        'other.list.sdf.1.2.nested': 'dict',
    }

    first_config = next(config)
    flattened = first_config.flatten()
    assert len(expected_result) == len(flattened)
    for key, value in expected_result.items():
        assert key in flattened
        assert flattened[key] == value
