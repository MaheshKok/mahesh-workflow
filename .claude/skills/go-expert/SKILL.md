---
name: go-expert
description: "Comprehensive Go development expert. Use when writing, reviewing, or refactoring .go files. Covers idiomatic patterns, concurrency, testing, and performance."
---

# Go Expert

Consolidated Go development skill with progressive disclosure. Read reference files only when the specific topic is relevant.

## When to Activate

- Writing or editing any .go file
- Reviewing Go code changes
- Designing Go packages and interfaces
- Debugging Go concurrency issues

## Core Rules (Always Apply)

1. Simplicity over cleverness — code should be obvious and boring.
2. Handle every error — never use blank identifier for errors unless documented why.
3. Wrap errors with context: fmt.Errorf("operation %s: %w", arg, err).
4. Accept interfaces, return structs.
5. Make the zero value useful — design types so they work without initialization.
6. Define interfaces where they're used (consumer), not where implemented (provider).
7. Keep interfaces small — prefer single-method interfaces, compose as needed.
8. Use context.Context as first parameter for cancellation and timeouts.
9. Never use panic for control flow — return errors instead.
10. Avoid package-level mutable state — use dependency injection.
11. Preallocate slices when size is known: make([]T, 0, len(input)).
12. Use strings.Builder or strings.Join instead of += in loops.
13. Use gofmt/goimports — formatting is non-negotiable.
14. Use table-driven tests as the default test pattern.
15. Context should not be stored in structs — pass as first function parameter.

## Reference Guide

| Topic | File | Read when... |
|-------|------|-------------|
| Patterns & Idioms | references/patterns.md | Error handling, interfaces, package org, struct design, functional options |
| Concurrency | references/concurrency.md | Goroutines, channels, sync, context, errgroup, worker pools |
| Testing | references/testing.md | Table-driven tests, subtests, benchmarks, fuzzing, mocking, HTTP handler tests |
| Performance | references/performance.md | Memory optimization, sync.Pool, string building, linter config, tooling |

## Constraints

- MUST read relevant reference file before writing code in that topic area
- MUST run go-reviewer agent after completing Go code changes
- MUST follow TDD: write test first, then implement
- MUST achieve 80%+ test coverage
