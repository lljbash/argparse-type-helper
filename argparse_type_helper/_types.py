import argparse
import copy
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Literal, cast

from argparse_type_helper._utils import (
    Sentry,
    copy_signature,
    inst_sentry,
    is_sentry,
)

__all__ = [
    "Unset",
    "Name",
    "Flag",
    "NameOrFlag",
    "StrAction",
    "TArg",
    "targ",
    "post_init",
    "TARGS_ATTR",
    "TARGS_FLAG_ATTR",
    "TARGS_POST_INIT_ATTR",
    "TARGS_GROUPS_ATTR",
    "TARGS_SUBCOMMANDS_ATTR",
    "TGROUP_FLAG_ATTR",
    "TGROUP_TITLE_ATTR",
    "TGROUP_DESCRIPTION_ATTR",
    "TEXCLUSIVE_FLAG_ATTR",
    "TEXCLUSIVE_REQUIRED_ATTR",
    "TSUBCOMMANDS_FLAG_ATTR",
    "TSUBCOMMANDS_TITLE_ATTR",
    "TSUBCOMMANDS_DESCRIPTION_ATTR",
    "TSUBCOMMANDS_REQUIRED_ATTR",
    "check_and_maybe_init_targs_class",
    "get_targs",
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


# ---------------------------------------------------------------------------
# Internal attribute names used to store metadata on classes
# ---------------------------------------------------------------------------

TARGS_ATTR = "_targs"
TARGS_FLAG_ATTR = "_targs_flag"
TARGS_POST_INIT_ATTR = "_targs_post_init"
TARGS_GROUPS_ATTR = "_targs_groups"
TARGS_SUBCOMMANDS_ATTR = "_targs_subcommands"

TGROUP_FLAG_ATTR = "_tgroup_flag"
TGROUP_TITLE_ATTR = "_tgroup_title"
TGROUP_DESCRIPTION_ATTR = "_tgroup_description"

TEXCLUSIVE_FLAG_ATTR = "_texclusive_flag"
TEXCLUSIVE_REQUIRED_ATTR = "_texclusive_required"

TSUBCOMMANDS_FLAG_ATTR = "_tsubcommands_flag"
TSUBCOMMANDS_TITLE_ATTR = "_tsubcommands_title"
TSUBCOMMANDS_DESCRIPTION_ATTR = "_tsubcommands_description"
TSUBCOMMANDS_REQUIRED_ATTR = "_tsubcommands_required"


def post_init[T, R](func: Callable[[T], R]) -> Callable[[T], R]:
    """Decorator to mark a function as a post-init function for targs classes."""
    setattr(func, TARGS_POST_INIT_ATTR, True)
    return func


# ---------------------------------------------------------------------------
# Internal helpers for targs class initialization
# ---------------------------------------------------------------------------


def check_and_maybe_init_targs_class(
    cls: type[object], raise_instead_of_init: bool
) -> None:
    if getattr(cls, TARGS_FLAG_ATTR, None) is not cls:
        if raise_instead_of_init:
            raise TypeError(
                f"{cls.__name__} is not a targs class. Use @targs decorator."
            )
        setattr(cls, TARGS_FLAG_ATTR, cls)
        setattr(cls, TARGS_ATTR, copy.deepcopy(getattr(cls, TARGS_ATTR, {})))


def get_targs(cls: type[object], *, check: bool = True) -> dict[str, TArg]:
    check_and_maybe_init_targs_class(cls, raise_instead_of_init=check)
    return getattr(cls, TARGS_ATTR)
