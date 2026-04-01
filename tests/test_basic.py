"""Tests for existing targs functionality: targ, Name, Flag, register_targs, extract_targs."""

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
)

# ---------------------------------------------------------------------------
# Basic positional and optional arguments
# ---------------------------------------------------------------------------


@targs
class BasicArgs:
    positional: str = targ(Name, help="A positional argument")
    optional: str = targ(Flag, default="default_val", help="An optional argument")


def test_basic_positional_and_optional():
    parser = argparse.ArgumentParser()
    register_targs(parser, BasicArgs)
    args = parser.parse_args(["hello", "--optional", "world"])
    result = extract_targs(args, BasicArgs)
    assert result.positional == "hello"
    assert result.optional == "world"


def test_basic_default_value():
    parser = argparse.ArgumentParser()
    register_targs(parser, BasicArgs)
    args = parser.parse_args(["hello"])
    result = extract_targs(args, BasicArgs)
    assert result.positional == "hello"
    assert result.optional == "default_val"


# ---------------------------------------------------------------------------
# Flag variants
# ---------------------------------------------------------------------------


@targs
class FlagVariants:
    simple: str = targ(Flag, default="x")
    with_dash: str = targ(Flag, default="y")
    with_short: str = targ(Flag("-s"), default="z")
    custom_long: str = targ("--my-custom", default="w")
    custom_pair: str = targ(("-c", "--my-pair"), default="v")


def test_flag_dash_conversion():
    """Underscore in attribute name becomes dash in flag."""
    parser = argparse.ArgumentParser()
    register_targs(parser, FlagVariants)
    args = parser.parse_args(["--with-dash", "val"])
    result = extract_targs(args, FlagVariants)
    assert result.with_dash == "val"


def test_flag_short_name():
    parser = argparse.ArgumentParser()
    register_targs(parser, FlagVariants)
    args = parser.parse_args(["-s", "short_val"])
    result = extract_targs(args, FlagVariants)
    assert result.with_short == "short_val"


def test_flag_custom_long():
    parser = argparse.ArgumentParser()
    register_targs(parser, FlagVariants)
    args = parser.parse_args(["--my-custom", "custom_val"])
    result = extract_targs(args, FlagVariants)
    assert result.custom_long == "custom_val"


def test_flag_custom_pair():
    parser = argparse.ArgumentParser()
    register_targs(parser, FlagVariants)
    args = parser.parse_args(["-c", "pair_val"])
    result = extract_targs(args, FlagVariants)
    assert result.custom_pair == "pair_val"

    args2 = parser.parse_args(["--my-pair", "pair_val2"])
    result2 = extract_targs(args2, FlagVariants)
    assert result2.custom_pair == "pair_val2"


# ---------------------------------------------------------------------------
# Custom positional name
# ---------------------------------------------------------------------------


@targs
class CustomNameArgs:
    custom_pos: str = targ("my_positional")


def test_custom_positional_name():
    parser = argparse.ArgumentParser()
    register_targs(parser, CustomNameArgs)
    args = parser.parse_args(["value"])
    result = extract_targs(args, CustomNameArgs)
    assert result.custom_pos == "value"


# ---------------------------------------------------------------------------
# Actions: store_true, append, extend, count, choices
# ---------------------------------------------------------------------------


@targs
class ActionArgs:
    flag: bool = targ(Flag, action="store_true")
    items: list[str] = targ(Flag, action="extend", nargs="+", default=[])
    choices: str = targ(Flag, choices=["a", "b", "c"], default="a")


def test_store_true_action():
    parser = argparse.ArgumentParser()
    register_targs(parser, ActionArgs)

    args = parser.parse_args(["--flag"])
    result = extract_targs(args, ActionArgs)
    assert result.flag is True

    args2 = parser.parse_args([])
    result2 = extract_targs(args2, ActionArgs)
    assert result2.flag is False


def test_extend_action():
    parser = argparse.ArgumentParser()
    register_targs(parser, ActionArgs)
    args = parser.parse_args(["--items", "x", "y", "--items", "z"])
    result = extract_targs(args, ActionArgs)
    assert result.items == ["x", "y", "z"]


def test_choices():
    parser = argparse.ArgumentParser()
    register_targs(parser, ActionArgs)
    args = parser.parse_args(["--choices", "b"])
    result = extract_targs(args, ActionArgs)
    assert result.choices == "b"


