#!/usr/bin/env python3
"""claudex-build verify — deterministic gates + acceptance seal.

Gates run OUTSIDE any model context: this script runs every manifest gate,
writes a machine verdict plus per-gate logs, and scans the diff for
gate-gaming patterns. A model reads the verdict (and, on RED, one gate's
log tail); it never re-witnesses a run. The seal snapshots exactly what the
round verifier approved so acceptance re-reviews only what changed since.

Artifacts live under $(git rev-parse --git-dir)/claudex-verify/ — inside
.git, never tracked, invisible to clean-tree gates.

Usage:
  verify.py gates --base <sha> [--stage round|accept] [--manifest <file>]
      Manifest (default .claudex-gates.json in repo root):
        [{"name": "...", "cmd": "...", "timeout_s": 1800, "stage": "accept"}]
      "stage" omitted = runs in both stages. No manifest file -> a single
      accept-stage gate is derived from $PROOF_CMD. Neither -> exit 2.
      Writes verdict.json + <gate>.log; prints one line per gate and a
      final "GATES: GREEN|RED warn=<n> verdict=<path>".
      Exit: 0 green, 1 red, 2 config error.
  verify.py seal write --base <sha>
      Snapshot per-file git blob hashes of every path dirty vs base
      (tracked + untracked) plus the digest of the current verdict.json.
      Root runs this at the moment it accepts the round verdict.
      Requires a verdict.json (gates must have run) — else exit 2.
  verify.py seal check --base <sha>
      SEAL: INTACT   (exit 0)  tree byte-identical to the seal, sealed
                               verdict green.
      SEAL: DELTA    (exit 1)  changed/new/gone paths listed — that list
                               plus its callers is the re-review scope.
      SEAL: SEALED-RED (exit 1) seal valid but sealed verdict was not green.
      SEAL: MALFORMED (exit 2) missing/corrupt seal, base mismatch, or the
                               verdict changed after sealing — fail closed.
"""

import hashlib
import json
import os
import re
import subprocess
import sys
import time

SCHEMA = "claudex-verify-v1"
DEFAULT_MANIFEST = ".claudex-gates.json"
DEFAULT_TIMEOUT_S = 1800
EXCERPT_LINES = 40

# Added-line patterns that make a green gate untrustworthy (gate-gaming).
WARN_PATTERNS = [
    ("focused-test", re.compile(r"\.only\s*\(|\bfdescribe\s*\(|\bfit\s*\(")),
    ("skipped-test", re.compile(r"\.skip\s*\(|\bxdescribe\s*\(|\bxit\s*\(|it\.todo")),
    ("lint-silenced", re.compile(r"eslint-disable|biome-ignore")),
    ("types-silenced", re.compile(r"@ts-ignore|@ts-expect-error|\btype:\s*ignore\b")),
    (
        "coverage-silenced",
        re.compile(r"istanbul ignore|pragma:\s*no\s*cover|c8 ignore"),
    ),
    ("lint-noqa", re.compile(r"#\s*noqa")),
]
TEST_FILE_RE = re.compile(r"(\.|_|/)(test|spec)s?\.|/(tests?|__tests__|spec)/")


def die(msg, code=2):
    print(msg, file=sys.stderr)
    sys.exit(code)


def git(*args):
    try:
        return subprocess.check_output(
            ("git",) + args, text=True, stderr=subprocess.PIPE
        ).strip()
    except subprocess.CalledProcessError as e:
        die(f"git {' '.join(args)}: {e.stderr.strip() or e}")


def verify_dir():
    d = os.path.join(git("rev-parse", "--git-dir"), "claudex-verify")
    os.makedirs(d, exist_ok=True)
    return d


def parse_flags(args):
    flags, i = {}, 0
    while i < len(args):
        if args[i].startswith("--"):
            if i + 1 >= len(args):
                die(f"{args[i]}: value required")
            flags[args[i][2:]] = args[i + 1]
            i += 2
        else:
            die(f"unexpected argument {args[i]!r}")
    return flags


def dirty_paths(base):
    """Every path dirty vs base: tracked diff + untracked. Sorted, unique."""
    tracked = git("diff", "--name-only", base).splitlines()
    untracked = git("ls-files", "--others", "--exclude-standard").splitlines()
    return sorted(set(p for p in tracked + untracked if p))


def blob_hash(path):
    if not os.path.isfile(path):
        return "GONE"
    return git("hash-object", path)


def snapshot(base):
    return {p: blob_hash(p) for p in dirty_paths(base)}


def file_sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def load_manifest(flags):
    path = flags.get("manifest") or os.environ.get("GATES_FILE") or DEFAULT_MANIFEST
    if os.path.isfile(path):
        try:
            gates = json.load(open(path))
        except json.JSONDecodeError as e:
            die(f"gates: {path} is not valid JSON: {e}")
        if not isinstance(gates, list) or not gates:
            die(f"gates: {path} must be a non-empty JSON array")
        for g in gates:
            if not isinstance(g, dict) or not g.get("name") or not g.get("cmd"):
                die(f"gates: every entry needs name+cmd, got: {g!r}")
            if g.get("stage") not in (None, "round", "accept"):
                die(f"gates: bad stage in {g.get('name')!r} (round|accept)")
        return gates, path
    proof = os.environ.get("PROOF_CMD")
    if proof:
        return [{"name": "proof", "cmd": proof, "stage": "accept"}], "$PROOF_CMD"
    die(f"gates: no manifest at {path} and no $PROOF_CMD set")


