# Python Concurrency

## When to Use Which Approach

| Scenario | Approach | Why |
|----------|----------|-----|
| I/O-bound (HTTP, file, DB) | `asyncio` or `ThreadPoolExecutor` | Threads/coroutines release GIL during I/O waits |
| CPU-bound (math, parsing) | `ProcessPoolExecutor` | Separate processes bypass the GIL |
| Simple parallel I/O | `ThreadPoolExecutor` | Easiest API, no async rewrite needed |
| High-concurrency I/O (1000+ tasks) | `asyncio` | Lower overhead than threads, scales better |
| Mixed I/O and CPU | `asyncio` + `ProcessPoolExecutor` | Offload CPU work from async event loop |

## Threading for I/O-Bound Tasks

### ThreadPoolExecutor

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

logger = logging.getLogger(__name__)

def fetch_url(url: str) -> tuple[str, int]:
    """Fetch a URL and return (url, status_code)."""
    import urllib.request
    with urllib.request.urlopen(url, timeout=10) as response:
        return url, response.status

def fetch_all_urls(urls: list[str], max_workers: int = 10) -> list[tuple[str, int]]:
    """Fetch multiple URLs concurrently using threads."""
    results: list[tuple[str, int]] = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {
            executor.submit(fetch_url, url): url
            for url in urls
        }

        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to fetch {url}: {e}")

    return results
```

### Using executor.map for ordered results

```python
def process_files(filepaths: list[Path]) -> list[str]:
    """Process files concurrently, preserving order."""
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(process_single_file, filepaths))
    return results
```

## Multiprocessing for CPU-Bound Tasks

### ProcessPoolExecutor

```python
from concurrent.futures import ProcessPoolExecutor
import math

def is_prime(n: int) -> bool:
    """Check if a number is prime (CPU-intensive for large numbers)."""
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    for i in range(5, int(math.isqrt(n)) + 1, 6):
        if n % i == 0 or n % (i + 2) == 0:
            return False
    return True

def find_primes_parallel(numbers: list[int], max_workers: int = 4) -> list[int]:
    """Find prime numbers using multiple CPU cores."""
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        results = executor.map(is_prime, numbers, chunksize=100)
    return [n for n, prime in zip(numbers, results) if prime]
```

### Important: pickling requirement

```python
# WRONG: Lambda and local functions cannot be pickled for multiprocessing
with ProcessPoolExecutor() as executor:
    results = executor.map(lambda x: x ** 2, range(100))  # Fails

# CORRECT: Use a module-level function
def square(x: int) -> int:
    return x ** 2

with ProcessPoolExecutor() as executor:
    results = list(executor.map(square, range(100)))
```

## Async/Await for Concurrent I/O

### Basic async pattern

```python
import asyncio
import aiohttp

async def fetch_json(session: aiohttp.ClientSession, url: str) -> dict:
    """Fetch JSON from a URL asynchronously."""
    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
        response.raise_for_status()
        return await response.json()

