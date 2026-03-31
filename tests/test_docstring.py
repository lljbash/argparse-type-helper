"""Tests for DocString parsing."""

from argparse_type_helper import DocString

# ---------------------------------------------------------------------------
# Basic parsing
# ---------------------------------------------------------------------------


def test_parse_none():
    doc = DocString.parse(None)
    assert doc.title is None
    assert doc.description is None
    assert doc.full is None


def test_parse_empty_string():
    doc = DocString.parse("")
    assert doc.title is None
    assert doc.description is None
    assert doc.full is None


def test_parse_whitespace_only():
    doc = DocString.parse("   \n   \n   ")
    assert doc.title is None
    assert doc.description is None


def test_parse_single_line():
    doc = DocString.parse("A short summary.")
    assert doc.title == "A short summary."
    assert doc.description is None
    assert doc.full == "A short summary."


def test_parse_single_line_with_whitespace():
    doc = DocString.parse("  A short summary.  ")
    assert doc.title == "A short summary."
    assert doc.description is None


# ---------------------------------------------------------------------------
# Multi-line parsing
# ---------------------------------------------------------------------------


def test_parse_two_paragraphs():
    doc = DocString.parse("Title line\n\nDetailed description here.")
    assert doc.title == "Title line"
    assert doc.description == "Detailed description here."
    assert doc.full == "Title line\n\nDetailed description here."


def test_parse_three_paragraphs():
    doc = DocString.parse("Title\n\nParagraph one.\n\nParagraph two.")
    assert doc.title == "Title"
    assert doc.description == "Paragraph one.\n\nParagraph two."


def test_parse_indented_docstring():
    """Simulate a real class docstring with indentation."""
    doc = DocString.parse("""
        A short summary.

        Detailed description that spans
        multiple lines.
        """)
    assert doc.title == "A short summary."
    assert doc.description == "Detailed description that spans\nmultiple lines."


def test_parse_title_only_multiline():
    """Single paragraph spanning multiple lines (no blank line separator)."""
    doc = DocString.parse("""
        A title that spans
        two lines.
        """)
    assert doc.title == "A title that spans\ntwo lines."
    assert doc.description is None


# ---------------------------------------------------------------------------
# full property
# ---------------------------------------------------------------------------


def test_full_with_both():
    doc = DocString(title="Title", description="Desc")
    assert doc.full == "Title\n\nDesc"


def test_full_title_only():
    doc = DocString(title="Title", description=None)
    assert doc.full == "Title"


def test_full_none():
    doc = DocString(title=None, description=None)
    assert doc.full is None
