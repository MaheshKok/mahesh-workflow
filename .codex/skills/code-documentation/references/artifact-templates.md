# Evidence-Grounded Artifact Templates

Use only the sections supported by inspected artifacts. Replace bracketed labels with verified facts or omit them. Do not add badges, versions, commands, paths, links, API members, or release claims without evidence.

## README

```markdown
# [Verified project name]

[Verified purpose and intended audience.]

## Quick start

[Verified prerequisites, setup, and minimal use path.]

## Configuration

[Verified configuration surface and defaults, if relevant.]

## Verification

[Verified checks or expected result.]
```

## API Reference

```markdown
### `[Verified public symbol]`

[Verified contract.]

- Inputs: [verified parameters and constraints]
- Returns: [verified result]
- Errors: [verified error behavior]
- Example: [verified runnable usage, if available]
```

## Architecture Overview

```markdown
## Components and boundaries

[Verified responsibilities and dependencies.]

## Data or control flow

[Verified sequence and failure behavior.]

## Decisions and trade-offs

[Verified decision context, consequence, and alternatives when recorded.]
```

## Developer Guide

```markdown
## Local workflow

[Verified setup, common task, and validation path.]

## Troubleshooting

[Verified symptom, cause, and recovery step.]
```

## Migration Guide

```markdown
## Who is affected

[Verified compatibility impact.]

## Steps

1. [Verified ordered action]
2. [Verified validation]

## Rollback

[Verified reversal or stated limitation.]
```

## Changelog Entry

```markdown
## [Verified release or change range]

### Changed

- [Verified user-visible behavior change.]
```

## Inline Documentation

```text
[Explain only a non-obvious invariant, side effect, compatibility constraint,
error condition, or external contract that source code alone does not convey.]
```
