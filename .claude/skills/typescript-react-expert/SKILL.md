---
name: typescript-react-expert
description: "Comprehensive TypeScript, React, and Next.js development expert. Use when writing, reviewing, or refactoring .ts or .tsx files."
---

# TypeScript & React Expert

Consolidated TypeScript/React development skill with progressive disclosure. Read reference files only when the specific topic is relevant.

## When to Activate

- Writing or editing any .ts or .tsx file
- Building React components
- Working with Next.js (App Router, API routes)
- Optimizing frontend performance

## Core Rules (Always Apply)

1. Use proper TypeScript types — never use `any`. Define interfaces for all props and data.
2. Use immutable patterns — spread operator for updates, never mutate directly.
3. Use descriptive naming — verb-noun for functions (fetchMarketData), clear variable names.
4. Handle errors comprehensively — try/catch with meaningful error messages.
5. Use functional components with typed props interfaces.
6. Use early returns to avoid deep nesting (guard clauses).
7. Use named constants for magic numbers (MAX_RETRIES, DEBOUNCE_DELAY_MS).
8. Use Promise.all() for independent async operations.
9. Use Zod schemas for input validation at API boundaries.
10. Use consistent API response format ({success, data, error, meta}).
11. Memoize expensive computations (useMemo) and callbacks (useCallback).
12. Code-split heavy components with lazy() + Suspense.

## Reference Guide

| Topic | File | Read when... |
|-------|------|-------------|
| TypeScript Standards | references/typescript-standards.md | Naming, types, error handling, async patterns, API design |
| React Components | references/react-components.md | Composition, compound components, render props, error boundaries |
| State & Hooks | references/state-hooks.md | Custom hooks, state management, Context+Reducer, data fetching |
| Performance | references/performance.md | Memoization, code splitting, virtualization, lazy loading |
| Forms & A11y | references/forms-accessibility.md | Form handling, validation, keyboard navigation, focus management |

## Constraints

- MUST read relevant reference file before writing code in that topic area
- MUST run code-reviewer agent after completing code changes
- Prefer composition over inheritance for components
- Use bun instead of npx for running tools
