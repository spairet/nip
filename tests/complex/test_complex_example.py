from utils.test_utils import NOTHING, deep_conditioned_compare


def config_replacer(config, name):
    config["other"]["list"][1]["sdf"][0]["sfds"]["abra"] = name


def test_config():
    from utils import builders
    from nip import load, nip

    nip(builders)
    result_iter = load("complex/configs/config.nip")
    expected_result = {
        "main": {
            "first": {"in1": "11", "in2": -12.5},
            "second": [1, 2, 3],
            "third": {"a": "123", "123": "qweqwe"},
            "inline_tuple": (17, 32, 42, "name"),
        },
        "other": {
            "main.other": {
                "first": {"in1": "11", "in2": -12.5},
                "second": [1, 2, 3],
                "third": {"a": "123", "123": "qweqwe"},
                "inline_tuple": (17, 32, 42, "name"),
            },
            "list": (
                ["this is float value -12.5", True, NOTHING],
                {"sdf": [{"sfds": {"abra": None}}, ["nested value", "one more", {"nested": "dict"}]]},
            ),
        },
    }

    iter_values = ["cadabra", "ababra", "avocado"]
    for result, iter_value in zip(result_iter, iter_values):
        config_replacer(expected_result, iter_value)
        assert deep_conditioned_compare(expected_result, result)
