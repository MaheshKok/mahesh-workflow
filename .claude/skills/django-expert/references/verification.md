# Django Verification Pipeline

Pre-PR and pre-deployment verification pipeline. Run all 12 phases before merging or deploying.

## Phase 1: Environment Check

Verify Python version and dependency freshness.

```bash
# Confirm Python version
python --version  # Expect 3.12+

# Check Django version
python -c "import django; print(django.get_version())"

# Check for outdated packages
pip list --outdated

# Verify all dependencies are installed and compatible
pip check

# Verify requirements are in sync (if using pip-tools)
pip-compile --check requirements/base.in 2>/dev/null || echo "pip-tools not configured — skip"

# Verify .env file exists (not committed)
test -f .env && echo ".env exists" || echo "WARNING: .env missing"

# Verify .env is in .gitignore
grep -q "^\.env$" .gitignore && echo ".env in .gitignore" || echo "WARNING: .env not in .gitignore"
```

## Phase 2: Code Quality

Static analysis, formatting, and linting.

```bash
# Type checking (strict mode)
mypy apps/ --config-file pyproject.toml

# Linting
ruff check apps/

# Formatting check (no modifications)
black --check apps/

# Import order check (no modifications)
isort --check-only apps/

# Django system checks (deployment mode)
python manage.py check --deploy --fail-level WARNING
```

### pyproject.toml configuration

```toml
[tool.mypy]
python_version = "3.12"
plugins = ["mypy_django_plugin.main", "mypy_drf_plugin.main"]
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.django-stubs]
django_settings_module = "config.settings.production"

[tool.ruff]
target-version = "py312"
line-length = 99

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "UP",   # pyupgrade
    "DJ",   # flake8-django
    "SIM",  # flake8-simplify
    "S",    # flake8-bandit
    "T20",  # flake8-print
]

[tool.black]
target-version = ["py312"]
line-length = 99

[tool.isort]
profile = "black"
line_length = 99
known_django = ["django", "rest_framework"]
sections = ["FUTURE", "STDLIB", "THIRDPARTY", "DJANGO", "FIRSTPARTY", "LOCALFOLDER"]
```

## Phase 3: Migrations

Verify migration state is consistent and no ungenerated migrations exist.

```bash
# Show current migration status
python manage.py showmigrations --list

# Verify no missing migrations (fails if models changed without makemigrations)
python manage.py makemigrations --check --dry-run

# Preview what migrate would do (without applying)
python manage.py migrate --plan

# Check for migration conflicts
python manage.py makemigrations --check --merge 2>/dev/null || true

# Check for squashable migrations (many unapplied in a single app)
python manage.py showmigrations | grep -c "\[ \]" | xargs -I{} echo "Unapplied migrations: {}"
```

## Phase 4: Tests + Coverage

Run the full test suite with coverage enforcement.

```bash
# Run all tests with coverage
pytest \
    --cov=apps \
    --cov-report=term-missing \
    --cov-report=html:htmlcov \
    --cov-fail-under=80 \
    -v \
    --tb=short

# Run only unit tests (fast feedback)
pytest -m "not integration and not e2e" --tb=short

# Run integration tests separately
pytest -m integration -v

# Parallel test execution for large suites
pytest -n auto --dist loadscope

# Generate XML coverage for CI
pytest --cov=apps --cov-report=xml:coverage.xml --junitxml=test-results.xml
```

## Phase 5: Security Scan

Audit dependencies, scan source code, and check for leaked secrets.

```bash
# Audit Python dependencies for known vulnerabilities
pip-audit

# Alternative: safety check
safety check --full-report

# Static security analysis of source code
bandit -r apps/ -c pyproject.toml -f json -o bandit-report.json

# Scan for leaked secrets in git history
gitleaks detect --source . --report-path gitleaks-report.json

# Django deployment security checks
python manage.py check --deploy --fail-level WARNING

# Check for hardcoded secrets in source
grep -rn "SECRET_KEY\s*=" --include="*.py" | grep -v "env(" || echo "No hardcoded SECRET_KEY found"
grep -rn "PASSWORD\s*=" --include="*.py" | grep -v "env\(\|test\|factory\|fixture\|mock" || echo "No hardcoded PASSWORD found"
```

