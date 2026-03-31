"""Tests for @tsubcommands subcommand support."""

import argparse

import pytest

from argparse_type_helper import (
    Flag,
    Name,
    extract_targs,
    post_init,
    register_targs,
    targ,
    targs,
    tgroup,
    tsubcommands,
)

# ---------------------------------------------------------------------------
# Basic subcommands
# ---------------------------------------------------------------------------


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


@targs
class GitArgs:
    verbose: bool = targ(Flag("-v"), action="store_true")
    command: Commands


def test_subcommand_push():
    parser = argparse.ArgumentParser()
    register_targs(parser, GitArgs)
    args = parser.parse_args(["--verbose", "push", "myremote", "-f"])
    result = extract_targs(args, GitArgs)
    assert result.verbose is True
    assert isinstance(result.command, push)
    assert result.command.remote == "myremote"
    assert result.command.force is True


def test_subcommand_pull():
    parser = argparse.ArgumentParser()
    register_targs(parser, GitArgs)
    args = parser.parse_args(["pull", "--rebase"])
    result = extract_targs(args, GitArgs)
    assert result.verbose is False
    assert isinstance(result.command, pull)
    assert result.command.remote == "origin"
    assert result.command.rebase is True


def test_subcommand_defaults():
    parser = argparse.ArgumentParser()
    register_targs(parser, GitArgs)
    args = parser.parse_args(["push"])
    result = extract_targs(args, GitArgs)
    assert isinstance(result.command, push)
    assert result.command.remote == "origin"
    assert result.command.force is False


def test_subcommand_none_when_not_specified():
    parser = argparse.ArgumentParser()
    register_targs(parser, GitArgs)
    args = parser.parse_args([])
    result = extract_targs(args, GitArgs)
    assert result.command is None


# ---------------------------------------------------------------------------
# Help text
# ---------------------------------------------------------------------------


def test_subcommand_help(capsys: pytest.CaptureFixture[str]):
    parser = argparse.ArgumentParser()
    register_targs(parser, GitArgs)
    parser.print_help()
    captured = capsys.readouterr()
    assert "push" in captured.out
    assert "pull" in captured.out
    assert "Push changes to remote" in captured.out
    assert "Pull changes from remote" in captured.out


# ---------------------------------------------------------------------------
# Repr
# ---------------------------------------------------------------------------


def test_subcommand_repr():
    parser = argparse.ArgumentParser()
    register_targs(parser, GitArgs)
    args = parser.parse_args(["push", "origin"])
    result = extract_targs(args, GitArgs)
    r = repr(result)
    assert "GitArgs" in r
    assert "command=" in r


# ---------------------------------------------------------------------------
# @tsubcommands decorator variants
# ---------------------------------------------------------------------------


@tsubcommands("Operations")
class TitledCommands:
    """All operations"""


@targs
class op_start(TitledCommands):
    """Start the service"""

    port: int = targ(Flag, default=8080)


@targs
class op_stop(TitledCommands):
    """Stop the service"""

    force: bool = targ(Flag, action="store_true")


@targs
class TitledArgs:
    operation: TitledCommands


def test_tsubcommands_with_title(capsys: pytest.CaptureFixture[str]):
    parser = argparse.ArgumentParser()
    register_targs(parser, TitledArgs)
    parser.print_help()
    captured = capsys.readouterr()
    assert "Operations" in captured.out


def test_tsubcommands_titled_extraction():
    parser = argparse.ArgumentParser()
    register_targs(parser, TitledArgs)
    args = parser.parse_args(["op_start", "--port", "9090"])
    result = extract_targs(args, TitledArgs)
    assert isinstance(result.operation, op_start)
    assert result.operation.port == 9090


# ---------------------------------------------------------------------------
# Required subcommands
# ---------------------------------------------------------------------------


@tsubcommands(required=True)
class RequiredCommands:
    pass


@targs
class cmd_run(RequiredCommands):
    """Run something"""

    target: str = targ(Name)


@targs
class ArgsRequired:
    cmd: RequiredCommands


