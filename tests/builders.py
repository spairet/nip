from nip import nip


@nip(wrap_call=True)
class SimpleClass:
    def __init__(self, name):
        self.name = name

    @nip("print_method")
    def print(self):
        print(self.name)
        return 312983


@nip("myfunc")
def MySecretFunction(a, b=0, c=0):
    return a + 2 * b + 3 * c


@nip
class MyClass:
    def __init__(self, name, f):
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
