# Python Security

## SQL Injection Prevention

Always use parameterized queries. Never interpolate user input into SQL strings.

```python
import sqlite3

# WRONG: String interpolation (SQL injection vulnerability)
def get_user_unsafe(username: str) -> dict | None:
    cursor.execute(f"SELECT * FROM users WHERE name = '{username}'")
    return cursor.fetchone()

# CORRECT: Parameterized query
def get_user(db: sqlite3.Connection, username: str) -> dict | None:
    """Fetch a user by username using a parameterized query."""
    cursor = db.execute(
        "SELECT * FROM users WHERE name = ?",
        (username,),
    )
    return cursor.fetchone()

# CORRECT: Named parameters
def search_users(db: sqlite3.Connection, name: str, age: int) -> list[dict]:
    """Search users with named parameters."""
    cursor = db.execute(
        "SELECT * FROM users WHERE name LIKE :name AND age > :age",
        {"name": f"%{name}%", "age": age},
    )
    return cursor.fetchall()

# CORRECT: SQLAlchemy with bound parameters
from sqlalchemy import text

def get_orders(session: Session, user_id: int, status: str) -> list:
    """Fetch orders using SQLAlchemy parameterized query."""
    result = session.execute(
        text("SELECT * FROM orders WHERE user_id = :uid AND status = :status"),
        {"uid": user_id, "status": status},
    )
    return result.fetchall()
```

## Command Injection Prevention

Never pass user input through `shell=True`. Use list arguments with `subprocess`.

```python
import subprocess
import shlex

# WRONG: Shell injection vulnerability
def list_files_unsafe(directory: str) -> str:
    return subprocess.check_output(
        f"ls -la {directory}",
        shell=True,
        text=True,
    )

# CORRECT: List arguments (no shell interpretation)
def list_files(directory: str) -> str:
    """List files in a directory safely."""
    return subprocess.check_output(
        ["ls", "-la", directory],
        text=True,
        timeout=30,
    )

# CORRECT: If shell=True is absolutely necessary, use shlex.quote
def grep_files(pattern: str, directory: str) -> str:
    """Search files using grep with properly escaped input."""
    safe_pattern = shlex.quote(pattern)
    safe_directory = shlex.quote(directory)
    return subprocess.check_output(
        f"grep -r {safe_pattern} {safe_directory}",
        shell=True,
        text=True,
        timeout=60,
    )
```

## Path Traversal Prevention

Validate and sanitize file paths to prevent directory traversal attacks.

```python
from pathlib import Path

ALLOWED_BASE_DIR = Path("/app/uploads").resolve()

def safe_read_file(user_path: str) -> str:
    """Read a file, ensuring it stays within the allowed directory."""
    # Resolve the full path (follows symlinks, resolves ..)
    requested = (ALLOWED_BASE_DIR / user_path).resolve()

    # Verify the resolved path is within the allowed directory
    if not requested.is_relative_to(ALLOWED_BASE_DIR):
        raise PermissionError(
            f"Access denied: path escapes base directory"
        )

    if not requested.is_file():
        raise FileNotFoundError(f"File not found: {user_path}")

    return requested.read_text()

# WRONG: No path validation
def read_unsafe(filename: str) -> str:
    return open(f"/uploads/{filename}").read()  # ../../../etc/passwd works

# Additional check: reject paths with suspicious components
def validate_filename(filename: str) -> str:
    """Validate that a filename contains no path traversal components."""
    if ".." in filename or "/" in filename or "\\" in filename:
        raise ValueError(f"Invalid filename: {filename}")
    if filename.startswith("."):
        raise ValueError(f"Hidden files not allowed: {filename}")
    return filename
```

## Eval/Exec Abuse Prevention

Never use `eval()`, `exec()`, or `compile()` with user-controlled input.

```python
# WRONG: eval with user input (arbitrary code execution)
def calculate_unsafe(expression: str) -> float:
    return eval(expression)  # User can run any Python code

# CORRECT: Use ast.literal_eval for safe literal parsing
import ast

def parse_config_value(value: str) -> object:
    """Safely parse a Python literal (strings, numbers, lists, dicts)."""
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError) as e:
        raise ValueError(f"Invalid literal value: {value}") from e

# CORRECT: Use a proper expression parser for math
# Install: pip install simpleeval
from simpleeval import simple_eval

def calculate(expression: str) -> float:
    """Safely evaluate a mathematical expression."""
    return simple_eval(expression)
```

## Unsafe Deserialization Prevention

Never unpickle data from untrusted sources. Prefer JSON or other safe formats.

```python
import json

# WRONG: pickle with untrusted data (arbitrary code execution)
import pickle

def load_data_unsafe(data: bytes) -> object:
    return pickle.loads(data)  # Can execute arbitrary code

# CORRECT: Use JSON for data interchange
def load_data(raw: str) -> dict:
    """Load data from a JSON string."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON data: {e}") from e

# CORRECT: If you must use pickle, restrict allowed classes
import io

class RestrictedUnpickler(pickle.Unpickler):
    """Unpickler that only allows specific safe classes."""

    ALLOWED_CLASSES: frozenset[tuple[str, str]] = frozenset({
        ("builtins", "dict"),
        ("builtins", "list"),
        ("builtins", "set"),
        ("builtins", "str"),
        ("builtins", "int"),
        ("builtins", "float"),
    })

    def find_class(self, module: str, name: str) -> type:
        if (module, name) not in self.ALLOWED_CLASSES:
            raise pickle.UnpicklingError(
                f"Forbidden class: {module}.{name}"
            )
        return super().find_class(module, name)

def safe_unpickle(data: bytes) -> object:
    """Unpickle data with restricted class loading."""
    return RestrictedUnpickler(io.BytesIO(data)).load()
```

