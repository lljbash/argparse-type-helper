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

    # --- Positional arguments (always required, never None) ---
    positional: str = targ(Name)
    """A required positional argument."""
    custom_name_pos: str = targ("my_positional")
    """A positional argument with a custom name."""

    # --- Flag naming variants ---
    # Flag without a default will be None when not provided — use `X | None`.
    optional: str | None = targ(Flag)
    """A basic optional flag (--optional)."""
    optional_dash: str | None = targ(Flag)
    """Underscores in the attribute name become dashes in the CLI (--optional-dash)."""
    optional_short: str | None = targ(Flag("-s"))
    """A flag with a short alias (-s / --optional-short)."""
    custom_name_opt: str | None = targ("--my-optional")
    """A flag with a fully custom name."""
    # required=True means the flag must be provided, so None is not possible.
    required_flag: str = targ(Flag, required=True)
    """A required optional flag (--required-flag)."""

    # --- Common argparse options ---
    # store_true / store_false automatically set default=False / True,
    # so `bool` is correct — no `| None` needed.
    flag: bool = targ(Flag("-d"), action="store_true")
    """A boolean flag (-d / --flag); defaults to False when not provided."""
    choices: str | None = targ(Flag, choices=["option1", "option2", "option3"])
    """A flag restricted to a fixed set of choices."""
    options: list[str] = targ(Flag, action="extend", nargs="+", default=[])
    """A flag that accumulates multiple values (action, nargs, default work as in argparse)."""

    # --- Type inference ---
    # For `int`, `float`, `str`, etc., no need to specify `type=`.
    default_type: int = targ(Flag, default=42)
    """Type is inferred from the type hint (int here)."""
    # `X | None` is also supported — the non-None type is used for inference.
    nullable_ratio: float | None = targ(Flag, default=None)
    """Type is inferred as float from `float | None`."""
    # For `Sequence[X]` (or `list[X]`) with `nargs`, the element type is inferred automatically.
    numbers: Sequence[int] = targ(Flag, nargs="+", default=[])
    """Type is inferred as int from `Sequence[int]` when nargs is set."""
    # You can always override inference with an explicit `type=`.
    custom_type: float = targ(Flag, type=lambda x: round(float(x), 1), default=3.14)
    """Explicit type= always takes priority over inference."""

    # --- Docstring as help text ---
    docstring_as_help: str = targ(Flag, default="default value")
    """
    When no help= is specified, the attribute docstring is used as the help text.
    Your LSP will also pick this up for inline documentation.
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
