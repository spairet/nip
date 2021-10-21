from nip import parse, construct, wrap_module
from nip.constructor import Constructor

wrap_module("builders")

node = parse("configs/strict_config.nip", strict=True)
constructor = Constructor(strict_typing=True)
print(constructor.construct(node))