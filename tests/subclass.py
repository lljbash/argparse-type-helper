import argparse

from argparse_type_helper import Name, register_targs, targ, targs


@targs
class ArgsA:
    a: int = targ(Name)
    """it is a"""


@targs
class ArgsB(ArgsA):
    b: str = targ(Name)
    """it is b"""


@targs
class MyArgs(ArgsB):
    c: float = targ(Name)
    """it is c"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    register_targs(parser, MyArgs, verbose=True)
    parser.print_help()
