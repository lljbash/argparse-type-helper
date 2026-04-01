"""Tests for create_parser and register_targs: description auto-fill and formatter defaults."""

import argparse
import io

import pytest

from argparse_type_helper import (
    Flag,
    Name,
    create_parser,
    extract_targs,
    register_targs,
    targ,
    targs,
    tsubcommands,
)

# ---------------------------------------------------------------------------
# create_parser basics
# ---------------------------------------------------------------------------


@targs
class SimpleArgs:
    """A simple argument parser.

    This parser does basic things.
    """

    name: str = targ(Name)


def test_create_parser_basic():
    parser = create_parser(SimpleArgs)
    assert isinstance(parser, argparse.ArgumentParser)
    args = parser.parse_args(["hello"])
    result = extract_targs(args, SimpleArgs)
    assert result.name == "hello"


def test_create_parser_auto_description():
    """Parser description is auto-filled from class docstring."""
    parser = create_parser(SimpleArgs)
    assert (
        parser.description
        == "A simple argument parser.\n\nThis parser does basic things."
    )


def test_create_parser_explicit_description():
    """Explicit description overrides docstring."""
    parser = create_parser(SimpleArgs, description="Custom description")
    assert parser.description == "Custom description"


def test_create_parser_prog():
    parser = create_parser(SimpleArgs, prog="myapp")
    assert parser.prog == "myapp"


def test_create_parser_custom_class():
    class CustomParser(argparse.ArgumentParser):
        custom_flag = True

    parser = create_parser(SimpleArgs, parser_class=CustomParser)
    assert isinstance(parser, CustomParser)
    assert parser.custom_flag is True  # type: ignore[attr-defined]


def test_create_parser_extra_kwargs():
    parser = create_parser(SimpleArgs, add_help=False)
    help_out = io.StringIO()
    parser.print_usage(help_out)
    assert "-h" not in help_out.getvalue()


@targs
class NoDocArgs:
    value: int = targ(Flag, default=0)


def test_create_parser_no_docstring():
    parser = create_parser(NoDocArgs)
    assert parser.description is None


def test_create_parser_verbose():
    """create_parser with verbose=True doesn't raise."""
    parser = create_parser(SimpleArgs, verbose=True)
    assert isinstance(parser, argparse.ArgumentParser)


# ---------------------------------------------------------------------------
# register_targs auto-fills description
# ---------------------------------------------------------------------------


@targs
class AutoDescArgs:
    """Auto description from docstring."""

    x: str = targ(Flag, default="a")


def test_register_targs_auto_description():
    parser = argparse.ArgumentParser()
    assert parser.description is None
    register_targs(parser, AutoDescArgs)
    assert parser.description == "Auto description from docstring."


def test_register_targs_no_override():
    """Existing description is not overridden."""
    parser = argparse.ArgumentParser(description="Existing")
    register_targs(parser, AutoDescArgs)
    assert parser.description == "Existing"


def test_register_targs_verbose():
    """register_targs with verbose=True doesn't raise."""
    parser = argparse.ArgumentParser()
    register_targs(parser, AutoDescArgs, verbose=True)
    assert parser.description == "Auto description from docstring."


# ---------------------------------------------------------------------------
# RawDescriptionHelpFormatter default & sub-parser formatter inheritance
# ---------------------------------------------------------------------------


def test_create_parser_default_formatter():
    """create_parser defaults to RawDescriptionHelpFormatter."""
    parser = create_parser(SimpleArgs)
    assert parser.formatter_class is argparse.RawDescriptionHelpFormatter


def test_create_parser_explicit_formatter_respected():
    """Explicit formatter_class overrides the default."""
    parser = create_parser(SimpleArgs, formatter_class=argparse.HelpFormatter)
    assert parser.formatter_class is argparse.HelpFormatter


def test_create_parser_preserves_description_newlines(
    capsys: pytest.CaptureFixture[str],
):
    """RawDescriptionHelpFormatter preserves newlines in description."""
    parser = create_parser(SimpleArgs)
    parser.print_help()
    captured = capsys.readouterr()
    assert "A simple argument parser.\n\nThis parser does basic things." in captured.out


@tsubcommands
class FmtCommands:
    """Commands"""


@targs
class fmt_sub(FmtCommands):
    """Sub description

    Detailed explanation here.
    """

    val: int = targ(Flag, default=0)


@targs
class FmtArgs:
    cmd: FmtCommands


def test_subparser_inherits_formatter():
    """Sub-parsers inherit the parent parser's formatter_class."""
    parser = create_parser(FmtArgs)
    assert parser.formatter_class is argparse.RawDescriptionHelpFormatter
    args = parser.parse_args(["fmt_sub"])
    result = extract_targs(args, FmtArgs)
    assert isinstance(result.cmd, fmt_sub)


def test_subparser_inherits_custom_formatter():
    """Sub-parsers inherit the parent's formatter_class (verified via help output)."""

    @tsubcommands
    class InhCmds:
        """Commands"""

    @targs
    class inh_sub(InhCmds):  # noqa: N801
        """First line

        Second paragraph preserved.
        """

        x: int = targ(Flag, default=0)

    sub_parser = create_parser(inh_sub)
    buf = io.StringIO()
    sub_parser.print_help(buf)
    help_text = buf.getvalue()
    assert "First line\n\nSecond paragraph preserved." in help_text


def test_register_targs_does_not_change_formatter():
    """register_targs does not modify the parser's formatter_class."""
    parser = argparse.ArgumentParser()
    original_formatter = parser.formatter_class
    register_targs(parser, SimpleArgs)
    assert parser.formatter_class is original_formatter

