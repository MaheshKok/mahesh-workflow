# Language Review Lenses

Apply only the lens matching the changed files.

## Python

- Mutable default arguments, broad exception swallowing, manual resource cleanup.
- Blocking calls inside `async def`; missing public type contracts.
- Ad-hoc dictionaries where an existing typed record is clearer.

## Go

- Dropped or poorly wrapped errors; goroutines without exits or context cancellation.
- Shared mutable state without ownership or synchronization; `defer` inside large loops.
- Nil map writes, unsafe nil dereferences, or panic in library code.

## TypeScript and JavaScript

- `any`, unsafe casts, or non-null assertions hiding a boundary problem.
- Floating promises, stale closures, non-exhaustive unions, or shared-object mutation.
- Serialized independent awaits and coercive equality where strict equality is intended.

## SQL and databases

- Interpolated queries, N+1 access, missing constraints or indexes.
- Migration locking, irreversibility, unsafe backfills, or silent row-order assumptions.
- Incorrect transaction scope, isolation, or lock ordering.

## React and UI

- Incomplete hook dependencies, missing effect cleanup, unstable list keys.
- Premature memoization; verify a real render cost first.
- Missing labels, alt text, focus behavior, or semantic elements.
