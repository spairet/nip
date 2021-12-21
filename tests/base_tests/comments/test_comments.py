def test_comment():
    import builders  # mb: from . import builders
    from nip import load
    res = load("base_tests/comments/configs/inline_comment.nip")
    assert isinstance(res, dict)
    assert 'main' in res
    assert res['main'] == {
        'number': 1,
        'float': 0.314159265,
        'modern_float': 3e-5,
        'string': 'this is some string 123^& !',
        'quated_string': "  !&and another one string 123 'qwe' @#!*^@%# "
    }
    assert 'other' in res
    assert res['other'] == res['main']
    assert 'obj' in res
    assert isinstance(res['obj'], builders.SimpleClass)
    assert res['obj'].name == "Ilya"
