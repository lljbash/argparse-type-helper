import types
import typing
from typing import Any

__all__ = ["infer_type_from_hint"]


def _get_union_args(hint: Any) -> tuple[Any, ...] | None:
    """Extract type arguments from a union type (X | Y or typing.Union[X, Y])."""
    if isinstance(hint, types.UnionType):
        return hint.__args__
    origin = getattr(hint, "__origin__", None)
    if origin is typing.Union:  # pyright: ignore[reportDeprecated]
        return hint.__args__
    return None


def infer_type_from_hint(type_hint: Any, has_nargs: bool) -> Any | None:
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
