def test_fstrings():
    pass


def test_iter_fstrings():
    from nip import load
    iter_values = [1, 2, 3]
    for config, value in zip(load("features/fstrings/configs/iter_fstrings.nip"), iter_values):
        assert 'main' in config
        assert config['main']['first'] == value
        assert config['main']['name'] == f"name_{value}"


