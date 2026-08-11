# Language-Specific Review Lenses

Per-language signals for the `code-review` skill's five axes. Apply the lens matching the changed files. Absorbed from the Python / Go / database / general reviewer domains.

## Python
- Mutable default arguments (`def f(x=[])`) — shared across calls; use a `None` sentinel.
- Bare `except:` or broad `except Exception` that swallows errors; catch narrow, re-raise or log with context.
- Resource cleanup via context managers (`with`), not manual close — files, sockets, locks.
- Type hints on public functions; explicit `Optional` rather than implicit `None`.
- Comprehension over a manual build loop; a generator for large streams.
- f-strings over `%` / `.format`; but keep `%`-style lazy args in `logging` calls on hot paths.
- `dataclass` / `NamedTuple` over ad-hoc dicts for structured records.
- async: no blocking call (`requests`, `time.sleep`, sync DB driver) inside an `async def`.
- PEP 8 / the project formatter; consistent import ordering.

## Go
- Every error checked and wrapped with context (`fmt.Errorf("...: %w", err)`); no discarded `_ = err`.
- Goroutine leaks: every goroutine has a clear exit; `context.Context` propagated and honored.
- `defer` for cleanup (Close / Unlock); watch `defer` inside a loop.
- Data races: shared mutable state guarded by a mutex or owned by one goroutine (assume `-race`).
- Channels: the sender closes; no send on a closed channel; buffered vs unbuffered chosen deliberately.
- Small interfaces defined at the consumer; accept interfaces, return structs.
- nil: writing a nil map panics; a nil slice is fine to `append`; guard nil-pointer derefs on error paths.
- No naked `panic` in library code — return errors.

## TypeScript / JavaScript
- `any` / `unknown` / casts that paper over a real type — make the boundary explicit instead.
- `strictNullChecks`; handle `null` / `undefined` rather than `!` non-null assertions.
- Floating promises: every promise awaited or explicitly handled; no unhandled rejection.
- `Promise.all` for independent awaits; don't serialize needlessly.
- Exhaustive `switch` on unions (a `never` default catches a missed case).
- Immutability: no mutation of shared objects / props; spread or structured copy.
- Equality: `===` not `==`; guard `NaN`.

## SQL / Database
- Parameterized queries only (see `security-checklist.md`).
- N+1 and missing indexes (see `performance-checklist.md`).
- Migrations reversible (a down migration) and non-locking on large tables (concurrent index build).
- Transactions atomic and correctly scoped; isolation level appropriate; consistent lock ordering to avoid deadlock.
- No logic silently depending on row order without an `ORDER BY`.

## React / UI
- Hook dependency arrays complete; no stale closures; effects clean up (subscriptions, timers).
- Stable `key` props on lists (not the array index when the list can reorder).
- Memoization only where a measured re-render cost exists — not by default.
- Accessibility basics: labels on inputs, alt text, focus management, semantic elements.
