import argparse
import copy
import types
import typing
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Literal, cast, dataclass_transform, get_type_hints

from argparse_type_helper.utils import (
    Sentry,
    copy_signature,
    get_attr_docstrings,
    inst_sentry,
    is_sentry,
    logger,
)

__all__ = [
    "Name",
    "Flag",
    "targ",
    "post_init",
    "targs",
    "tgroup",
    "texclusive",
    "tsubcommands",
    "register_targs",
    "extract_targs",
]


class Unset:
    pass


class Name:
    pass


@dataclass
class Flag:
    short: str | None = None


type NameOrFlag = str | tuple[str, str]

type StrAction = Literal[
    "store",
    "store_const",
    "store_true",
    "store_false",
    "append",
    "append_const",
    "extend",
    "count",
    "help",
    "version",
]


@dataclass
class TArg:
    name_or_flag: NameOrFlag | Sentry[Name] | Sentry[Flag]
    action: StrAction | type[argparse.Action] | None | Sentry[Unset] = Unset
    nargs: int | Literal["?", "*", "+"] | None | Sentry[Unset] = Unset
    const: Any | Sentry[Unset] = Unset
    default: Any | Sentry[Unset] = Unset
    type: Callable[[str], Any] | None | Sentry[Unset] = Unset
    choices: list[str] | None | Sentry[Unset] = Unset
    required: bool | None | Sentry[Unset] = Unset
    help: str | None | Sentry[Unset] = Unset
    metavar: str | None | Sentry[Unset] = Unset
    dest: str | None | Sentry[Unset] = Unset
    deprecated: bool | None | Sentry[Unset] = Unset

    _real_name_or_flag: NameOrFlag | None = field(default=None, init=False)

    def dump(self) -> dict[str, Any]:
        return {
            k: v
            for k, v in asdict(self).items()
            if k != "name_or_flag" and not k.startswith("_") and not is_sentry(v, Unset)
        }

    def _init_real_name_or_flag(self, name: str) -> None:
        if is_sentry(self.name_or_flag, Name):
            self._real_name_or_flag = name
        elif is_sentry(self.name_or_flag, Flag):
            flag = inst_sentry(self.name_or_flag, Flag)
            name = name.replace("_", "-")  # Convert underscores to dashes for flags
            self._real_name_or_flag = (
                (flag.short, f"--{name}") if flag.short else f"--{name}"
            )
        else:
            self._real_name_or_flag = cast(NameOrFlag, self.name_or_flag)

    def name_or_flag_tuple(self) -> tuple[str] | tuple[str, str]:
        assert self._real_name_or_flag is not None, "name_or_flag must be initialized"
        if isinstance(self._real_name_or_flag, str):
            return (self._real_name_or_flag,)
        return self._real_name_or_flag

    def _get_dest_from_one_name_or_flag(self, name_or_flag: str) -> str:
        return name_or_flag.lstrip("-").replace("-", "_")

    def get_dest(self) -> str:
        assert self._real_name_or_flag is not None, "name_or_flag must be initialized"
        if isinstance(self.dest, str):
            return self.dest
        if isinstance(self._real_name_or_flag, str):
            return self._get_dest_from_one_name_or_flag(self._real_name_or_flag)
        assert all(
            nf.startswith("-") for nf in self._real_name_or_flag
        ), "only one name is allowed for positional arguments"
        first_long = next(
            (nf for nf in self._real_name_or_flag if nf.startswith("--")),
            self._real_name_or_flag[0],
        )
        return self._get_dest_from_one_name_or_flag(first_long)

    def __set_name__(self, owner: "type", name: str) -> None:
        self._init_real_name_or_flag(name)
        get_targs(owner, check=False)[name] = self


@copy_signature(TArg)
def targ(*args: Any, **kwargs: Any) -> Any:
    """defines an argument in a targs class."""
    return TArg(*args, **kwargs)


_TARGS_ATTR = "_targs"
_TARGS_FLAG_ATTR = "_targs_flag"
_TARGS_POST_INIT_ATTR = "_targs_post_init"
_TARGS_GROUPS_ATTR = "_targs_groups"
_TARGS_SUBCOMMANDS_ATTR = "_targs_subcommands"

_TGROUP_FLAG_ATTR = "_tgroup_flag"
_TGROUP_TITLE_ATTR = "_tgroup_title"
_TGROUP_DESCRIPTION_ATTR = "_tgroup_description"

_TEXCLUSIVE_FLAG_ATTR = "_texclusive_flag"
_TEXCLUSIVE_REQUIRED_ATTR = "_texclusive_required"

