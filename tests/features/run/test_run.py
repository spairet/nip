def test_simple_run():
    from nip import run, nip
    import class_example
    nip(class_example)
    value = run("features/run/configs/run.nip", func=class_example.simple_class_printer,
                verbose=True)
    assert value == 42


def test_inter_run():
    from nip import run, nip
    import builders
    nip(builders)
    run("features/run/configs/run_config_param.nip", func=builders.main, config_parameter="config")