# ---------------------------------------------------------------------------
# Repr
# ---------------------------------------------------------------------------


def test_repr():
    parser = argparse.ArgumentParser()
    register_targs(parser, BasicArgs)
    args = parser.parse_args(["hello"])
    result = extract_targs(args, BasicArgs)
    r = repr(result)
    assert "BasicArgs" in r
    assert "hello" in r
    assert "default_val" in r


# ---------------------------------------------------------------------------
# Constructor
# ---------------------------------------------------------------------------


def test_constructor_direct():
    obj = BasicArgs(positional="a", optional="b")
    assert obj.positional == "a"
    assert obj.optional == "b"


def test_constructor_default():
    obj = BasicArgs(positional="a")
    assert obj.optional == "default_val"


def test_constructor_missing_required():
    with pytest.raises(ValueError, match="Missing required argument"):
        BasicArgs()


# ---------------------------------------------------------------------------
# Post-init
# ---------------------------------------------------------------------------


@targs
class PostInitArgs:
    value: int = targ(Name)

    @post_init
    def validate(self) -> None:
        if self.value < 0:
            raise ValueError("value must be non-negative")


def test_post_init_passes():
    parser = argparse.ArgumentParser()
    register_targs(parser, PostInitArgs)
    args = parser.parse_args(["42"])
    result = extract_targs(args, PostInitArgs)
    assert result.value == 42


def test_post_init_fails():
    with pytest.raises(ValueError, match="non-negative"):
        PostInitArgs(value=-1)


# ---------------------------------------------------------------------------
# Docstring as help text
# ---------------------------------------------------------------------------


@targs
class DocstringArgs:
    my_arg: str = targ(Flag, default="x")
    """This is the help from docstring."""


def test_docstring_help(capsys: pytest.CaptureFixture[str]):
    parser = argparse.ArgumentParser()
    register_targs(parser, DocstringArgs)
    parser.print_help()
    captured = capsys.readouterr()
    assert "This is the help from docstring." in captured.out


# ---------------------------------------------------------------------------
# Hybrid usage (mix targs with native add_argument)
# ---------------------------------------------------------------------------


@targs
class HybridArgs:
    typed_arg: str = targ(Name)


def test_hybrid_usage():
    parser = argparse.ArgumentParser()
    register_targs(parser, HybridArgs)
    parser.add_argument("--native", default="native_default")

    args = parser.parse_args(["hello", "--native", "native_val"])
    result = extract_targs(args, HybridArgs)
    assert result.typed_arg == "hello"
    assert args.native == "native_val"


# ---------------------------------------------------------------------------
# Subclassing
# ---------------------------------------------------------------------------


@targs
class ParentArgs:
    parent_arg: int = targ(Name)
    """parent arg"""

    @post_init
    def validate_parent(self) -> None:
        if self.parent_arg < 0:
            raise ValueError("parent_arg must be non-negative")


@targs
class ChildArgs(ParentArgs):
    child_arg: str = targ(Name)
    """child arg"""

    @post_init
    def validate_child(self) -> None:
        if self.child_arg == "bad":
            raise ValueError("child_arg cannot be 'bad'")


@targs
class GrandchildArgs(ChildArgs):
    grandchild_arg: float = targ(Name)


def test_subclass_inherits_args():
    parser = argparse.ArgumentParser()
    register_targs(parser, ChildArgs)
    args = parser.parse_args(["42", "hello"])
    result = extract_targs(args, ChildArgs)
    assert result.parent_arg == 42
    assert result.child_arg == "hello"


def test_subclass_inherits_post_init():
    with pytest.raises(ValueError, match="non-negative"):
        ChildArgs(parent_arg=-1, child_arg="ok")

    with pytest.raises(ValueError, match="cannot be 'bad'"):
        ChildArgs(parent_arg=1, child_arg="bad")


def test_grandchild():
    parser = argparse.ArgumentParser()
    register_targs(parser, GrandchildArgs)
    args = parser.parse_args(["10", "hello", "3.14"])
    result = extract_targs(args, GrandchildArgs)
    assert result.parent_arg == 10
    assert result.child_arg == "hello"
    assert result.grandchild_arg == 3.14