async def fetch_all(urls: list[str]) -> list[dict]:
    """Fetch multiple URLs concurrently with aiohttp."""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_json(session, url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    successful: list[dict] = []
    for url, result in zip(urls, results):
        if isinstance(result, Exception):
            logger.error(f"Failed to fetch {url}: {result}")
        else:
            successful.append(result)
    return successful

# Entry point
async def main() -> None:
    urls = [
        "https://api.example.com/users",
        "https://api.example.com/posts",
        "https://api.example.com/comments",
    ]
    data = await fetch_all(urls)
    for item in data:
        print(item)

if __name__ == "__main__":
    asyncio.run(main())
```

### Async context managers and iterators

```python
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator, AsyncIterator

@asynccontextmanager
async def managed_connection(url: str) -> AsyncGenerator[Connection, None]:
    """Async context manager for database connections."""
    conn = await connect(url)
    try:
        yield conn
    finally:
        await conn.close()

async def stream_records(query: str) -> AsyncIterator[dict]:
    """Async generator for streaming database records."""
    async with managed_connection("postgres://localhost/db") as conn:
        cursor = await conn.execute(query)
        async for row in cursor:
            yield dict(row)

# Consuming an async iterator
async def process_stream() -> None:
    async for record in stream_records("SELECT * FROM users"):
        await process_record(record)
```

### Semaphore for rate limiting

```python
async def fetch_with_limit(
    urls: list[str],
    max_concurrent: int = 5,
) -> list[dict]:
    """Fetch URLs with a concurrency limit."""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def limited_fetch(session: aiohttp.ClientSession, url: str) -> dict:
        async with semaphore:
            return await fetch_json(session, url)

    async with aiohttp.ClientSession() as session:
        tasks = [limited_fetch(session, url) for url in urls]
        return await asyncio.gather(*tasks)
```

### Timeouts

```python
async def fetch_with_timeout(url: str, timeout_seconds: float = 5.0) -> dict:
    """Fetch with an explicit timeout."""
    try:
        async with asyncio.timeout(timeout_seconds):
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    return await response.json()
    except TimeoutError:
        logger.error(f"Request to {url} timed out after {timeout_seconds}s")
        raise
```

### Running CPU-bound work from async code

```python
async def process_data_async(data: list[int]) -> list[int]:
    """Offload CPU-bound work to a process pool from async code."""
    loop = asyncio.get_running_loop()
    with ProcessPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, cpu_intensive_function, data)
    return result
```

## Thread Safety

### threading.Lock

```python
import threading

class ThreadSafeCounter:
    """A thread-safe counter using a lock."""

    def __init__(self) -> None:
        self._value: int = 0
        self._lock: threading.Lock = threading.Lock()

    def increment(self) -> int:
        """Atomically increment and return the new value."""
        with self._lock:
            self._value += 1
            return self._value

    @property
    def value(self) -> int:
        with self._lock:
            return self._value
```

### threading.RLock (reentrant lock)

```python
class ThreadSafeCache:
    """A cache that allows nested locking from the same thread."""

    def __init__(self) -> None:
        self._data: dict[str, object] = {}
        self._lock: threading.RLock = threading.RLock()

    def get_or_compute(self, key: str, compute: Callable[[], object]) -> object:
        with self._lock:
            if key not in self._data:
                self._data[key] = compute()
            return self._data[key]

    def clear(self) -> None:
        with self._lock:
            self._data.clear()
```

### Event for signaling between threads

```python
def producer_consumer_example() -> None:
    """Demonstrate thread communication with Event."""
    data_ready = threading.Event()
    shared_data: list[str] = []

    def producer() -> None:
        shared_data.append("result")
        data_ready.set()

    def consumer() -> None:
        data_ready.wait(timeout=5.0)
        if data_ready.is_set():
            logger.info(f"Received: {shared_data}")

    t1 = threading.Thread(target=producer)
    t2 = threading.Thread(target=consumer)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
```

## Common Pitfalls

1. **GIL misconception**: Threading does NOT speed up CPU-bound Python code. Use `ProcessPoolExecutor` for CPU work.
2. **Forgetting to join threads**: Always join threads or use a context manager (`ThreadPoolExecutor`) to avoid orphaned threads.
3. **Shared mutable state without locks**: Always protect shared data with `threading.Lock` or use thread-safe structures like `queue.Queue`.
4. **Blocking the event loop**: Never call blocking I/O (e.g., `requests.get()`) inside `async` functions. Use `aiohttp` or `run_in_executor`.
5. **Too many threads**: Threads consume memory. Use a pool with a bounded `max_workers`. A good default for I/O is `min(32, os.cpu_count() + 4)`.
6. **Pickling failures in multiprocessing**: Functions and data passed to `ProcessPoolExecutor` must be picklable. Avoid lambdas, closures, and unpicklable objects.