## Secret Management

```python
import os
from pathlib import Path

# WRONG: Hardcoded secrets
API_KEY = "sk-1234567890abcdef"
DB_PASSWORD = "supersecret123"

# CORRECT: Environment variables
def get_required_env(name: str) -> str:
    """Get a required environment variable or fail fast."""
    value = os.environ.get(name)
    if value is None:
        raise RuntimeError(
            f"Required environment variable {name} is not set"
        )
    return value

API_KEY: str = get_required_env("API_KEY")
DB_PASSWORD: str = get_required_env("DB_PASSWORD")

# CORRECT: Using python-dotenv for local development
from dotenv import load_dotenv

def initialize_config() -> None:
    """Load environment from .env file (local dev only)."""
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path)

# .env file (MUST be in .gitignore)
# API_KEY=sk-1234567890abcdef
# DB_PASSWORD=supersecret123

# .gitignore entry:
# .env
# .env.*
# !.env.example
```

## Weak Crypto Detection

```python
import hashlib
import secrets

# WRONG: MD5/SHA1 for security purposes (collision-vulnerable)
password_hash = hashlib.md5(password.encode()).hexdigest()
token = hashlib.sha1(os.urandom(16)).hexdigest()

# CORRECT: Use bcrypt or argon2 for password hashing
# Install: pip install bcrypt
import bcrypt

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a bcrypt hash."""
    return bcrypt.checkpw(
        password.encode("utf-8"),
        hashed.encode("utf-8"),
    )

# CORRECT: Use secrets module for tokens
def generate_token(nbytes: int = 32) -> str:
    """Generate a cryptographically secure token."""
    return secrets.token_urlsafe(nbytes)

def generate_api_key() -> str:
    """Generate a secure API key."""
    return f"sk-{secrets.token_hex(24)}"

# CORRECT: SHA-256 or SHA-3 for integrity checks (non-password hashing)
def compute_file_hash(filepath: Path) -> str:
    """Compute SHA-256 hash of a file for integrity verification."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()
```

## YAML Unsafe Load Prevention

```python
import yaml

# WRONG: yaml.load without Loader (can execute arbitrary Python)
def load_config_unsafe(path: str) -> dict:
    with open(path) as f:
        return yaml.load(f)  # Dangerous: allows arbitrary code execution

# CORRECT: Always use safe_load
def load_config(path: Path) -> dict:
    """Load YAML configuration safely."""
    with open(path) as f:
        return yaml.safe_load(f)

# CORRECT: If you need custom types, use SafeLoader explicitly
def load_with_custom_tags(path: Path) -> dict:
    """Load YAML with a custom SafeLoader."""
    loader = yaml.SafeLoader
    # Add custom constructors to SafeLoader, not the base Loader
    with open(path) as f:
        return yaml.load(f, Loader=loader)
```

## Bandit Security Scanning

Bandit is a static analysis tool that finds common security issues in Python code.

```bash
# Install
pip install bandit

# Scan a directory
bandit -r src/ -f json -o bandit-report.json

# Scan with specific severity
bandit -r src/ -ll  # Only HIGH and above

# Scan excluding tests
bandit -r src/ --exclude tests/

# Common bandit issue codes:
# B101 - assert used (not reliable in production)
# B105 - hardcoded password
# B108 - hardcoded tmp directory
# B301 - pickle usage
# B307 - eval usage
# B320 - lxml without defusing
# B602 - subprocess with shell=True
# B608 - SQL injection (string formatting in queries)
```

### pyproject.toml bandit config

```toml
[tool.bandit]
exclude_dirs = ["tests", "scripts"]
skips = ["B101"]  # Allow assert in non-production code
```

## Input Validation Patterns

```python
from dataclasses import dataclass
import re

# Pattern: validate at system boundary, trust internally
@dataclass(frozen=True)
class Email:
    """Validated email address value object."""
    value: str

    def __post_init__(self) -> None:
        # Basic email validation pattern
        # Pattern: local-part@domain with at least one dot in domain
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, self.value):
            raise ValueError(f"Invalid email address: {self.value}")
        if len(self.value) > 254:
            raise ValueError("Email address too long (max 254 characters)")

@dataclass(frozen=True)
class Port:
    """Validated network port number."""
    value: int

    def __post_init__(self) -> None:
        if not 1 <= self.value <= 65535:
            raise ValueError(
                f"Port must be between 1 and 65535, got {self.value}"
            )

# Sanitize HTML to prevent XSS
# Install: pip install bleach
import bleach

def sanitize_html(user_input: str) -> str:
    """Remove dangerous HTML tags and attributes."""
    return bleach.clean(
        user_input,
        tags=["b", "i", "em", "strong", "a", "p", "br"],
        attributes={"a": ["href", "title"]},
        strip=True,
    )

# Validate and constrain string length
def validate_username(username: str) -> str:
    """Validate username format and length."""
    username = username.strip()
    if not username:
        raise ValueError("Username cannot be empty")
    if len(username) < 3 or len(username) > 32:
        raise ValueError("Username must be 3-32 characters")
    if not re.match(r"^[a-zA-Z0-9_-]+$", username):
        raise ValueError(
            "Username may only contain letters, digits, hyphens, and underscores"
        )
    return username
```
