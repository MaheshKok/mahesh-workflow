# Behavior-Preserving Examples

Use these examples only when the code has the same contract. They illustrate checks to make before proposing a simplification; they are not rewrite recipes.

## TypeScript and JavaScript

`||` and `??` have different absence rules. Keep `||` when `0`, `false`, and `""` intentionally fall back; use `??` only when those values are meaningful.

```ts
const label = input.label || "untitled"; // empty label falls back
const limit = input.limit ?? 20; // 0 remains a valid limit
```

Do not automatically remove `await` from `return await`. It can affect a local `try`/`catch` and async stack/error behavior.

```ts
async function loadUser(id: string): Promise<User> {
  try {
    return await client.fetchUser(id);
  } catch (error) {
    throw new UserLoadError(id, { cause: error });
  }
}
```

## Python

Guard clauses can preserve the same errors while reducing indentation when checks occur in the same order.

```python
def process(record):
    if record is None:
        raise TypeError("record is required")
    if not record.is_valid():
        raise ValueError("invalid record")
    return store(record)
```

Use a comprehension only when it preserves ordering, evaluation count, and exception behavior.

```python
names_by_id = {item.id: item.name for item in items}
```

## React

Extract a render-only value when it does not change keys, hook order, props, or effect timing.

```tsx
function UserBadge({ user }: { user: { isAdmin: boolean } }) {
  const label = user.isAdmin ? "Admin" : "User";
  return <Badge variant={user.isAdmin ? "admin" : "default"}>{label}</Badge>;
}
```

Keep effect cleanup and dependency semantics intact; do not silence a dependency warning by changing an array without proving the closure contract.
