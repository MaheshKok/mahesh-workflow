# React Doctor validation

Use this when adding React Doctor to a React/React-webview project or when a project already exposes a `react-doctor` validation script.

## Setup pattern

1. Install as a dev dependency with the project's package manager:

   ```bash
   bun add -d react-doctor
   # or: npm install -D react-doctor / pnpm add -D react-doctor
   ```

2. Add a package script:

   ```json
   {
     "scripts": {
       "react-doctor": "react-doctor -y"
     }
   }
   ```

3. Use `doctor.config.json` (not `react-doctor.config.json`) for JSON config. A good default for local/CI validation is:

   ```json
   {
     "offline": true,
     "share": false,
     "failOn": "error",
     "respectInlineDisables": true
   }
   ```

4. Run it before final typecheck/build/test validation:

   ```bash
   bun run react-doctor
   ```

## Interpreting output

- Error-level diagnostics should be fixed before considering the task complete.
- Warning-level diagnostics may be numerous on an existing codebase. Triage them and fix high-confidence ones, but do not mix a huge warning cleanup into an unrelated feature unless the user asked for it.
- If warnings are intentionally left, report the count and make clear the validation passed because there are no error-level diagnostics.

## Common fixes

### Conditional hooks

React Doctor catches hooks called after an early return. Move every hook before conditional returns:

```tsx
function Badge({ visible }: { visible: boolean }) {
  const [pos, setPos] = React.useState(null);
  React.useEffect(() => () => cleanup(), []);

  if (!visible) return null;
  return <span />;
}
```

### Prop-sync effects

Avoid `useEffect(() => setLocalState(prop), [prop])` when local state can be derived from a prop-scoped override. Store the prop key that created the override and derive the effective state during render:

```tsx
const [override, setOverride] = useState<{ key: string; value: string } | null>(null);
const effectiveValue = override?.key === propKey ? override.value : propValue;
```

This preserves optimistic local UI state while automatically dropping stale overrides when the parent context changes.

### Intentional command-signal effects

Some UI state changes are intentionally driven by monotonic command signals from props, such as `expandAllSignal`, `collapseAllSignal`, or refresh feedback. If refactoring would make the code less clear, add a narrow inline suppression immediately before the state setter and document why:

```tsx
// react-doctor-disable-next-line react-doctor/no-adjust-state-on-prop-change
setExpandedDirs(new Set());
```

Do not blanket-disable a whole file unless there is no practical alternative.

### Reduced motion

For webview shells or shared app CSS, add a `prefers-reduced-motion: reduce` guard so spinners, transitions, and animations respect accessibility settings:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

## Validation loop

After fixes:

```bash
bun run format
bun run react-doctor
bun run typecheck
bun run build
bun run test
```

Then run the project's full validation chain from AGENTS.md/CLAUDE.md before committing.
