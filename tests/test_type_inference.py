"""Tests for expanded type inference in _register_single_targ / _infer_type_from_hint."""

import argparse
from collections.abc import Sequence
from typing import Optional  # pyright: ignore[reportDeprecated]

from argparse_type_helper import (
    Flag,
    Name,
    extract_targs,
    register_targs,
    targ,
    targs,
)

# ---------------------------------------------------------------------------
# X | None inference
# ---------------------------------------------------------------------------


@targs
class OptionalTypeArgs:
    ratio: float | None = targ(Flag, default=None)
    count: int | None = targ(Flag, default=None)
    name: str | None = targ(Flag, default=None)


def test_float_or_none_inference():
    parser = argparse.ArgumentParser()
    register_targs(parser, OptionalTypeArgs)
    args = parser.parse_args(["--ratio", "3.14"])
    result = extract_targs(args, OptionalTypeArgs)
    assert result.ratio == 3.14
    assert isinstance(result.ratio, float)


def test_int_or_none_inference():
    parser = argparse.ArgumentParser()
    register_targs(parser, OptionalTypeArgs)
    args = parser.parse_args(["--count", "42"])
    result = extract_targs(args, OptionalTypeArgs)
    assert result.count == 42
    assert isinstance(result.count, int)


def test_str_or_none_inference():
    parser = argparse.ArgumentParser()
    register_targs(parser, OptionalTypeArgs)
    args = parser.parse_args(["--name", "hello"])
    result = extract_targs(args, OptionalTypeArgs)
    assert result.name == "hello"


def test_optional_defaults_to_none():
    parser = argparse.ArgumentParser()
    register_targs(parser, OptionalTypeArgs)
    args = parser.parse_args([])
    result = extract_targs(args, OptionalTypeArgs)
    assert result.ratio is None
    assert result.count is None
    assert result.name is None


# ---------------------------------------------------------------------------
# typing.Optional[X] inference
# ---------------------------------------------------------------------------


@targs
class TypingOptionalArgs:
    value: Optional[float] = targ(  # pyright: ignore[reportDeprecated]
        Flag, default=None
    )


def test_typing_optional_inference():
    parser = argparse.ArgumentParser()
    register_targs(parser, TypingOptionalArgs)
    args = parser.parse_args(["--value", "2.5"])
    result = extract_targs(args, TypingOptionalArgs)
    assert result.value == 2.5
    assert isinstance(result.value, float)


# ---------------------------------------------------------------------------
# list[X] / Sequence[X] with nargs inference
# ---------------------------------------------------------------------------


@targs
class ListTypeArgs:
    numbers: list[int] = targ(Flag, nargs="+", default=[])
    names: list[str] = targ(Name, nargs="*")


def test_list_int_nargs_inference():
    parser = argparse.ArgumentParser()
    register_targs(parser, ListTypeArgs)
    args = parser.parse_args(["--numbers", "1", "2", "3"])
    result = extract_targs(args, ListTypeArgs)
    assert result.numbers == [1, 2, 3]
    assert all(isinstance(n, int) for n in result.numbers)


def test_list_str_nargs_star():
    parser = argparse.ArgumentParser()
    register_targs(parser, ListTypeArgs)
    args = parser.parse_args(["a", "b", "c"])
    result = extract_targs(args, ListTypeArgs)
    assert result.names == ["a", "b", "c"]


# ---------------------------------------------------------------------------
# Sequence[X] with nargs inference (recommended over list[X])
# ---------------------------------------------------------------------------


@targs
class SequenceTypeArgs:
    numbers: Sequence[int] = targ(Flag, nargs="+", default=[])
    names: Sequence[str] = targ(Name, nargs="*")


def test_sequence_int_nargs_inference():
    parser = argparse.ArgumentParser()
    register_targs(parser, SequenceTypeArgs)
    args = parser.parse_args(["--numbers", "1", "2", "3"])
    result = extract_targs(args, SequenceTypeArgs)
    assert result.numbers == [1, 2, 3]
    assert all(isinstance(n, int) for n in result.numbers)


def test_sequence_str_nargs_star():
    parser = argparse.ArgumentParser()
    register_targs(parser, SequenceTypeArgs)
    args = parser.parse_args(["a", "b", "c"])
    result = extract_targs(args, SequenceTypeArgs)
    assert result.names == ["a", "b", "c"]


# ---------------------------------------------------------------------------
# bool protection — should NOT auto-infer type
# ---------------------------------------------------------------------------


@targs
class BoolActionArgs:
    flag: bool = targ(Flag, action="store_true")
    no_flag: bool = targ(Flag, action="store_false")


def test_bool_with_action_works():
    """Bool with explicit action should work fine."""
    parser = argparse.ArgumentParser()
    register_targs(parser, BoolActionArgs)
    args = parser.parse_args(["--flag"])
    result = extract_targs(args, BoolActionArgs)
    assert result.flag is True
    assert result.no_flag is True  # store_false default is True


@targs
class BoolOrNoneArgs:
    opt_flag: bool | None = targ(Flag, action="store_true")


def test_bool_or_none_with_action():
    """bool | None with explicit action should work."""
    parser = argparse.ArgumentParser()
    register_targs(parser, BoolOrNoneArgs)
    args = parser.parse_args(["--opt-flag"])
    result = extract_targs(args, BoolOrNoneArgs)
    assert result.opt_flag is True


# ---------------------------------------------------------------------------
# Bare callable types (existing behavior preserved)
# ---------------------------------------------------------------------------


@targs
class BareTypeArgs:
    count: int = targ(Flag, default=0)
    ratio: float = targ(Flag, default=1.0)
    name: str = targ(Name)


def test_bare_int_inference():
    parser = argparse.ArgumentParser()
    register_targs(parser, BareTypeArgs)
    args = parser.parse_args(["hello", "--count", "42"])
    result = extract_targs(args, BareTypeArgs)
    assert result.count == 42
    assert isinstance(result.count, int)


def test_bare_float_inference():
    parser = argparse.ArgumentParser()
    register_targs(parser, BareTypeArgs)
    args = parser.parse_args(["hello", "--ratio", "2.5"])
    result = extract_targs(args, BareTypeArgs)
    assert result.ratio == 2.5


# ---------------------------------------------------------------------------
# Non-inferable types (should not crash)
# ---------------------------------------------------------------------------


@targs
class AmbiguousUnionArgs:
    val: int | str = targ(Flag, type=str, default="x")


def test_ambiguous_union_with_explicit_type():
    """int | str can't be inferred but explicit type= works."""
    parser = argparse.ArgumentParser()
    register_targs(parser, AmbiguousUnionArgs)
    args = parser.parse_args(["--val", "hello"])
    result = extract_targs(args, AmbiguousUnionArgs)
    assert result.val == "hello"


# ---------------------------------------------------------------------------
# Explicit type= still takes priority
# ---------------------------------------------------------------------------


@targs
class ExplicitTypeArgs:
    value: float = targ(Flag, type=lambda x: round(float(x), 1), default=0.0)


def test_explicit_type_overrides_inference():
    parser = argparse.ArgumentParser()
    register_targs(parser, ExplicitTypeArgs)
    args = parser.parse_args(["--value", "3.456"])
    result = extract_targs(args, ExplicitTypeArgs)
    assert result.value == 3.5
