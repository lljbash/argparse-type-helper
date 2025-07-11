import argparse
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

__all__ = ["Name", "Flag", "targ", "targs", "register_targs", "extract_targs"]


class Unset:
    pass


class Name:
    pass


@dataclass
class Flag:
    short: str | None = None


type NameOrFlag = str | tuple[str, str]

type Action = Literal[
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
    action: Action | argparse.BooleanOptionalAction | None | Sentry[Unset] = Unset
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
    return TArg(*args, **kwargs)


_TARGS_ATTR = "_targs"
_TARGS_FLAG_ATTR = "_targs_flag"


@dataclass_transform(kw_only_default=True, field_specifiers=(targ, TArg))
def targs[T](cls: type[T]) -> type[T]:
    def __init__(self: T, **kwargs: Any) -> None:
        targs_dict = get_targs(self.__class__)
        for attr, arg_config in targs_dict.items():
            if attr in kwargs:
                setattr(self, attr, kwargs[attr])
            elif is_sentry(arg_config.default, Unset):
                raise ValueError(f"Missing required argument: {attr}")
            else:
                setattr(self, attr, arg_config.default)

    def __repr__(self: T) -> str:
        targs_attrs = get_targs(self.__class__).keys()
        return f"{self.__class__.__name__}({', '.join(f'{attr}={getattr(self, attr)!r}' for attr in targs_attrs)})"

    cls.__init__ = __init__
    cls.__repr__ = __repr__
    setattr(cls, _TARGS_FLAG_ATTR, True)
    return cls


def get_targs(cls: type[object], *, check: bool = True) -> dict[str, TArg]:
    if check and not getattr(cls, _TARGS_FLAG_ATTR, False):
        raise TypeError(f"{cls.__name__} is not a targs class. Use @targs decorator.")
    if not hasattr(cls, _TARGS_ATTR):
        setattr(cls, _TARGS_ATTR, {})
    return getattr(cls, _TARGS_ATTR)


def register_targs(
    parser: argparse.ArgumentParser, cls: type[object], *, verbose: bool = False
) -> None:
    targs_dict = get_targs(cls)
    type_hints = get_type_hints(cls)
    docstrings = get_attr_docstrings(cls)
    for attr, arg_config in targs_dict.items():
        name_part = arg_config.name_or_flag_tuple()
        config_part = arg_config.dump()

        type_hint = type_hints.get(attr, None)
        if type_hint is None:
            raise TypeError(f"Type hint for argument '{attr}' is missing.")
        if callable(type_hint) and config_part.get("action") is None:
            config_part.setdefault("type", type_hint)

        doc = docstrings.get(attr)
        if doc is not None:
            config_part.setdefault("help", doc)

        if verbose:
            logger.debug(f"Registering argument {name_part} with config: {config_part}")
        parser.add_argument(*name_part, **config_part)


def extract_targs[T](args: argparse.Namespace, cls: type[T]) -> T:
    targs_dict = get_targs(cls)
    targs_instance = cls.__new__(cls)
    for attr, arg_config in targs_dict.items():
        dest = arg_config.get_dest()
        if hasattr(args, dest):
            setattr(targs_instance, attr, getattr(args, dest))
        else:
            raise AttributeError(f"Argument '{dest}' not found in parsed args.")
    return targs_instance
