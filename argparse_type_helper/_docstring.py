import inspect
from dataclasses import dataclass
from typing import Self

__all__ = ["DocString"]


@dataclass(frozen=True)
class DocString:
    """Parsed docstring with title/description separation.

    Follows PEP 257 convention: the first paragraph is the title (short summary),
    and the rest is the description (detailed explanation).
    """

    title: str | None
    """First paragraph of the docstring (short summary)."""
    description: str | None
    """Remaining paragraphs after the first (detailed description)."""

    @property
    def full(self) -> str | None:
        """Complete docstring text (title + description joined)."""
        if self.title is None:
            return None
        if self.description:
            return f"{self.title}\n\n{self.description}"
        return self.title

    @classmethod
    def parse(cls, doc: str | None) -> Self:
        """Parse a raw docstring into title and description.

        Uses ``inspect.cleandoc`` to normalize indentation, then splits on the
        first blank line.  If the docstring is ``None`` or empty, both fields
        will be ``None``.
        """
        if not doc:
            return cls(title=None, description=None)
        cleaned = inspect.cleandoc(doc)
        if not cleaned or not cleaned.strip():
            return cls(title=None, description=None)
        parts = cleaned.split("\n\n", maxsplit=1)
        title = parts[0].strip() or None
        description = parts[1].strip() if len(parts) > 1 else None
        return cls(title=title, description=description)
