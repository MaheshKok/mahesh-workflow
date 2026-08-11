# Performance Review Checklist

Quantify cost where possible. Do not report speculative slowdowns as facts.

## Data access

- Query inside a row loop: batch, join, or use a data loader.
- Unbounded collection or list endpoint: paginate and enforce a limit.
- Missing index on high-volume filter, join, or ordering paths.
- Long transactions, per-call connections, or pool exhaustion risks.

## Compute and memory

- Nested scans over large inputs where a map or set removes the inner scan.
- Large per-request allocations, full buffering of streamable data, or unbounded caches.
- Listeners, timers, tasks, goroutines, or promises without a bounded lifetime.

## Concurrency and I/O

- Blocking I/O on an async or request path.
- Independent awaits serialized without a dependency.
- Network calls without timeouts or unbounded concurrent fan-out.

## Frontend

- Unstable props or broad context causing expensive re-renders.
- Heavy dependencies for small functionality, unsplit heavy routes, oversized assets, or unvirtualized long lists.

Do not recommend caching without a measured repeated cost and a clear invalidation rule.
