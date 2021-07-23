from nip.stream import Stream
from pathlib import Path


path = "configs/config.nip"
path = Path(path)
with path.open() as f_stream:
    string_representation = f_stream.read()

stream = Stream(string_representation)
print(stream.lines)