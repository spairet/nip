def test_numpy():
    import numpy as np
    from nip import load, wrap_module, nip

    nip(np, wrap_builtins=True)
    result = load('/configs/numpy.nip')
    assert len(result.keys()) and 'array' in result
    assert np.all(result['array'] == np.zeros((2, 3, 4)))


def test_simple_class():
    import builders
    from nip import load
    result = load("/configs/simple_tag_config.nip")
    assert 'obj' in result
    assert isinstance(result['obj'], builders.SimpleClass)
    assert result['obj'].name == 'Hello World!'


def test_simple_func():
    import builders
    from nip import load
    result = load("/configs/simple_tag_config.nip")
    assert 'func' in result
    assert result['func'] == 7


def test_one_line_func():
    import builders
    from nip import load
    result = load("/configs/simple_tag_config.nip")
    assert 'single' in result
    assert result['single'] == 1


def test_no_args():
    import builders
    from nip import load
    try:
        load("/configs/no_args_func_error.nip")
    except TypeError as e:
        pass