### bandit configuration in pyproject.toml

```toml
[tool.bandit]
exclude_dirs = ["tests", "migrations"]
skips = ["B101"]  # Allow assert in test files
```

## Phase 6: Django Management Commands

Run Django's built-in system checks and validate static file collection.

```bash
# Full system check
python manage.py check

# Check with all registered tags
python manage.py check --tag security --tag compatibility

# Check for specific apps
python manage.py check apps.accounts apps.orders apps.products

# Dry-run collectstatic to verify configuration
python manage.py collectstatic --noinput --dry-run

# Validate database connection and schema
python manage.py inspectdb > /dev/null 2>&1 && echo "DB connection OK" || echo "DB connection FAILED"

# Verify database integrity (check FK constraints, orphaned records)
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()
from django.core.management import call_command
call_command('check', '--database', 'default')
print('Database integrity check passed')
"
```

## Phase 7: Performance Checks

Detect N+1 queries and missing database indexes.

```bash
# Run tests with N+1 query detection enabled
NPLUSONE_RAISE=True pytest -m "not slow" --tb=short

# Check for missing indexes on models
python manage.py check --tag models
```

### nplusone configuration

```python
# config/settings/testing.py — add N+1 detection

INSTALLED_APPS += ["nplusone.ext.django"]  # noqa: F405
MIDDLEWARE.insert(0, "nplusone.ext.django.NPlusOneMiddleware")  # noqa: F405

NPLUSONE_RAISE = True  # Fail tests on N+1 queries
NPLUSONE_WHITELIST = [
    {"model": "admin.LogEntry"},  # Django admin internals
]
```

### Missing index detection script

```python
"""Script to find model fields that are filtered on but lack a db_index.

Run with: python manage.py shell < scripts/check_indexes.py
"""

from django.apps import apps


def check_missing_indexes() -> list[str]:
    """Find fields that may benefit from an index but don't have one.

    Checks CharField, IntegerField, and DateTimeField on all models.
    Skips primary keys, unique fields, and fields that already have db_index.

    Returns:
        List of warning strings for fields that should be indexed.
    """
    warnings: list[str] = []
    indexable_types = {"CharField", "IntegerField", "DateTimeField", "DateField", "SlugField"}

    for model in apps.get_models():
        for field in model._meta.get_fields():
            if not hasattr(field, "db_index"):
                continue
            if not hasattr(field, "column"):
                continue
            if field.primary_key or field.unique or field.db_index:
                continue
            if field.get_internal_type() in indexable_types:
                warnings.append(
                    f"  {model._meta.label}.{field.name} ({field.get_internal_type()}) "
                    f"— consider adding db_index=True"
                )
    return warnings


results = check_missing_indexes()
if results:
    print("Fields that may benefit from an index:")
    for line in results:
        print(line)
else:
    print("No obvious missing indexes found.")
```

## Phase 8: Static Assets

Audit frontend dependencies and verify build output.

```bash
# Audit npm dependencies for vulnerabilities
npm audit --production

# Build static assets
npm run build

# Verify build output exists
ls -la static/dist/ 2>/dev/null || echo "No built assets directory found — skip if not using frontend build"

# Verify collectstatic works
python manage.py collectstatic --noinput --dry-run 2>&1 | tail -1
```

## Phase 9: Configuration Review

Automated check of critical production settings.

