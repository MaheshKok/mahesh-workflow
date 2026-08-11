# Python Patterns & Idioms

## EAFP (Easier to Ask Forgiveness than Permission)

Prefer try/except over pre-checking conditions. This is more Pythonic and often faster when the common case succeeds.

```python
# WRONG: LBYL (Look Before You Leap)
if "key" in dictionary:
    value = dictionary["key"]
else:
    value = default_value

# CORRECT: EAFP
try:
    value = dictionary["key"]
except KeyError:
    value = default_value

# BEST: Use dict.get() when it fits
value = dictionary.get("key", default_value)
```

```python
# WRONG: Check before file access
import os
if os.path.exists(filepath):
    with open(filepath) as f:
        data = f.read()

# CORRECT: Try and handle failure
try:
    with open(filepath) as f:
        data = f.read()
except FileNotFoundError:
    data = ""
```

## List Comprehensions vs C-Style Loops

Use comprehensions for simple transforms. Use explicit loops when logic is complex or has side effects.

```python
# WRONG: C-style accumulation
squares = []
for x in range(10):
    squares.append(x ** 2)

# CORRECT: List comprehension
squares = [x ** 2 for x in range(10)]

# Filtering
evens = [x for x in range(20) if x % 2 == 0]

# Nested comprehension (keep it readable)
flat = [cell for row in matrix for cell in row]

# Dict comprehension
word_lengths = {word: len(word) for word in words}

# Set comprehension
unique_lengths = {len(word) for word in words}

# WRONG: Overly complex comprehension (use a loop instead)
result = [transform(x) for x in data if validate(x) and x.status == "active" and x.score > threshold]

# CORRECT: Break into a loop when complexity grows
result = []
for x in data:
    if not validate(x):
        continue
    if x.status != "active" or x.score <= threshold:
        continue
    result.append(transform(x))
```

## Generator Expressions and Generator Functions

Use generators for large or infinite sequences to avoid loading everything into memory.

```python
# Generator expression (lazy evaluation)
total = sum(x ** 2 for x in range(1_000_000))

# Generator function
def fibonacci() -> Generator[int, None, None]:
    """Yield Fibonacci numbers indefinitely."""
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

# Take first N items from a generator
from itertools import islice
first_ten = list(islice(fibonacci(), 10))

# Generator for file processing (memory-efficient)
def read_large_file(filepath: Path) -> Generator[str, None, None]:
    """Yield lines from a large file without loading it entirely."""
    with open(filepath) as f:
        for line in f:
            yield line.strip()

# Chaining generators
def parse_lines(lines: Iterable[str]) -> Generator[dict, None, None]:
    """Parse each line as JSON."""
    for line in lines:
        if line:
            yield json.loads(line)

records = parse_lines(read_large_file(Path("data.jsonl")))
```

## Context Managers

### Using @contextmanager decorator

```python
from contextlib import contextmanager
from typing import Generator

@contextmanager
def temporary_directory() -> Generator[Path, None, None]:
    """Create a temporary directory and clean it up on exit."""
    tmp_dir = Path(tempfile.mkdtemp())
    try:
        yield tmp_dir
    finally:
        shutil.rmtree(tmp_dir)

# Usage
with temporary_directory() as tmp:
    (tmp / "data.txt").write_text("hello")
```

### Class-based context manager

```python
class DatabaseConnection:
    """Manage a database connection lifecycle."""

    def __init__(self, connection_string: str) -> None:
        self._connection_string = connection_string
        self._connection: Connection | None = None

    def __enter__(self) -> Connection:
        self._connection = create_connection(self._connection_string)
        return self._connection

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        if self._connection is not None:
            if exc_type is not None:
                self._connection.rollback()
            else:
                self._connection.commit()
            self._connection.close()
        return False  # Do not suppress exceptions
```

## Decorators

### Function decorator

```python
import functools
import logging
import time

logger = logging.getLogger(__name__)

def log_execution_time(func: Callable[..., T]) -> Callable[..., T]:
    """Log the execution time of the decorated function."""
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.info(f"{func.__name__} executed in {elapsed:.4f}s")
        return result
    return wrapper

@log_execution_time
def process_data(items: list[str]) -> list[str]:
    return [item.upper() for item in items]
```

### Parameterized decorator

```python
def retry(max_attempts: int = 3, delay: float = 1.0) -> Callable:
    """Retry a function on exception with configurable attempts and delay."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(
                        f"{func.__name__} attempt {attempt}/{max_attempts} failed: {e}"
                    )
                    if attempt < max_attempts:
                        time.sleep(delay)
            raise last_exception  # type: ignore[misc]
        return wrapper
    return decorator

@retry(max_attempts=5, delay=2.0)
def fetch_data(url: str) -> dict:
    ...
```

