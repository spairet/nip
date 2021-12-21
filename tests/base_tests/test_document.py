def test():
    from nip import load, parse
    import builders
    print(parse("configs/document.nip"))

    result = load("configs/document.nip")
    print(result)