_TSUBCOMMANDS_FLAG_ATTR = "_tsubcommands_flag"
_TSUBCOMMANDS_TITLE_ATTR = "_tsubcommands_title"
_TSUBCOMMANDS_DESCRIPTION_ATTR = "_tsubcommands_description"
_TSUBCOMMANDS_REQUIRED_ATTR = "_tsubcommands_required"


def post_init[T, R](func: Callable[[T], R]) -> Callable[[T], R]:
    """Decorator to mark a function as a post-init function for targs classes."""
    setattr(func, _TARGS_POST_INIT_ATTR, True)
    return func


# ---------------------------------------------------------------------------
# Detection helpers
# ---------------------------------------------------------------------------


def _is_tgroup_class(cls: object) -> bool:
    return isinstance(cls, type) and getattr(cls, _TGROUP_FLAG_ATTR, False) is True


def _is_texclusive_class(cls: object) -> bool:
    return isinstance(cls, type) and getattr(cls, _TEXCLUSIVE_FLAG_ATTR, False) is True


def _is_tsubcommands_class(cls: object) -> bool:
    return (
        isinstance(cls, type) and getattr(cls, _TSUBCOMMANDS_FLAG_ATTR, False) is True
    )


def _is_group_like(cls: object) -> bool:
    return _is_tgroup_class(cls) or _is_texclusive_class(cls)


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
        if _is_group_like(hint):
            groups[attr] = hint
        elif _is_tsubcommands_class(hint):
            subcommands[attr] = hint
    return groups, subcommands


# ---------------------------------------------------------------------------
# @targs decorator
# ---------------------------------------------------------------------------


@dataclass_transform(kw_only_default=True, field_specifiers=(targ, TArg))
def targs[T](cls: type[T]) -> type[T]:
    """Decorator to transform a class into a targs class."""

    # Scan for groups and subcommands before generating __init__
    own_groups, own_subcommands = _scan_special_attrs(cls)
    # Merge with inherited
    inherited_groups: dict[str, type] = copy.copy(getattr(cls, _TARGS_GROUPS_ATTR, {}))
    inherited_subcommands: dict[str, type] = copy.copy(
        getattr(cls, _TARGS_SUBCOMMANDS_ATTR, {})
    )
    inherited_groups.update(own_groups)
    inherited_subcommands.update(own_subcommands)
    setattr(cls, _TARGS_GROUPS_ATTR, inherited_groups)
    setattr(cls, _TARGS_SUBCOMMANDS_ATTR, inherited_subcommands)

    def __init__(self: T, **kwargs: Any) -> None:
        targs_dict = get_targs(self.__class__)
        for attr, arg_config in targs_dict.items():
            if attr in kwargs:
                setattr(self, attr, kwargs[attr])
            elif is_sentry(arg_config.default, Unset):
                raise ValueError(f"Missing required argument: {attr}")
            else:
                setattr(self, attr, arg_config.default)

        # Set group attributes
        groups = getattr(self.__class__, _TARGS_GROUPS_ATTR, {})
        for attr in groups:
            if attr in kwargs:
                setattr(self, attr, kwargs[attr])
            else:
                raise ValueError(f"Missing required group: {attr}")

        # Set subcommand attributes (default to None if not provided)
        subcommands = getattr(self.__class__, _TARGS_SUBCOMMANDS_ATTR, {})
        for attr in subcommands:
            setattr(self, attr, kwargs.get(attr, None))

        for cls in reversed(type(self).__mro__):
            if not hasattr(cls, _TARGS_FLAG_ATTR):
                continue
            for _, member in cls.__dict__.items():
                if callable(member) and getattr(member, _TARGS_POST_INIT_ATTR, False):
                    member(self)

    def __repr__(self: T) -> str:
        parts: list[str] = []
        targs_attrs = get_targs(self.__class__).keys()
        for attr in targs_attrs:
            parts.append(f"{attr}={getattr(self, attr)!r}")
        groups = getattr(self.__class__, _TARGS_GROUPS_ATTR, {})
        for attr in groups:
            parts.append(f"{attr}={getattr(self, attr)!r}")
        subcommands = getattr(self.__class__, _TARGS_SUBCOMMANDS_ATTR, {})
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
    setattr(cls, _TGROUP_FLAG_ATTR, True)
    setattr(cls, _TGROUP_TITLE_ATTR, title or cls.__name__)
    setattr(cls, _TGROUP_DESCRIPTION_ATTR, description or cls.__doc__)
    return cls


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
    setattr(cls, _TEXCLUSIVE_FLAG_ATTR, True)
    setattr(cls, _TEXCLUSIVE_REQUIRED_ATTR, required)
    return cls


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
    setattr(cls, _TSUBCOMMANDS_FLAG_ATTR, True)
    setattr(cls, _TSUBCOMMANDS_TITLE_ATTR, title)
    setattr(cls, _TSUBCOMMANDS_DESCRIPTION_ATTR, description or cls.__doc__)
    setattr(cls, _TSUBCOMMANDS_REQUIRED_ATTR, required)
    return cls


