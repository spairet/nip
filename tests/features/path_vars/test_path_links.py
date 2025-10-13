from nip import load


def test_path_links():
    output = load("features/path_vars/configs/path_links.nip")
    expected = {
        "main": ["some", 123, {"items": [4, 5, 6, 7]}],
        "other_main": {"hmm": [4, 5, 6, 7], "ll": 6},
    }
    assert output == expected
    assert output["main"][2]["items"] is output["other_main"]["hmm"]


def test_inline_paths():
    output = load("features/path_vars/configs/inline_paths.nip", as_dictobj=True)
    from utils import builders

    print(output.func)
    assert output.func == 14
    assert isinstance(output.obj, builders.MyClass)
    assert output.obj.name == "pam"
    assert output["obj"].f == [1, 2, 3]
    assert output["clones"].obj is output.obj
    assert output.clones.f is output.obj.f