def run_gate(gate, vdir):
    cmd = gate["cmd"]
    timeout = int(gate.get("timeout_s", DEFAULT_TIMEOUT_S))
    log_path = os.path.join(vdir, f"{gate['name']}.log")
    t0 = time.time()
    try:
        p = subprocess.run(
            cmd,
            shell=True,
            text=True,
            timeout=timeout,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        rc, out = p.returncode, p.stdout or ""
    except subprocess.TimeoutExpired as e:
        rc = 124
        out = (e.stdout or "") if isinstance(e.stdout, str) else ""
        out += f"\n[verify] TIMEOUT after {timeout}s"
    secs = round(time.time() - t0, 1)
    with open(log_path, "w") as f:
        f.write(out)
    excerpt = "\n".join(out.splitlines()[-EXCERPT_LINES:])
    return {
        "name": gate["name"],
        "cmd": cmd,
        "exit": rc,
        "secs": secs,
        "log": log_path,
        "excerpt": excerpt,
    }


def warn_scan(base):
    warns = []
    diff = git("diff", "--unified=0", base)
    loc = "?"
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            loc = line[6:]
        elif line.startswith("+") and not line.startswith("+++"):
            for rule, pat in WARN_PATTERNS:
                if pat.search(line):
                    warns.append(
                        {"rule": rule, "file": loc, "text": line[1:].strip()[:160]}
                    )
    for row in git("diff", "--name-status", base).splitlines():
        parts = row.split("\t")
        if parts and parts[0].startswith("D") and TEST_FILE_RE.search(parts[-1]):
            warns.append({"rule": "test-file-deleted", "file": parts[-1], "text": ""})
    return warns


def cmd_gates(args):
    flags = parse_flags(args)
    base = flags.get("base") or die("gates: --base <sha> required")
    stage = flags.get("stage", "accept")
    if stage not in ("round", "accept"):
        die("gates: --stage must be round|accept")
    gates, source = load_manifest(flags)
    todo = [g for g in gates if g.get("stage") in (None, stage)]
    if not todo:
        die(f"gates: manifest {source} has no gates for stage {stage!r}")
    vdir = verify_dir()
    results = []
    for g in todo:
        r = run_gate(g, vdir)
        results.append(r)
        state = "OK" if r["exit"] == 0 else f"FAIL({r['exit']})"
        print(f"gate {r['name']}: {state} {r['secs']}s")
    warns = warn_scan(base)
    green = all(r["exit"] == 0 for r in results)
    verdict = {
        "schema": SCHEMA,
        "base": base,
        "stage": stage,
        "source": source,
        "green": green,
        "gates": results,
        "warns": warns,
    }
    vpath = os.path.join(vdir, "verdict.json")
    with open(vpath, "w") as f:
        json.dump(verdict, f, indent=1)
    print(f"GATES: {'GREEN' if green else 'RED'} warn={len(warns)} verdict={vpath}")
    sys.exit(0 if green else 1)


def cmd_seal(args):
    if not args or args[0] not in ("write", "check"):
        die("seal: usage: seal write|check --base <sha>")
    action, flags = args[0], parse_flags(args[1:])
    base = flags.get("base") or die(f"seal {action}: --base <sha> required")
    vdir = verify_dir()
    vpath = os.path.join(vdir, "verdict.json")
    spath = os.path.join(vdir, "seal.json")

    if action == "write":
        if not os.path.isfile(vpath):
            die("seal write: no verdict.json — run gates first (fail closed)")
        verdict = json.load(open(vpath))
        seal = {
            "schema": SCHEMA,
            "base": base,
            "files": snapshot(base),
            "verdict_sha256": file_sha256(vpath),
            "verdict_green": bool(verdict.get("green")),
            "warns_open": len(verdict.get("warns", [])),
        }
        with open(spath, "w") as f:
            json.dump(seal, f, indent=1)
        print(f"SEAL: WRITTEN files={len(seal['files'])} green={seal['verdict_green']}")
        return

    try:
        seal = json.load(open(spath))
    except (OSError, json.JSONDecodeError):
        print("SEAL: MALFORMED (missing or unreadable seal.json)")
        sys.exit(2)
    if seal.get("schema") != SCHEMA or seal.get("base") != base:
        print(f"SEAL: MALFORMED (schema/base mismatch: sealed base {seal.get('base')})")
        sys.exit(2)
    if not os.path.isfile(vpath) or file_sha256(vpath) != seal.get("verdict_sha256"):
        print("SEAL: MALFORMED (verdict.json changed after sealing)")
        sys.exit(2)
    current = snapshot(base)
    sealed = seal.get("files", {})
    changed = sorted(p for p in sealed if p in current and current[p] != sealed[p])
    new = sorted(p for p in current if p not in sealed)
    gone = sorted(p for p in sealed if p not in current)
    if changed or new or gone:
        print(f"SEAL: DELTA changed={changed} new={new} gone={gone}")
        sys.exit(1)
    if not seal.get("verdict_green"):
        print("SEAL: SEALED-RED (sealed verdict was not green)")
        sys.exit(1)
    print(f"SEAL: INTACT files={len(sealed)} warns_open={seal.get('warns_open', 0)}")


COMMANDS = {"gates": cmd_gates, "seal": cmd_seal}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        die("usage: verify.py gates|seal ... (see module docstring)")
    COMMANDS[sys.argv[1]](sys.argv[2:])


if __name__ == "__main__":
    main()
