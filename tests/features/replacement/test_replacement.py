import nip
from utils import builders


def test_inter_run():
    result = nip.load("features/replacement/configs/config.nip")
    assert isinstance(result["object"], builders.SimpleClass) and result["object"].name == "abra"
    assert result["value"] == 123
    assert result["inserted"]["some"]["deep"]["key"] == "secret-key"
    assert result["inserted"]["some"]["deep"]["value"] == 123
    assert result["inserted"]["some"]["deep"]["object"] == result["object"]