def test_required_subcommand():
    parser = argparse.ArgumentParser()
    register_targs(parser, ArgsRequired)
    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_required_subcommand_provided():
    parser = argparse.ArgumentParser()
    register_targs(parser, ArgsRequired)
    args = parser.parse_args(["cmd_run", "mytarget"])
    result = extract_targs(args, ArgsRequired)
    assert isinstance(result.cmd, cmd_run)
    assert result.cmd.target == "mytarget"


# ---------------------------------------------------------------------------
# Subcommand with groups
# ---------------------------------------------------------------------------


@tgroup("Server Options")
class ServerOpts:
    host: str = targ(Flag, default="0.0.0.0")
    port: int = targ(Flag, default=8080)


@tsubcommands
class ServiceCommands:
    pass


@targs
class serve(ServiceCommands):
    """Start the server"""

    server: ServerOpts


@targs
class ServiceArgs:
    debug: bool = targ(Flag, action="store_true")
    action: ServiceCommands


def test_subcommand_with_group():
    parser = argparse.ArgumentParser()
    register_targs(parser, ServiceArgs)
    args = parser.parse_args(["serve", "--host", "127.0.0.1", "--port", "3000"])
    result = extract_targs(args, ServiceArgs)
    assert isinstance(result.action, serve)
    assert result.action.server.host == "127.0.0.1"
    assert result.action.server.port == 3000


# ---------------------------------------------------------------------------
# Subcommand with post_init
# ---------------------------------------------------------------------------


@tsubcommands
class ValidatedCommands:
    pass


@targs
class validated_cmd(ValidatedCommands):
    """A validated command"""

    count: int = targ(Name)

    @post_init
    def check_count(self) -> None:
        if self.count <= 0:
            raise ValueError("count must be positive")


@targs
class ValidatedArgs:
    cmd: ValidatedCommands


def test_subcommand_post_init_valid():
    parser = argparse.ArgumentParser()
    register_targs(parser, ValidatedArgs)
    args = parser.parse_args(["validated_cmd", "5"])
    result = extract_targs(args, ValidatedArgs)
    assert isinstance(result.cmd, validated_cmd)
    assert result.cmd.count == 5


def test_subcommand_post_init_invalid():
    parser = argparse.ArgumentParser()
    register_targs(parser, ValidatedArgs)
    args = parser.parse_args(["validated_cmd", "-1"])
    with pytest.raises(ValueError, match="count must be positive"):
        extract_targs(args, ValidatedArgs)


# ---------------------------------------------------------------------------
# Subcommand direct construction
# ---------------------------------------------------------------------------


def test_subcommand_direct_construction():
    p = push(remote="origin", force=True)
    assert p.remote == "origin"
    assert p.force is True


def test_parent_with_subcommand_direct_construction():
    p = push(remote="origin", force=False)
    obj = GitArgs(verbose=True, command=p)
    assert obj.verbose is True
    assert isinstance(obj.command, push)
    assert obj.command.remote == "origin"


# ---------------------------------------------------------------------------
# Pattern matching
# ---------------------------------------------------------------------------


def test_pattern_matching():
    parser = argparse.ArgumentParser()
    register_targs(parser, GitArgs)

    args = parser.parse_args(["push", "myremote", "-f"])
    result = extract_targs(args, GitArgs)

    matched = False
    match result.command:
        case push(remote=r, force=f):
            assert r == "myremote"
            assert f is True
            matched = True
        case pull():
            matched = False
        case _:
            matched = False

    assert matched


# ---------------------------------------------------------------------------
# Shared args on @tsubcommands base
# ---------------------------------------------------------------------------


@tsubcommands
class SharedBase:
    """Commands with shared args"""


@targs
class shared_cmd_a(SharedBase):
    """Command A"""

    name: str = targ(Name)


@targs
class shared_cmd_b(SharedBase):
    """Command B"""

    count: int = targ(Flag, default=1)


@targs
class SharedArgs:
    cmd: SharedBase


def test_shared_subcommand_a():
    parser = argparse.ArgumentParser()
    register_targs(parser, SharedArgs)
    args = parser.parse_args(["shared_cmd_a", "hello"])
    result = extract_targs(args, SharedArgs)
    assert isinstance(result.cmd, shared_cmd_a)
    assert result.cmd.name == "hello"


