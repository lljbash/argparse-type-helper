# Agent Instructions for argparse-type-helper

This repository contains a lightweight Python library that provides type-hinted argument parsing for `argparse`. The project is in Beta stage and uses modern Python tooling with `uv` for dependency management.

## Important Principles

1. **Ask for clarification when uncertain** - When facing design choices, feature scope, or multiple implementation options, use the ask_user tool to inquire rather than making assumptions.
2. **When encountering difficulties, ask how to proceed** - If execution becomes blocked or unclear, use the ask_user tool to ask what to do rather than stopping work.
3. **Update README and AGENTS.md** - After making changes to the codebase, always update the README.md and this AGENTS.md file to reflect your work. Keep these files in sync with actual implementation.
4. **Communicate in the user's language** - Respond and communicate in the same language the user is using. If they write in Chinese, respond in Chinese. If they write in English, respond in English.
5. **Always use `uv run`** - Never use bare `python3` or `pip`. Always use `uv run python`, `uv run pytest`, etc. for all Python commands.

## Build, Test, and Lint Commands

### Setup
```bash
uv sync --all-extras --dev
```

### Type Checking (basedpyright)
```bash
uv run basedpyright **/*.py
```

### Code Formatting
```bash
# Format with Black
uv run black argparse_type_helper tests

# Sort imports with isort
uv run isort argparse_type_helper tests
```

### Running Tests
```bash
# Run all tests
uv run pytest tests/

# Run specific test file
uv run pytest tests/test_basic.py -v

# Run with verbose output
uv run pytest tests/ -v --tb=short
```

### Manual Testing
Manual testing can be done by running the example scripts:
```bash
uv run python tests/example.py
uv run python tests/example_groups.py
uv run python tests/example_subcommands.py
```

### Auto-Documentation
The example scripts are synced to the README.md using MARKDOWN-AUTO-DOCS. After updating examples, run the following command to update the README:
```bash
npm i -g markdown-autodocs  # Install globally if not already installed
markdown-autodocs -c code-block -o ./README.md
```

## High-Level Architecture

**Core Problem:** `argparse` doesn't integrate well with type hints. This library bridges that gap by allowing you to define arguments using dataclass-like syntax with full type support, while remaining compatible with standard `argparse`.

**Design Pattern — Six Internal Modules:**

All internal modules use `_` prefix to signal they are not public API. All public symbols are exported via `__init__.py`.

1. **`_types.py`** — Core types and argument definition
   - `Name`, `Flag`: Marker classes for positional vs optional arguments
   - `TArg`: Dataclass holding all argument metadata, with `__set_name__` descriptor protocol
   - `Unset`: Sentinel type for unset optional values
   - `targ()`: Function that creates `TArg` configuration objects
   - `post_init`: Decorator for post-extraction validation hooks
   - `get_targs()`, `check_and_maybe_init_targs_class()`: Internal helpers shared by decorators and registry
   - Detection helpers: `is_tgroup_class()`, `is_texclusive_class()`, `is_tsubcommands_class()`, `is_tsubcommand_class()`, `is_group_like()` — shared by `_decorators` and `_registry`

2. **`_decorators.py`** — Class decorators
   - `@targs`: Transforms a class into a typed arguments container (generates `__init__`, `__repr__`)
   - `@tgroup`: Marks a class as an argument group (title/description from docstring or params)
   - `@texclusive`: Marks a class as a mutually exclusive group
   - `@tsubcommands`: Marks a class as a subcommands base
   - `@tsubcommand(name=..., aliases=[...])`: Marks a class as a named subcommand (must inherit from a `@tsubcommands` base); `name` is required, `aliases` is optional
   - `_scan_special_attrs()`: Discovers group/subcommand references via type annotations

3. **`_registry.py`** — Parser registration and extraction
   - `register_targs(parser, cls)`: Wires up all arguments on an `ArgumentParser`
   - `extract_targs(args, cls)`: Reconstructs a typed instance from parsed `Namespace`
   - `create_parser(cls, ...)`: Creates an `ArgumentParser` and registers in one step

4. **`_inference.py`** — Type inference
   - `infer_type_from_hint()`: Infers `type=` from type hints (`X | None`, `list[X]`, bare types, etc.)
   - `_get_union_args()`: Helper to extract union member types

5. **`_docstring.py`** — Docstring parsing
   - `DocString`: Frozen dataclass with `title`, `description`, `full` property, and `parse()` classmethod
   - Splitting rule: first paragraph → title, rest → description

6. **`_utils.py`** — Shared utilities
   - `Sentry`: Pattern where a value can be either a type class or an instance
   - `logger`: Module-level logger
   - `copy_signature()`: Signature-preserving decorator helper
   - `get_attr_docstrings()`: AST-based attribute docstring extraction

**Key Technical Details:**

