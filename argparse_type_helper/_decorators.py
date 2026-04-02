import copy
from collections.abc import Sequence
from typing import (
    Any,
    Callable,
    cast,
    dataclass_transform,
    get_type_hints,
    overload,
)

from argparse_type_helper._docstring import DocString
from argparse_type_helper._types import (
    TARGS_FLAG_ATTR,
    TARGS_GROUPS_ATTR,
    TARGS_POST_INIT_ATTR,
    TARGS_SUBCOMMANDS_ATTR,
    TEXCLUSIVE_FLAG_ATTR,
    TEXCLUSIVE_REQUIRED_ATTR,
    TGROUP_DESCRIPTION_ATTR,
    TGROUP_FLAG_ATTR,
    TGROUP_TITLE_ATTR,
    TSUBCOMMAND_ALIASES_ATTR,
    TSUBCOMMAND_FLAG_ATTR,
    TSUBCOMMAND_NAME_ATTR,
    TSUBCOMMANDS_DESCRIPTION_ATTR,
    TSUBCOMMANDS_FLAG_ATTR,
    TSUBCOMMANDS_REQUIRED_ATTR,
    TSUBCOMMANDS_TITLE_ATTR,
    TArg,
    Unset,
    check_and_maybe_init_targs_class,
    get_targs,
    is_group_like,
    is_tsubcommands_class,
    targ,
)
from argparse_type_helper._utils import is_sentry

__all__ = [
    "targs",
    "tgroup",
    "texclusive",
    "tsubcommands",
    "tsubcommand",
]


# ---------------------------------------------------------------------------
# Scan type hints for group / subcommand references
# ---------------------------------------------------------------------------


def _scan_special_attrs(cls: type[object]) -> tuple[dict[str, type], dict[str, type]]:
    """Scan type hints for tgroup/texclusive/tsubcommands references.

    Returns (groups_dict, subcommands_dict) mapping attr name -> class.
    """
    groups: dict[str, type] = {}
    subcommands: dict[str, type] = {}
    hints = get_type_hints(cls)
    own_annotations = cls.__annotations__ if hasattr(cls, "__annotations__") else {}
    for attr in own_annotations:
        hint = hints.get(attr)
        if hint is None:
            continue
        if is_group_like(hint):
            groups[attr] = hint
        elif is_tsubcommands_class(hint):
            subcommands[attr] = hint
    return groups, subcommands


# ---------------------------------------------------------------------------
# @targs decorator
# ---------------------------------------------------------------------------


@dataclass_transform(kw_only_default=True, field_specifiers=(targ, TArg))
def targs[T](cls: type[T]) -> type[T]:
    """Decorator to transform a class into a targs class.

    Note:
        TARGS_ATTR: auto-filled by TArg descriptors via __set_name__
        TARGS_GROUPS_ATTR / TARGS_SUBCOMMANDS_ATTR: manually populated by _scan_special_attrs()
    """

    # Scan for groups and subcommands before generating __init__
    own_groups, own_subcommands = _scan_special_attrs(cls)
    # Merge with inherited
    inherited_groups: dict[str, type] = copy.copy(getattr(cls, TARGS_GROUPS_ATTR, {}))
    inherited_subcommands: dict[str, type] = copy.copy(
        getattr(cls, TARGS_SUBCOMMANDS_ATTR, {})
    )
    inherited_groups.update(own_groups)
    inherited_subcommands.update(own_subcommands)
    setattr(cls, TARGS_GROUPS_ATTR, inherited_groups)
    setattr(cls, TARGS_SUBCOMMANDS_ATTR, inherited_subcommands)

    def __init__(self: T, **kwargs: Any) -> None:
        targs_dict = get_targs(self.__class__)
        for attr, arg_config in targs_dict.items():
            if attr in kwargs:
                setattr(self, attr, kwargs[attr])
            elif is_sentry(arg_config.default, Unset):
                raise ValueError(f"Missing required argument: {attr}")
            else:
                default: Any = arg_config.default
                # Copy mutable defaults to avoid shared reference across instances
                if isinstance(default, (list, dict, set)):
                    default = copy.copy(cast(Any, default))
                setattr(self, attr, default)

        # Set group attributes
        groups = getattr(self.__class__, TARGS_GROUPS_ATTR, {})
        for attr in groups:
            if attr in kwargs:
                setattr(self, attr, kwargs[attr])
            else:
                raise ValueError(f"Missing required group: {attr}")

        # Set subcommand attributes (default to None if not provided)
        subcommands = getattr(self.__class__, TARGS_SUBCOMMANDS_ATTR, {})
        for attr in subcommands:
            setattr(self, attr, kwargs.get(attr, None))

        for base_cls in reversed(type(self).__mro__):
            if not hasattr(base_cls, TARGS_FLAG_ATTR):
                continue
            for _, member in base_cls.__dict__.items():
                if callable(member) and getattr(member, TARGS_POST_INIT_ATTR, False):
                    member(self)

    def __repr__(self: T) -> str:
        parts: list[str] = []
        targs_attrs = get_targs(self.__class__).keys()
        for attr in targs_attrs:
            parts.append(f"{attr}={getattr(self, attr)!r}")
        groups = getattr(self.__class__, TARGS_GROUPS_ATTR, {})
        for attr in groups:
            parts.append(f"{attr}={getattr(self, attr)!r}")
        subcommands = getattr(self.__class__, TARGS_SUBCOMMANDS_ATTR, {})
        for attr in subcommands:
            parts.append(f"{attr}={getattr(self, attr)!r}")
        return f"{self.__class__.__name__}({', '.join(parts)})"

    cls.__init__ = __init__
    cls.__repr__ = __repr__

    check_and_maybe_init_targs_class(cls, raise_instead_of_init=False)
    return cls


