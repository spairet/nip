from nip import load
from nip.dict import DictObject


def test_dictobj_list():
    output = load("features/dictobj/configs/dictobj.nip", as_dictobj=True)
    print(output)
    assert isinstance(output, DictObject)
    assert isinstance(output.main, list)
    assert isinstance(output.other_main, DictObject)

    output = load("features/dictobj/configs/dictobj.nip", as_dictobj=False)
    assert not isinstance(output, DictObject)
    assert isinstance(output, dict)
    assert not isinstance(output["other_main"], DictObject)

    output = load("features/dictobj/configs/dictobj_list.nip", as_dictobj=True)
    assert isinstance(output, list)
    assert isinstance(output[0], DictObject)
    assert isinstance(output[1], DictObject)

    output = load("features/dictobj/configs/dictobj_list.nip", as_dictobj=False)
    assert isinstance(output, list)
    assert not isinstance(output[0], DictObject)
    assert not isinstance(output[1], DictObject)
