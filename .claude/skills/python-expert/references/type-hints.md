# Python Type Hints

## Basic Type Annotations

```python
# Variable annotations
name: str = "Alice"
age: int = 30
score: float = 95.5
active: bool = True

# Function signatures (always type-hint parameters and return)
def greet(name: str, excited: bool = False) -> str:
    """Return a greeting message."""
    suffix = "!" if excited else "."
    return f"Hello, {name}{suffix}"

# None return type
def log_message(message: str) -> None:
    """Log a message to the console."""
    logger.info(message)
```

## Modern Type Hints (Python 3.9+ Built-in Generics)

Prefer built-in generics over typing module equivalents. Since we target Python 3.12, always use these.

```python
# WRONG: Old-style typing imports (pre-3.9)
from typing import List, Dict, Tuple, Set, FrozenSet

def process(items: List[str]) -> Dict[str, int]:
    ...

# CORRECT: Built-in generics (3.9+)
def process(items: list[str]) -> dict[str, int]:
    ...

# Common built-in generic types
names: list[str] = ["Alice", "Bob"]
scores: dict[str, float] = {"Alice": 95.5}
coordinates: tuple[float, float] = (1.0, 2.0)
unique_ids: set[int] = {1, 2, 3}
frozen_tags: frozenset[str] = frozenset({"a", "b"})

# Variable-length tuples
values: tuple[int, ...] = (1, 2, 3, 4, 5)

# Nested generics
matrix: list[list[float]] = [[1.0, 2.0], [3.0, 4.0]]
registry: dict[str, list[int]] = {"evens": [2, 4], "odds": [1, 3]}
```

## Union Types (Python 3.10+)

```python
# WRONG: Old-style Union
from typing import Union, Optional
def parse(value: Union[str, int]) -> Optional[float]:
    ...

# CORRECT: PEP 604 union syntax (3.10+)
def parse(value: str | int) -> float | None:
    ...

# Multiple union members
def normalize(value: str | int | float | None) -> str:
    if value is None:
        return ""
    return str(value)
```

## Type Aliases

```python
# Simple type alias (3.12+ syntax with `type` statement)
type UserId = int
type Headers = dict[str, str]
type Matrix = list[list[float]]
type Callback = Callable[[str, int], bool]

# Using the alias
def get_user(user_id: UserId) -> dict[str, str]:
    ...

def send_request(url: str, headers: Headers) -> bytes:
    ...

# Pre-3.12 alias syntax (still valid)
JsonValue = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
```

## TypeVar

```python
from typing import TypeVar

T = TypeVar("T")

def first(items: list[T]) -> T:
    """Return the first item from a list."""
    if not items:
        raise ValueError("Cannot get first item from empty list")
    return items[0]

# Bounded TypeVar
from typing import TypeVar

Numeric = TypeVar("Numeric", int, float)

def add(a: Numeric, b: Numeric) -> Numeric:
    """Add two numeric values of the same type."""
    return a + b

# Upper-bound TypeVar
from typing import TypeVar

Comparable = TypeVar("Comparable", bound="SupportsLessThan")

def min_value(a: Comparable, b: Comparable) -> Comparable:
    return a if a < b else b
```

## Protocol-Based Duck Typing

Use Protocol when you care about structure (what methods/attributes an object has), not its class hierarchy.

```python
from typing import Protocol, runtime_checkable

class Readable(Protocol):
    """Any object that has a read() method."""

    def read(self, size: int = -1) -> str: ...

class Writable(Protocol):
    """Any object that has a write() method."""

    def write(self, data: str) -> int: ...

# Combining protocols
class ReadWritable(Readable, Writable, Protocol):
    """Any object that is both readable and writable."""
    ...

# Usage: any object with a read() method satisfies Readable
def load_config(source: Readable) -> dict[str, str]:
    """Load config from any readable source."""
    content = source.read()
    return parse_config(content)

# Works with files, StringIO, custom objects, etc.
load_config(open("config.txt"))
load_config(io.StringIO("key=value"))
```