# ---------------------------------------------------------------------------
# @tgroup decorator
# ---------------------------------------------------------------------------


@dataclass_transform(kw_only_default=True, field_specifiers=(targ, TArg))
def _apply_tgroup(
    cls: type[Any],
    title: str | None,
    description: str | None,
) -> type[Any]:
    """Internal: apply tgroup metadata + targs to a class."""
    cls = targs(cls)
    setattr(cls, TGROUP_FLAG_ATTR, True)
    doc = DocString.parse(cls.__doc__)
    setattr(cls, TGROUP_TITLE_ATTR, title or doc.title or cls.__name__)
    setattr(cls, TGROUP_DESCRIPTION_ATTR, description or doc.description)
    return cls


@overload
def tgroup(cls_or_title: type[Any]) -> type[Any]: ...


@overload
def tgroup(cls_or_title: str, /) -> Callable[[type[Any]], type[Any]]: ...


@overload
def tgroup(
    *,
    title: str | None = None,
    description: str | None = None,
) -> Callable[[type[Any]], type[Any]]: ...


def tgroup(
    cls_or_title: type[Any] | str | None = None,
    *,
    title: str | None = None,
    description: str | None = None,
) -> Any:
    """Decorator to mark a class as an argument group.

    Usage:
        @tgroup                          # title defaults to class name
        @tgroup("Custom Title")          # title as positional arg
        @tgroup(title="...", description="...")
    """
    if isinstance(cls_or_title, type):
        # Called as @tgroup without arguments
        return _apply_tgroup(cls_or_title, title=title, description=description)
    elif isinstance(cls_or_title, str):
        # Called as @tgroup("title")
        actual_title = cls_or_title

        def decorator(cls: type[Any]) -> type[Any]:
            return _apply_tgroup(cls, title=actual_title, description=description)

        return decorator
    else:
        # Called as @tgroup(title="...", description="...")
        def decorator(cls: type[Any]) -> type[Any]:
            return _apply_tgroup(cls, title=title, description=description)

        return decorator


# ---------------------------------------------------------------------------
# @texclusive decorator
# ---------------------------------------------------------------------------


@dataclass_transform(kw_only_default=True, field_specifiers=(targ, TArg))
def _apply_texclusive(
    cls: type[Any],
    required: bool,
) -> type[Any]:
    """Internal: apply texclusive metadata + targs to a class."""
    cls = targs(cls)
    setattr(cls, TEXCLUSIVE_FLAG_ATTR, True)
    setattr(cls, TEXCLUSIVE_REQUIRED_ATTR, required)
    return cls


@overload
def texclusive(cls: type[Any]) -> type[Any]: ...


@overload
def texclusive(
    *,
    required: bool = False,
) -> Callable[[type[Any]], type[Any]]: ...


