import argparse

from argparse_type_helper import (
    Name,
    extract_targs,
    post_init,
    register_targs,
    targ,
    targs,
)


@targs
class ArgsA:
    a: int = targ(Name)
    """it is a"""

    @post_init
    def post_a(self):
        print(f"post_init for ArgsA: {self.a}")


@targs
class ArgsB(ArgsA):
    b: str = targ(Name)
    """it is b"""

    @post_init
    def post_b(self):
        print(f"post_init for ArgsB: {self.b}")


@targs
class MyArgs(ArgsB):
    c: float = targ(Name)
    """it is c"""

    @post_init
    def post_myargs(self):
        print(f"post_init for MyArgs: {self.c}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    register_targs(parser, MyArgs, verbose=True)
    args = parser.parse_args()
    my_args = extract_targs(args, MyArgs)
    print(my_args)
