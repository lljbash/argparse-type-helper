# Argparse Type Helper

A lightweight helper that lets you leverage type hints with `argparse`.

## Installation

```bash
pip install argparse-type-helper
```

## Features

- **Class-based schema**
  Bundle all your arguments in a single `@targs`-decorated class.
- **Identical API**
  Each field uses the same parameters as `argparse.add_argument` (`help`, `action`, `nargs`, etc.).
- **Automatic registration**
  One call to `register_targs(parser, YourArgs)` wires up all arguments on your `ArgumentParser`.
- **Typed extraction**
  After `parse_args()`, call `extract_targs()` to get a fully-typed instance of your class.
- **Hybrid usage**
  Mix native `parser.add_argument(...)` calls with class-based definitions in the same parser.
- **Docstring support**
  Use docstrings to automatically generate help text for your arguments.

## Why not [typed-argparse](https://typed-argparse.github.io/typed-argparse/)?

typed-argparse is a great library, but it replaces the familiar `argparse.add_argument` API with its own argument-definition interface, which can be a hurdle when integrating into an existing codebase.

argparse-type-helper, by contrast, is a simple helper that allows you to use type hints with argparse with minimal learning curve. It uses the same `argparse` API you’re already familiar with, and you can even mix native `argparse` usage with class-based definitions in the same parser.

## Usage

<!-- MARKDOWN-AUTO-DOCS:START (CODE:src=./tests/example.py) -->
<!-- The below code snippet is automatically added from ./tests/example.py -->
```py
import argparse
import sys
from typing import Never

from argparse_type_helper import (
    Flag,
    Name,
    extract_targs,
    post_init,
    register_targs,
    targ,
    targs,
)


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
```
<!-- MARKDOWN-AUTO-DOCS:END -->
