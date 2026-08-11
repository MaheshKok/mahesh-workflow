# Credential Security Patterns

Patterns for handling credentials in VS Code extensions and git operations
without leaking them to config files, process lists, or syncable settings.

---

## Rule 1: Secrets go in SecretStorage, never in settings

VS Code settings (`package.json` contributes → `configuration.properties`) are
stored in plaintext `settings.json` and synced via Settings Sync. Do not put
tokens, PATs, or passwords there.

**Bad:**
```json
// package.json
"intelligit.gitlab.personalAccessToken": {
  "type": "string",
  "default": ""
}
```

**Good:**
```typescript
// Store
await context.secrets.store("myApp.providerToken", token);

// Retrieve
const token = await context.secrets.get("myApp.providerToken");

// Delete
await context.secrets.delete("myApp.providerToken");
```

**Migration path for existing settings-based tokens:**
1. Read the legacy setting value once.
2. Store it in SecretStorage.
3. Clear the setting value (`config.update(key, undefined, true)`).
4. Never read the setting again — remove the config schema entry.

---

## Rule 2: Authenticated git clone URLs must be cleaned up

When you clone with `https://user:TOKEN@github.com/user/repo.git`, git records
that full URL as the `origin` remote in `.git/config`. The token persists on
disk indefinitely.

**Fix: reset the remote immediately after clone.**

```typescript
await executor.run(["clone", authenticatedUrl, repoDir]);

// Strip credentials from the persisted origin URL
await executor.run(["remote", "set-url", "origin", cleanUrl]);
```

Wrap the cleanup in its own try/catch — it's non-fatal. If cleanup fails, warn
the user so they can inspect `.git/config` themselves.

```typescript
try {
    const cleanup = new GitExecutor(targetPath);
    await cleanup.run(["remote", "set-url", "origin", cleanRemoteUrl]);
} catch {
    vscode.window.showWarningMessage(
        "Cloned successfully, but could not clean the remote URL. " +
        "You may want to verify the origin remote in .git/config.",
    );
}
```

**Documentation**: Do not claim tokens are "never persisted." The token IS
briefly in `.git/config` during the clone. Say "reset after successful clone
so credentials are not left when cleanup succeeds."

---

## Rule 3: Credentials in CLI arguments are visible in the process list

`git clone https://user:TOKEN@host/repo` exposes the token to any process
inspector on the system (ps, /proc, Activity Monitor).

Mitigations (in order of preference):
1. Use OAuth/session-based auth where the CLI tool handles tokens internally
   (e.g., `gh auth git-credential`, Git Credential Manager).
2. Pass credentials via environment variables and configure the tool to read them.
3. As a last resort, embed in the URL but clean up immediately (Rule 2).

The simple-git library used by this project passes arguments directly to the git
binary, so option 3 is the pragmatic choice when no credential helper is
available. Always pair with Rule 2.

---

## Rule 4: fs.access catch blocks must check error codes

A bare `catch {}` after `fs.access(targetPath)` treats every error as
"file not found" — including permission errors, broken paths, and I/O failures.

**Bad:**
```typescript
try {
    await fs.access(targetPath);
} catch {
    // Assumes file doesn't exist — WRONG for EACCES, EPERM, etc.
    await doTheThing();
}
```

**Good:**
```typescript
try {
    await fs.access(targetPath);
} catch (err) {
    if ((err as NodeJS.ErrnoException).code === "ENOENT") {
        // File truly does not exist
        await doTheThing();
        return;
    }
    // Permission error, invalid path, etc. — surface to user
    vscode.window.showErrorMessage(`Cannot access "${path}": ${getErrorMessage(err)}`);
    return;
}
```

Only `ENOENT` means "does not exist." Everything else means "something is
wrong" and should stop execution.

---

## Rule 5: Separate deletion from existence checks

If a directory exists and you want to remove it before proceeding, keep the
existence check, the user confirmation, and the deletion as three guarded
stages — never one broad try/catch.

```typescript
// Stage 1: check existence (only ENOENT means "doesn't exist")
try { await fs.access(targetPath); } catch (err) {
    if ((err as NodeJS.ErrnoException).code === "ENOENT") { await proceed(); return; }
    showErrorAndReturn(err);
}

// Stage 2: user confirmation
const confirm = await vscode.window.showWarningMessage(..., "Overwrite");
if (confirm !== "Overwrite") return;

// Stage 3: deletion (own try/catch, separate error path)
try { await fs.rm(targetPath, { recursive: true, force: true }); } catch (err) {
    showErrorAndReturn(err);
}

await proceed();
```
