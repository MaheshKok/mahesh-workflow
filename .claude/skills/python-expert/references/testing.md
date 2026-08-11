# Python Testing

## TDD Workflow (Red-Green-Refactor)

1. **RED**: Write a test that describes the desired behavior. Run it. It must fail.
2. **GREEN**: Write the minimal implementation to make the test pass.
3. **REFACTOR**: Clean up the code while keeping all tests green.
4. Repeat for each new behavior.

```python
# Step 1 (RED): Write the test first
def test_calculate_discount_applies_ten_percent_for_premium():
    customer = Customer(tier="premium")
    result = calculate_discount(customer, 100.0)
    assert result == 90.0

# Step 2 (GREEN): Minimal implementation
def calculate_discount(customer: Customer, price: float) -> float:
    if customer.tier == "premium":
        return price * 0.9
    return price

# Step 3 (REFACTOR): Improve without changing behavior
DISCOUNT_RATES: dict[str, float] = {
    "premium": 0.10,
    "gold": 0.15,
    "standard": 0.0,
}

def calculate_discount(customer: Customer, price: float) -> float:
    rate = DISCOUNT_RATES.get(customer.tier, 0.0)
    return price * (1 - rate)
```

## pytest Fundamentals

### Test structure

```python
# tests/test_calculator.py

def test_add_positive_numbers():
    """Adding two positive numbers returns their sum."""
    result = add(2, 3)
    assert result == 5

def test_add_negative_numbers():
    """Adding two negative numbers returns a negative sum."""
    result = add(-2, -3)
    assert result == -5
```

### Assertions

```python
# Equality
assert result == expected

# Approximate equality (floating point)
assert result == pytest.approx(3.14, abs=1e-2)

# Boolean
assert is_valid
assert not is_expired

# Membership
assert "key" in result_dict
assert item not in excluded_list

# Type
assert isinstance(result, MyClass)

# None
assert result is None
assert result is not None

# String patterns
assert "error" in message.lower()
```

## Fixtures

### Basic fixture

```python
import pytest

@pytest.fixture
def sample_user() -> User:
    """Create a sample user for testing."""
    return User(name="Alice", email="alice@example.com", age=30)

def test_user_display_name(sample_user: User):
    assert sample_user.display_name == "Alice"
```

### Setup and teardown with yield

```python
@pytest.fixture
def temp_database() -> Generator[Database, None, None]:
    """Create a temporary database and clean up after test."""
    db = Database.create_temporary()
    db.initialize_schema()
    yield db
    db.drop_all_tables()
    db.close()
```

### Fixture scopes

```python
# function (default): Created for each test function
@pytest.fixture(scope="function")
def fresh_connection() -> Connection:
    return Connection()

# class: Created once per test class
@pytest.fixture(scope="class")
def shared_client() -> ApiClient:
    return ApiClient()

# module: Created once per test module (.py file)
@pytest.fixture(scope="module")
def database() -> Database:
    return Database.connect()

# session: Created once per entire test session
@pytest.fixture(scope="session")
def expensive_resource() -> Resource:
    return Resource.initialize()
```

### Parametrized fixtures

```python
@pytest.fixture(params=["sqlite", "postgres", "mysql"])
def database_backend(request: pytest.FixtureRequest) -> str:
    """Run tests against multiple database backends."""
    return request.param

def test_insert_record(database_backend: str):
    db = create_database(backend=database_backend)
    db.insert({"key": "value"})
    assert db.count() == 1
```

### Autouse fixtures

```python
@pytest.fixture(autouse=True)
def reset_environment():
    """Automatically reset environment before each test."""
    os.environ.clear()
    yield
    os.environ.clear()
```

### conftest.py

Shared fixtures go in `conftest.py`. pytest discovers them automatically.

```python
# tests/conftest.py

@pytest.fixture
def api_client() -> ApiClient:
    """Shared API client fixture available to all tests."""
    return ApiClient(base_url="http://localhost:8000")

@pytest.fixture
def auth_token() -> str:
    """Shared auth token for authenticated tests."""
    return "test-token-12345"
```

## Parametrization

### Basic parametrize

```python
@pytest.mark.parametrize("input_val,expected", [
    (1, 1),
    (2, 4),
    (3, 9),
    (0, 0),
    (-2, 4),
])
def test_square(input_val: int, expected: int):
    assert square(input_val) == expected
```

### Parametrize with IDs

```python
@pytest.mark.parametrize("email,is_valid", [
    ("user@example.com", True),
    ("user@.com", False),
    ("", False),
    ("user@sub.domain.com", True),
], ids=["valid_email", "invalid_domain", "empty_string", "subdomain"])
def test_validate_email(email: str, is_valid: bool):
    assert validate_email(email) == is_valid
```

### Multiple parametrize (cartesian product)

```python
@pytest.mark.parametrize("x", [1, 2, 3])
@pytest.mark.parametrize("y", [10, 20])
def test_multiply(x: int, y: int):
    assert multiply(x, y) == x * y
# Runs 6 tests: (1,10), (1,20), (2,10), (2,20), (3,10), (3,20)
```

## Mocking

### Mock a function

