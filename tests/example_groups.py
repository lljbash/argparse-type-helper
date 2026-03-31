from argparse_type_helper import (
    Flag,
    create_parser,
    extract_targs,
    targ,
    targs,
    texclusive,
    tgroup,
)


# Use @tgroup to organize related arguments into named groups.
# The docstring's first paragraph becomes the group title,
# and the rest becomes the group description.
@tgroup()
class DbOptions:
    """Database Options

    Database connection settings used by the application.
    """

    host: str = targ(Flag, default="localhost")
    """Database host"""
    port: int = targ(Flag, default=5432)
    """Database port"""


# Use @texclusive to define arguments that cannot be used together.
@texclusive(required=True)
class VerbosityMode:
    verbose: bool = targ(Flag("-v"), action="store_true")
    """Enable verbose output."""
    quiet: bool = targ(Flag("-q"), action="store_true")
    """Suppress all output."""


# Reference groups and exclusive groups via type annotations.
@targs
class MyArgs:
    """Groups and exclusive example.

    Demonstrates argument groups and mutually exclusive arguments.
    """

    db: DbOptions
    mode: VerbosityMode


if __name__ == "__main__":
    # create_parser auto-fills description from the class docstring
    parser = create_parser(MyArgs)

    args = parser.parse_args()
    my_args = extract_targs(args, MyArgs)

    print(f"DB: {my_args.db.host}:{my_args.db.port}")
    print(f"Verbose: {my_args.mode.verbose}, Quiet: {my_args.mode.quiet}")
