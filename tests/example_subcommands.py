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
        case _:
            pass
