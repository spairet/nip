class Note:
    def __init__(self, name, comment):
        self.name = name
        self.comment = comment

    def __nip__(self):
        return self.__dict__

    def __eq__(self, other):
        return self.name == other.name and self.comment == other.comment