def test_subclass_docstring_help(capsys: pytest.CaptureFixture[str]):
    parser = argparse.ArgumentParser()
    register_targs(parser, ChildArgs)
    parser.print_help()
    captured = capsys.readouterr()
    assert "parent arg" in captured.out
    assert "child arg" in captured.out


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


class NotTargs:
    x: int = 5


def test_non_targs_class_raises():
    with pytest.raises(TypeError, match="not a targs class"):
        register_targs(argparse.ArgumentParser(), NotTargs)


@targs
class NoHint:
    x = targ(Name)  # type: ignore


def test_missing_type_hint_raises():
    with pytest.raises(TypeError, match="Type hint"):
        register_targs(argparse.ArgumentParser(), NoHint)


# ---------------------------------------------------------------------------
# Docstring extraction for inner (indented) classes
# ---------------------------------------------------------------------------


def test_inner_class_docstring_extraction():
    """textwrap.dedent fix: docstring extraction works for indented classes."""
    from argparse_type_helper._utils import get_attr_docstrings

    @targs
    class InnerArgs:
        field: str = targ(Flag, default="x")
        """Help from inner docstring."""

    docstrings = get_attr_docstrings(InnerArgs)
    assert docstrings.get("field") == "Help from inner docstring."


def test_inner_class_docstring_in_help(capsys: pytest.CaptureFixture[str]):
    """Docstrings from inner classes appear in help output."""

    @targs
    class InnerHelpArgs:
        inner_field: str = targ(Flag, default="y")
        """Inner field help text."""

    parser = argparse.ArgumentParser()
    register_targs(parser, InnerHelpArgs)
    parser.print_help()
    captured = capsys.readouterr()
    assert "Inner field help text." in captured.out


# ---------------------------------------------------------------------------
# Post-init failure via parse_args flow
# ---------------------------------------------------------------------------


def test_post_init_fails_via_parse_args():
    parser = argparse.ArgumentParser()
    register_targs(parser, PostInitArgs)
    args = parser.parse_args(["-1"])
    with pytest.raises(ValueError, match="non-negative"):
        extract_targs(args, PostInitArgs)


# ---------------------------------------------------------------------------
# Missing action types: store_false, store_const, append, count, append_const
# ---------------------------------------------------------------------------


@targs
class MoreActionArgs:
    no_color: bool = targ(Flag, action="store_false")
    mode: str = targ(Flag, action="store_const", const="debug", default="release")
    items: list[str] = targ(Flag, action="append", default=[])
    verbosity: int = targ(Flag("-v"), action="count", default=0)
    tags: list[str] = targ(Flag, action="append_const", const="latest", default=[])


def test_store_false_action():
    parser = argparse.ArgumentParser()
    register_targs(parser, MoreActionArgs)

    args = parser.parse_args(["--no-color"])
    result = extract_targs(args, MoreActionArgs)
    assert result.no_color is False

    args2 = parser.parse_args([])
    result2 = extract_targs(args2, MoreActionArgs)
    assert result2.no_color is True


def test_store_const_action():
    parser = argparse.ArgumentParser()
    register_targs(parser, MoreActionArgs)

    args = parser.parse_args(["--mode"])
    result = extract_targs(args, MoreActionArgs)
    assert result.mode == "debug"

    args2 = parser.parse_args([])
    result2 = extract_targs(args2, MoreActionArgs)
    assert result2.mode == "release"


def test_append_action():
    parser = argparse.ArgumentParser()
    register_targs(parser, MoreActionArgs)
    args = parser.parse_args(["--items", "x", "--items", "y"])
    result = extract_targs(args, MoreActionArgs)
    assert result.items == ["x", "y"]


def test_count_action():
    parser = argparse.ArgumentParser()
    register_targs(parser, MoreActionArgs)
    args = parser.parse_args(["-vvv"])
    result = extract_targs(args, MoreActionArgs)
    assert result.verbosity == 3


def test_append_const_action():
    parser = argparse.ArgumentParser()
    register_targs(parser, MoreActionArgs)
    args = parser.parse_args(["--tags", "--tags"])
    result = extract_targs(args, MoreActionArgs)
    assert result.tags == ["latest", "latest"]


# ---------------------------------------------------------------------------
# Custom argparse.Action subclass
# ---------------------------------------------------------------------------


class UpperAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):  # type: ignore[override]
        setattr(namespace, self.dest, str(values).upper())


@targs
class CustomActionArgs:
    name: str = targ(Flag, action=UpperAction, default="default")


