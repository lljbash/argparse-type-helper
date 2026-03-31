"""Tests for @tgroup and @texclusive argument groups."""

import argparse

import pytest

from argparse_type_helper import (
    Flag,
    Name,
    extract_targs,
    register_targs,
    targ,
    targs,
    texclusive,
    tgroup,
)

# ---------------------------------------------------------------------------
# @tgroup basics
# ---------------------------------------------------------------------------


@tgroup("Database Options")
class DbOptions:
    """Database connection settings"""

    host: str = targ(Flag, default="localhost")
    """Database host"""
    port: int = targ(Flag, default=5432)
    """Database port"""


@targs
class ArgsWithGroup:
    verbose: bool = targ(Flag, action="store_true")
    db: DbOptions


def test_group_basic_registration_and_extraction():
    parser = argparse.ArgumentParser()
    register_targs(parser, ArgsWithGroup)
    args = parser.parse_args(["--host", "db.example.com", "--port", "3306"])
    result = extract_targs(args, ArgsWithGroup)
    assert result.db.host == "db.example.com"
    assert result.db.port == 3306
    assert result.verbose is False


def test_group_defaults():
    parser = argparse.ArgumentParser()
    register_targs(parser, ArgsWithGroup)
    args = parser.parse_args([])
    result = extract_targs(args, ArgsWithGroup)
    assert result.db.host == "localhost"
    assert result.db.port == 5432


def test_group_help_text(capsys: pytest.CaptureFixture[str]):
    parser = argparse.ArgumentParser()
    register_targs(parser, ArgsWithGroup)
    parser.print_help()
    captured = capsys.readouterr()
    assert "Database Options" in captured.out
    assert "Database host" in captured.out
    assert "Database port" in captured.out


def test_group_repr():
    parser = argparse.ArgumentParser()
    register_targs(parser, ArgsWithGroup)
    args = parser.parse_args(["--verbose"])
    result = extract_targs(args, ArgsWithGroup)
    r = repr(result)
    assert "ArgsWithGroup" in r
    assert "verbose=True" in r
    assert "db=" in r


# ---------------------------------------------------------------------------
# @tgroup decorator variants
# ---------------------------------------------------------------------------


@tgroup
class DefaultTitleGroup:
    x: str = targ(Flag, default="a")


@targs
class ArgsDefaultTitleGroup:
    g: DefaultTitleGroup


def test_tgroup_no_args_uses_classname():
    parser = argparse.ArgumentParser()
    register_targs(parser, ArgsDefaultTitleGroup)
    args = parser.parse_args([])
    result = extract_targs(args, ArgsDefaultTitleGroup)
    assert result.g.x == "a"


@tgroup(title="Custom Title", description="Custom description")
class KwargGroup:
    y: str = targ(Flag, default="b")


@targs
class ArgsKwargGroup:
    g: KwargGroup


def test_tgroup_kwargs():
    parser = argparse.ArgumentParser()
    register_targs(parser, ArgsKwargGroup)

    import io

    help_out = io.StringIO()
    parser.print_help(help_out)
    assert "Custom Title" in help_out.getvalue()


# ---------------------------------------------------------------------------
# Multiple groups
# ---------------------------------------------------------------------------


@tgroup("Input Options")
class InputOpts:
    input_file: str = targ(Flag, default="stdin")


@tgroup("Output Options")
class OutputOpts:
    output_file: str = targ(Flag, default="stdout")
    format: str = targ(Flag, default="json")


@targs
class MultiGroupArgs:
    input: InputOpts
    output: OutputOpts


def test_multiple_groups():
    parser = argparse.ArgumentParser()
    register_targs(parser, MultiGroupArgs)
    args = parser.parse_args(["--input-file", "data.csv", "--format", "csv"])
    result = extract_targs(args, MultiGroupArgs)
    assert result.input.input_file == "data.csv"
    assert result.output.output_file == "stdout"
    assert result.output.format == "csv"


# ---------------------------------------------------------------------------
# Group with regular targs
# ---------------------------------------------------------------------------


@targs
class MixedArgs:
    name: str = targ(Name)
    db: DbOptions


def test_group_mixed_with_regular_targs():
    parser = argparse.ArgumentParser()
    register_targs(parser, MixedArgs)
    args = parser.parse_args(["myname", "--host", "remote", "--port", "1234"])
    result = extract_targs(args, MixedArgs)
    assert result.name == "myname"
    assert result.db.host == "remote"
    assert result.db.port == 1234


# ---------------------------------------------------------------------------
# Group constructor
# ---------------------------------------------------------------------------


def test_group_direct_construction():
    db = DbOptions(host="myhost", port=9999)
    assert db.host == "myhost"
    assert db.port == 9999


def test_args_with_group_direct_construction():
    db = DbOptions(host="h", port=1)
    obj = ArgsWithGroup(verbose=True, db=db)
    assert obj.verbose is True
    assert obj.db.host == "h"


# ---------------------------------------------------------------------------
# @texclusive basics
# ---------------------------------------------------------------------------


@texclusive(required=True)
class VerbosityMode:
    verbose: bool = targ(Flag("-v"), action="store_true")
    quiet: bool = targ(Flag("-q"), action="store_true")


@targs
class ArgsWithExclusive:
    mode: VerbosityMode


def test_exclusive_verbose():
    parser = argparse.ArgumentParser()
    register_targs(parser, ArgsWithExclusive)
    args = parser.parse_args(["--verbose"])
    result = extract_targs(args, ArgsWithExclusive)
    assert result.mode.verbose is True
    assert result.mode.quiet is False


def test_exclusive_quiet():
    parser = argparse.ArgumentParser()
    register_targs(parser, ArgsWithExclusive)
    args = parser.parse_args(["--quiet"])
    result = extract_targs(args, ArgsWithExclusive)
    assert result.mode.verbose is False
    assert result.mode.quiet is True


def test_exclusive_conflict():
    parser = argparse.ArgumentParser()
    register_targs(parser, ArgsWithExclusive)
    with pytest.raises(SystemExit):
        parser.parse_args(["--verbose", "--quiet"])


def test_exclusive_required():
    parser = argparse.ArgumentParser()
    register_targs(parser, ArgsWithExclusive)
    with pytest.raises(SystemExit):
        parser.parse_args([])


# ---------------------------------------------------------------------------
# @texclusive without required
# ---------------------------------------------------------------------------


@texclusive
class OptionalMode:
    debug: bool = targ(Flag, action="store_true")
    release: bool = targ(Flag, action="store_true")


@targs
class ArgsOptionalExclusive:
    build: OptionalMode


def test_exclusive_optional():
    parser = argparse.ArgumentParser()
    register_targs(parser, ArgsOptionalExclusive)
    args = parser.parse_args([])
    result = extract_targs(args, ArgsOptionalExclusive)
    assert result.build.debug is False
    assert result.build.release is False


# ---------------------------------------------------------------------------
# Group + exclusive combined
# ---------------------------------------------------------------------------


@targs
class CombinedArgs:
    name: str = targ(Name)
    db: DbOptions
    mode: VerbosityMode


def test_group_and_exclusive_combined():
    parser = argparse.ArgumentParser()
    register_targs(parser, CombinedArgs)
    args = parser.parse_args(["myname", "--host", "h", "--verbose"])
    result = extract_targs(args, CombinedArgs)
    assert result.name == "myname"
    assert result.db.host == "h"
    assert result.mode.verbose is True
