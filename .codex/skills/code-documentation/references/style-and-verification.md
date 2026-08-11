# Style and Verification

Use this reference when drafting or checking documentation quality.

## Writing Principles

- State what the reader needs to do or understand first; add detail progressively.
- Prefer concrete nouns, active voice, present tense, and short paragraphs.
- Explain intent, contracts, constraints, and consequences; do not narrate obvious syntax.
- Match existing terminology, heading structure, language, and tone unless a rewrite is requested.
- Use a diagram only when relationships or sequence are less clear in prose.

## Language Conventions

- Python: docstrings describe public behavior, arguments, returns, raised errors, and non-obvious side effects; follow local docstring style.
- TypeScript/JavaScript: JSDoc or TSDoc documents public contracts, nullability, async behavior, errors, and compatibility; do not restate inferred types without value.
- Go: exported identifiers begin with the identifier name and document behavior, errors, and concurrency constraints where relevant.
- Rust: rustdoc for public items documents behavior, errors, panics, safety, and ownership constraints when verified; follow the local rustdoc style.
- Java: Javadoc documents public contracts, parameters, returns, thrown errors, and lifecycle or threading constraints when verified; follow local conventions.
- C/C++: use the repository's Doxygen or comment style to document ownership, lifetime, error, and thread-safety contracts only when supported by source evidence.
- SQL and migrations: record data effect, compatibility, lock or availability implications, verification, and rollback when known.

## Completeness and Cross-Reference Checks

- Match every public item included in scope to a verified signature, behavior, and error contract where relevant.
- Recheck commands, paths, symbols, configuration keys, examples, versions, and internal links against current artifacts.
- Confirm examples use real argument shapes and describe observable output only when it was verified.
- Cross-reference related guides only when the target exists and the relationship is useful.
- Mark a critical unknown `cannot_verify` and block the artifact if its omission would mislead the audience.
