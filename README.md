# NIP
Nice Iterable Parser


### Main features:
1. Simple @nip wrapper to register class or fucntion for auto constructing python object by config
2. Simple Access to config elements (e.g. config['model']) and partial config loading.
3. Any config element can be converted to python object as is: dicts and lists with to_python() method.
4. Config iterators: you are able to write iterable variables in config (e.g. path: @ ['/first', '/second', '/third']) and as a result you will get an iterator over this configs or constructed objects (using `parse` or `load` method respectively).
5. Module wrapping. With @nip you can automatically wrap everything under module.
6. `Args` element: you can unite both args and kwargs in one element for convenient object creation.


### Examples
Examples currently presented in /test directory.

Take a look at /test/test.py and /test/configs/* for understanding the functionality and interfaces of the module.


### Some differencees from yaml
1. Still not as powerfull as YAML, but has some usefull features.
2. In-line dicts needs quotes for keys (e.g. my_kwargs: {'a': 1, 'b': 2})
3. Named list items are not supported: vanilla PyYAML creates single element dict for this case which does not seems convenient. (e.g. expressions like `- item_name: 42` are not supported. List items still can be constructed with a tag)


### Future plans
1. Multiline strings with """ operator (currently only single string lines are supported)
2. Auto-wrapping everything in locals() with @nip
5. \_\_init\_\_ wrapper for convenient object dumping (currently object dumping is not supported. only config dumping)
6. Multi document parsing.
7. PyPI module
8. List node as an iterable node (currently only simple python-lists are supported for iterators)
9. python code inserts with in-scope
10. strict parser: check typing and reloading dict keys


### Feedback
Everything currently presented in nip and future plans are discussable. Feel free to suggest any ideas for future updates with Issues or PRs.

If you find any bugs or unexpected behaviour please report it with attached config file.
