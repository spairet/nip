class SimpleClass:
    def __init__(self, name: str, value: int):
        self.name = name
        self.value = value


def simple_class_printer(obj: SimpleClass):
    print(f"Name is: {obj.name}")
    return obj.value * 3
