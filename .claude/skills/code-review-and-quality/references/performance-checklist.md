# Performance Review Checklist

Depth for the performance axis of the `code-review` skill. Each failed check is a finding; quantify the cost when you can.

## Data access
- N+1 queries: a query inside a loop over rows → batch it (join, `IN (...)`, or a dataloader).
- `SELECT *` where only a few columns are used.
- Missing index on a column used in `WHERE` / `JOIN` / `ORDER BY` on a large table.
- Unbounded result sets: list endpoints paginated; queries carry a `LIMIT`.
- Transactions scoped tightly; no long-held locks; the connection pool isn't exhausted by per-call connections.

## Compute & memory
- Algorithmic complexity: nested loops over large N (O(n²)); a map/set lookup usually replaces the inner scan.
- Large allocations in hot paths or per-request; reuse buffers where it measurably matters.
- Streaming vs buffering: large files/responses streamed, not read fully into memory.
- Obvious leaks: unbounded caches/maps, listeners/timers never removed, goroutines/promises that never settle.

## Concurrency & IO
- Blocking / synchronous IO on an async or request-handling path → make it async.
- Independent awaits serialized that could run concurrently (`Promise.all`, errgroup).
- Missing timeouts on network calls; no bound on concurrent fan-out.

## Caching
- Repeated identical expensive work within one request is memoized.
- Cache invalidation is correct (staleness bounded). Don't add a cache before a profiler shows the need — a hand-rolled TTL cache is a bug farm.

## Frontend (if applicable)
- Unnecessary re-renders: unstable props, missing memoization on expensive children, context scoped too broadly.
- Large bundles: a heavy dependency pulled in for a small need; heavy routes not code-split.
- Images/assets sized and lazy-loaded; long lists virtualized.

Rule: don't assert a slowdown you haven't reasoned about. "This adds one query per row, ~N round-trips" beats "this looks slow."
