import argparse
from typing import Any, get_type_hints

from argparse_type_helper._docstring import DocString
from argparse_type_helper._inference import infer_type_from_hint
from argparse_type_helper._types import (
    TARGS_FLAG_ATTR,
    TARGS_GROUPS_ATTR,
    TARGS_SUBCOMMANDS_ATTR,
    TEXCLUSIVE_FLAG_ATTR,
    TEXCLUSIVE_REQUIRED_ATTR,
    TGROUP_DESCRIPTION_ATTR,
    TGROUP_FLAG_ATTR,
    TGROUP_TITLE_ATTR,
    TSUBCOMMANDS_DESCRIPTION_ATTR,
    TSUBCOMMANDS_REQUIRED_ATTR,
    TSUBCOMMANDS_TITLE_ATTR,
    TArg,
    get_targs,
)
from argparse_type_helper._utils import get_attr_docstrings, logger

__all__ = [
    "create_parser",
    "register_targs",
    "extract_targs",
]


def _is_tgroup_class(cls: object) -> bool:
    return isinstance(cls, type) and getattr(cls, TGROUP_FLAG_ATTR, False) is True


def _is_texclusive_class(cls: object) -> bool:
    return isinstance(cls, type) and getattr(cls, TEXCLUSIVE_FLAG_ATTR, False) is True


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
        inferred = infer_type_from_hint(type_hint, has_nargs)
        if inferred is not None:
            config_part["type"] = inferred

    doc = docstrings.get(attr)
    if doc is not None:
        config_part.setdefault("help", doc)

    if verbose:
        logger.debug(f"Registering argument {name_part} with config: {config_part}")
    container.add_argument(*name_part, **config_part)


def register_targs(
    parser: argparse.ArgumentParser, cls: type[object], *, verbose: bool = False
) -> None:
    targs_dict = get_targs(cls)
    type_hints = get_type_hints(cls)
    docstrings = get_attr_docstrings(cls)

    # Auto-fill parser description from class docstring if not already set
    if parser.description is None:
        cls_doc = DocString.parse(cls.__doc__)
        if cls_doc.full is not None:
            parser.description = cls_doc.full

    # Register regular targs
    for attr, arg_config in targs_dict.items():
        _register_single_targ(
            parser, attr, arg_config, type_hints, docstrings, verbose=verbose
        )

    # Register argument groups
    groups: dict[str, type] = getattr(cls, TARGS_GROUPS_ATTR, {})
    for attr, group_cls in groups.items():
        if _is_tgroup_class(group_cls):
            group_title = getattr(group_cls, TGROUP_TITLE_ATTR, attr)
            group_desc = getattr(group_cls, TGROUP_DESCRIPTION_ATTR, None)
            container = parser.add_argument_group(
                title=group_title, description=group_desc
            )
        elif _is_texclusive_class(group_cls):
            req = getattr(group_cls, TEXCLUSIVE_REQUIRED_ATTR, False)
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
    subcommands: dict[str, type] = getattr(cls, TARGS_SUBCOMMANDS_ATTR, {})
    for attr, subcmd_base in subcommands.items():
        sub_title = getattr(subcmd_base, TSUBCOMMANDS_TITLE_ATTR, None)
        sub_desc = getattr(subcmd_base, TSUBCOMMANDS_DESCRIPTION_ATTR, None)
        sub_required = getattr(subcmd_base, TSUBCOMMANDS_REQUIRED_ATTR, None)

        sp_kwargs: dict[str, Any] = {"dest": attr}
        if sub_title is not None:
            sp_kwargs["title"] = sub_title
        if sub_desc is not None:
            sp_kwargs["description"] = sub_desc
        if sub_required is not None:
            sp_kwargs["required"] = sub_required

        subparsers = parser.add_subparsers(**sp_kwargs)

        for subcmd_cls in subcmd_base.__subclasses__():
            if not getattr(subcmd_cls, TARGS_FLAG_ATTR, None):
                continue
            subcmd_doc = DocString.parse(subcmd_cls.__doc__)
            sub_parser = subparsers.add_parser(
                subcmd_cls.__name__,
                help=subcmd_doc.title,
                description=subcmd_doc.full,
                formatter_class=parser.formatter_class,
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
    groups: dict[str, type] = getattr(cls, TARGS_GROUPS_ATTR, {})
    for attr, group_cls in groups.items():
        kwargs[attr] = extract_targs(args, group_cls)

    # Extract subcommands
    subcommands: dict[str, type] = getattr(cls, TARGS_SUBCOMMANDS_ATTR, {})
    for attr, subcmd_base in subcommands.items():
        chosen_name = getattr(args, attr, None)
        if chosen_name is not None:
            for subcmd_cls in subcmd_base.__subclasses__():
                if subcmd_cls.__name__ == chosen_name:
                    kwargs[attr] = extract_targs(args, subcmd_cls)
                    break
    return cls(**kwargs)


def create_parser(
    cls: type[object],
    *,
    parser_class: type[argparse.ArgumentParser] = argparse.ArgumentParser,
    description: str | None = None,
    prog: str | None = None,
    verbose: bool = False,
    **kwargs: Any,
) -> argparse.ArgumentParser:
    """Create an ArgumentParser pre-configured with a targs class.

    If *description* is not provided, the class docstring is used
    automatically (``full`` — title + description joined).

    Defaults to ``RawDescriptionHelpFormatter`` so that docstring
    formatting (newlines, blank lines) is preserved in ``--help``.
    Pass an explicit ``formatter_class`` to override.

    Extra keyword arguments are forwarded to *parser_class*.
    """
    if description is None:
        cls_doc = DocString.parse(cls.__doc__)
        description = cls_doc.full
    parser_kwargs: dict[str, Any] = {**kwargs}
    parser_kwargs.setdefault("formatter_class", argparse.RawDescriptionHelpFormatter)
    if description is not None:
        parser_kwargs["description"] = description
    if prog is not None:
        parser_kwargs["prog"] = prog
    parser = parser_class(**parser_kwargs)
    register_targs(parser, cls, verbose=verbose)
    return parser
