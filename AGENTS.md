# Agent Instructions for argparse-type-helper

This repository contains a lightweight Python library that provides type-hinted argument parsing for `argparse`. The project is in Alpha stage and uses modern Python tooling with `uv` for dependency management.

## Important Principles

1. **Ask for clarification when uncertain** - When facing design choices, feature scope, or multiple implementation options, use the ask_user tool to inquire rather than making assumptions.
2. **When encountering difficulties, ask how to proceed** - If execution becomes blocked or unclear, use the ask_user tool to ask what to do rather than stopping work.
3. **Update README and AGENTS.md** - After making changes to the codebase, always update the README.md and this AGENTS.md file to reflect your work. Keep these files in sync with actual implementation.
4. **Communicate in the user's language** - Respond and communicate in the same language the user is using. If they write in Chinese, respond in Chinese. If they write in English, respond in English.

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
npm i -g markdown-auto-docs  # Install globally if not already installed
markdown-auto-docs -c code-block -o ./README.md
```

## High-Level Architecture

**Core Problem:** `argparse` doesn't integrate well with type hints. This library bridges that gap by allowing you to define arguments using dataclass-like syntax with full type support, while remaining compatible with standard `argparse`.

**Design Pattern - Five Main Components:**

1. **Argument Definition** (`targ()` + `@targs` decorator)
   - `targ()`: Function that creates `TArg` configuration objects containing all argument metadata
   - `@targs`: Class decorator that transforms a regular class into a typed arguments container
   - `Name` and `Flag`: Marker classes/dataclasses that indicate positional vs optional arguments

2. **Argument Groups** (`@tgroup` + `@texclusive`)
   - `@tgroup("title")`: Decorator that marks a class as an argument group. Internally applies `@targs` + stores group metadata (title, description).
   - `@texclusive(required=...)`: Decorator for mutually exclusive argument groups.
   - Group classes are defined at module level and referenced via type annotations in `@targs` classes.
   - After extraction, group attributes provide nested access (e.g., `my_args.db.host`).

3. **Subcommands** (`@tsubcommands`)
   - `@tsubcommands`: Decorator that marks a class as a subcommands base.
   - Subcommands are `@targs` classes that inherit from the `@tsubcommands` base class.
   - Subcommands are discovered automatically via `__subclasses__()`.
   - After extraction, `isinstance` and pattern matching work for type narrowing.

4. **Registration** (`register_targs()`)
   - Takes a class and an `ArgumentParser`
   - Registers regular targs, then groups (`add_argument_group`/`add_mutually_exclusive_group`), then subcommands (`add_subparsers`)
   - Recursively handles subcommands (which can have their own groups)
   - Automatically infers type from type hints if not specified
   - Uses docstrings as help text if `help` parameter not provided

5. **Extraction** (`extract_targs()`)
   - Takes parsed `Namespace` from `parser.parse_args()` and the argument class
   - Reconstructs a fully-typed instance of your arguments class
   - Recursively extracts group instances (nested access)
   - Identifies chosen subcommand and extracts its typed instance
   - Maps argument destinations (with dash-to-underscore conversion) back to class attributes

**Key Technical Details:**

- **Sentry Pattern** (utils.py): A clever pattern where a value can be either a type class OR an instance. Used for marking unset optional values without requiring special sentinels.
- **Descriptor Protocol** (`TArg.__set_name__`): Auto-registers argument configs when the class is created, no manual tracking needed.
- **Post-init Hooks** (`@post_init` decorator): Allows validation logic after argument extraction.
- **Docstring Extraction** (utils.py): Uses AST parsing to extract docstrings from attributes and use them as help text.
- **Decorator Consistency**: All three decorators (`@tgroup`, `@texclusive`, `@tsubcommands`) support dual calling styles: bare `@decorator` and parameterized `@decorator(...)`. Title can be passed as the first positional argument or via keyword. Note: `@texclusive` does not support `title`/`description` — this is a limitation of `argparse.MutuallyExclusiveGroup`.
- **Docstring Extraction** (utils.py): Uses AST parsing with `textwrap.dedent` to extract docstrings from attributes. Works for both module-level and function-scoped (indented) classes.

## Key Conventions

### Naming Rules
- **Underscores to Dashes**: When using `Flag` for optional arguments, underscores in the class attribute name are automatically converted to dashes in the CLI (e.g., `optional_dash` becomes `--optional-dash`).
- **Dest Mapping**: The `get_dest()` method handles converting flag names back to attribute names when extracting from `Namespace`.
- **Subcommand Names**: The class name of a `@targs` subclass is used as the subcommand name.

### Type Hint Requirements
- All `targ()` fields **must** have a type hint.
- **Type inference rules** (in `_infer_type_from_hint()`):
  1. User explicit `type=` → always used (highest priority)
  2. Has `action` → skip inference (actions handle their own types)
  3. `bool` / `bool | None` → skip inference (require explicit `action="store_true/store_false"`)
  4. `X | None` / `Optional[X]` where X is a non-bool callable → use X
  5. `list[X]` etc. with `nargs` set → use element type X
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
- `__init__.py`: Public API exports (Name, Flag, targ, targs, tgroup, texclusive, tsubcommands, post_init, register_targs, extract_targs)
- `targs.py`: Core logic (TArg dataclass, all decorators, registration/extraction)
- `utils.py`: Helper utilities (Sentry pattern, logger, AST-based docstring extraction)

### Internal Attributes
- `_targs` / `_targs_flag`: Per-class targs dict and initialization marker
- `_targs_groups`: Dict mapping attribute name → group class (set by `@targs`)
- `_targs_subcommands`: Dict mapping attribute name → subcommands base class (set by `@targs`)
- `_tgroup_flag` / `_tgroup_title` / `_tgroup_description`: Group metadata (set by `@tgroup`)
- `_texclusive_flag` / `_texclusive_required`: Exclusive group metadata (set by `@texclusive`)
- `_tsubcommands_flag` / `_tsubcommands_title` / `_tsubcommands_description` / `_tsubcommands_required`: Subcommand metadata (set by `@tsubcommands`)

### Testing
- Located in `tests/` directory
- `test_basic.py`: Core functionality (targ, Name, Flag, register, extract, subclass, post_init, docstrings, all action types, custom Action, nargs, required, metavar, dest)
- `test_groups.py`: Argument groups and mutually exclusive groups
- `test_subcommands.py`: Subcommands with inheritance, groups inside subcommands, pattern matching
- `test_type_inference.py`: Type inference expansion (X | None, Optional[X], list[X]+nargs, bool protection)
- Example files: `example.py`, `example_groups.py`, `example_subcommands.py` (synced to README via MARKDOWN-AUTO-DOCS)
