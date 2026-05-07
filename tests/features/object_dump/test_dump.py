def test_base(tmp_path):
    from nip import dump, load

    obj = {"first": 1, "second": "2"}
    dump_path = tmp_path / "obj.nip"
    dump(str(dump_path), obj)
    assert load(str(dump_path)) == obj


def test_complex(tmp_path):
    from some_classes import BigComplexClass, SmallButValuableClass
    from nip import dump, load

    small_obj_1 = SmallButValuableClass("Popo")
    small_obj_2 = SmallButValuableClass("Pepe")
    big_obj = BigComplexClass(
        {"dict": "with", "some": "data", "number": 42},
        childs=[small_obj_1, small_obj_2],
    )
    dump_path = tmp_path / "complex.nip"
    dump(str(dump_path), big_obj)
    result = load(str(dump_path))
    assert result.data == {"dict": "with", "some": "data", "number": 42}
    assert (
        isinstance(result.childs[0], SmallButValuableClass)
        and result.childs[0].just_name == "Popo"
    )
    assert (
        isinstance(result.childs[1], SmallButValuableClass)
        and result.childs[1].just_name == "Pepe"
    )


def test_no_default_dumper(tmp_path):
    import some_classes
    import nip

    nip.nip(some_classes, convertable=True)
    value = some_classes.BigComplexClass("data_value", [1, 2, 3])
    obj = some_classes.NoDefaultDumper("just_a_name", value=value)
    dump_path = tmp_path / "no_default.nip"
    nip.dump(str(dump_path), obj)
    result = nip.load(str(dump_path))
    assert isinstance(result, some_classes.NoDefaultDumper)
    assert isinstance(result.value, some_classes.BigComplexClass)
    assert result.value.data == "data_value" and result.value.childs == [1, 2, 3]
