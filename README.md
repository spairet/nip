# NIP
Nice Iterable Parser

Short documentation can be found in [doc directory](https://github.com/spairet/nip/tree/pypi/doc)


Call for Contributions
--
Everything currently presented in nip and future plans are discussable. Feel free to suggest any ideas for future updates or PRs.

If you find any bugs or unexpected behaviour please report it with an attached config file.


#### Future plans for realization

1. Multiline strings with """ operator (currently only single string lines are supported)
2. Auto-wrapping everything in locals() with @nip
5. \_\_init\_\_ wrapper for convenient object dumping (currently object dumping is not supported. only config dumping)
6. Multi document parsing.
8. List node as an iterable node (currently only simple python-lists are supported for iterators)
9. python code inserts with in-scope
10. strict parser: check typing and reloading dict keys