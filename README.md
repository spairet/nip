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


#### Features and plans

- [x] Auto-wrapping everything inside module with `nip`
- [x] List node as an iterable node (currently only simple python-lists are supported for iterators)
- [x] python code inserts with in-scope
- [x] fstrings
- [X] strict: check typing and reloading dict keys
- [x] `run` function
- [x] object dumping
- [ ] Multiline strings with """ operator (questionable)
- [ ] \_\_init\_\_ wrapper for convenient object dumping (currently only config dumping. questionable)
