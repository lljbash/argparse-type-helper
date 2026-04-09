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


# ---------------------------------------------------------------------------
# @tgroup docstring → title/description split
# ---------------------------------------------------------------------------


@tgroup
class DocstringTitleGroup:
    """Database connection

    Configure database host and port for the application.
    """

    host: str = targ(Flag, default="localhost")
    port: int = targ(Flag, default=5432)


@targs
class GroupDocArgs:
    db: DocstringTitleGroup


def test_tgroup_docstring_title(capsys: pytest.CaptureFixture[str]):
    """First line of docstring becomes group title."""
    parser = argparse.ArgumentParser()
    register_targs(parser, GroupDocArgs)
    parser.print_help()
    captured = capsys.readouterr()
    assert "Database connection" in captured.out


def test_tgroup_docstring_description(capsys: pytest.CaptureFixture[str]):
    """Rest of docstring becomes group description."""
    parser = argparse.ArgumentParser()
    register_targs(parser, GroupDocArgs)
    parser.print_help()
    captured = capsys.readouterr()
    assert "Configure database host" in captured.out


@tgroup("Explicit Title")
class ExplicitTitleGroup:
    """This docstring title is ignored.

    But this description is used.
    """

    val: str = targ(Flag, default="x")


@targs
class ExplicitGroupArgs:
    g: ExplicitTitleGroup


def test_tgroup_explicit_title_overrides_docstring(capsys: pytest.CaptureFixture[str]):
    """Explicit string arg overrides docstring title."""
    parser = argparse.ArgumentParser()
    register_targs(parser, ExplicitGroupArgs)
    parser.print_help()
    captured = capsys.readouterr()
    assert "Explicit Title" in captured.out
    assert "This docstring title is ignored" not in captured.out


def test_tgroup_explicit_title_docstring_description(
    capsys: pytest.CaptureFixture[str],
):
    """Docstring description is still used when title is overridden."""
    parser = argparse.ArgumentParser()
    register_targs(parser, ExplicitGroupArgs)
    parser.print_help()
    captured = capsys.readouterr()
    assert "But this description is used" in captured.out


@tgroup(title="T", description="Explicit description")
class FullyExplicitGroup:
    """Ignored title.

    Ignored description.
    """

    val: str = targ(Flag, default="x")


@targs
class FullyExplicitGroupArgs:
    g: FullyExplicitGroup


def test_tgroup_fully_explicit(capsys: pytest.CaptureFixture[str]):
    """Explicit title= and description= both override docstring."""
    parser = argparse.ArgumentParser()
    register_targs(parser, FullyExplicitGroupArgs)
    parser.print_help()
    captured = capsys.readouterr()
    assert "T" in captured.out
    assert "Explicit description" in captured.out
    assert "Ignored" not in captured.out


# ---------------------------------------------------------------------------
# @texclusive direct construction
# ---------------------------------------------------------------------------


def test_exclusive_direct_construction():
    """texclusive instances can be created directly."""
    mode = VerbosityMode(verbose=True, quiet=False)
    assert mode.verbose is True
    assert mode.quiet is False


# ---------------------------------------------------------------------------
# @texclusive nested inside @tgroup
# ---------------------------------------------------------------------------


@texclusive(required=True)
class NestedExclusive:
    alpha: bool = targ(Flag, action="store_true")
    beta: bool = targ(Flag, action="store_true")


@tgroup("Container Group")
class GroupWithExclusive:
    """A group that contains both regular args and an exclusive sub-group."""

    tag: str = targ(Flag, default="latest")
    choice: NestedExclusive


@targs
class ArgsWithNestedExclusive:
    name: str = targ(Name)
    container: GroupWithExclusive


def test_nested_exclusive_registration_and_parsing():
    """texclusive nested inside tgroup registers and parses correctly."""
    parser = argparse.ArgumentParser()
    register_targs(parser, ArgsWithNestedExclusive)
    args = parser.parse_args(["hello", "--alpha", "--tag", "v2"])
    result = extract_targs(args, ArgsWithNestedExclusive)
    assert result.name == "hello"
    assert result.container.tag == "v2"
    assert result.container.choice.alpha is True
    assert result.container.choice.beta is False


