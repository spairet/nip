import numpy as np
from nip import load, nip


@nip
def load_numpy(_):
    return np

res = load("../features/inline/configs/inline_config.nip")
print(res['array_3'])
