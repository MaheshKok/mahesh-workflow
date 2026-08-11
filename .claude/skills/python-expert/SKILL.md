---
name: python-expert
description: "Comprehensive Python development expert. Use when writing, reviewing, or refactoring Python code. Covers patterns, testing, security, and tooling."
---

# Python Expert

Consolidated Python development skill with progressive disclosure. Read reference files only when the specific topic is relevant.

## When to Activate

- Writing or editing any .py file
- Reviewing Python code changes
- Setting up Python project infrastructure
- Debugging Python issues

## Core Rules (Always Apply)

1. Target Python 3.12. No deprecated APIs.
2. Type-hint ALL function signatures. Prefer built-in generics (list[str], dict[str, int]).
3. Follow PEP 8. Use black for formatting, ruff for linting, isort for imports.
4. Use context managers (with) for all resource management.
5. Never use bare except. Catch specific exceptions. Chain with `from e`.
6. Never use mutable default arguments (def f(x=[])). Use None + check.
7. Prefer list comprehensions over C-style loops for simple transforms.
8. Use isinstance() not type(). Use `is None` not `== None`.
9. Use f-strings for formatting. Use "".join() for string building in loops.
10. Use dataclasses for data containers. Use frozen=True for immutability.
11. Use Protocol for duck typing, ABC for nominal typing.
12. Prefer composition over inheritance.
13. Use logging module, not print().
14. Validate all inputs at system boundaries.
15. Use pathlib.Path for path operations.

## Reference Guide

| Topic | File | Read when... |
|-------|------|-------------|
| Patterns & Idioms | references/patterns.md | Writing Pythonic code, decorators, generators, comprehensions, dataclasses, package organization |
| Type Hints | references/type-hints.md | Working with type annotations, Protocol, TypeVar, generics |
| Testing | references/testing.md | Writing pytest tests, fixtures, mocking, parametrization, coverage |
| Concurrency | references/concurrency.md | Threading, multiprocessing, async/await, concurrent.futures |
| Security | references/security.md | Handling user input, secrets, SQL, file uploads, bandit scanning |
| Tooling | references/tooling.md | Configuring ruff, black, mypy, pyproject.toml, project structure |

## Constraints

- MUST read relevant reference file before writing code in that topic area
- MUST run python-reviewer agent after completing Python code changes
- MUST follow TDD: write test first, then implement
- MUST achieve 80%+ test coverage
