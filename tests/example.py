import argparse
import sys
from collections.abc import Sequence
from typing import Never

from argparse_type_helper import (
    Flag,
    Name,
    create_parser,
    extract_targs,
    post_init,
    targ,
    targs,
)


# Define your typed arguments as a targ class
@targs
class MyArgs:
    """Process some data arguments.

    A comprehensive example showing common targ usage patterns
    including positional/optional arguments, type inference, and docstrings.
    """

    positional: str = targ(Name)
    """A positional argument (positional)."""
    custom_name_pos: str = targ("my_positional")
    """A custom named positional argument."""

    optional: str = targ(Flag)
    """An optional argument (--optional)."""
    optional_dash: str = targ(Flag)
    """Underscore is replaced with dash (--optional-dash)."""
    optional_short: str = targ(Flag("-s"))
    """You can also add a short name (-s, --optional-short)."""
    custom_name_opt: str = targ("--my-optional")
    """A custom named optional argument."""
    custom_name_opt_short: str = targ(("-c", "--my-short-optional"))
    """A custom named optional argument with a short name. (note the tuple)"""

    options: list[str] = targ(Flag, action="extend", nargs="+", default=[])
    """All options (`help`, `action`, `nargs`, etc.) are the same as argparse."""
    choices: str = targ(Flag, choices=["option1", "option2", "option3"])
    """Another example argument with choices."""
    flag: bool = targ(Flag("-d"), action="store_true")
    """Another example boolean flag."""

    # Type is automatically inferred from the type hint.
    # For `int`, `float`, `str`, etc., no need to specify `type=`.
    default_type: int = targ(Flag, default=42)
    """type is inferred from the type hint (type=int in this case)."""
    # `X | None` (e.g. `float | None`) is also supported — the non-None type is used.
    nullable_ratio: float | None = targ(Flag, default=None)
    """type is inferred as float from `float | None`."""
    # For `Sequence[X]` (or `list[X]`) with `nargs`, the element type is inferred automatically.
    numbers: Sequence[int] = targ(Flag, nargs="+", default=[])
    """type is inferred as int from `Sequence[int]` when nargs is set."""
    # You can always override inference with an explicit `type=`.
    custom_type: float = targ(Flag, type=lambda x: round(float(x), 1), default=3.14)
    """explicit type= always takes priority over inference."""

    docstring_as_help: str = targ(Flag, default="default value")
    """
    If you don't specify a help, it will use the docstring as the help text.
    This is useful for documentation purposes.
    Your LSP will also pick this up.
    """

    # You can also use the `post_init` decorator to execute some code after the arguments are extracted.
    # This is useful for validation or other post-processing.
    @post_init
    def validate(self) -> None:
        if self.positional == "error":
            raise ValueError("positional argument cannot be 'error'")


# You can register the targs with a custom parser
class MyParser(argparse.ArgumentParser):
    def error(self, message: str) -> Never:
        sys.stderr.write("error: %s\n" % message)
        self.print_help()
        sys.exit(2)


if __name__ == "__main__":
    # Create a parser using create_parser (description from class docstring)
    parser = create_parser(MyArgs, parser_class=MyParser, verbose=True)

    # Hybrid usage example
    parser.add_argument("--version", action="version", version="MyArgs 1.0.0")

    # Parse the arguments
    args = parser.parse_args()

    # Extract the targs from the parsed arguments
    my_args = extract_targs(args, MyArgs)
    print(f"Parsed arguments: {my_args}")
