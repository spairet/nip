from nip import load, parse, dump, construct

import builders

# Load config file as python object:
result = load("tags/configs/simple_tag_config.nip")
result['obj'].print()
print(result['func'])


# Load only part of config:
tree = parse("tags/configs/simple_tag_config.nip")
result = construct(tree['func'])
print(result)


# Parsing and saving config with iterators:
configs = parse("configs/config.nip")
for config in configs:
    # get some staff from the deep
    print("3: ", config['other']['list'][3])
    filename = "config_dumps/" + config['other']['list'][3]['sfds']['abra'].to_python() + ".yaml"
    print("Saving: ", filename)
    dump(filename, config)


# You can always convert your parsed config to python without constructing:
tree = parse("tags/configs/simple_tag_config.nip")
print(tree.to_python())

configs = next(parse("configs/config.nip"))  # get first config
print(configs['other'])
print(configs['other'].to_python())


# Iterate over objects Cartesian product of config iterators:
objects = load("../features/iter/configs/iter_config.yaml")
for obj in objects:
    print(obj)