def tsubcommands(
    cls_or_title: type[Any] | str | None = None,
    *,
    title: str | None = None,
    description: str | None = None,
    required: bool | None = None,
) -> Any:
    """Decorator to mark a class as a subcommands base.

    Subcommands are @targs classes that inherit from this class.
    They are discovered automatically via __subclasses__().

    Usage:
        @tsubcommands                              # basic
        @tsubcommands("Commands")                  # title as positional arg
        @tsubcommands(required=True)               # require a subcommand
        @tsubcommands(title="...", description="...", required=True)
    """
    if isinstance(cls_or_title, type):
        return _apply_tsubcommands(
            cls_or_title, title=title, description=description, required=required
        )
    elif isinstance(cls_or_title, str):
        actual_title = cls_or_title

        def decorator(cls: type[Any]) -> type[Any]:
            return _apply_tsubcommands(
                cls, title=actual_title, description=description, required=required
            )

        return decorator
    else:

        def decorator(cls: type[Any]) -> type[Any]:
            return _apply_tsubcommands(
                cls, title=title, description=description, required=required
            )

        return decorator


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def check_and_maybe_init_targs_class(
    cls: type[object], raise_instead_of_init: bool
) -> None:
    if getattr(cls, _TARGS_FLAG_ATTR, None) is not cls:
        if raise_instead_of_init:
            raise TypeError(
                f"{cls.__name__} is not a targs class. Use @targs decorator."
            )
        setattr(cls, _TARGS_FLAG_ATTR, cls)
        setattr(cls, _TARGS_ATTR, copy.deepcopy(getattr(cls, _TARGS_ATTR, {})))


def get_targs(cls: type[object], *, check: bool = True) -> dict[str, TArg]:
    check_and_maybe_init_targs_class(cls, raise_instead_of_init=check)
    return getattr(cls, _TARGS_ATTR)


def _get_union_args(hint: Any) -> tuple[Any, ...] | None:
    """Extract type arguments from a union type (X | Y or typing.Union[X, Y])."""
    if isinstance(hint, types.UnionType):
        return hint.__args__
    origin = getattr(hint, "__origin__", None)
    if origin is typing.Union:  # pyright: ignore[reportDeprecated]
        return hint.__args__
    return None


def _infer_type_from_hint(type_hint: Any, has_nargs: bool) -> Any | None:
    """Infer the argparse ``type`` converter from a type hint.

    Returns a callable to use as the ``type`` parameter, or ``None`` if
    the type cannot be inferred automatically.

    Rules (in priority order):
    1. ``bool`` or ``bool | None`` → ``None`` (require explicit action).
    2. ``X | None`` / ``Optional[X]`` where *X* is a non-bool callable → *X*.
    3. Generic with ``nargs`` (e.g. ``list[int]``) → element type.
    4. Bare callable (``int``, ``str``, ``float``, …) excluding ``bool`` → itself.
    5. Anything else → ``None``.
    """
    # Handle union types: X | None, Optional[X], X | Y, etc.
    union_args = _get_union_args(type_hint)
    if union_args is not None:
        non_none = [a for a in union_args if a is not type(None)]
        if len(non_none) == 1:
            inner = non_none[0]
            if inner is bool:
                return None
            if callable(inner):
                return inner
        return None

    # Skip bool — it doesn't work as a type converter
    if type_hint is bool:
        return None

    # Generic types like list[int], tuple[str, ...] — extract element type when nargs is set
    origin = getattr(type_hint, "__origin__", None)
    if origin is not None:
        args = getattr(type_hint, "__args__", None)
        if has_nargs and args:
            elem = args[0]
            if elem is not bool and callable(elem):
                return elem
        return None

    # Bare callable types (int, str, float, etc.)
    if callable(type_hint):
        return type_hint

    return None


