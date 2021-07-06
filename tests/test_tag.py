import numpy as np
from nip import load, wrap_module, nip

nip(np, wrap_builtins=True)
print(load('configs/numpy.nip'))