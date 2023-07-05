from nip import nip, dump_string


@nip
class SimpleClass:
    def __init__(self, name: str):
        self.name = name

    @nip("print_method")
    def print(self):
        print("My name is: ", self.name)
        return 312983


@nip("myfunc")
def MySecretFunction(a: int, b: int = 0, c: int = 0):
    return a + 2 * b + 3 * c


@nip
class MyClass:
    def __init__(self, name: str, f: object):
        self.name = name
        self.f = f

    def __str__(self):
        return f"name: {self.name}, func result: {self.f}"


class NotNipClass:
    def __init__(self, name):
        self.name = name


def NoNipFunc(name):
    print("NoYapFunc:", name)


def show(*args, **kwargs):
    print('args:', args)
    print('kwargs:', kwargs)


def main(param, config):
    print(dump_string(config))
    return param + " from main with love", dump_string(config)


@nip("def_class")
class ClassWithDefaults:
    def __init__(self, name: str = "something"):
        self.name = name


class Note:
    def __init__(self, name, comment):
        self.name = name
        self.comment = comment

    def __nip__(self):
        return self.__dict__

    def __eq__(self, other):
        return self.name == other.name and self.comment == other.comment


@nip(['first_tag', 'second_tag'])
class MultiTagClass:
    def __init__(self, name: str = ''):
        self.name = name