def texclusive(
    cls: type[Any] | None = None,
    *,
    required: bool = False,
) -> Any:
    """Decorator to mark a class as a mutually exclusive argument group.

    Usage:
        @texclusive                  # required defaults to False
        @texclusive(required=True)
    """
    if isinstance(cls, type):
        # Called as @texclusive without arguments
        return _apply_texclusive(cls, required=required)
    else:
        # Called as @texclusive(required=...)
        def decorator(inner_cls: type[Any]) -> type[Any]:
            return _apply_texclusive(inner_cls, required=required)

        return decorator


# ---------------------------------------------------------------------------
# @tsubcommands decorator
# ---------------------------------------------------------------------------


def _apply_tsubcommands(
    cls: type[Any],
    title: str | None,
    description: str | None,
    required: bool | None,
) -> type[Any]:
    """Internal: apply tsubcommands metadata to a class."""
    setattr(cls, TSUBCOMMANDS_FLAG_ATTR, True)
    doc = DocString.parse(cls.__doc__)
    setattr(cls, TSUBCOMMANDS_TITLE_ATTR, title or doc.title)
    setattr(cls, TSUBCOMMANDS_DESCRIPTION_ATTR, description or doc.description)
    setattr(cls, TSUBCOMMANDS_REQUIRED_ATTR, required)
    return cls


@overload
def tsubcommands(cls_or_title: type[Any]) -> type[Any]: ...


@overload
def tsubcommands(cls_or_title: str, /) -> Callable[[type[Any]], type[Any]]: ...


@overload
def tsubcommands(
    *,
    title: str | None = None,
    description: str | None = None,
    required: bool | None = None,
) -> Callable[[type[Any]], type[Any]]: ...


def tsubcommands(
    cls_or_title: type[Any] | str | None = None,
    *,
    title: str | None = None,
    description: str | None = None,
    required: bool | None = None,
) -> Any:
    """Decorator to mark a class as a subcommands base.

    Subcommands are @tsubcommand classes that inherit from this class.
    They are discovered automatically via __subclasses__().

    Usage:
        @tsubcommands                              # basic
        @tsubcommands("Commands")                  # title as positional arg
        @tsubcommands(required=True)               # require a subcommand
        @tsubcommands(title="...", description="...", required=True)
    """
    if isinstance(cls_or_title, type):
        # Called as @tsubcommands without arguments
        return _apply_tsubcommands(
            cls_or_title, title=title, description=description, required=required
        )
    elif isinstance(cls_or_title, str):
        # Called as @tsubcommands("title")
        actual_title = cls_or_title

        def decorator(cls: type[Any]) -> type[Any]:
            return _apply_tsubcommands(
                cls, title=actual_title, description=description, required=required
            )

        return decorator
    else:
        # Called as @tsubcommands(title="...", description="...", required=...)
        def decorator(cls: type[Any]) -> type[Any]:
            return _apply_tsubcommands(
                cls, title=title, description=description, required=required
            )

        return decorator


# ---------------------------------------------------------------------------
# @tsubcommand decorator (singular — marks individual subcommands)
# ---------------------------------------------------------------------------


@dataclass_transform(kw_only_default=True, field_specifiers=(targ, TArg))
def _apply_tsubcommand(cls: type[Any], name: str, aliases: Sequence[str]) -> type[Any]:
    """Internal: apply tsubcommand metadata + targs to a class."""
    cls = targs(cls)
    setattr(cls, TSUBCOMMAND_FLAG_ATTR, True)
    setattr(cls, TSUBCOMMAND_NAME_ATTR, name)
    setattr(cls, TSUBCOMMAND_ALIASES_ATTR, tuple(aliases))
    return cls


@dataclass_transform(kw_only_default=True, field_specifiers=(targ, TArg))
def tsubcommand(
    *, name: str, aliases: Sequence[str] = ()
) -> Callable[[type[Any]], type[Any]]:
    """Decorator to mark a class as a named subcommand.

    The ``name`` parameter is required — it is the CLI token users type
    to select this subcommand.  ``aliases`` provides alternative tokens.
    The decorated class must inherit from a ``@tsubcommands`` base.

    Usage::

        @tsubcommand(name="run-fixed")
        class RunFixed(Commands):
            count: int = targ(Flag, default=10)

        @tsubcommand(name="run-fixed", aliases=["rf"])
        class RunFixed(Commands):
            count: int = targ(Flag, default=10)
    """

    def decorator(cls: type[Any]) -> type[Any]:
        return _apply_tsubcommand(cls, name=name, aliases=aliases)

    return decorator
