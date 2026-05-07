import nip
from utils.builders import SimpleClass


def test_flatten_update():
    basic_config = nip.parse("features/update/configs/basic_config.nip")
    updating_config = nip.parse("features/update/configs/flatten_update.nip")
    config = nip.update_flatten(
        base_config=basic_config, updating_config=updating_config
    )
    data = config.construct()
    assert data["params"]["second"] == "updated_two"
    assert (
        isinstance(data["some_class"], SimpleClass) and data["some_class"].name == "qwe"
    )
    assert data["some"]["deep"][0]["parameter"] == 42
    assert data["some"]["deep"][1] == "new_list_param"


def test_tree_update():  # actually update is just more flexible than update_flatten
    base_config = nip.parse("features/update/configs/basic_config.nip")
    updating_config = nip.parse("features/update/configs/tree_update.nip")
    config = nip.update(base_config=base_config, updating_config=updating_config)
    data = config.construct()
    assert data["params"]["first"] == 2
    assert data["params"]["second"] == "three"
    assert (
        isinstance(data["some_class"], SimpleClass) and data["some_class"].name == "qwe"
    )
    assert data["some"]["deep"][0]["parameter"] == 42


def test_directive_base_update():
    data = nip.load("features/update/configs/directive_base_update.nip")
    assert data["params"]["first"] == 2
    assert data["params"]["second"] == "three"
    assert (
        isinstance(data["some_class"], SimpleClass) and data["some_class"].name == "qwe"
    )
    assert data["some"]["deep"][0]["parameter"] == 42


def test_directive_update():
    data = nip.load("features/update/configs/directive_update.nip")
    assert data["params"]["first"] == 2
    assert data["params"]["second"] == "three"
    assert (
        isinstance(data["some_class"], SimpleClass) and data["some_class"].name == "qwe"
    )
    assert data["some"]["deep"][0]["parameter"] == 42


def test_node_update(
    tmp_path,
):  # actually update is just more flexible than update_flatten
    config = nip.parse("features/update/configs/node_update.nip")
    dump_path = tmp_path / "node_updated_config.nip"
    nip.dump(str(dump_path), config)
    data = nip.load(str(dump_path))
    assert data["some"]["inserted_node"]["params"]["first"] == 2
    assert data["some"]["inserted_node"]["params"]["second"] == "three"
