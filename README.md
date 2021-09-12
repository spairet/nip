# NIP
Nice Iterable Parser

User guide can be found in [doc directory](https://github.com/spairet/nip/tree/main/doc)


Installation
--

``` sh
$ pip install nip-config
```

Call for Contributions
--
Everything currently presented in nip and future plans are discussable. Feel free to suggest any ideas for future updates or PRs.

If you find any bugs or unexpected behaviour please report it with an attached config file.


#### To realize

- [ ] Multiline strings with """ operator (currently only single string lines are supported)
- [x] Module auto-wrapping everything in locals() with @nip
- [ ] \_\_init\_\_ wrapper for convenient object dumping (currently object dumping is not supported. only config dumping)
- [ ] Multi document parsing.
- [ ] List node as an iterable node (currently only simple python-lists are supported for iterators)
- [x] python code inserts with in-scope \check
- [ ] strict parser: check typing and reloading dict keys
