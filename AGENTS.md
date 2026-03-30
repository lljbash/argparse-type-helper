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

### Manual Testing
The project currently does not have automated tests. Manual testing should be done by running the example scripts:
```bash
uv run python tests/example.py
uv run python tests/subclass.py
uv run python tests/subclass2.py
```

## High-Level Architecture

**Core Problem:** `argparse` doesn't integrate well with type hints. This library bridges that gap by allowing you to define arguments using dataclass-like syntax with full type support, while remaining compatible with standard `argparse`.

**Design Pattern - Three Main Components:**

1. **Argument Definition** (`targ()` + `@targs` decorator)
   - `targ()`: Function that creates `TArg` configuration objects containing all argument metadata
   - `@targs`: Class decorator that transforms a regular class into a typed arguments container
   - `Name` and `Flag`: Marker classes/dataclasses that indicate positional vs optional arguments

2. **Registration** (`register_targs()`)
   - Takes a class and an `ArgumentParser`
   - Iterates through `TArg` configurations and calls `parser.add_argument()` for each
   - Automatically infers type from type hints if not specified
   - Uses docstrings as help text if `help` parameter not provided

3. **Extraction** (`extract_targs()`)
   - Takes parsed `Namespace` from `parser.parse_args()` and the argument class
   - Reconstructs a fully-typed instance of your arguments class
   - Maps argument destinations (with dash-to-underscore conversion) back to class attributes

**Key Technical Details:**

- **Sentry Pattern** (utils.py): A clever pattern where a value can be either a type class OR an instance. Used for marking unset optional values without requiring special sentinels.
- **Descriptor Protocol** (`TArg.__set_name__`): Auto-registers argument configs when the class is created, no manual tracking needed.
- **Post-init Hooks** (`@post_init` decorator): Allows validation logic after argument extraction.
- **Docstring Extraction** (utils.py): Uses AST parsing to extract docstrings from attributes and use them as help text.

## Key Conventions

### Naming Rules
- **Underscores to Dashes**: When using `Flag` for optional arguments, underscores in the class attribute name are automatically converted to dashes in the CLI (e.g., `optional_dash` becomes `--optional-dash`).
- **Dest Mapping**: The `get_dest()` method handles converting flag names back to attribute names when extracting from `Namespace`.

### Type Hint Requirements
- All `targ()` fields **must** have a type hint. If `type=` is not specified in the configuration, the type hint is used as the type converter.
- Type checking is **strict** (see `pyproject.toml`: `typeCheckingMode = "strict"`).

### Argument Configuration
- All parameters accepted by `argparse.add_argument()` are supported (`action`, `nargs`, `choices`, `default`, `help`, etc.)
- `Name` marks a positional argument (required)
- `Flag` or custom string/tuple marks an optional argument
- Can mix class-based definitions with native `parser.add_argument()` calls

### Code Style
- **Python 3.12+** (see `pyproject.toml`: `requires-python = ">=3.12"`)
- **Black 25+** for formatting
- **isort** with Black profile for import sorting
- **basedpyright strict mode** for type checking

### Module Organization
- `__init__.py`: Public API exports only (Name, Flag, targ, targs, register_targs, extract_targs, post_init)
- `targs.py`: Core logic (TArg dataclass, decorators, registration/extraction)
- `utils.py`: Helper utilities (Sentry pattern, logger, AST-based docstring extraction)

### Testing/Example Files
- Located in `tests/` directory
- Currently used for manual testing and documentation
- Files show real-world usage patterns (subclassing, custom parsers, validation)
