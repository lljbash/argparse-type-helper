"""Tests for create_parser, docstring → description/title, and mutable defaults."""

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
    tgroup,
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


# ---------------------------------------------------------------------------
# @tgroup docstring → title/description split
# ---------------------------------------------------------------------------


@tgroup
class DocstringGroup:
    """Database connection

    Configure database host and port for the application.
    """

    host: str = targ(Flag, default="localhost")
    port: int = targ(Flag, default=5432)


@targs
class GroupDocArgs:
    db: DocstringGroup


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
    parser = argparse.ArgumentParser()
    register_targs(parser, ExplicitGroupArgs)
    parser.print_help()
    captured = capsys.readouterr()
    assert "Explicit Title" in captured.out
    assert "This docstring title is ignored" not in captured.out


def test_tgroup_explicit_title_docstring_description(
    capsys: pytest.CaptureFixture[str],
):
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
    parser = argparse.ArgumentParser()
    register_targs(parser, FullyExplicitGroupArgs)
    parser.print_help()
    captured = capsys.readouterr()
    assert "T" in captured.out
    assert "Explicit description" in captured.out
    assert "Ignored" not in captured.out


# ---------------------------------------------------------------------------
# @tsubcommands docstring → title/description split
# ---------------------------------------------------------------------------


@tsubcommands
class DocCommands:
    """Available commands

    Choose one of the available commands below.
    """


@targs
class doc_cmd_a(DocCommands):
    """Start the service

    Start the background service with the specified port.
    """

    port: int = targ(Flag, default=8080)


@targs
class ArgsDocSubcommands:
    cmd: DocCommands


def test_tsubcommands_docstring_title(capsys: pytest.CaptureFixture[str]):
    parser = argparse.ArgumentParser()
    register_targs(parser, ArgsDocSubcommands)
    parser.print_help()
    captured = capsys.readouterr()
    assert "Available commands" in captured.out


def test_subcommand_help_uses_title(capsys: pytest.CaptureFixture[str]):
    """Subcommand help in the listing uses only the first line."""
    parser = argparse.ArgumentParser()
    register_targs(parser, ArgsDocSubcommands)
    parser.print_help()
    captured = capsys.readouterr()
    assert "Start the service" in captured.out


def test_subcommand_parser_description_uses_full(capsys: pytest.CaptureFixture[str]):
    """The sub-parser description uses the full docstring."""
    parser = argparse.ArgumentParser()
    register_targs(parser, ArgsDocSubcommands)
    # Parse a specific subcommand and check its help output
    sub_parser = argparse.ArgumentParser()
    register_targs(sub_parser, doc_cmd_a)
    sub_parser.print_help()
    captured = capsys.readouterr()
    assert "Start the service" in captured.out
    assert "Start the background service" in captured.out


# ---------------------------------------------------------------------------
# Mutable default value fix
# ---------------------------------------------------------------------------


@targs
class MutableDefaultArgs:
    items: list[str] = targ(Flag, action="extend", nargs="+", default=[])
    tags: dict[str, str] = targ(Flag, type=str, default={})


def test_mutable_default_list_independence():
    """Each instance gets its own list, not shared reference."""
    a = MutableDefaultArgs()
    b = MutableDefaultArgs()
    a.items.append("x")
    assert b.items == []


def test_mutable_default_dict_independence():
    """Each instance gets its own dict, not shared reference."""
    a = MutableDefaultArgs()
    b = MutableDefaultArgs()
    a.tags["key"] = "val"  # type: ignore[index]
    assert b.tags == {}


# ---------------------------------------------------------------------------
# DocString robustness (dynamic classes)
# ---------------------------------------------------------------------------


def test_get_attr_docstrings_dynamic_class():
    """Dynamic classes (no source) don't crash docstring extraction."""
    from argparse_type_helper._utils import get_attr_docstrings

    DynClass = type("DynClass", (), {"x": 1})
    result = get_attr_docstrings(DynClass)
    assert result == {}
