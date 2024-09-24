def test_config():
    from nip import parse, dump

    config = parse("features/modification/configs/config.nip")
    config["main"]["first"] = "modified_value"
    config["main"]["second"] = (1, 3)
    dump("features/modification/dumps/config.nip", config)


def test_object():
    from nip import parse, dump, load, nip
    from utils.builders import Note

    config = parse("features/modification/configs/object_config.nip")
    config[1] = Note("interesting note", "new comment")
    dump("features/modification/dumps/object_config.nip", config)

    nip(Note)
    result = load("features/modification/dumps/object_config.nip")
    assert result[0] == Note("first note", "nothing special here")
    assert result[1] == Note("interesting note", "new comment")


def test_object_2():
    from nip import parse, dump, load, nip
    from utils.builders import Note

    config = parse("features/modification/configs/object_config.nip")
    config[1]["comment"] = "what a comment!"
    dump("features/modification/dumps/object_config_2.nip", config)

    nip(Note)
    result = load("features/modification/dumps/object_config_2.nip")
    assert result[0] == Note("first note", "nothing special here")
    assert result[1] == Note("interesting note", "what a comment!")
