def test_base():
    from nip import dump, load
    obj = {
        'first': 1,
        'second': '2'
    }
    dump('features/object_dump/dumps/obj.nip', obj)
    assert load('features/object_dump/dumps/obj.nip') == obj


def test_complex():
    from some_classes import BigComplexClass, SmallButValuableClass
    from nip import dump, load

    small_obj_1 = SmallButValuableClass("Popo")
    small_obj_2 = SmallButValuableClass("Pepe")
    big_obj = BigComplexClass({'dict': 'with', 'some': 'data', 'number': 42},
                              childs=[small_obj_1, small_obj_2])
    dump("features/object_dump/dumps/complex.nip", big_obj)
    result = load("features/object_dump/dumps/complex.nip")
    assert result.data == {'dict': 'with', 'some': 'data', 'number': 42}
    assert isinstance(result.childs[0], SmallButValuableClass) and \
           result.childs[0].just_name == 'Popo'
    assert isinstance(result.childs[1], SmallButValuableClass) and \
           result.childs[1].just_name == 'Pepe'