### Runtime-checkable Protocol

```python
@runtime_checkable
class Closeable(Protocol):
    """Any object with a close() method."""

    def close(self) -> None: ...

def cleanup(resource: object) -> None:
    """Close a resource if it supports closing."""
    if isinstance(resource, Closeable):
        resource.close()
```

### Protocol with properties

```python
class Sized(Protocol):
    """Any object with a size property."""

    @property
    def size(self) -> int: ...

class HasName(Protocol):
    """Any object with a name attribute."""

    name: str

class NamedSized(HasName, Sized, Protocol):
    """Combines name and size."""
    ...
```

## Callable Types

```python
from typing import Callable
from collections.abc import Callable as AbcCallable

# Function that takes (int, str) and returns bool
type Predicate = Callable[[int, str], bool]

# Function that takes no args and returns None
type VoidCallback = Callable[[], None]

# Function with variable arguments
type AnyFunc = Callable[..., Any]

# Using Callable in signatures
def apply_transform(
    data: list[str],
    transform: Callable[[str], str],
) -> list[str]:
    """Apply a transform function to each item."""
    return [transform(item) for item in data]

# Higher-order function returning a function
def make_multiplier(factor: float) -> Callable[[float], float]:
    """Create a multiplier function."""
    def multiplier(value: float) -> float:
        return value * factor
    return multiplier
```

## Other Useful typing Module Types

```python
from typing import (
    Any,
    ClassVar,
    Final,
    Literal,
    Never,
    Self,
    TypeGuard,
    overload,
)

# Literal: restrict to specific values
def set_mode(mode: Literal["read", "write", "append"]) -> None:
    ...

# Final: constant that cannot be reassigned
MAX_RETRIES: Final[int] = 3

# ClassVar: class-level attribute (not per-instance)
from dataclasses import dataclass

@dataclass
class Config:
    max_retries: ClassVar[int] = 3
    timeout: float = 30.0

# Self: return type referring to the current class (3.11+)
class Builder:
    def set_name(self, name: str) -> Self:
        self._name = name
        return self

# TypeGuard: narrowing type in conditionals
def is_string_list(val: list[object]) -> TypeGuard[list[str]]:
    return all(isinstance(item, str) for item in val)

# Never: function that never returns
def fail(message: str) -> Never:
    raise RuntimeError(message)

# overload: multiple signatures for a single function
@overload
def process(value: str) -> str: ...
@overload
def process(value: int) -> int: ...
def process(value: str | int) -> str | int:
    if isinstance(value, str):
        return value.upper()
    return value * 2
```

## Annotating Generators and Iterators

```python
from collections.abc import Generator, Iterator, Iterable

# Simple iterator (yields only)
def count_up(limit: int) -> Iterator[int]:
    for i in range(limit):
        yield i

# Full generator (yield type, send type, return type)
def accumulator() -> Generator[float, float, str]:
    """Yield running total, accept values via send(), return summary."""
    total = 0.0
    count = 0
    while True:
        value = yield total
        if value is None:
            break
        total += value
        count += 1
    return f"Processed {count} values, total={total}"

# Iterable parameter (accepts any iterable)
def sum_all(values: Iterable[float]) -> float:
    return sum(values)
```

## Best Practices

1. Always annotate public function signatures. Internal helper variables can often be inferred.
2. Use `X | None` instead of `Optional[X]` (3.10+).
3. Use built-in generics (`list`, `dict`, `tuple`, `set`) instead of `typing.List`, etc.
4. Use `Protocol` for structural typing (duck typing). Use `ABC` for nominal typing.
5. Avoid `Any` unless interfacing with untyped code. Be as specific as possible.
6. Use `TypeVar` when a function preserves the input type in its output.
7. Run `mypy --strict` to catch type errors during development.
8. Use `# type: ignore[error-code]` sparingly and only with a specific error code.