- **Sentry Pattern** (`_utils.py`): A clever pattern where a value can be either a type class OR an instance. Used for marking unset optional values without requiring special sentinels.
- **Descriptor Protocol** (`TArg.__set_name__`): Auto-registers argument configs when the class is created, no manual tracking needed.
- **Post-init Hooks** (`@post_init` decorator): Allows validation logic after argument extraction.
- **Docstring Extraction** (`_utils.py`): Uses AST parsing with `textwrap.dedent` to extract docstrings from attributes. Works for both module-level and function-scoped (indented) classes.
- **DocString Splitting** (`_docstring.py`): Uses `inspect.cleandoc()` then splits on `"\n\n"` (first blank line). First paragraph = title, rest = description. Applied consistently to `@targs`, `@tgroup`, `@tsubcommands`, and subcommand classes.
- **Mutable Default Safety**: `list`, `dict`, and `set` defaults are shallow-copied in the generated `__init__` to prevent sharing across instances.
- **Decorator Consistency**: All three decorators (`@tgroup`, `@texclusive`, `@tsubcommands`) support dual calling styles: bare `@decorator` and parameterized `@decorator(...)`. Title can be passed as the first positional argument or via keyword. Note: `@texclusive` does not support `title`/`description` — this is a limitation of `argparse.MutuallyExclusiveGroup`. `@tsubcommand` always requires `name` — no bare form.

## Key Conventions

### Naming Rules
- **Underscores to Dashes**: When using `Flag` for optional arguments, underscores in the class attribute name are automatically converted to dashes in the CLI (e.g., `optional_dash` becomes `--optional-dash`).
- **Dest Mapping**: The `get_dest()` method handles converting flag names back to attribute names when extracting from `Namespace`.
- **Subcommand Names**: Subcommand classes must use `@tsubcommand(name="...", aliases=[...])` — the `name` parameter is the CLI token. There is no default name; it must always be explicitly provided. `aliases` is optional and provides alternative names. Bare `@targs` on a `@tsubcommands` subclass raises `TypeError` during registration.

### Type Hint Requirements
- All `targ()` fields **must** have a type hint.
- **Type inference rules** (in `infer_type_from_hint()`):
  1. User explicit `type=` → always used (highest priority)
  2. Has `action` → skip inference (actions handle their own types)
  3. `bool` / `bool | None` → skip inference (require explicit `action="store_true/store_false"`)
  4. `X | None` / `Optional[X]` where X is a non-bool callable → use X
  5. `list[X]` / `Sequence[X]` etc. with `nargs` set → use element type X (`Sequence` is recommended over `list`)
  6. Bare callable (`int`, `str`, `float`, …) excluding `bool` → use itself
  7. Anything else (`int | str`, etc.) → skip inference
- Group references use type annotations: `db: DbOptions` where `DbOptions` is a `@tgroup` class.
- Subcommand references use type annotations: `command: Commands` where `Commands` is a `@tsubcommands` class.
- Type checking is **strict** (see `pyproject.toml`: `typeCheckingMode = "strict"`).

### Argument Configuration
- All parameters accepted by `argparse.add_argument()` are supported (`action`, `nargs`, `choices`, `default`, `help`, etc.)
- `Name` marks a positional argument (required)
- `Flag` or custom string/tuple marks an optional argument
- Can mix class-based definitions with native `parser.add_argument()` calls

### Code Style
- **Python 3.12+** (see `pyproject.toml`: `requires-python = ">=3.12"`)
- **Black 26+** for formatting (target: py312)
- **isort** with Black profile for import sorting
- **basedpyright strict mode** for type checking

### Module Organization
- `__init__.py`: Public API exports (Name, Flag, DocString, targ, targs, tgroup, texclusive, tsubcommands, tsubcommand, post_init, register_targs, extract_targs, create_parser)
- `_types.py`: Core types, TArg, targ(), post_init, constants
- `_decorators.py`: All class decorators (@targs, @tgroup, @texclusive, @tsubcommands, @tsubcommand)
- `_registry.py`: register_targs, extract_targs, create_parser
- `_inference.py`: Type inference logic
- `_docstring.py`: DocString dataclass with parsing logic
- `_utils.py`: Sentry pattern, logger, copy_signature, attribute docstring extraction

### Internal Attributes
- `_targs` / `_targs_flag`: Per-class targs dict and initialization marker
- `_targs_groups`: Dict mapping attribute name → group class (set by `@targs`)
- `_targs_subcommands`: Dict mapping attribute name → subcommands base class (set by `@targs`)
- `_tgroup_flag` / `_tgroup_title` / `_tgroup_description`: Group metadata (set by `@tgroup`)
- `_texclusive_flag` / `_texclusive_required`: Exclusive group metadata (set by `@texclusive`)
- `_tsubcommands_flag` / `_tsubcommands_title` / `_tsubcommands_description` / `_tsubcommands_required`: Subcommand base metadata (set by `@tsubcommands`)
- `_tsubcommand_flag` / `_tsubcommand_name` / `_tsubcommand_aliases`: Individual subcommand metadata (set by `@tsubcommand`)

### Testing
- Located in `tests/` directory
- `test_basic.py`: Core functionality (targ, Name, Flag, register, extract, subclass, post_init, docstrings, all action types, custom Action, nargs, required, metavar, dest)
- `test_groups.py`: Argument groups and mutually exclusive groups
- `test_subcommands.py`: Subcommands with inheritance, groups inside subcommands, pattern matching
- `test_type_inference.py`: Type inference expansion (X | None, Optional[X], list[X]+nargs, bool protection)
- `test_docstring.py`: DocString.parse() unit tests (single/multi/empty/whitespace edge cases)
- `test_create_parser.py`: create_parser, docstring→title/desc split, mutable defaults, robustness
- Example files: `example.py`, `example_groups.py`, `example_subcommands.py` (synced to README via MARKDOWN-AUTO-DOCS)