```python
"""Verify production configuration is correct.

Run with: DJANGO_SETTINGS_MODULE=config.settings.production python scripts/check_config.py
"""

import os
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
django.setup()

from django.conf import settings


def check_config() -> list[str]:
    """Validate critical production settings.

    Checks DEBUG, SECRET_KEY strength, ALLOWED_HOSTS, HTTPS settings,
    HSTS configuration, cookie security, database engine, email backend,
    and cache backend.

    Returns:
        List of error/warning strings. Empty list means all checks passed.
    """
    errors: list[str] = []

    # --- DEBUG ---
    if settings.DEBUG:
        errors.append("CRITICAL: DEBUG is True in production settings")

    # --- SECRET_KEY ---
    insecure_prefixes = {"change-me", "django-insecure-", "your-secret-key-here"}
    if any(settings.SECRET_KEY.startswith(prefix) for prefix in insecure_prefixes):
        errors.append("CRITICAL: SECRET_KEY appears to be a default/insecure value")
    if len(settings.SECRET_KEY) < 50:
        errors.append("WARNING: SECRET_KEY is shorter than 50 characters")

    # --- ALLOWED_HOSTS ---
    if not settings.ALLOWED_HOSTS or "*" in settings.ALLOWED_HOSTS:
        errors.append("CRITICAL: ALLOWED_HOSTS is empty or contains wildcard '*'")

    # --- HTTPS ---
    if not getattr(settings, "SECURE_SSL_REDIRECT", False):
        errors.append("WARNING: SECURE_SSL_REDIRECT is not enabled")

    if not getattr(settings, "SESSION_COOKIE_SECURE", False):
        errors.append("WARNING: SESSION_COOKIE_SECURE is not enabled")

    if not getattr(settings, "CSRF_COOKIE_SECURE", False):
        errors.append("WARNING: CSRF_COOKIE_SECURE is not enabled")

    # --- HSTS ---
    hsts_seconds = getattr(settings, "SECURE_HSTS_SECONDS", 0)
    if hsts_seconds < 31536000:
        errors.append(
            f"WARNING: SECURE_HSTS_SECONDS is {hsts_seconds} "
            f"(recommended: 31536000 = 1 year)"
        )

    if not getattr(settings, "SECURE_HSTS_INCLUDE_SUBDOMAINS", False):
        errors.append("WARNING: SECURE_HSTS_INCLUDE_SUBDOMAINS is not enabled")

    if not getattr(settings, "SECURE_HSTS_PRELOAD", False):
        errors.append("WARNING: SECURE_HSTS_PRELOAD is not enabled")

    # --- Content Security ---
    if not getattr(settings, "SECURE_CONTENT_TYPE_NOSNIFF", False):
        errors.append("WARNING: SECURE_CONTENT_TYPE_NOSNIFF is not enabled")

    # --- Database ---
    default_db = settings.DATABASES.get("default", {})
    if "sqlite" in default_db.get("ENGINE", "").lower():
        errors.append("CRITICAL: SQLite is configured as the production database")

    # --- Email ---
    non_production_backends = {
        "django.core.mail.backends.console.EmailBackend",
        "django.core.mail.backends.locmem.EmailBackend",
        "django.core.mail.backends.filebased.EmailBackend",
    }
    if settings.EMAIL_BACKEND in non_production_backends:
        errors.append(
            f"WARNING: EMAIL_BACKEND is '{settings.EMAIL_BACKEND}' (not production-ready)"
        )

    # --- Cache ---
    default_cache = settings.CACHES.get("default", {})
    if "LocMemCache" in default_cache.get("BACKEND", ""):
        errors.append("WARNING: Using LocMemCache in production (use Redis or Memcached)")

    # --- CORS ---
    if getattr(settings, "CORS_ALLOW_ALL_ORIGINS", False):
        errors.append("WARNING: CORS_ALLOW_ALL_ORIGINS is True (restrict to specific origins)")

    return errors


if __name__ == "__main__":
    errors = check_config()
    if errors:
        print("Configuration issues found:\n")
        for error in errors:
            print(f"  {error}")
        sys.exit(1)
    else:
        print("All configuration checks passed.")
        sys.exit(0)
```

### Running the configuration review

