from nip import run, nip
import builders

nip(builders)

run("features/run/configs/run.nip", func=builders.SimpleClass.print, verbose=True)

run("features/run/configs/run_config_param.nip", func=builders.main, config_parameter="config")




