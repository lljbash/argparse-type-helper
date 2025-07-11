import ast
import inspect
import logging
from typing import Any, Callable, Concatenate, TypeGuard

__all__ = ["logger", "Sentry", "is_sentry", "inst_sentry", "get_attr_docstrings"]

_formatter = logging.Formatter(fmt="[%(module)s|%(levelname)s] %(message)s")
_handler = logging.StreamHandler()
_handler.setFormatter(_formatter)
logger = logging.getLogger("targs")
logger.setLevel(logging.DEBUG)
logger.addHandler(_handler)

type Sentry[T] = type[T] | T


def is_sentry[T](value: Any, sentry_type: type[T]) -> TypeGuard[Sentry[T]]:
    return isinstance(value, sentry_type) or value is sentry_type


def inst_sentry[T](value: Sentry[T], sentry_type: type[T]) -> T:
    return value if isinstance(value, sentry_type) else sentry_type()


def copy_signature[**P, R1, R2](
    fn: Callable[P, R1],
) -> Callable[[Callable[P, R2]], Callable[P, R2]]:
    """Copy the signature of a function, allowing easier function wrapping with type hints."""
    del fn  # Unused parameter
    return lambda fn: fn


def copy_signature_remove_first[**P, R1, R2, F](
    fn: Callable[Concatenate[F, P], R1],
) -> Callable[[Callable[P, R2]], Callable[P, R2]]:
    """Like `copy_signature`, but removes the first parameter from the signature."""
    del fn  # Unused parameter
    return lambda fn: fn


def get_attr_docstrings(cls: type[object]) -> dict[str, str]:
    """Best effort to get docstrings for attributes in a class."""
    source = inspect.getsource(cls)
    tree = ast.parse(source)
    classdef = tree.body[0]
    assert isinstance(classdef, ast.ClassDef), "Expected a class definition"

    attr_docstrings: dict[str, str] = {}
    cur_attr: str | None = None
    for stmt in classdef.body:
        if isinstance(stmt, ast.AnnAssign):
            if isinstance(stmt.target, ast.Name):
                cur_attr = stmt.target.id
        elif isinstance(stmt, ast.Assign):
            if len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                cur_attr = stmt.targets[0].id
        elif isinstance(stmt, ast.Expr):
            if isinstance(stmt.value, ast.Constant) and cur_attr is not None:
                attr_docstrings[cur_attr] = inspect.cleandoc(str(stmt.value.value))
                cur_attr = None
    return attr_docstrings