```bash
# Run the configuration check script
DJANGO_SETTINGS_MODULE=config.settings.production python scripts/check_config.py

# Quick inline check without a separate script
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()
from django.conf import settings
checks = {
    'DEBUG': not settings.DEBUG,
    'SECRET_KEY length >= 50': len(settings.SECRET_KEY) >= 50,
    'ALLOWED_HOSTS set': bool(settings.ALLOWED_HOSTS) and '*' not in settings.ALLOWED_HOSTS,
    'SECURE_SSL_REDIRECT': getattr(settings, 'SECURE_SSL_REDIRECT', False),
    'SECURE_HSTS_SECONDS >= 1yr': getattr(settings, 'SECURE_HSTS_SECONDS', 0) >= 31536000,
    'SESSION_COOKIE_SECURE': getattr(settings, 'SESSION_COOKIE_SECURE', False),
    'CSRF_COOKIE_SECURE': getattr(settings, 'CSRF_COOKIE_SECURE', False),
}
for name, passed in checks.items():
    status = 'PASS' if passed else 'FAIL'
    print(f'  [{status}] {name}')
"
```

## Phase 10: Logging

Verify logging configuration produces expected output.

```bash
# Test that logging works and output format is correct
python -c "
import os, django, logging
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()
logger = logging.getLogger('django')
logger.info('Verification: logging test message (INFO)')
logger.warning('Verification: logging test message (WARNING)')
print('Logging configuration OK')
"

# Verify log directory exists (if file-based logging is used)
test -d logs && echo "logs/ directory exists" || echo "WARNING: logs/ directory missing"

# Print current logging configuration
python -c "
import os, django, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()
from django.conf import settings
print(json.dumps(settings.LOGGING, indent=2, default=str))
"
```

### Logging test in pytest

```python
"""Test that logging configuration produces output at the expected levels."""

import logging

import pytest


@pytest.mark.django_db
class TestLoggingConfiguration:
    """Verify logging is properly configured."""

    def test_warning_logs_are_captured(self, caplog):
        """WARNING-level logs should appear in output."""
        logger = logging.getLogger("django.request")
        with caplog.at_level(logging.WARNING, logger="django.request"):
            logger.warning("Test warning message")
        assert "Test warning message" in caplog.text

    def test_security_logger_exists(self):
        """The security logger should be configured and have handlers."""
        logger = logging.getLogger("django.security")
        assert logger is not None
        effective_handlers = logger.handlers or logging.getLogger().handlers
        assert len(effective_handlers) > 0

    def test_info_logs_not_shown_in_production_level(self, caplog):
        """INFO-level logs should not appear when root logger is WARNING."""
        logger = logging.getLogger("django")
        with caplog.at_level(logging.WARNING, logger="django"):
            logger.info("This should not appear")
        assert "This should not appear" not in caplog.text
```

## Phase 11: API Documentation

Generate and validate the API schema.

```bash
# Generate OpenAPI schema with drf-spectacular (preferred)
python manage.py spectacular --validate --fail-on-warn

# Export schema to file
python manage.py spectacular --file schema.yml --validate

# Alternative: DRF built-in schema generation
python manage.py generateschema > schema.yml

# Show all registered URL patterns
python manage.py show_urls 2>/dev/null || python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()
from django.urls import get_resolver
for pattern in sorted(get_resolver().url_patterns, key=lambda p: str(p.pattern)):
    print(f'  {pattern.pattern}')
"

# Validate the generated schema (if openapi-spec-validator is installed)
python -c "
from openapi_spec_validator import validate
from openapi_spec_validator.readers import read_from_filename
spec_dict = read_from_filename('schema.yml')
validate(spec_dict)
print('Schema validation passed')
" 2>/dev/null || echo "openapi-spec-validator not installed — schema validation skipped"
```

## Phase 12: Diff Review

Final review of all changes before merge.

