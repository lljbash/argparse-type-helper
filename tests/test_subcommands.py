"""Tests for @tsubcommands subcommand support."""

import argparse

import pytest

from argparse_type_helper import (
    Flag,
    Name,
    create_parser,
    extract_targs,
    post_init,
    register_targs,
    targ,
    targs,
    tgroup,
    tsubcommand,
    tsubcommands,
)

# ---------------------------------------------------------------------------
# Basic subcommands
# ---------------------------------------------------------------------------


@tsubcommands
class Commands:
    """Available commands"""


@tsubcommand(name="push")
class push(Commands):
    """Push changes to remote"""

    remote: str = targ(Name, nargs="?", default="origin")
    force: bool = targ(Flag("-f"), action="store_true")


@tsubcommand(name="pull")
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


@tsubcommand(name="op_start")
class op_start(TitledCommands):
    """Start the service"""

    port: int = targ(Flag, default=8080)


@tsubcommand(name="op_stop")
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


@tsubcommand(name="cmd_run")
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


@tsubcommand(name="serve")
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


@tsubcommand(name="validated_cmd")
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


@tsubcommand(name="shared_cmd_a")
class shared_cmd_a(SharedBase):
    """Command A"""

    name: str = targ(Name)


@tsubcommand(name="shared_cmd_b")
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


@tsubcommand(name="inherit_a")
class inherit_a(InheritedBase):
    """Inheriting command A"""

    verbose: bool = targ(Flag("-v"), action="store_true")
    target: str = targ(Name)


@tsubcommand(name="inherit_b")
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


@tsubcommand(name="inner_start")
class inner_start(InnerCommands):
    """Start the inner service"""

    port: int = targ(Flag, default=8080)


@tsubcommand(name="inner_stop")
class inner_stop(InnerCommands):
    """Stop the inner service"""

    force: bool = targ(Flag, action="store_true")


@tsubcommand(name="outer_service")
class outer_service(OuterCommands):
    """Service management"""

    inner: InnerCommands


@tsubcommand(name="outer_info")
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


def test_nested_bare_targs_raises():
    """Bare @targs sub-subcommand raises TypeError in nested context."""

    @tsubcommands
    class NestOuter:
        pass

    @tsubcommands
    class NestInner:
        pass

    @targs
    class BadInner(NestInner):  # pyright: ignore[reportUnusedClass]
        val: int = targ(Flag, default=0)

    @tsubcommand(name="service")
    class NestService(NestOuter):  # pyright: ignore[reportUnusedClass]
        inner: NestInner

    @targs
    class NestTopArgs:
        cmd: NestOuter

    parser = argparse.ArgumentParser()
    with pytest.raises(TypeError, match=r"@tsubcommand\(name="):
        register_targs(parser, NestTopArgs)


def test_nested_subcommand_aliases():
    """Aliases work in nested (sub-sub) subcommands."""

    @tsubcommands
    class NAOuter:
        pass

    @tsubcommands
    class NAInner:
        pass

    @tsubcommand(name="start", aliases=["s", "up"])
    class NAStart(NAInner):
        port: int = targ(Flag, default=8080)

    @tsubcommand(name="svc")
    class NASvc(NAOuter):
        action: NAInner

    @targs
    class NATopArgs:
        cmd: NAOuter

    parser = argparse.ArgumentParser()
    register_targs(parser, NATopArgs)

    # Canonical name
    args = parser.parse_args(["svc", "start", "--port", "9090"])
    result = extract_targs(args, NATopArgs)
    assert isinstance(result.cmd, NASvc)
    assert isinstance(result.cmd.action, NAStart)
    assert result.cmd.action.port == 9090

    # Alias
    args = parser.parse_args(["svc", "s"])
    result = extract_targs(args, NATopArgs)
    assert isinstance(result.cmd, NASvc)
    assert isinstance(result.cmd.action, NAStart)
    assert result.cmd.action.port == 8080

    # Second alias
    args = parser.parse_args(["svc", "up", "--port", "3000"])
    result = extract_targs(args, NATopArgs)
    assert isinstance(result.cmd, NASvc)
    assert isinstance(result.cmd.action, NAStart)
    assert result.cmd.action.port == 3000


# ---------------------------------------------------------------------------
# @tsubcommands docstring → title/description split
# ---------------------------------------------------------------------------


@tsubcommands
class DocCommands:
    """Available commands

    Choose one of the available commands below.
    """


@tsubcommand(name="doc_cmd_a")
class doc_cmd_a(DocCommands):
    """Start the service

    Start the background service with the specified port.
    """

    port: int = targ(Flag, default=8080)


@targs
class ArgsDocSubcommands:
    cmd: DocCommands


def test_tsubcommands_docstring_title(capsys: pytest.CaptureFixture[str]):
    """First line of @tsubcommands docstring becomes subparser group title."""
    parser = argparse.ArgumentParser()
    register_targs(parser, ArgsDocSubcommands)
    parser.print_help()
    captured = capsys.readouterr()
    assert "Available commands" in captured.out


