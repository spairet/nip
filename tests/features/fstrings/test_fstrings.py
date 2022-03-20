def test_implicit():
    from nip import load
    res = load("features/fstrings/configs/fstrings.nip")
    expected = {
        'first_name': "Ilya",
        'second_name': "Vasiliev",
        'call': "Your highness the great and beautiful lord, Ilya Vasiliev",
        'implicit': "{first_name} the {second_name}"  # implicit fstrings are not supported
    }
    assert res == expected


def test_iter_fstrings():
    from nip import load
    iter_values = [1, 2, 3]
    for config, value in zip(load("features/fstrings/configs/iter_fstrings.nip"), iter_values):
        assert 'main' in config
        assert config['main']['first'] == value
        assert config['main']['name'] == f"name_{value}"


