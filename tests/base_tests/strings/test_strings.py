def test_different_strings():
    from nip import load
    result = load("base_tests/strings/configs/long_strings_config.nip")
    expected = {
        'double_quote_string': 'asdvjhdbvkjdhfbv',
        'single_quote_string': 'vfduds84l8yv8hvdln4uk',
        'no_quote_abc_string': 'vdfvsbdfvklurjflr',
        'no_quote_1a_string': '12d123fhfl494fhfnvnv84lih5'
    }
    assert expected == result


if __name__ == "__main__":
    test_different_strings()
