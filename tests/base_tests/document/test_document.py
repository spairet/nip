def test_document():
    from nip import load, parse
    from nip.elements import Document
    from utils import builders

    parsed = parse("base_tests/document/configs/document.nip")
    assert isinstance(parsed, Document)
    assert parsed._name == "Strange_and_2_long_DocumentName"

    result = load("base_tests/document/configs/document.nip")
    assert isinstance(result, builders.MyClass)
    assert result.name == "some_name"
    assert result.f == 5
