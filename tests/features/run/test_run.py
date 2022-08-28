def test_simple_run():
    from nip import run, nip
    import class_example
    nip(class_example)
    value = run("features/run/configs/run.nip", func=class_example.simple_class_printer,
                verbose=False)
    assert value == 42


def test_inter_run():
    from nip import run, nip
    import builders
    nip(builders)
    value, dumped = run("features/run/configs/run_config_param.nip",
                        func=builders.main,
                        config_parameter="config",
                        verbose=False)
    assert value == "some parameter value from main with love"
    assert dumped == '---\nparam: "some parameter value"'
    '--- \nparam: "some parameter value"'

# mb: test verbose?