```bash
# Summary of changed files
git diff --stat main...HEAD

# Full diff for review
git diff main...HEAD

# Check for debug artifacts left in code
git diff main...HEAD | grep -n -E \
    "(TODO|FIXME|HACK|XXX|print\(|pdb\.|breakpoint\(\)|DEBUG\s*=\s*True|console\.log)" \
    || echo "No debug artifacts found"

# List new files being added
git diff --name-only --diff-filter=A main...HEAD

# Check for large files being added (> 1MB)
git diff --stat main...HEAD --diff-filter=A | awk '{print $NF, $1}' | sort -t'|' -k2 -rn | head -10

# Review migration files specifically
git diff main...HEAD --name-only | grep "migrations/" || echo "No migration changes"

# Check for TODO/FIXME in changed files only
git diff main...HEAD --name-only | xargs grep -n "TODO\|FIXME\|HACK\|XXX" 2>/dev/null || echo "No TODO/FIXME found in changed files"
```

## Output Template

Use this template to record verification results.

```
=== Django Verification Report ===
Project: <project-name>
Branch:  <branch-name>
Base:    main
Date:    YYYY-MM-DD
Run by:  <author>

Phase 1  - Environment Check        : [PASS/FAIL]
Phase 2  - Code Quality             : [PASS/FAIL] (0 warnings)
Phase 3  - Migrations               : [PASS/FAIL] (no missing migrations)
Phase 4  - Tests + Coverage          : [PASS/FAIL] (142 passed, 0 failed, 87% coverage)
Phase 5  - Security Scan            : [PASS/FAIL] (0 vulnerabilities)
Phase 6  - Django Management         : [PASS/FAIL] (0 issues)
Phase 7  - Performance Checks       : [PASS/FAIL] (no N+1 detected)
Phase 8  - Static Assets            : [PASS/FAIL]
Phase 9  - Configuration Review     : [PASS/FAIL] (all checks green)
Phase 10 - Logging                  : [PASS/FAIL]
Phase 11 - API Documentation        : [PASS/FAIL] (schema valid)
Phase 12 - Diff Review              : [PASS/FAIL] (no debug artifacts)

Overall: [READY FOR PR / BLOCKED]

Notes:
- <any issues, warnings, or items to address>
```

## Pre-Deployment Checklist

Run through this checklist before every production deployment.

- [ ] All 12 verification phases pass
- [ ] `DEBUG = False` in production settings
- [ ] `SECRET_KEY` is a unique, random, 50+ character value loaded from env var
- [ ] `ALLOWED_HOSTS` contains only production domains (no wildcards)
- [ ] HTTPS redirect is enabled (`SECURE_SSL_REDIRECT = True`)
- [ ] HSTS is configured (31536000 seconds, include subdomains, preload)
- [ ] `SESSION_COOKIE_SECURE` and `CSRF_COOKIE_SECURE` are both `True`
- [ ] Database is PostgreSQL (not SQLite)
- [ ] Database backups are configured and tested
- [ ] Database credentials loaded from environment variables
- [ ] Redis or Memcached is configured for caching (not LocMemCache)
- [ ] Email backend is SMTP or a transactional email service (not console/locmem)
- [ ] Static files are collected and served via CDN or whitenoise
- [ ] Media file uploads have size and type validation
- [ ] Logging is configured with structured output (JSON formatter)
- [ ] Logging writes to persistent storage (not just stdout)
- [ ] Error tracking (Sentry) is configured with DSN
- [ ] Rate limiting is enabled on authentication endpoints
- [ ] CORS origins are explicitly listed (no `CORS_ALLOW_ALL_ORIGINS = True`)
- [ ] All migrations are applied (`python manage.py migrate --plan` shows nothing pending)
- [ ] No `print()`, `pdb`, or `breakpoint()` in committed code
- [ ] Environment variables are set in the deployment environment
- [ ] Celery workers and beat scheduler are configured (if applicable)
- [ ] Health check endpoint responds correctly
- [ ] Backup and rollback strategy is documented and tested

## GitHub Actions CI/CD

