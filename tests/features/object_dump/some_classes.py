from typing import List
from nip import nip


class A:
    def question(self):
        return "Ultimate Question of Life, the Universe, and Everything"


class B:
    def answer(self):
        return 42


@nip("Complex")
class BigComplexClass(A, B):
    def __init__(self, data, childs: List):
        self.data = data
        self.childs = childs

    def __nip__(self):
        return [self.data, self.childs]


@nip("Small")
class SmallButValuableClass:
    def __init__(self, name):
        self.just_name = name

    def __nip__(self):
        return self.just_name


class NoDefaultDumper:
    def __init__(self, name, value):
        self.name = name
        self.value = value
