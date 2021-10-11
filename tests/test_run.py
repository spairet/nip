from nip import run, wrap_module

wrap_module("builders")

run("configs/run.nip", verbose=True)

run("configs/run_config_param.nip", config_parameter="config")