# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.0.0] - Unreleased

### Added
- **Argument groups** (`@tgroup`) — organize related arguments into named groups
- **Mutually exclusive groups** (`@texclusive`) — define arguments that cannot be used together
- **Subcommands** (`@tsubcommands`) — define subcommands via class inheritance with full type safety
- **`create_parser()`** — one-step convenience function for parser creation with auto-filled description
- **Docstring-driven help** — class/attribute docstrings automatically used as descriptions and help text
- **Smart type inference** — automatically infers `type=` from type hints (`X | None`, `list[X]`, bare types)
- **`DocString`** dataclass — structured docstring parsing with title/description splitting
- **Mutable default safety** — `list`, `dict`, `set` defaults are shallow-copied to prevent sharing
- Comprehensive test suite (146 tests)
- Example scripts for groups (`example_groups.py`) and subcommands (`example_subcommands.py`)

### Changed
- **Internal module reorganization** — split monolithic `targs.py` and `utils.py` into focused modules:
  `_types.py`, `_decorators.py`, `_registry.py`, `_inference.py`, `_docstring.py`, `_utils.py`
- All internal modules prefixed with `_` to clearly separate public API from internals
- `register_targs` now preserves docstring formatting in help output
- Improved subclass handling and attribute copying

### Fixed
- Docstring formatting preserved in `--help` output
- Various edge cases in type inference and argument registration

## [0.2.5] - 2025

### Added
- `py.typed` marker file for PEP 561 compliance

## [0.2.4] - 2025

### Fixed
- Added `type[Action]` to `TArg.action` for custom actions

## [0.2.3] - 2025

### Fixed
- Fixed shallow copy of targs attributes when subclassing

## [0.2.2] - 2025

### Fixed
- Made `post_init` work with subclassed targs classes

## [0.2.1] - 2025

### Fixed
- Made `get_attr_docstrings` search through class hierarchy

## [0.2.0] - 2025

### Added
- `post_init` decorator for validation hooks after argument extraction

## [0.1.0] - 2025

### Changed
- Renamed package from `targs` to `argparse_type_helper`
- Initial public release on PyPI
