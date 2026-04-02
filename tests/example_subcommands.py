from argparse_type_helper import (
    Flag,
    Name,
    create_parser,
    extract_targs,
    targ,
    targs,
    tsubcommand,
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
@tsubcommand(name="push")
class Push(Commands):
    """Push changes to remote

    Upload local commits to the specified remote repository.
    Supports force push with the -f flag.
    """

    remote: str = targ(Name, nargs="?", default="origin")
    """Remote name to push to."""
    force: bool = targ(Flag("-f"), action="store_true")
    """Force push even if remote has diverged."""


@tsubcommand(name="pull")
class Pull(Commands):
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
        case Push(remote=r, force=f):
            print(f"Pushing to {r}, force={f}")
        case Pull(remote=r, rebase=rb):
            print(f"Pulling from {r}, rebase={rb}")
        case _:
            print("No command specified")
