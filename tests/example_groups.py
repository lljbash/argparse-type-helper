import argparse

from argparse_type_helper import (
    Flag,
    extract_targs,
    register_targs,
    targ,
    targs,
    texclusive,
    tgroup,
)


# Use @tgroup to organize related arguments into named groups.
# Groups affect --help display and provide nested access after extraction.
@tgroup("Database Options")
class DbOptions:
    """Database connection settings"""

    host: str = targ(Flag, default="localhost")
    """Database host"""
    port: int = targ(Flag, default=5432)
    """Database port"""


# Use @texclusive to define arguments that cannot be used together.
@texclusive(required=True)
class VerbosityMode:
    verbose: bool = targ(Flag("-v"), action="store_true")
    quiet: bool = targ(Flag("-q"), action="store_true")


# Reference groups and exclusive groups via type annotations.
@targs
class MyArgs:
    db: DbOptions
    mode: VerbosityMode


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Groups and exclusive example.")
    register_targs(parser, MyArgs)

    args = parser.parse_args()
    my_args = extract_targs(args, MyArgs)

    print(f"DB: {my_args.db.host}:{my_args.db.port}")
    print(f"Verbose: {my_args.mode.verbose}, Quiet: {my_args.mode.quiet}")
