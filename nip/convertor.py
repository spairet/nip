from typing import Dict, Optional, Callable, Union

from nip.elements import Element, Args, Tag, Value
from nip.constructor import global_builders

global_convertors = {}


class Convertor:
    def __init__(self, load_globals: bool = True):
        self.convertors = {}
        if load_globals:
            self._load_globals()

    def convert(self, obj: object) -> Element:
        class_name = type(obj).__name__
        if class_name in self.convertors:
            tag, convertor = self.convertors[class_name]
            return Tag(tag, self.convert(convertor(obj)))

        if hasattr(obj, "__nip__"):
            return Tag(class_name, self.convert(obj.__nip__()))

        if isinstance(obj, dict):
            kwargs = {}
            for key, value in obj.items():
                kwargs[key] = self.convert(value)
            return Args('args', ([], kwargs))

        if isinstance(obj, (list, tuple)):
            return Args('args', ([self.convert(value) for value in obj], {}))

        if isinstance(obj, (int, float, str, bool)):
            return Value('value', obj)

        raise ConvertorError(obj, "No convertor specified for this class")

    def register(self, class_: Union[type, str], func: Callable, tag: Optional[str] = None):
        if isinstance(class_, type):
            class_name = class_.__name__
        elif isinstance(class_, str):
            class_name = class_
        else:
            raise TypeError("Expected type or str as class_ argument")
        if tag is None:
            for builder_tag, builder in global_builders.items:
                if isinstance(builder, type) and builder.__class__.__name__ == class_name:
                    tag = builder_tag
            tag = tag or class_name
        self.convertors[class_name] = (tag, func)

    def _load_globals(self):
        self.convertors.update(global_convertors)


class ConvertorError(Exception):
    def __init__(self, obj, message: str):
        self.class_name = obj.__class__.__name__
        self.obj = obj
        self.message = message

    def __str__(self):
        return f"Unable to convert object {self.obj} of class {self.class_name} to nip: " \
               f"{self.message}"


def pin(tag: str):
    assert tag is None or len(tag) > 0, "name should be nonempty"

    def _(item):
        global_convertors[tag] = item
        return item

    return _
