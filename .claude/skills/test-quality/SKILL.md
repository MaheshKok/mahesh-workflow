---
name: test-quality
description: Adversarial test-writing discipline — write tests from the spec/contract not the implementation, cover boundary/null/type-coercion/state/error-path cases, apply a mutation-testing mindset, avoid tautological or over-mocked tests. Use when writing, updating, or reviewing tests, or when asked to improve coverage. Coverage is a side effect of good tests, not the goal.
---

# Test Quality — Bug-Finding Over Coverage

> Companion to the always-on `testing.md` rule (80% coverage, TDD RED-GREEN-REFACTOR).
> Coverage is a side effect of good tests, not a goal.

## Scope

Apply this rule globally across repositories, languages, and agents whenever tests
are added, updated, or reviewed. When a coverage target conflicts with meaningful
bug-finding tests, improve the tests rather than optimizing for coverage alone.

## Core Principle

**Tests exist to find bugs, not to prove the code works.**

A test that cannot fail when the implementation is wrong is worthless.
A test written by reading the implementation and mirroring its logic is worthless.

## MANDATORY: Write Tests From the Spec, Not the Code

When testing an existing function:

1. Read ONLY the function signature, docstring, and types
2. DO NOT read the function body before writing tests
3. Derive expected behavior from the contract (name, docs, types, caller expectations)
4. Write all test cases based on that contract
5. ONLY THEN run the tests against the implementation
6. If tests pass on first run — be suspicious. Review whether you accidentally wrote tautological tests

When the function has no docstring or clear contract:
- Ask the user what the function SHOULD do
- Or infer the contract from its callers, not its implementation

## Anti-Patterns — NEVER Do These

### 1. Implementation Mirroring
```
# BAD: Test just re-implements the function
def test_calculate_discount():
    price = 100
    discount = 0.2
    assert calculate_discount(price, discount) == price * (1 - discount)
    # ↑ This is the implementation itself. It catches nothing.

# GOOD: Test uses independently derived expected values
def test_calculate_discount():
    assert calculate_discount(100, 0.2) == 80.0
    assert calculate_discount(0, 0.5) == 0.0
    assert calculate_discount(99.99, 0.1) == 89.991  # precision matters?
```

### 2. Happy Path Only
```
# BAD: Only tests the obvious success case
def test_parse_email():
    assert parse_email("user@example.com") == ("user", "example.com")

# GOOD: Tests the boundaries where bugs live
def test_parse_email():
    assert parse_email("user@example.com") == ("user", "example.com")
    assert parse_email("USER@EXAMPLE.COM") == ("user", "example.com")  # case?
    assert parse_email("a@b.c") == ("a", "b.c")  # minimal valid
    assert parse_email("user+tag@example.com") == ("user+tag", "example.com")
    with pytest.raises(ValueError):
        parse_email("")
    with pytest.raises(ValueError):
        parse_email("no-at-sign")
    with pytest.raises(ValueError):
        parse_email("@no-local-part.com")
    with pytest.raises(ValueError):
        parse_email("spaces in@email.com")
```

### 3. Snapshot-Matching Without Thought
Don't capture the current output and assert it matches. That just locks in existing behavior — including existing bugs.

### 4. Over-Mocking
If you mock everything the function touches, you're testing nothing. Mock external
boundaries (network — API calls only, do not mock DB queries), filesystem, clock),
not internal logic. DB queries are internal logic — mocking them hides real bugs
where mocked tests pass but production queries fail.

## MANDATORY: Adversarial Test Categories

For EVERY function under test, consider ALL of these categories. Skip a category only if it genuinely doesn't apply, and state why.

### Boundary Values
- Zero, empty string, empty array, empty object
- One element, single character
- Maximum expected size
- Off-by-one (length-1, length, length+1)
- Negative numbers when positive expected
- Float precision (0.1 + 0.2 ≠ 0.3)

### Null / Undefined / Missing
- null or undefined where a value is expected
- Missing optional fields
- Extra unexpected fields
- Empty vs missing (empty string vs null vs undefined)

### Type Coercion & Edge Types
- String "0" vs number 0 vs boolean false
- NaN, Infinity, -Infinity
- Very large numbers (Number.MAX_SAFE_INTEGER + 1)
- Unicode, emoji, RTL characters in strings
- Whitespace-only strings

### State & Ordering
- Calling function twice with same input (idempotency)
- Calling in unexpected order
- Concurrent calls (if applicable)
- Empty initial state

### Error Paths
- Does it throw the RIGHT error for the RIGHT reason?
- Does the error message help debugging?
- Does it fail gracefully or corrupt state?
- Are resources cleaned up on error (files closed, connections released)?

## Mutation Testing Mindset

After writing tests, mentally apply these mutations to the implementation:
- Replace `<` with `<=` — does a test fail?
- Replace `+` with `-` — does a test fail?
- Remove an if-branch — does a test fail?
- Return early — does a test fail?
- Off-by-one the loop — does a test fail?

If any mutation would NOT be caught, you're missing a test case. Add it.

## Test Independence

- Each test must set up its own state
- No test should depend on another test's execution
- Tests must pass when run individually AND in any order
- Shared setup is fine (fixtures/beforeEach) but shared mutable state is not

## Naming Convention

Test names must describe the scenario AND expected outcome:
```
# BAD
test_process()
test_error()

# GOOD
test_process_returns_empty_list_when_input_is_none()
test_process_raises_value_error_for_negative_amounts()
test_discount_rounds_to_two_decimal_places()
```

## Self-Check Before Submitting Tests

- [ ] I wrote tests from the spec/contract, NOT by reading the function body
- [ ] I included adversarial edge cases, not just happy path
- [ ] Each test would FAIL if the implementation had a specific class of bug
- [ ] I mentally applied mutation testing — each mutation is caught
- [ ] Test names describe scenario + expected outcome
- [ ] Mocks are minimal — only external boundaries (API calls, filesystem, clock), never DB queries
- [ ] No test re-implements the function's logic in the assertion
