import argparse
import sys
from typing import Never

from argparse_type_helper import Flag, Name, extract_targs, register_targs, targ, targs


# Define your typed arguments as a targ class
@targs
class MyArgs:
    # This example will show the common usage of targ.

    positional: str = targ(Name, help="A positional argument (positional).")
    custom_name_pos: str = targ(
        "my_positional", help="A custom named positional argument."
    )

    optional: str = targ(Flag, help="An optional argument (--optional).")
    optional_dash: str = targ(
        Flag, help="underscore is replaced with dash (--optional-dash)."
    )
    optional_short: str = targ(
        Flag("-s"), help="You can also add a short name (-s, --optional-short)."
    )
    custom_name_opt: str = targ(
        "--my-optional",
        help="A custom named optional argument.",
    )
    custom_name_opt_short: str = targ(
        ("-c", "--my-short-optional"),
        help="A custom named optional argument with a short name. (note the tuple)",
    )

    options: list[str] = targ(
        Flag,
        action="extend",
        nargs="+",
        default=[],
        help="All options (`help`, `action`, `nargs`, etc.) are the same as argparse.",
    )
    choices: str = targ(
        Flag,
        choices=["option1", "option2", "option3"],
        help="Another example argument with choices.",
    )
    flag: bool = targ(
        Flag("-d"), action="store_true", help="Another example boolean flag."
    )

    default_type: int = targ(
        Flag,
        default=42,
        help="if type is not specified, it defaults to the type hint. (type=int in this case)",
    )
    custom_type: float = targ(
        Flag,
        type=lambda x: round(float(x), 1),
        default=3.14,
        help="You can also specify a custom type",
    )

    docstring_as_help: str = targ(Flag, default="default value")
    """
    If you don't specify a help, it will use the docstring as the help text.
    This is useful for documentation purposes.
    Your LSP will also pick this up.
    """


# You can register the targs with a custom parser
class MyParser(argparse.ArgumentParser):
    def error(self, message: str) -> Never:
        sys.stderr.write("error: %s\n" % message)
        self.print_help()
        sys.exit(2)


if __name__ == "__main__":
    # Create a parser
    parser = MyParser(description="Process some data arguments.")

    # Register the targs with the parser
    # verbose=True will print the registered arguments
    register_targs(parser, MyArgs, verbose=True)

    # Hybrid usage example
    parser.add_argument("--version", action="version", version="MyArgs 1.0.0")

    # Parse the arguments
    args = parser.parse_args()

    # Extract the targs from the parsed arguments
    my_args = extract_targs(args, MyArgs)
    print(f"Parsed arguments: {my_args}")
