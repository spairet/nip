from nip import nip, load, parse
import builders
nip(builders)

# for cofig in parse("configs/complex_iter.nip"):
#     print(cofig)

for obj in load("configs/complex_iter.nip"):
    print(obj)
