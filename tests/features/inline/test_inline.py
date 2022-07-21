import numpy as np
from nip import load, nip


@nip
def load_numpy():
    return np


def test_inline():
    np.random.seed(42)
    a = np.random.random((3, 4))
    b = np.ones((3, 4)) * 5
    c = a + b
    np.random.seed(42)
    res = load("features/inline/configs/inline_config.nip")

    assert res['main'] == 'Hello World!'
    assert res['iqwe'] == 2
    assert res['sdkichabskjchskjdhb'] == np
    assert res['other'] == "hey ho Hello World!"
    assert res['other_int'] == 7
    assert np.all(res['array'] == a)
    assert np.all(res['array_2'] == b)
    assert np.all(res['array_3'] == c)
