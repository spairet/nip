from nip import load, wrap_module


def main():
    wrap_module("builders")
    # alternative variant:
    # import builders
    # wrap_module(builders)

    res = load("configs/auto_wrap_config.yaml")
    print(res['class'])
    print(res['func'])


if __name__ == "__main__":
    main()
