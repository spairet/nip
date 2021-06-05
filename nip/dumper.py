# Dumper for Element tree objects
from typing import Union
from pathlib import Path


class Dumper:
    def __init__(self, indent: int = 0, default_shift: int = 2, create_dirs: bool = True):
        self.indent = indent
        self.default_shift = default_shift
        self.create_dirs = create_dirs

    def dumps(self, element):
        return element.dump(self).strip()

    def dump(self, filepath: Union[str, Path], element):
        string = element.dump(self).strip()
        filepath = Path(filepath)
        if self.create_dirs:
            filepath.parent.mkdir(parents=True, exist_ok=True)
        with filepath.open("w") as f:
            f.write(string)

    def __add__(self, shift: int):
        return Dumper(self.indent + shift, self.default_shift)


class DumpError(Exception):
    pass
