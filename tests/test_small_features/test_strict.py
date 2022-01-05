from nip import parse, construct, wrap_module, load, run
from nip.constructor import Constructor

wrap_module("builders")

# node = parse("configs/strict_config.nip", strict=True)
# constructor = Constructor(strict_typing=True)
# print(constructor.construct(node))

print(load("../features/strict/configs/strict_config.nip", strict=True))
run("../features/run/configs/run.nip", strict=False)