### Class-based decorator

```python
class CacheResult:
    """Cache function results with a TTL."""

    def __init__(self, ttl_seconds: int = 300) -> None:
        self._ttl = ttl_seconds
        self._cache: dict[str, tuple[float, Any]] = {}

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            key = f"{args}:{kwargs}"
            now = time.time()
            if key in self._cache:
                cached_time, cached_value = self._cache[key]
                if now - cached_time < self._ttl:
                    return cached_value
            result = func(*args, **kwargs)
            self._cache[key] = (now, result)
            return result
        return wrapper

@CacheResult(ttl_seconds=60)
def get_user(user_id: int) -> dict:
    ...
```

## Data Classes

### Basic dataclass

```python
from dataclasses import dataclass, field

@dataclass
class User:
    """Represents a user account."""
    name: str
    email: str
    age: int
    tags: list[str] = field(default_factory=list)
```

### Dataclass with validation via __post_init__

```python
@dataclass
class Temperature:
    """Temperature value with validation."""
    celsius: float

    def __post_init__(self) -> None:
        if self.celsius < -273.15:
            raise ValueError(
                f"Temperature {self.celsius}C is below absolute zero"
            )

    @property
    def fahrenheit(self) -> float:
        return self.celsius * 9 / 5 + 32
```

### Frozen (immutable) dataclass

```python
@dataclass(frozen=True)
class Point:
    """An immutable 2D point."""
    x: float
    y: float

    def distance_to(self, other: "Point") -> float:
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5

p1 = Point(1.0, 2.0)
p2 = Point(3.0, 4.0)
# p1.x = 5.0  # Raises FrozenInstanceError
```

## Named Tuples

```python
from typing import NamedTuple

class Coordinate(NamedTuple):
    """A geographic coordinate."""
    latitude: float
    longitude: float
    altitude: float = 0.0

point = Coordinate(40.7128, -74.0060)
lat, lon, alt = point  # Unpacking works
print(point.latitude)  # Named access works
```

## Package Organization

### Standard layout

```
my_package/
    pyproject.toml
    src/
        my_package/
            __init__.py
            core/
                __init__.py
                engine.py
                models.py
            utils/
                __init__.py
                helpers.py
                validators.py
            cli.py
    tests/
        __init__.py
        conftest.py
        core/
            __init__.py
            test_engine.py
            test_models.py
        utils/
            __init__.py
            test_helpers.py
            test_validators.py
```

### __init__.py exports

```python
# src/my_package/__init__.py
"""My Package: A brief description of what it does."""

from my_package.core.engine import Engine
from my_package.core.models import Config, Result

__all__ = ["Config", "Engine", "Result"]
```

### Import conventions

```python
# CORRECT: Absolute imports
from my_package.core.engine import Engine
from my_package.utils.helpers import format_output

# CORRECT: Relative imports within the same package
from .models import Config
from ..utils.helpers import format_output

# WRONG: Wildcard imports
from my_package.core import *
```

## Anti-Patterns to Avoid

### Mutable default arguments

```python
# WRONG: Mutable default is shared across calls
def add_item(item: str, items: list[str] = []) -> list[str]:
    items.append(item)
    return items

# CORRECT: Use None sentinel
def add_item(item: str, items: list[str] | None = None) -> list[str]:
    if items is None:
        items = []
    items.append(item)
    return items
```

### type() vs isinstance()

```python
# WRONG: Breaks with inheritance
if type(obj) == MyClass:
    ...

# CORRECT: Works with inheritance
if isinstance(obj, MyClass):
    ...

# CORRECT: Check multiple types
if isinstance(obj, (int, float)):
    ...
```

### Bare except

```python
# WRONG: Catches SystemExit, KeyboardInterrupt, etc.
try:
    risky_operation()
except:
    pass

# CORRECT: Catch specific exceptions
try:
    risky_operation()
except (ValueError, IOError) as e:
    logger.error(f"Operation failed: {e}")
    raise OperationError("Failed to complete operation") from e
```

### Identity checks for None

```python
# WRONG: Uses equality
if x == None:
    ...

# CORRECT: Uses identity
if x is None:
    ...

if x is not None:
    ...
```

### Wildcard imports

```python
# WRONG: Pollutes namespace, hides origins
from os.path import *

# CORRECT: Explicit imports
from os.path import join, exists, dirname
```
