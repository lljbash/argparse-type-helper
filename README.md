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
- **Smart type inference**
  Automatically infers `type` from type hints — including `X | None`, `Optional[X]`, `list[X]` with `nargs`, and bare types like `int`/`float`/`str`. Skips `bool` (use `action="store_true/store_false"` instead).
- **Typed extraction**
  After `parse_args()`, call `extract_targs()` to get a fully-typed instance of your class.
- **Hybrid usage**
  Mix native `parser.add_argument(...)` calls with class-based definitions in the same parser.
- **Docstring support**
  Use docstrings to automatically generate help text for your arguments.
- **Argument groups** (`@tgroup`)
  Organize arguments into groups for cleaner `--help` output.
- **Mutually exclusive groups** (`@texclusive`)
  Define arguments that cannot be used together.
- **Subcommands** (`@tsubcommands`)
  Define subcommands using class inheritance with full type safety and `isinstance`/`match` support.

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

## Argument Groups

Use `@tgroup` to organize related arguments into groups. Use `@texclusive` to define arguments that cannot be used together. Groups affect `--help` display and provide nested access after extraction.

<!-- MARKDOWN-AUTO-DOCS:START (CODE:src=./tests/example_groups.py) -->
<!-- The below code snippet is automatically added from ./tests/example_groups.py -->
```py
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
```
<!-- MARKDOWN-AUTO-DOCS:END -->

The `@tgroup` decorator supports multiple calling styles:
```python
@tgroup                                  # title defaults to class name
@tgroup("Custom Title")                  # title as positional arg
@tgroup(title="...", description="...")   # keyword args
```

> **Note:** Unlike `@tgroup` and `@tsubcommands`, `@texclusive` does not support `title` or `description` parameters. This is a limitation of `argparse.MutuallyExclusiveGroup` itself.

## Subcommands

Use `@tsubcommands` to define subcommands via class inheritance. Each subcommand is a `@targs` class inheriting from the `@tsubcommands` base. Subcommands are discovered automatically via `__subclasses__()` — no manual registration needed.

<!-- MARKDOWN-AUTO-DOCS:START (CODE:src=./tests/example_subcommands.py) -->
<!-- The below code snippet is automatically added from ./tests/example_subcommands.py -->
```py
import argparse

from argparse_type_helper import (
    Flag,
    Name,
    extract_targs,
    register_targs,
    targ,
    targs,
    tsubcommands,
)


# Use @tsubcommands to define a base class for subcommands.
# Subcommands are @targs classes that inherit from this base.
@tsubcommands
class Commands:
    """Available commands"""


@targs
class push(Commands):
    """Push changes to remote"""

    remote: str = targ(Name, nargs="?", default="origin")
    force: bool = targ(Flag("-f"), action="store_true")


@targs
class pull(Commands):
    """Pull changes from remote"""

    remote: str = targ(Name, nargs="?", default="origin")
    rebase: bool = targ(Flag, action="store_true")


# Reference the subcommands base via type annotation.
@targs
class GitArgs:
    verbose: bool = targ(Flag("-v"), action="store_true")
    command: Commands


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Subcommands example.")
    register_targs(parser, GitArgs)

    args = parser.parse_args()
    my_args = extract_targs(args, GitArgs)

    # Use isinstance or pattern matching for type-safe access:
    match my_args.command:
        case push(remote=r, force=f):
            print(f"Pushing to {r}, force={f}")
        case pull(remote=r, rebase=rb):
            print(f"Pulling from {r}, rebase={rb}")
        case None:
            print("No command specified")
```
<!-- MARKDOWN-AUTO-DOCS:END -->

The `@tsubcommands` decorator supports:
```python
@tsubcommands                                        # basic
@tsubcommands("Commands")                            # title as positional arg
@tsubcommands(required=True)                         # require a subcommand
@tsubcommands(title="...", description="...", required=True)
```

Type narrowing with `isinstance`:
```python
if isinstance(my_args.command, push):
    print(my_args.command.remote)  # type-safe!
```
