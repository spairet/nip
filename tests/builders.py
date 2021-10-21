from nip import nip, dumps


@nip
class SimpleClass:
    def __init__(self, name):
        self.name = name

    @nip("print_method")
    def print(self):
        print(self.name)
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
    print(param)
    print(dumps(config))