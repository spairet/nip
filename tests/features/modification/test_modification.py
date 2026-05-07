def test_config(tmp_path):
    from nip import parse, dump, load

    config = parse("features/modification/configs/config.nip")
    config["main"]["first"] = "modified_value"
    config["main.second"] = (1, 3)
    config.main.third = "third_value"
    dump_path = tmp_path / "config.nip"
    dump(str(dump_path), config)
    data = load(str(dump_path))
    assert data["main"]["first"] == "modified_value"
    assert data["main"]["second"] == [
        1,
        3,
    ]  # not tuple actually... mb: make is consistent
    assert data["main"]["third"] == "third_value"
    # mb: make this test more complex with deep comparison with result


def test_object(tmp_path):
    from nip import parse, dump, load, nip
    from utils.builders import Note

    config = parse("features/modification/configs/object_config.nip")
    config[1] = Note("interesting note", "new comment")
    dump_path = tmp_path / "object_config.nip"
    dump(str(dump_path), config)

    nip(Note)
    result = load(str(dump_path))
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
