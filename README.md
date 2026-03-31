# Argparse Type Helper

A lightweight helper that lets you leverage type hints with `argparse`.

## Table of Contents

- [Installation](#installation)
- [Features](#features)
- [Usage](#usage)
- [Parser Setup](#parser-setup)
- [Argument Groups](#argument-groups)
- [Subcommands](#subcommands)
- [Docstring-Driven Help](#docstring-driven-help)
- [Why not typed-argparse?](#why-not-typed-argparse)

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
- **Quick parser creation**
  `create_parser(YourArgs)` creates and registers in one step, with description auto-filled from the class docstring.
- **Smart type inference**
  Automatically infers `type` from type hints — including `X | None`, `Optional[X]`, `list[X]` with `nargs`, and bare types like `int`/`float`/`str`. Skips `bool` (use `action="store_true/store_false"` instead).
- **Typed extraction**
  After `parse_args()`, call `extract_targs()` to get a fully-typed instance of your class.
- **Hybrid usage**
  Mix native `parser.add_argument(...)` calls with class-based definitions in the same parser.
- **Docstring-driven help**
  Use docstrings everywhere — on arguments (as help text), on classes (as parser/group/subcommand descriptions). Your IDE picks them up too.
- **Argument groups** (`@tgroup`)
  Organize arguments into groups for cleaner `--help` output.
- **Mutually exclusive groups** (`@texclusive`)
  Define arguments that cannot be used together.
- **Subcommands** (`@tsubcommands`)
  Define subcommands using class inheritance with full type safety and `isinstance`/`match` support.

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
    # For `list[X]` with `nargs`, the element type is inferred automatically.
    numbers: list[int] = targ(Flag, nargs="+", default=[])
    """type is inferred as int from `list[int]` when nargs is set."""
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
```
<!-- MARKDOWN-AUTO-DOCS:END -->

## Parser Setup

There are two ways to set up a parser:

**`create_parser()`** — one-step convenience function:

```python
from argparse_type_helper import create_parser, extract_targs

parser = create_parser(MyArgs)                          # description from docstring
parser = create_parser(MyArgs, parser_class=MyParser)   # custom parser class
parser = create_parser(MyArgs, description="Override")  # explicit description

# You can still add more arguments after create_parser
parser.add_argument("--version", action="version", version="1.0")

args = parser.parse_args()
my_args = extract_targs(args, MyArgs)
```

`create_parser` accepts the same keyword arguments as `ArgumentParser` (`prog`, `description`, `formatter_class`, etc.), plus `parser_class` and `verbose`. It defaults to `RawDescriptionHelpFormatter` so docstring formatting is preserved in `--help`.

**`register_targs()`** — separate parser creation and registration:

```python
import argparse
from argparse_type_helper import register_targs, extract_targs

parser = argparse.ArgumentParser(
    description="My tool.",
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
register_targs(parser, MyArgs, verbose=True)

args = parser.parse_args()
my_args = extract_targs(args, MyArgs)
```

Use `register_targs` when you need full control over parser construction. Note that `register_targs` does not change the parser's `formatter_class` — if you want newlines preserved in descriptions, pass `RawDescriptionHelpFormatter` yourself.

## Argument Groups

Use `@tgroup` to organize related arguments into groups. Use `@texclusive` to define arguments that cannot be used together. Groups affect `--help` display and provide nested access after extraction.

<!-- MARKDOWN-AUTO-DOCS:START (CODE:src=./tests/example_groups.py) -->
<!-- The below code snippet is automatically added from ./tests/example_groups.py -->
```py
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
```
<!-- MARKDOWN-AUTO-DOCS:END -->

The `@tgroup` decorator supports multiple calling styles:
```python
@tgroup                                  # title/description from docstring
@tgroup()                                # same — title/description from docstring
@tgroup("Custom Title")                  # explicit title, description from docstring
@tgroup(title="...", description="...")   # fully explicit
```

Docstring splitting rule: the first paragraph (up to the first blank line) becomes the **title**, the rest becomes the **description**. Explicit `title`/`description` parameters always override docstring values.

> **Note:** Unlike `@tgroup` and `@tsubcommands`, `@texclusive` does not support `title` or `description` parameters. This is a limitation of `argparse.MutuallyExclusiveGroup` itself.

## Subcommands

Use `@tsubcommands` to define subcommands via class inheritance. Each subcommand is a `@targs` class inheriting from the `@tsubcommands` base. Subcommands are discovered automatically via `__subclasses__()` — no manual registration needed.

<!-- MARKDOWN-AUTO-DOCS:START (CODE:src=./tests/example_subcommands.py) -->
<!-- The below code snippet is automatically added from ./tests/example_subcommands.py -->
```py
from argparse_type_helper import (
    Flag,
    Name,
    create_parser,
    extract_targs,
    targ,
    targs,
    tsubcommands,
)


# Use @tsubcommands to define a base class for subcommands.
# The docstring's first paragraph becomes the subparser title,
# and the rest becomes the subparser description.
@tsubcommands
class Commands:
    """Available commands

    Choose one of the following git-like commands to run.
    """


# Each subcommand's docstring first paragraph is shown in the
# top-level help listing; the full docstring is used in the
# subcommand's own --help.
@targs
class push(Commands):
    """Push changes to remote

    Upload local commits to the specified remote repository.
    Supports force push with the -f flag.
    """

    remote: str = targ(Name, nargs="?", default="origin")
    """Remote name to push to."""
    force: bool = targ(Flag("-f"), action="store_true")
    """Force push even if remote has diverged."""


@targs
class pull(Commands):
    """Pull changes from remote

    Download and integrate commits from the specified remote.
    """

    remote: str = targ(Name, nargs="?", default="origin")
    """Remote name to pull from."""
    rebase: bool = targ(Flag, action="store_true")
    """Rebase instead of merge."""


# Reference the subcommands base via type annotation.
@targs
class GitArgs:
    """A git-like CLI tool.

    Demonstrates subcommand support with typed arguments.
    """

    verbose: bool = targ(Flag("-v"), action="store_true")
    """Enable verbose output."""
    command: Commands


if __name__ == "__main__":
    # create_parser auto-fills description from class docstring
    parser = create_parser(GitArgs)

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
        case _:
            pass
```
<!-- MARKDOWN-AUTO-DOCS:END -->

The `@tsubcommands` decorator supports:
```python
@tsubcommands                                        # title/description from docstring
@tsubcommands("Commands")                            # explicit title
@tsubcommands(required=True)                         # require a subcommand
@tsubcommands(title="...", description="...", required=True)
```

Subcommand docstrings follow the same splitting rule: the first paragraph becomes the subcommand's **help** text (shown in the parent `--help` listing), while the full docstring becomes the subcommand's own parser **description** (shown in `<subcommand> --help`).

Type narrowing with `isinstance`:
```python
if isinstance(my_args.command, push):
    print(my_args.command.remote)  # type-safe!
```

## Docstring-Driven Help

Docstrings serve double duty: they provide IDE tooltips **and** CLI help text. The library uses a consistent splitting rule across all decorators:

- **First paragraph** (up to the first blank line) → **title** / **help**
- **Remaining text** → **description**

| Decorator | First paragraph used as | Rest used as |
|---|---|---|
| `@targs` class | `parser.description` (full docstring) | — |
| `@tgroup` class | group title | group description |
| `@tsubcommands` class | subparser title | subparser description |
| Subcommand class | `help=` in parent listing | sub-parser `description` (full docstring) |
| Attribute | `help=` text (full docstring) | — |

Explicit `title=`, `description=`, or `help=` parameters always take priority over docstring values.

> **Note on formatting:** By default, `argparse` collapses newlines in description text. `create_parser` uses `RawDescriptionHelpFormatter` automatically so docstring formatting is preserved. If you use `register_targs` directly, pass `formatter_class=argparse.RawDescriptionHelpFormatter` to your `ArgumentParser` for the same effect. Sub-parsers (subcommands) automatically inherit the parent parser's `formatter_class`.

## Why not [typed-argparse](https://typed-argparse.github.io/typed-argparse/)?

typed-argparse is a great library, but it replaces the familiar `argparse.add_argument` API with its own argument-definition interface, which can be a hurdle when integrating into an existing codebase.

argparse-type-helper, by contrast, is a simple helper that allows you to use type hints with argparse with minimal learning curve. It uses the same `argparse` API you’re already familiar with, and you can even mix native `argparse` usage with class-based definitions in the same parser.