```python
from unittest.mock import patch, MagicMock

def test_send_notification(mocker):
    """Test that notification calls the email service."""
    mock_send = mocker.patch("myapp.notifications.send_email")

    notify_user(user_id=42, message="Hello")

    mock_send.assert_called_once_with(
        to="user42@example.com",
        subject="Notification",
        body="Hello",
    )
```

### Mock return values

```python
def test_fetch_user_returns_cached(mocker):
    mock_cache = mocker.patch("myapp.cache.get")
    mock_cache.return_value = {"name": "Alice", "id": 1}

    result = fetch_user(user_id=1)

    assert result["name"] == "Alice"
    mock_cache.assert_called_once_with("user:1")
```

### Mock exceptions

```python
def test_handles_network_error(mocker):
    mock_request = mocker.patch("myapp.client.request")
    mock_request.side_effect = ConnectionError("Network unreachable")

    with pytest.raises(ServiceUnavailableError):
        fetch_data("https://api.example.com/data")
```

### Mock context managers

```python
def test_read_config(mocker):
    mock_open = mocker.patch(
        "builtins.open",
        mocker.mock_open(read_data='{"key": "value"}'),
    )

    config = load_config("config.json")

    assert config["key"] == "value"
    mock_open.assert_called_once_with("config.json")
```

### Autospec (validates call signatures)

```python
def test_with_autospec(mocker):
    """Autospec ensures mock matches the real function signature."""
    mock_process = mocker.patch(
        "myapp.processor.process_data",
        autospec=True,
    )
    mock_process.return_value = ProcessResult(status="ok")

    result = run_pipeline(data=[1, 2, 3])

    assert result.status == "ok"
```

### Mock properties

```python
def test_user_is_active(mocker):
    mock_user = MagicMock()
    type(mock_user).is_active = mocker.PropertyMock(return_value=True)

    assert mock_user.is_active is True
```

## Async Testing with pytest-asyncio

```python
import pytest

@pytest.mark.asyncio
async def test_fetch_data():
    """Test async data fetching."""
    client = AsyncClient()
    result = await client.fetch("/api/data")
    assert result.status == 200
    assert "items" in result.json()

@pytest.fixture
async def async_db() -> AsyncGenerator[AsyncDatabase, None]:
    """Async fixture with cleanup."""
    db = await AsyncDatabase.connect("test_db")
    yield db
    await db.disconnect()

@pytest.mark.asyncio
async def test_insert_record(async_db: AsyncDatabase):
    await async_db.insert({"key": "value"})
    count = await async_db.count()
    assert count == 1
```

## Testing Exceptions

```python
def test_divide_by_zero_raises():
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)

def test_invalid_age_raises_with_message():
    with pytest.raises(ValueError, match=r"Age must be.*positive"):
        create_user(name="Alice", age=-5)

def test_exception_attributes():
    with pytest.raises(ValidationError) as exc_info:
        validate_input({"name": ""})
    assert exc_info.value.field == "name"
    assert "required" in str(exc_info.value)
```

## Test Organization

### Directory structure

```
project/
    src/
        myapp/
            __init__.py
            models.py
            services.py
            utils.py
    tests/
        __init__.py
        conftest.py          # Shared fixtures
        unit/
            __init__.py
            test_models.py
            test_utils.py
        integration/
            __init__.py
            conftest.py      # Integration-specific fixtures
            test_services.py
        e2e/
            __init__.py
            test_workflows.py
```

### Test classes for grouping related tests

```python
class TestUserCreation:
    """Tests for user creation logic."""

    def test_create_user_with_valid_data(self):
        user = create_user(name="Alice", email="alice@example.com")
        assert user.name == "Alice"

    def test_create_user_rejects_empty_name(self):
        with pytest.raises(ValueError, match="name.*required"):
            create_user(name="", email="alice@example.com")

    def test_create_user_rejects_invalid_email(self):
        with pytest.raises(ValueError, match="invalid email"):
            create_user(name="Alice", email="not-an-email")
```

## Coverage Configuration and Commands

### pyproject.toml coverage config

```toml
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
```

### Commands

```bash
# Run tests with coverage
bun pytest --cov=src --cov-report=term-missing

# Generate HTML report
bun pytest --cov=src --cov-report=html

# Check coverage threshold
bun pytest --cov=src --cov-report=term --cov-fail-under=80
```

## Best Practices

### DO

- Name tests descriptively: `test_<function>_<scenario>_<expected_result>`
- One assertion per test (or one logical assertion group)
- Use fixtures for shared setup; avoid setup/teardown methods
- Test behavior, not implementation details
- Use parametrize for data-driven tests
- Keep tests fast (mock I/O, databases, network calls)
- Use `autospec=True` with mocks to catch API mismatches
- Put shared fixtures in `conftest.py`
- Write tests before code (TDD)

### DON'T

- Don't test private methods directly (test through public API)
- Don't use `sleep()` in tests (use mocks or async utilities)
- Don't share mutable state between tests
- Don't test framework/library code
- Don't write tests that depend on execution order
- Don't use `assert True` or `assert False` as placeholders
- Don't mock everything; prefer integration tests where appropriate
- Don't ignore flaky tests; fix or remove them