def test_shared_subcommand_b():
    parser = argparse.ArgumentParser()
    register_targs(parser, SharedArgs)
    args = parser.parse_args(["shared_cmd_b", "--count", "5"])
    result = extract_targs(args, SharedArgs)
    assert isinstance(result.cmd, shared_cmd_b)
    assert result.cmd.count == 5


# ---------------------------------------------------------------------------
# Inherited targ fields on @tsubcommands base
# ---------------------------------------------------------------------------


@tsubcommands
class InheritedBase:
    pass


@targs
class inherit_a(InheritedBase):
    """Inheriting command A"""

    verbose: bool = targ(Flag("-v"), action="store_true")
    target: str = targ(Name)


@targs
class inherit_b(InheritedBase):
    """Inheriting command B"""

    verbose: bool = targ(Flag("-v"), action="store_true")
    output: str = targ(Flag, default="out.txt")


@targs
class InheritedArgs:
    cmd: InheritedBase


def test_inherited_base_subcmd_a():
    parser = argparse.ArgumentParser()
    register_targs(parser, InheritedArgs)
    args = parser.parse_args(["inherit_a", "-v", "src"])
    result = extract_targs(args, InheritedArgs)
    assert isinstance(result.cmd, inherit_a)
    assert result.cmd.verbose is True
    assert result.cmd.target == "src"


def test_inherited_base_subcmd_b():
    parser = argparse.ArgumentParser()
    register_targs(parser, InheritedArgs)
    args = parser.parse_args(["inherit_b", "--output", "result.txt"])
    result = extract_targs(args, InheritedArgs)
    assert isinstance(result.cmd, inherit_b)
    assert result.cmd.verbose is False
    assert result.cmd.output == "result.txt"


# ---------------------------------------------------------------------------
# Nested subcommands (sub-sub-commands)
# ---------------------------------------------------------------------------


@tsubcommands
class OuterCommands:
    pass


@tsubcommands
class InnerCommands:
    pass


@targs
class inner_start(InnerCommands):
    """Start the inner service"""

    port: int = targ(Flag, default=8080)


@targs
class inner_stop(InnerCommands):
    """Stop the inner service"""

    force: bool = targ(Flag, action="store_true")


@targs
class outer_service(OuterCommands):
    """Service management"""

    inner: InnerCommands


@targs
class outer_info(OuterCommands):
    """Show info"""

    detail: bool = targ(Flag, action="store_true")


@targs
class NestedArgs:
    cmd: OuterCommands


def test_nested_subcommand_inner_start():
    parser = argparse.ArgumentParser()
    register_targs(parser, NestedArgs)
    args = parser.parse_args(["outer_service", "inner_start", "--port", "9090"])
    result = extract_targs(args, NestedArgs)
    assert isinstance(result.cmd, outer_service)
    assert isinstance(result.cmd.inner, inner_start)
    assert result.cmd.inner.port == 9090


def test_nested_subcommand_inner_stop():
    parser = argparse.ArgumentParser()
    register_targs(parser, NestedArgs)
    args = parser.parse_args(["outer_service", "inner_stop", "--force"])
    result = extract_targs(args, NestedArgs)
    assert isinstance(result.cmd, outer_service)
    assert isinstance(result.cmd.inner, inner_stop)
    assert result.cmd.inner.force is True


def test_nested_subcommand_outer_info():
    parser = argparse.ArgumentParser()
    register_targs(parser, NestedArgs)
    args = parser.parse_args(["outer_info", "--detail"])
    result = extract_targs(args, NestedArgs)
    assert isinstance(result.cmd, outer_info)
    assert result.cmd.detail is True


def test_nested_subcommand_none():
    parser = argparse.ArgumentParser()
    register_targs(parser, NestedArgs)
    args = parser.parse_args(["outer_service"])
    result = extract_targs(args, NestedArgs)
    assert isinstance(result.cmd, outer_service)
    assert result.cmd.inner is None