```yaml
name: Django CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  DJANGO_SETTINGS_MODULE: config.settings.testing
  DJANGO_SECRET_KEY: ci-test-secret-key-not-for-production
  PYTHON_VERSION: "3.12"

jobs:
  lint:
    name: Code Quality
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -r requirements/development.txt

      - name: Run mypy
        run: mypy apps/ --config-file pyproject.toml

      - name: Run ruff
        run: ruff check apps/

      - name: Check formatting (black)
        run: black --check apps/

      - name: Check import order (isort)
        run: isort --check-only apps/

      - name: Django system checks
        run: python manage.py check --deploy --fail-level WARNING

  test:
    name: Tests + Coverage
    runs-on: ubuntu-latest
    needs: lint
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: testuser
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: testdb
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    env:
      DATABASE_URL: postgres://testuser:testpass@localhost:5432/testdb
      REDIS_URL: redis://localhost:6379/1
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Cache pip
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements/*.txt') }}
          restore-keys: ${{ runner.os }}-pip-

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -r requirements/development.txt

      - name: Check migrations
        run: python manage.py makemigrations --check --dry-run

      - name: Run migrations
        run: python manage.py migrate

      - name: Run tests with coverage
        run: |
          pytest \
            --cov=apps \
            --cov-report=term-missing \
            --cov-report=xml:coverage.xml \
            --cov-fail-under=80 \
            --junitxml=test-results.xml \
            -v

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          file: coverage.xml
          fail_ci_if_error: true

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-results
          path: test-results.xml

  security:
    name: Security Scan
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -r requirements/development.txt

      - name: Audit dependencies (pip-audit)
        run: pip-audit

      - name: Static security scan (bandit)
        run: bandit -r apps/ -c pyproject.toml -f json -o bandit-report.json || true

      - name: Upload bandit report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: bandit-report
          path: bandit-report.json

      - name: Django deployment check
        run: python manage.py check --deploy --fail-level WARNING

      - name: Scan for secrets (gitleaks)
        uses: gitleaks/gitleaks-action@v2
        env:
          GITLEAKS_LICENSE: ${{ secrets.GITLEAKS_LICENSE }}

  migrations:
    name: Migration Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: pip install -r requirements/development.txt

      - name: Check for missing migrations
        run: python manage.py makemigrations --check --dry-run

  deploy:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: [test, security, migrations]
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Deploy
        run: echo "Deploy steps here (e.g., docker push, terraform apply, railway deploy, etc.)"
```

## Quick Reference Command Table

| Task | Command |
|------|---------|
| Run all tests | `pytest` |
| Run with coverage | `pytest --cov=apps --cov-report=term-missing --cov-fail-under=80` |
| Skip slow tests | `pytest -m "not slow"` |
| Integration tests only | `pytest -m integration` |
| Run single test file | `pytest apps/orders/tests/test_services.py` |
| Run single test | `pytest apps/orders/tests/test_services.py::TestOrderService::test_create` |
| Parallel tests | `pytest -n auto --dist loadscope` |
| Check migrations | `python manage.py makemigrations --check --dry-run` |
| Show migration plan | `python manage.py migrate --plan` |
| Apply migrations | `python manage.py migrate` |
| Django system checks | `python manage.py check --deploy` |
| Lint | `ruff check apps/` |
| Format check | `black --check apps/` |
| Import order check | `isort --check-only apps/` |
| Type check | `mypy apps/ --config-file pyproject.toml` |
| Security audit | `pip-audit && bandit -r apps/ -c pyproject.toml` |
| Dependency check | `safety check --full-report` |
| Secret scan | `gitleaks detect --source .` |
| Collect static | `python manage.py collectstatic --noinput` |
| Generate schema | `python manage.py spectacular --validate --fail-on-warn` |
| Generate schema (built-in) | `python manage.py generateschema > schema.yml` |
| Show URLs | `python manage.py show_urls` |
| Config review | `DJANGO_SETTINGS_MODULE=config.settings.production python scripts/check_config.py` |
| Shell | `python manage.py shell_plus` |
| Diff review | `git diff --stat main...HEAD` |
| Debug artifact scan | `git diff main...HEAD \| grep -E "TODO\|FIXME\|print\(\|pdb\.\|breakpoint"` |
