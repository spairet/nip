#from nip import parse, construct, load, dump
from nip.constructor import  global_calls
from nip.dumper import Dumper
import builders

#obj = load("configs/call_wrapper_config.yaml")
obj = builders.SimpleClass(name="abra")
print(global_calls)
print(obj)

print(global_calls[obj])

dumper = Dumper
#dumper.dump(obj)
# c = parse("configs/call_wrapper_config.yaml")
# print(dump("config_dumps/tag_dump.yaml", c))