def test_nested_exclusive_other_option():
    """The other exclusive option works correctly."""
    parser = argparse.ArgumentParser()
    register_targs(parser, ArgsWithNestedExclusive)
    args = parser.parse_args(["hello", "--beta"])
    result = extract_targs(args, ArgsWithNestedExclusive)
    assert result.container.choice.alpha is False
    assert result.container.choice.beta is True


def test_nested_exclusive_conflict():
    """Mutually exclusive constraint is enforced inside a tgroup."""
    parser = argparse.ArgumentParser()
    register_targs(parser, ArgsWithNestedExclusive)
    with pytest.raises(SystemExit):
        parser.parse_args(["hello", "--alpha", "--beta"])


def test_nested_exclusive_required():
    """required=True on nested texclusive is enforced."""
    parser = argparse.ArgumentParser()
    register_targs(parser, ArgsWithNestedExclusive)
    with pytest.raises(SystemExit):
        parser.parse_args(["hello"])


def test_nested_exclusive_help_text(capsys: pytest.CaptureFixture[str]):
    """Help output shows the tgroup title with exclusive args underneath."""
    parser = argparse.ArgumentParser()
    register_targs(parser, ArgsWithNestedExclusive)
    parser.print_help()
    captured = capsys.readouterr()
    assert "Container Group" in captured.out
    assert "--alpha" in captured.out
    assert "--beta" in captured.out
    assert "--tag" in captured.out


def test_nested_exclusive_defaults():
    """Defaults work for both the group arg and nested exclusive args."""
    parser = argparse.ArgumentParser()
    register_targs(parser, ArgsWithNestedExclusive)
    # required=True means we must supply one exclusive option
    args = parser.parse_args(["myname", "--alpha"])
    result = extract_targs(args, ArgsWithNestedExclusive)
    assert result.container.tag == "latest"  # default
    assert result.container.choice.alpha is True


def test_nested_exclusive_repr():
    """repr() of nested structure is correct."""
    parser = argparse.ArgumentParser()
    register_targs(parser, ArgsWithNestedExclusive)
    args = parser.parse_args(["myname", "--beta"])
    result = extract_targs(args, ArgsWithNestedExclusive)
    r = repr(result)
    assert "ArgsWithNestedExclusive" in r
    assert "GroupWithExclusive" in r
    assert "NestedExclusive" in r


def test_nested_exclusive_direct_construction():
    """Direct construction of tgroup with nested texclusive works."""
    excl = NestedExclusive(alpha=True, beta=False)
    group = GroupWithExclusive(tag="v3", choice=excl)
    obj = ArgsWithNestedExclusive(name="test", container=group)
    assert obj.container.choice.alpha is True
    assert obj.container.tag == "v3"


# ---------------------------------------------------------------------------
# @texclusive(required=False) nested inside @tgroup
# ---------------------------------------------------------------------------


@texclusive
class OptionalNestedExclusive:
    dry_run: bool = targ(Flag, action="store_true")
    force: bool = targ(Flag, action="store_true")


@tgroup("Deploy Options")
class DeployGroup:
    target: str = targ(Flag, default="staging")
    safety: OptionalNestedExclusive


@targs
class ArgsOptionalNestedExclusive:
    deploy: DeployGroup


def test_nested_exclusive_optional_none_selected():
    """Optional nested texclusive allows no selection."""
    parser = argparse.ArgumentParser()
    register_targs(parser, ArgsOptionalNestedExclusive)
    args = parser.parse_args([])
    result = extract_targs(args, ArgsOptionalNestedExclusive)
    assert result.deploy.safety.dry_run is False
    assert result.deploy.safety.force is False
    assert result.deploy.target == "staging"


