from nip import load, parse, dump, construct

import builders

# Load config file as python object:
result = load("configs/simple_tag_config.yaml")
result['obj'].print()
print(result['func'])


# Load only part of config:
tree = parse("configs/simple_tag_config.yaml")
result = construct(tree['func'])
print(result)


# Parsing and saving config with iterators:
configs = parse("configs/config.yaml")
for config in configs:
    # get some staff from the deep
    filename = "config_dumps/" + config['other']['list'][2]['abra'].to_python() + ".yaml"
    print("Saving: ", filename)
    dump(filename, config)


# You can always convert your parsed config to python without constructing:
tree = parse("configs/simple_tag_config.yaml")
print(tree.to_python())

configs = next(parse("configs/config.yaml"))  # get first config
print(configs['other'].to_python())


# Iterate over objects Cartesian product of config iterators:
objects = load("configs/iter_config.yaml")
for obj in objects:
    print(obj)