def test_tsubcommands_docstring_description(capsys: pytest.CaptureFixture[str]):
    """The rest of the @tsubcommands docstring becomes subparser description."""
    parser = create_parser(ArgsDocSubcommands)
    parser.print_help()
    captured = capsys.readouterr()
    assert "Choose one of the available commands below." in captured.out


def test_subcommand_help_uses_title(capsys: pytest.CaptureFixture[str]):
    """Subcommand help listing uses only the first line of the subcommand docstring."""
    parser = argparse.ArgumentParser()
    register_targs(parser, ArgsDocSubcommands)
    parser.print_help()
    captured = capsys.readouterr()
    assert "Start the service" in captured.out


def test_subcommand_parser_description_uses_full(capsys: pytest.CaptureFixture[str]):
    """The sub-parser description uses the full docstring (title + body)."""
    sub_parser = argparse.ArgumentParser()
    register_targs(sub_parser, doc_cmd_a)
    sub_parser.print_help()
    captured = capsys.readouterr()
    assert "Start the service" in captured.out
    assert "Start the background service" in captured.out


@tsubcommands(title="Named Operations", description="Pick one operation below.")
class KwargTitleCommands:
    pass


@tsubcommand(name="kwarg_op")
class kwarg_op(KwargTitleCommands):
    """Do the operation"""

    val: int = targ(Flag, default=0)


@targs
class KwargTitleArgs:
    cmd: KwargTitleCommands


def test_tsubcommands_kwarg_title(capsys: pytest.CaptureFixture[str]):
    """tsubcommands(title=...) kwarg form sets the subparser group title."""
    parser = argparse.ArgumentParser()
    register_targs(parser, KwargTitleArgs)
    parser.print_help()
    captured = capsys.readouterr()
    assert "Named Operations" in captured.out


def test_tsubcommands_kwarg_description(capsys: pytest.CaptureFixture[str]):
    """tsubcommands(description=...) kwarg form sets the subparser description."""
    parser = argparse.ArgumentParser()
    register_targs(parser, KwargTitleArgs)
    parser.print_help()
    captured = capsys.readouterr()
    assert "Pick one operation below." in captured.out


# ---------------------------------------------------------------------------
# Custom subcommand name via @tsubcommand(name=...)
# ---------------------------------------------------------------------------


@tsubcommands(required=True)
class NamedCommands:
    """Available commands"""


@tsubcommand(name="run-fixed")
class RunFixed(NamedCommands):
    """Run with fixed prompts"""

    count: int = targ(Flag, default=10)


@tsubcommand(name="load-csv")
class LoadCsv(NamedCommands):
    """Load CSV results"""

    path: str = targ(Name)


@targs
class NamedArgs:
    cmd: NamedCommands


def test_custom_name_parsing():
    """@tsubcommand(name=...) sets the subcommand name on the CLI."""
    parser = argparse.ArgumentParser()
    register_targs(parser, NamedArgs)
    args = parser.parse_args(["run-fixed", "--count", "42"])
    result = extract_targs(args, NamedArgs)
    assert isinstance(result.cmd, RunFixed)
    assert result.cmd.count == 42


def test_custom_name_positional():
    parser = argparse.ArgumentParser()
    register_targs(parser, NamedArgs)
    args = parser.parse_args(["load-csv", "data.csv"])
    result = extract_targs(args, NamedArgs)
    assert isinstance(result.cmd, LoadCsv)
    assert result.cmd.path == "data.csv"


def test_custom_name_help(capsys: pytest.CaptureFixture[str]):
    """Custom subcommand names appear in --help."""
    parser = argparse.ArgumentParser()
    register_targs(parser, NamedArgs)
    parser.print_help()
    captured = capsys.readouterr()
    assert "run-fixed" in captured.out
    assert "load-csv" in captured.out
    assert "Run with fixed prompts" in captured.out


def test_custom_name_invalid_choice():
    """Original class name is not accepted when a custom name is set."""
    parser = argparse.ArgumentParser()
    register_targs(parser, NamedArgs)
    with pytest.raises(SystemExit):
        parser.parse_args(["RunFixed"])


# ---------------------------------------------------------------------------
# Custom name with multi-inheritance
# ---------------------------------------------------------------------------


@tsubcommands(required=True)
class MixinCommands:
    pass


@targs
class SharedRunArgs:
    url: str = targ(Name)
    concurrency: int = targ(Flag("-c"), required=True)


@tsubcommand(name="run-benchmark")
class RunBenchmark(SharedRunArgs, MixinCommands):
    """Run benchmark"""

    iterations: int = targ(Flag, default=100)


@tsubcommand(name="show-results")
class ShowResults(MixinCommands):
    """Show results"""

    csv_path: str = targ(Name)


@targs
class MixinArgs:
    command: MixinCommands


def test_custom_name_multi_inheritance():
    """@tsubcommand(name=...) works with multi-inheritance subcommands."""
    parser = argparse.ArgumentParser()
    register_targs(parser, MixinArgs)
    args = parser.parse_args(["run-benchmark", "http://host", "-c", "5"])
    result = extract_targs(args, MixinArgs)
    assert isinstance(result.command, RunBenchmark)
    assert result.command.url == "http://host"
    assert result.command.concurrency == 5
    assert result.command.iterations == 100