def _register_single_targ(
    container: Any,
    attr: str,
    arg_config: TArg,
    type_hints: dict[str, Any],
    docstrings: dict[str, str],
    *,
    verbose: bool = False,
) -> None:
    """Register a single TArg on a container (parser or argument group)."""
    name_part = arg_config.name_or_flag_tuple()
    config_part = arg_config.dump()

    type_hint = type_hints.get(attr, None)
    if type_hint is None:
        raise TypeError(f"Type hint for argument '{attr}' is missing.")
    if config_part.get("action") is None and "type" not in config_part:
        has_nargs = "nargs" in config_part
        inferred = _infer_type_from_hint(type_hint, has_nargs)
        if inferred is not None:
            config_part["type"] = inferred

    doc = docstrings.get(attr)
    if doc is not None:
        config_part.setdefault("help", doc)

    if verbose:
        logger.debug(f"Registering argument {name_part} with config: {config_part}")
    container.add_argument(*name_part, **config_part)


# ---------------------------------------------------------------------------
# register_targs / extract_targs
# ---------------------------------------------------------------------------


def register_targs(
    parser: argparse.ArgumentParser, cls: type[object], *, verbose: bool = False
) -> None:
    targs_dict = get_targs(cls)
    type_hints = get_type_hints(cls)
    docstrings = get_attr_docstrings(cls)

    # Register regular targs
    for attr, arg_config in targs_dict.items():
        _register_single_targ(
            parser, attr, arg_config, type_hints, docstrings, verbose=verbose
        )

    # Register argument groups
    groups: dict[str, type] = getattr(cls, _TARGS_GROUPS_ATTR, {})
    for attr, group_cls in groups.items():
        if _is_tgroup_class(group_cls):
            group_title = getattr(group_cls, _TGROUP_TITLE_ATTR, attr)
            group_desc = getattr(group_cls, _TGROUP_DESCRIPTION_ATTR, None)
            container = parser.add_argument_group(
                title=group_title, description=group_desc
            )
        elif _is_texclusive_class(group_cls):
            req = getattr(group_cls, _TEXCLUSIVE_REQUIRED_ATTR, False)
            container = parser.add_mutually_exclusive_group(required=req)
        else:
            continue

        group_targs = get_targs(group_cls)
        group_type_hints = get_type_hints(group_cls)
        group_docstrings = get_attr_docstrings(group_cls)
        for g_attr, g_config in group_targs.items():
            _register_single_targ(
                container,
                g_attr,
                g_config,
                group_type_hints,
                group_docstrings,
                verbose=verbose,
            )

    # Register subcommands
    subcommands: dict[str, type] = getattr(cls, _TARGS_SUBCOMMANDS_ATTR, {})
    for attr, subcmd_base in subcommands.items():
        sub_title = getattr(subcmd_base, _TSUBCOMMANDS_TITLE_ATTR, None)
        sub_desc = getattr(subcmd_base, _TSUBCOMMANDS_DESCRIPTION_ATTR, None)
        sub_required = getattr(subcmd_base, _TSUBCOMMANDS_REQUIRED_ATTR, None)

        sp_kwargs: dict[str, Any] = {"dest": attr}
        if sub_title is not None:
            sp_kwargs["title"] = sub_title
        if sub_desc is not None:
            sp_kwargs["description"] = sub_desc
        if sub_required is not None:
            sp_kwargs["required"] = sub_required

        subparsers = parser.add_subparsers(**sp_kwargs)

        for subcmd_cls in subcmd_base.__subclasses__():
            if not getattr(subcmd_cls, _TARGS_FLAG_ATTR, None):
                continue
            sub_parser = subparsers.add_parser(
                subcmd_cls.__name__, help=subcmd_cls.__doc__
            )
            register_targs(sub_parser, subcmd_cls, verbose=verbose)


def extract_targs[T](args: argparse.Namespace, cls: type[T]) -> T:
    targs_dict = get_targs(cls)
    kwargs: dict[str, Any] = {}

    # Extract regular targs
    for attr, arg_config in targs_dict.items():
        dest = arg_config.get_dest()
        if hasattr(args, dest):
            kwargs[attr] = getattr(args, dest)
        else:
            raise AttributeError(f"Argument '{dest}' not found in parsed args.")

    # Extract groups (recursive)
    groups: dict[str, type] = getattr(cls, _TARGS_GROUPS_ATTR, {})
    for attr, group_cls in groups.items():
        kwargs[attr] = extract_targs(args, group_cls)

    # Extract subcommands
    subcommands: dict[str, type] = getattr(cls, _TARGS_SUBCOMMANDS_ATTR, {})
    for attr, subcmd_base in subcommands.items():
        chosen_name = getattr(args, attr, None)
        if chosen_name is not None:
            for subcmd_cls in subcmd_base.__subclasses__():
                if subcmd_cls.__name__ == chosen_name:
                    kwargs[attr] = extract_targs(args, subcmd_cls)
                    break
    return cls(**kwargs)
