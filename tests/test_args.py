from nip import parse, load, wrap_module
wrap_module("builders")

res = parse("configs/args_config.yaml")
print(res.to_python())

print(load("configs/args_config.yaml"))