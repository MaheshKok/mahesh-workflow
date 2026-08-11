# Python Tooling

## ruff (Linter and Formatter)

ruff is an extremely fast Python linter and formatter that replaces flake8, isort, pyupgrade, and many other tools.

### Commands

```bash
# Lint
ruff check src/
ruff check src/ --fix          # Auto-fix what it can
ruff check src/ --fix --unsafe-fixes  # Include unsafe fixes

# Format (replaces black)
ruff format src/
ruff format src/ --check       # Check without modifying

# Watch mode
ruff check src/ --watch
```

### pyproject.toml configuration

```toml
[tool.ruff]
target-version = "py312"
line-length = 88
src = ["src", "tests"]

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "N",    # pep8-naming
    "UP",   # pyupgrade
    "B",    # flake8-bugbear
    "SIM",  # flake8-simplify
    "S",    # flake8-bandit (security)
    "A",    # flake8-builtins
    "C4",   # flake8-comprehensions
    "DTZ",  # flake8-datetimez
    "T20",  # flake8-print (no print statements)
    "RET",  # flake8-return
    "PTH",  # flake8-use-pathlib
    "ERA",  # eradicate (commented-out code)
    "PL",   # pylint
    "RUF",  # ruff-specific rules
]
ignore = [
    "E501",   # line too long (handled by formatter)
    "S101",   # assert usage (allowed in tests)
]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["S101", "PLR2004"]  # Allow assert and magic values in tests

[tool.ruff.lint.isort]
known-first-party = ["myapp"]
force-single-line = false
```

## black (Formatter)

black is an opinionated code formatter. If using ruff format, you may not need black separately, but many projects still use it.

### Commands

```bash
# Format files
black src/ tests/

# Check without modifying
black --check src/ tests/

# Show diff of what would change
black --diff src/ tests/
```

### pyproject.toml configuration

```toml
[tool.black]
target-version = ["py312"]
line-length = 88
```

## mypy (Static Type Checker)

### Commands

```bash
# Type check
mypy src/

# Strict mode (recommended)
mypy --strict src/

# Show error codes (useful for targeted ignores)
mypy src/ --show-error-codes

# Generate HTML report
mypy src/ --html-report mypy-report/
```

### pyproject.toml configuration

```toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
follow_imports = "normal"
show_error_codes = true

# Per-module overrides
[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false

[[tool.mypy.overrides]]
module = "third_party_lib.*"
ignore_missing_imports = true
```

## isort (Import Sorting)

If using ruff with the `I` rule, isort is handled automatically. Standalone configuration shown for reference.

### pyproject.toml configuration

```toml
[tool.isort]
profile = "black"
known_first_party = ["myapp"]
line_length = 88
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
```

## Complete pyproject.toml Example

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "myapp"
version = "1.0.0"
description = "A well-structured Python application"
readme = "README.md"
license = "MIT"
requires-python = ">=3.12"
authors = [
    { name = "Your Name", email = "you@example.com" },
]
dependencies = [
    "httpx>=0.27",
    "pydantic>=2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "pytest-asyncio>=0.23",
    "pytest-mock>=3.14",
    "mypy>=1.11",
    "ruff>=0.6",
    "bandit>=1.7",
    "pre-commit>=3.8",
]

[project.scripts]
myapp = "myapp.cli:main"

# --- Tool Configuration ---

[tool.ruff]
target-version = "py312"
line-length = 88
src = ["src", "tests"]

[tool.ruff.lint]
select = ["E", "W", "F", "I", "N", "UP", "B", "SIM", "S", "A", "C4", "DTZ", "T20", "RET", "PTH", "RUF"]
ignore = ["E501"]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["S101", "PLR2004"]

[tool.ruff.lint.isort]
known-first-party = ["myapp"]

[tool.mypy]
python_version = "3.12"
strict = true
show_error_codes = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-ra -q --strict-markers"
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks integration tests",
]
asyncio_mode = "auto"

[tool.coverage.run]
source = ["src"]
branch = true
omit = ["*/tests/*", "*/__main__.py"]

[tool.coverage.report]
fail_under = 80
show_missing = true
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.",
    "@overload",
]

[tool.bandit]
exclude_dirs = ["tests"]
skips = ["B101"]
```

## Standard Project Layout

```
myapp/
    pyproject.toml
    Makefile
    .gitignore
    .env.example
    src/
        myapp/
            __init__.py
            cli.py               # CLI entry point (argparse)
            config.py            # Configuration loading
            core/
                __init__.py
                engine.py        # Core business logic
                models.py        # Domain models (dataclasses)
            services/
                __init__.py
                user_service.py  # Service layer
            repositories/
                __init__.py
                user_repo.py     # Data access
            utils/
                __init__.py
                validators.py    # Input validation
                helpers.py       # Utility functions
    tests/
        __init__.py
        conftest.py              # Shared fixtures
        unit/
            __init__.py
            core/
                __init__.py
                test_engine.py
                test_models.py
            utils/
                __init__.py
                test_validators.py
        integration/
            __init__.py
            conftest.py          # Integration fixtures
            test_user_service.py
        e2e/
            __init__.py
            test_cli.py
```

## Essential CLI Commands

```bash
# Format code
ruff format src/ tests/

# Lint code (with auto-fix)
ruff check src/ tests/ --fix

# Type check
mypy src/

# Run tests with coverage
bun pytest --cov=src --cov-report=term-missing

# Run specific test file
bun pytest tests/unit/test_models.py -v

# Run tests matching a pattern
bun pytest -k "test_create_user" -v

# Security scan
bandit -r src/ -ll

# Full quality check (add as Makefile target)
# make check
ruff format --check src/ tests/ && \
ruff check src/ tests/ && \
mypy src/ && \
bun pytest --cov=src --cov-report=term-missing --cov-fail-under=80 && \
bandit -r src/ -ll
```

## Makefile Targets

```makefile
.PHONY: help format lint typecheck test security check clean

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

format:  ## Format code with ruff
	ruff format src/ tests/

lint:  ## Lint code with ruff (auto-fix)
	ruff check src/ tests/ --fix

typecheck:  ## Run mypy type checker
	mypy src/

test:  ## Run tests with coverage
	bun pytest --cov=src --cov-report=term-missing

security:  ## Run bandit security scan
	bandit -r src/ -ll

check: format lint typecheck test security  ## Run all checks
```

## Pre-commit Configuration

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.11.0
    hooks:
      - id: mypy
        additional_dependencies: []

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.9
    hooks:
      - id: bandit
        args: [-r, src/, -ll]
```

Install hooks:

```bash
pre-commit install
pre-commit run --all-files
```
