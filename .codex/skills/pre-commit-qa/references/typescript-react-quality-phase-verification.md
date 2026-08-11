# TypeScript/React quality phase verification

Use this when the user asks whether quality-tooling phases are implemented.

## Verify both implementation and branch shape

If the user's plan says `Phase N branch`, check two separate things:

1. Phase content exists and is wired:
   - dependencies in `package.json` / lockfile;
   - scripts in `package.json`;
   - config files such as `eslint.config.mjs`, `knip.json`, `.dependency-cruiser.cjs`, `doctor.config.*`;
   - changelog entries if this branch already has a release/version entry.
2. Git shape matches the user's wording:
   - list branch names that look phase/tool related;
   - list commits on the active branch not in `main`;
   - say explicitly whether the phase is a separate physical branch or only a phase-scoped commit.

Do not answer simply "implemented" when the tooling exists but the requested physical branch split does not.

## Focused proof commands

For the phase set used in this repo, focused proof usually includes:

```bash
git status --short --branch
git log --oneline --decorate main..HEAD
node - <<'NODE'
const p=require('./package.json');
console.log(JSON.stringify({scripts:p.scripts, devDependencies:p.devDependencies}, null, 2));
NODE
bun run lint
bun run lint:strict
bun run deps:check
bun run architecture:check
```

Use full validation before committing code changes. For read-only phase verification, focused gates are acceptable if the user only asked for status.

## CI warning-gate nuance

When a phase says warnings should not fail CI until cleanup is complete, inspect the actual workflow command. Warning-level ESLint rules still fail if CI runs `eslint --max-warnings=0` or a strict script. It is only non-failing if CI runs a non-strict lint command, or if all warnings have already been cleaned/staged below the threshold.

Report this nuance directly:

- "CI runs `bun run lint`, so warning-level SonarJS findings do not fail CI."
- "Local `bun run lint:strict` still exists and currently passes."

## Checklist style

Return a bullet-by-bullet status mapped to the user's phase list, with caveats at the top. Avoid burying the important distinction between phase content and phase branch topology.
