import symtable

import nip.elements
from .constructor import Constructor
from typing import Dict, Any


class NonSequentialConstructor(Constructor):
    def __init__(
        self,
        base_config: "nip.elements.Node",
        ignore_rewriting=False,
        load_builders=True,
        strict_typing=False,
    ):
        super().__init__(ignore_rewriting, load_builders, strict_typing)
        self.links = {}  # name -> node
        self._find_links(base_config)
        self.constructed_nodes = {}  # node -> obj  # store here because of gc
        self.in_progress = set()

    def _find_links(self, node: "nip.elements.Node"):
        if isinstance(node, nip.elements.LinkCreation):
            assert node._name not in self.links, "Redefined link."
            self.links[node._name] = node
        if isinstance(node, nip.elements.Args):
            for key, sub_node in node:
                self._find_links(sub_node)
        if isinstance(node._value, nip.elements.Node):
            self._find_links(node._value)

    def __contains__(self, item):
        assert isinstance(item, (str, nip.elements.Node))
        if isinstance(item, str):
            return item in self.links
        return id(item) in self.constructed_nodes

    def __setitem__(self, key, value):
        if isinstance(key, str):  # we already found all the links for nonseq
            return
        assert isinstance(key, nip.elements.Node)
        self.constructed_nodes[id(key)] = value

    def __getitem__(self, item):
        if isinstance(item, str):
            if item not in self.links:
                raise NonSequentialConstructorError(f"Unresolved reference '{item}'")  # mb: link, ref or var
            item = self.links[item]
        assert isinstance(item, nip.elements.Node)
        if id(item) in self.in_progress:
            raise NonSequentialConstructorError(f"Recursive construction of '{item}'.")
        if id(item) not in self.constructed_nodes:
            self.in_progress.add(id(item))
            self.constructed_nodes[id(item)] = item._construct(self)
            self.in_progress.remove(id(item))
        return self.constructed_nodes[id(item)]


class NonSequentialConstructorError(Exception):
    def __init__(self, massage):
        self.massage = massage

    def __str__(self):
        return self.massage


def preload_vars(code, constructor: Constructor):
    if not isinstance(constructor, NonSequentialConstructor):
        return
    table = symtable.symtable(code, "string", "exec")
    for name in constructor.links:
        try:
            if table.lookup(name).is_global():
                constructor.links[name]
        except KeyError:
            pass