def test_custom_action():
    parser = argparse.ArgumentParser()
    register_targs(parser, CustomActionArgs)
    args = parser.parse_args(["--name", "hello"])
    result = extract_targs(args, CustomActionArgs)
    assert result.name == "HELLO"


def test_custom_action_default():
    parser = argparse.ArgumentParser()
    register_targs(parser, CustomActionArgs)
    args = parser.parse_args([])
    result = extract_targs(args, CustomActionArgs)
    assert result.name == "default"


# ---------------------------------------------------------------------------
# Missing parameter config tests: nargs, required, metavar, dest
# ---------------------------------------------------------------------------


@targs
class NargsArgs:
    optional_pos: str = targ(Name, nargs="?", default="default_pos")
    multi: list[str] = targ(Name, nargs="*")
    exactly_two: list[str] = targ(Flag, nargs=2, default=["a", "b"])


def test_nargs_optional():
    parser = argparse.ArgumentParser()
    register_targs(parser, NargsArgs)
    args = parser.parse_args([])
    result = extract_targs(args, NargsArgs)
    assert result.optional_pos == "default_pos"
    assert result.multi == []


def test_nargs_int():
    parser = argparse.ArgumentParser()
    register_targs(parser, NargsArgs)
    args = parser.parse_args(["val", "x", "y", "--exactly-two", "p", "q"])
    result = extract_targs(args, NargsArgs)
    assert result.optional_pos == "val"
    assert result.multi == ["x", "y"]
    assert result.exactly_two == ["p", "q"]


@targs
class RequiredFlagArgs:
    name: str = targ(Flag, required=True)


def test_required_flag():
    parser = argparse.ArgumentParser()
    register_targs(parser, RequiredFlagArgs)
    args = parser.parse_args(["--name", "hello"])
    result = extract_targs(args, RequiredFlagArgs)
    assert result.name == "hello"


def test_required_flag_missing():
    parser = argparse.ArgumentParser()
    register_targs(parser, RequiredFlagArgs)
    with pytest.raises(SystemExit):
        parser.parse_args([])


@targs
class MetavarArgs:
    output: str = targ(Flag, metavar="FILE", default="out.txt")


def test_metavar_in_help(capsys: pytest.CaptureFixture[str]):
    parser = argparse.ArgumentParser()
    register_targs(parser, MetavarArgs)
    parser.print_help()
    captured = capsys.readouterr()
    assert "FILE" in captured.out


@targs
class DestArgs:
    output_file: str = targ(Flag, dest="output", default="out.txt")


def test_custom_dest():
    parser = argparse.ArgumentParser()
    register_targs(parser, DestArgs)
    args = parser.parse_args(["--output-file", "result.txt"])
    result = extract_targs(args, DestArgs)
    assert result.output_file == "result.txt"


# ---------------------------------------------------------------------------
# Subclass scenarios: multi-level inheritance with post_init at each level
# ---------------------------------------------------------------------------


@targs
class SubclassParent:
    a: int = targ(Name)

    @post_init
    def validate_a(self) -> None:
        if self.a < 0:
            raise ValueError("a must be non-negative")


@targs
class SubclassChild(SubclassParent):
    b: str = targ(Name)

    @post_init
    def validate_b(self) -> None:
        if self.b == "bad":
            raise ValueError("b cannot be 'bad'")


@targs
class SubclassGrandchild(SubclassChild):
    c: float = targ(Name)

    @post_init
    def validate_c(self) -> None:
        if self.c < 0:
            raise ValueError("c must be non-negative")


def test_multilevel_post_init_via_parse_args():
    """Post-init at each level fires during parse_args flow."""
    parser = argparse.ArgumentParser()
    register_targs(parser, SubclassGrandchild)
    args = parser.parse_args(["10", "good", "3.14"])
    result = extract_targs(args, SubclassGrandchild)
    assert result.a == 10
    assert result.b == "good"
    assert result.c == 3.14


def test_multilevel_post_init_parent_fails_via_parse_args():
    parser = argparse.ArgumentParser()
    register_targs(parser, SubclassGrandchild)
    args = parser.parse_args(["-1", "good", "3.14"])
    with pytest.raises(ValueError, match="a must be non-negative"):
        extract_targs(args, SubclassGrandchild)


