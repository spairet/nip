from .constructor import Constructor, ConstructorError
from .elements import Element, Args, LinkCreation


class VarsDict:
    def __init__(self, base_config, constructor):
        self.base_config = base_config
        self.constructor = constructor
        self.links = {}
        self.vars = {}
        self.in_progress = set()
        self._find_links(base_config)

    def _find_links(self, node: Element):
        if isinstance(node, LinkCreation):
            assert node.name not in self.links, "Redefined link."
            self.links[node.name] = node
        if isinstance(node, Args):
            for sub_node in node:
                self._find_links(sub_node)
        if isinstance(node.value, Element):
            self._find_links(node.value)

    def __getitem__(self, item):
        if item in self.vars:
            return self.vars[item]
        if item not in self.links:
            raise NonSequentialConstructorError(f"Unresolved link '{item}'")
        if item in self.in_progress:
            raise NonSequentialConstructorError(f"Recursive construction of '{item}'.")
        self.in_progress.add(item)
        self.links[item].construct(self.constructor)
        self.in_progress.remove(item)
        return self.vars[item]

    def __setitem__(self, key, value):
        self.vars[key] = value


class NonSequentialConstructor(Constructor):
    def __init__(self, base_config: Element, ignore_rewriting=False, load_builders=True,
                 strict_typing=False):
        super().__init__(ignore_rewriting, load_builders, strict_typing)
        self.vars = VarsDict(base_config, self)


class NonSequentialConstructorError(Exception):
    def __init__(self, massage):
        self.massage = massage

    def __str__(self):
        return self.massage
