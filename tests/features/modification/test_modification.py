def test_config(tmp_path):
    from nip import parse, dump, load

    config = parse("features/modification/configs/config.nip")
    config["main"]["first"]["in1"] = "modified_value"
    config["main.second"] = (1, 3)
    config.main.third = "third_value"
    dump_path = tmp_path / "config.nip"
    dump(str(dump_path), config)
    data = load(str(dump_path))
    assert data["main"]["first"]["in1"] == "modified_value"
    assert data["main"]["second"] == [
        1,
        3,
    ]  # not tuple actually... mb: make is consistent
    assert data["main"]["third"] == "third_value"
    # mb: make this test more complex with deep comparison with result


def test_config_linked(tmp_path):
    from nip import parse, dump, load

    config = parse("features/modification/configs/config.nip")
    config["main"]["first"]["in2"] = 42
    config.main.second = "qwerty"
    config.main.third = 1e-3
    data = config.construct()
    print(data)
    assert data["other"]["list"][0] == "this is float value 42"
    assert data["other"]["main"] == data["main"]
    assert data["other"]["main"]["second"] == "qwerty"
    assert data["other"]["main"]["third"] == 1e-3


def test_object(tmp_path):
    from nip import parse, dump, load, nip
    from utils.builders import Note

    config = parse("features/modification/configs/object_config.nip")
    config[1] <<= Note("interesting note", "new comment")
    dump_path = tmp_path / "object_config.nip"
    dump(dump_path, config)

    nip(Note)
    result = load(dump_path)
    assert result[0] == Note("first note", "nothing special here")
    assert result[1] == Note("interesting note", "new comment")


def test_object_2(tmp_path):
    from nip import parse, dump, load, nip
    from utils.builders import Note

    config = parse("features/modification/configs/object_config.nip")
    config[1]["comment"] = "what a comment!"
    dump_path = tmp_path / "object_config_2.nip"
    dump(str(dump_path), config)

    nip(Note)
    result = load(str(dump_path))
    assert result[0] == Note("first note", "nothing special here")
    assert result[1] == Note("interesting note", "what a comment!")