def test_custom_name_multi_inheritance_pattern_match():
    parser = argparse.ArgumentParser()
    register_targs(parser, MixinArgs)
    args = parser.parse_args(["show-results", "out.csv"])
    result = extract_targs(args, MixinArgs)
    match result.command:
        case ShowResults(csv_path=p):
            assert p == "out.csv"
        case _:
            assert False, "Pattern match failed"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_bare_targs_subclass_raises():
    """Bare @targs subclass of @tsubcommands base raises TypeError during registration."""

    @tsubcommands(required=True)
    class ErrorCommands:
        pass

    @targs
    class BadSubcmd(ErrorCommands):  # pyright: ignore[reportUnusedClass]
        val: int = targ(Flag, default=0)

    @targs
    class ErrorArgs:
        cmd: ErrorCommands

    parser = argparse.ArgumentParser()
    with pytest.raises(TypeError, match=r"@tsubcommand\(name="):
        register_targs(parser, ErrorArgs)


def test_bare_targs_multi_inherit_raises():
    """Bare @targs subclass with multi-inheritance also raises TypeError."""

    @tsubcommands(required=True)
    class MICommands:
        pass

    @targs
    class SharedBase:
        url: str = targ(Name)

    @targs
    class MIBadSubcmd(SharedBase, MICommands):  # pyright: ignore[reportUnusedClass]
        """Multi-inherited but missing @tsubcommand."""

        extra: int = targ(Flag, default=0)

    @targs
    class MIArgs:
        cmd: MICommands

    parser = argparse.ArgumentParser()
    with pytest.raises(TypeError, match=r"@tsubcommand\(name="):
        register_targs(parser, MIArgs)


def test_plain_subclass_without_decorators_ignored():
    """A plain subclass (no @targs, no @tsubcommand) is silently skipped."""

    @tsubcommands(required=True)
    class SkipCommands:
        pass

    @tsubcommand(name="valid")
    class ValidCmd(SkipCommands):
        val: int = targ(Flag, default=0)

    class PlainSubclass(SkipCommands):  # pyright: ignore[reportUnusedClass]
        """No decorator at all — should be silently ignored."""

        pass

    @targs
    class SkipArgs:
        cmd: SkipCommands

    parser = argparse.ArgumentParser()
    register_targs(parser, SkipArgs)
    # Should work; PlainSubclass is ignored, ValidCmd is registered
    args = parser.parse_args(["valid"])
    result = extract_targs(args, SkipArgs)
    assert isinstance(result.cmd, ValidCmd)


# ---------------------------------------------------------------------------
# Aliases
# ---------------------------------------------------------------------------


@tsubcommands(required=True)
class AliasCommands:
    """Alias test commands"""


@tsubcommand(name="run-benchmark", aliases=["rb", "bench"])
class BenchCmd(AliasCommands):
    """Run the benchmark"""

    iterations: int = targ(Flag, default=100)


@tsubcommand(name="show-results", aliases=["sr"])
class ShowCmd(AliasCommands):
    """Show results"""

    path: str = targ(Name)


@targs
class AliasArgs:
    cmd: AliasCommands


def test_alias_canonical_name():
    """Canonical name works as expected."""
    parser = argparse.ArgumentParser()
    register_targs(parser, AliasArgs)
    args = parser.parse_args(["run-benchmark", "--iterations", "50"])
    result = extract_targs(args, AliasArgs)
    assert isinstance(result.cmd, BenchCmd)
    assert result.cmd.iterations == 50


def test_alias_short():
    """Alias is accepted on the CLI."""
    parser = argparse.ArgumentParser()
    register_targs(parser, AliasArgs)
    args = parser.parse_args(["rb", "--iterations", "25"])
    result = extract_targs(args, AliasArgs)
    assert isinstance(result.cmd, BenchCmd)
    assert result.cmd.iterations == 25


def test_alias_second():
    """Multiple aliases all work."""
    parser = argparse.ArgumentParser()
    register_targs(parser, AliasArgs)
    args = parser.parse_args(["bench"])
    result = extract_targs(args, AliasArgs)
    assert isinstance(result.cmd, BenchCmd)


def test_alias_in_help(capsys: pytest.CaptureFixture[str]):
    """Aliases appear in --help output."""
    parser = argparse.ArgumentParser()
    register_targs(parser, AliasArgs)
    parser.print_help()
    captured = capsys.readouterr()
    assert "run-benchmark" in captured.out
    assert "show-results" in captured.out


def test_alias_positional_subcmd():
    """Alias with positional argument subcommand."""
    parser = argparse.ArgumentParser()
    register_targs(parser, AliasArgs)
    args = parser.parse_args(["sr", "out.csv"])
    result = extract_targs(args, AliasArgs)
    assert isinstance(result.cmd, ShowCmd)
    assert result.cmd.path == "out.csv"