def test_nested_exclusive_optional_one_selected():
    """Optional nested texclusive works with a selection."""
    parser = argparse.ArgumentParser()
    register_targs(parser, ArgsOptionalNestedExclusive)
    args = parser.parse_args(["--force", "--target", "production"])
    result = extract_targs(args, ArgsOptionalNestedExclusive)
    assert result.deploy.safety.force is True
    assert result.deploy.safety.dry_run is False
    assert result.deploy.target == "production"


# ---------------------------------------------------------------------------
# Multiple @texclusive inside one @tgroup
# ---------------------------------------------------------------------------


@texclusive
class ColorMode:
    color: bool = targ(Flag, action="store_true")
    no_color: bool = targ(Flag, action="store_true")


@texclusive
class WidthMode:
    wide: bool = targ(Flag, action="store_true")
    narrow: bool = targ(Flag, action="store_true")


@tgroup("Display Settings")
class DisplayGroup:
    colors: ColorMode
    widths: WidthMode


@targs
class ArgsMultiExclusive:
    display: DisplayGroup


def test_multiple_exclusive_in_group():
    """Multiple texclusive groups can coexist inside a single tgroup."""
    parser = argparse.ArgumentParser()
    register_targs(parser, ArgsMultiExclusive)
    args = parser.parse_args(["--color", "--narrow"])
    result = extract_targs(args, ArgsMultiExclusive)
    assert result.display.colors.color is True
    assert result.display.colors.no_color is False
    assert result.display.widths.wide is False
    assert result.display.widths.narrow is True


def test_multiple_exclusive_in_group_conflict_within():
    """Conflict within one exclusive subgroup is still enforced."""
    parser = argparse.ArgumentParser()
    register_targs(parser, ArgsMultiExclusive)
    with pytest.raises(SystemExit):
        parser.parse_args(["--color", "--no-color"])


def test_multiple_exclusive_in_group_cross_group_ok():
    """Options from different exclusive subgroups don't conflict."""
    parser = argparse.ArgumentParser()
    register_targs(parser, ArgsMultiExclusive)
    args = parser.parse_args(["--no-color", "--wide"])
    result = extract_targs(args, ArgsMultiExclusive)
    assert result.display.colors.no_color is True
    assert result.display.widths.wide is True


# ---------------------------------------------------------------------------
# @tgroup with texclusive + regular args + create_parser
# ---------------------------------------------------------------------------


def test_nested_exclusive_with_create_parser():
    """create_parser works with nested texclusive inside tgroup."""
    from argparse_type_helper import create_parser

    parser = create_parser(ArgsWithNestedExclusive)
    args = parser.parse_args(["test", "--beta", "--tag", "v1"])
    result = extract_targs(args, ArgsWithNestedExclusive)
    assert result.name == "test"
    assert result.container.tag == "v1"
    assert result.container.choice.beta is True


# ---------------------------------------------------------------------------
# Invalid nesting (rejected at decoration time)
# ---------------------------------------------------------------------------


def test_tgroup_inside_tgroup_raises():
    """@tgroup nested inside @tgroup is rejected."""

    @tgroup
    class Inner:
        x: str = targ(Flag, default="a")

    with pytest.raises(
        TypeError, match="Only @texclusive can be nested inside @tgroup"
    ):

        @tgroup
        class Outer:
            inner: Inner


def test_tgroup_inside_texclusive_raises():
    """@tgroup nested inside @texclusive is rejected."""

    @tgroup
    class Inner:
        x: str = targ(Flag, default="a")

    with pytest.raises(TypeError, match="@texclusive cannot contain nested groups"):

        @texclusive
        class Outer:
            inner: Inner


def test_texclusive_inside_texclusive_raises():
    """@texclusive nested inside @texclusive is rejected."""

    @texclusive
    class Inner:
        x: bool = targ(Flag, action="store_true")

    with pytest.raises(TypeError, match="@texclusive cannot contain nested groups"):

        @texclusive
        class Outer:
            inner: Inner
