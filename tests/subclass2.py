import argparse

from argparse_type_helper import (
    Name,
    register_targs,
    targ,
    targs,
)


@targs
class ArgsA:
    a: str = targ(Name)


@targs
class ArgsB(ArgsA):
    b: int = targ(Name)


@targs
class ArgsC(ArgsA):
    c: float = targ(Name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    register_targs(parser, ArgsB, verbose=True)
    register_targs(parser, ArgsC, verbose=True)
