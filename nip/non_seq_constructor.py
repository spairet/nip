import symtable

import nip.elements

from .constructor import Constructor, ConstructorError


class VarsDict:
    def __init__(self, constructor):
        super().__init__()
        self.constructor = constructor
        self.vars = {}
        self.in_progress = set()

    def __getitem__(self, item):
        if item in self.vars:
            return self.vars[item]
        if item not in self.constructor.links:
            raise NonSequentialConstructorError(f"Unresolved link '{item}'")
        if item in self.in_progress:
            raise NonSequentialConstructorError(f"Recursive construction of '{item}'.")
        self.in_progress.add(item)
        self.constructor.links[item].construct(self.constructor)
        self.in_progress.remove(item)
        return self.vars[item]

    def __setitem__(self, key, value):
        if key not in self.vars:  # was not constructed earlier
            self.vars[key] = value

    def __iter__(self):
        return iter(self.vars)

    def items(self):
        return self.vars.items()

    def keys(self):
        return self.vars.keys()


class NonSequentialConstructor(Constructor):
    def __init__(self, base_config: "nip.elements.Element",
                 ignore_rewriting=False,
                 load_builders=True,
                 strict_typing=False):
        super().__init__(ignore_rewriting, load_builders, strict_typing)
        self.vars = VarsDict(self)
        self.links = {}
        self._find_links(base_config)

    def _find_links(self, node: "nip.elements.Element"):
        if isinstance(node, nip.elements.LinkCreation):
            assert node.name not in self.links, "Redefined link."
            self.links[node.name] = node
        if isinstance(node, nip.elements.Args):
            for sub_node in node:
                self._find_links(sub_node)
        if isinstance(node.value, nip.elements.Element):
            self._find_links(node.value)


class NonSequentialConstructorError(Exception):
    def __init__(self, massage):
        self.massage = massage

    def __str__(self):
        return self.massage


def preload_vars(code, constructor: Constructor):
    if not isinstance(constructor, NonSequentialConstructor):
        return
    table = symtable.symtable(code, 'string', 'exec')
    for name in constructor.links:
        try:
            if table.lookup(name).is_global():
                constructor.vars[name]
        except KeyError:
            pass
