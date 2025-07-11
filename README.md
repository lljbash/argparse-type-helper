# Argparse Type Helper

A lightweight helper that lets you leverage type hints with `argparse`.

## Features

- **Class-based schema**
  Bundle all your arguments in a single `@targs`-decorated class.
- **Identical API**
  Each field uses the same parameters as `argparse.add_argument` (`help`, `action`, `nargs`, etc.).
- **Automatic registration**
  One call to `register_targs(parser, YourArgs)` wires up all arguments on your `ArgumentParser`.
- **Typed extraction**
  After `parse_args()`, call `extract_targs()` to get a fully-typed instance of your class.
- **Hybrid usage**
  Mix native `parser.add_argument(...)` calls with class-based definitions in the same parser.
- **Docstring support**
  Use docstrings to automatically generate help text for your arguments.

## Installation

```bash
pip install argparse-type-helper
```

## Usage

See [example.py](/tests/example.py).

## Why not [typed-argparse](https://typed-argparse.github.io/typed-argparse/)?

typed-argparse is a great library, but it replaces the familiar `argparse.add_argument` API with its own argument-definition interface, which can be a hurdle when integrating into an existing codebase.

argparse-type-helper, by contrast, is a simple helper that allows you to use type hints with argparse with minimal learning curve. It uses the same `argparse` API you’re already familiar with, and you can even mix native `argparse` usage with class-based definitions in the same parser.