def test_multilevel_post_init_child_fails_via_parse_args():
    parser = argparse.ArgumentParser()
    register_targs(parser, SubclassGrandchild)
    args = parser.parse_args(["10", "bad", "3.14"])
    with pytest.raises(ValueError, match="b cannot be 'bad'"):
        extract_targs(args, SubclassGrandchild)


def test_multilevel_post_init_grandchild_fails_via_parse_args():
    parser = argparse.ArgumentParser()
    register_targs(parser, SubclassGrandchild)
    args = parser.parse_args(["10", "good", "-1.0"])
    with pytest.raises(ValueError, match="c must be non-negative"):
        extract_targs(args, SubclassGrandchild)


# ---------------------------------------------------------------------------
# Subclass scenarios: sibling classes from same parent
# ---------------------------------------------------------------------------


@targs
class SiblingParent:
    a: str = targ(Name)


@targs
class SiblingChildB(SiblingParent):
    b: int = targ(Name)


@targs
class SiblingChildC(SiblingParent):
    c: float = targ(Name)


def test_sibling_classes_independent():
    """Sibling classes from same parent don't interfere with each other."""
    parser_b = argparse.ArgumentParser()
    register_targs(parser_b, SiblingChildB)
    args_b = parser_b.parse_args(["hello", "42"])
    result_b = extract_targs(args_b, SiblingChildB)
    assert result_b.a == "hello"
    assert result_b.b == 42

    parser_c = argparse.ArgumentParser()
    register_targs(parser_c, SiblingChildC)
    args_c = parser_c.parse_args(["world", "3.14"])
    result_c = extract_targs(args_c, SiblingChildC)
    assert result_c.a == "world"
    assert result_c.c == 3.14


def test_sibling_parent_has_only_own_args():
    """Parent class only has its own args, not children's."""
    parser = argparse.ArgumentParser()
    register_targs(parser, SiblingParent)
    args = parser.parse_args(["test"])
    result = extract_targs(args, SiblingParent)
    assert result.a == "test"
    assert not hasattr(result, "b")
    assert not hasattr(result, "c")


# ---------------------------------------------------------------------------
# Mutable defaults
# ---------------------------------------------------------------------------


@targs
class MutableDefaultArgs:
    items: list[str] = targ(Flag, action="extend", nargs="+", default=[])
    tags: dict[str, str] = targ(Flag, type=str, default={})


def test_mutable_default_list_independence():
    """Each instance gets its own list, not a shared reference."""
    a = MutableDefaultArgs()
    b = MutableDefaultArgs()
    a.items.append("x")
    assert b.items == []


def test_mutable_default_dict_independence():
    """Each instance gets its own dict, not a shared reference."""
    a = MutableDefaultArgs()
    b = MutableDefaultArgs()
    a.tags["key"] = "val"  # type: ignore[index]
    assert b.tags == {}


@targs
class SetDefaultArgs:
    items: set[str] = targ(Flag, type=str, default=set[str]())


def test_mutable_default_set_independence():
    """Each instance gets its own set, not a shared reference."""
    a = SetDefaultArgs()
    b = SetDefaultArgs()
    a.items.add("x")  # type: ignore[union-attr]
    assert b.items == set()


# ---------------------------------------------------------------------------
# extract_targs / get_targs error paths
# ---------------------------------------------------------------------------


def test_extract_targs_missing_dest():
    """extract_targs raises AttributeError when dest is missing from namespace."""
    parser = create_parser(BasicArgs)
    args = parser.parse_args(["hello"])
    delattr(args, "positional")
    with pytest.raises(AttributeError, match="not found in parsed args"):
        extract_targs(args, BasicArgs)


def test_get_targs_error_on_non_targs_class():
    """get_targs raises TypeError on a class without @targs."""
    from argparse_type_helper._types import get_targs

    class Plain:
        pass

    with pytest.raises(TypeError, match="not a targs class"):
        get_targs(Plain, check=True)


# ---------------------------------------------------------------------------
# Invalid choices
# ---------------------------------------------------------------------------


@targs
class ChoicesArgs:
    mode: str = targ(Flag, choices=["fast", "slow"], default="fast")


def test_invalid_choice_exits():
    """argparse exits when an invalid choice is provided."""
    parser = argparse.ArgumentParser()
    register_targs(parser, ChoicesArgs)
    with pytest.raises(SystemExit):
        parser.parse_args(["--mode", "invalid"])
