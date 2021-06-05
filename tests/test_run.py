from nip import run, wrap_module

wrap_module("builders")

run("configs/run_config.yaml", verbose=True)
