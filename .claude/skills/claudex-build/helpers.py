#!/usr/bin/env python3
"""claudex-build helpers — deterministic enforcement of the effort ladder,
session routing, and telemetry policy. SKILL.md prose explains WHY; this
script decides. Its output is binding on the orchestrator.

python3, not bash: shell-hook wrappers (e.g. lean-ctx allowlists) block
`bash` in orchestrator sessions; python3 script files run unhooked.

Usage:
  helpers.py telemetry <stream.jsonl> [rollout.jsonl]
      -> "PEAK=<n> LAST=<n> PCT=<n>% NONRESUMABLE=yes|no"
         Peak-based; falls back to the rollout when the stream has no usage
         events; zero events anywhere -> NONRESUMABLE=yes (fails closed).
  helpers.py route fix <round#>
      -> "EFFORT=xhigh MODE=fresh" | "TAKEOVER (...)"
         MODE is always fresh — nothing in the round loop resumes. A legacy
         <nonresumable> third argument is accepted and ignored.
  helpers.py route continuation <n>
      -> "EFFORT=base MODE=fresh" | "TAKEOVER (...)"   (base = $BUILD_EFFORT)
  helpers.py route phase
      -> "EFFORT=base MODE=fresh"
  helpers.py watch <rollout.jsonl> [stale_secs=600]
      -> heartbeat for Bash run_in_background: exits 1 with one line after
         2 consecutive frozen samples (mtime age > stale AND size flat AND
         token-event count flat); self-expires after 3h. Alert = trigger to
         corroborate, never an automatic kill.
  helpers.py sha
      -> "SKILL-SHA <12hex> <path>" lines for SKILL.md + helpers.py + verify.py
"""

import hashlib
import os
import re
import sys
import time

DEFAULT_WINDOW = 258400
USAGE_RE = re.compile(r'"last_token_usage":\{"input_tokens":(\d+)')
WINDOW_RE = re.compile(r'"model_context_window":(\d+)')


def die(msg, code=2):
    print(msg, file=sys.stderr)
    sys.exit(code)


def scan(path):
    """Return (peak, last, window) over usage events in a jsonl file."""
    peak = last = 0
    window = DEFAULT_WINDOW
    try:
        with open(path, "r", errors="replace") as f:
            for line in f:
                m = WINDOW_RE.search(line)
                if m:
                    window = int(m.group(1))
                for m in USAGE_RE.finditer(line):
                    last = int(m.group(1))
                    if last > peak:
                        peak = last
    except OSError as e:
        die(f"telemetry: cannot read {path}: {e}")
    return peak, last, window


def cmd_telemetry(args):
    if not args:
        die("telemetry: stream file required")
    peak, last, window = scan(args[0])
    if peak == 0 and len(args) > 1 and os.path.isfile(args[1]):
        peak, last, window = scan(args[1])
    pct = peak * 100 // window if window else 100
    nonres = peak == 0 or pct > 85 or last * 2 < peak
    print(
        f"PEAK={peak} LAST={last} PCT={pct}% NONRESUMABLE={'yes' if nonres else 'no'}"
    )


def cmd_route(args):
    if not args:
        die("route: kind required (fix|continuation|phase)")
    kind = args[0]
    if kind == "fix":
        if len(args) < 2:
            die("route fix: usage: route fix <round#>")
        n = int(args[1])
        if n > 2:
            print("TAKEOVER (fix rounds exhausted: MAX_FIX_ROUNDS=2)")
            return
        # No escalation ladder: both fix rounds run at the launch effort. Measured
        # on a real campaign -- two `max` rounds, same repo/reviewer: the one that
        # spent 76% more reasoning turns was the one REJECTED (7 findings), because
        # extra effort optimizes harder against a mis-stated objective rather than
        # repairing it. Spec quality and root review moved outcomes; the tier never
        # did. `ultra` is not a rung above `max` either -- codex-cli rewrites
        # ultra->max before the request leaves the machine (wire-captured, 0.144.1),
        # so emitting it would only make the log claim an effort that never shipped.
        effort = "xhigh"
        # MODE is always fresh: a resumed builder re-reads its own rejected
        # reasoning next to the correction and drifts back toward it, and its
        # context compounds round over round. A legacy <nonresumable> third
        # argument is still accepted, and deliberately ignored.
        print(f"EFFORT={effort} MODE=fresh")
    elif kind == "continuation":
        if len(args) < 2:
            die("route continuation: usage: route continuation <n>")
        if int(args[1]) > 2:
            print("TAKEOVER (continuation cap: 2 per phase)")
            return
        print("EFFORT=base MODE=fresh")
    elif kind == "phase":
        print("EFFORT=base MODE=fresh")
    else:
        die(f"route: unknown kind {kind!r}")


def cmd_watch(args):
    if not args:
        die("watch: rollout file required")
    rollout = args[0]
    stale = int(args[1]) if len(args) > 1 else 600
    expire = 3 * 3600
    frozen, last_sz, last_tk = 0, -1, -1
    start = time.time()
    while time.time() - start < expire:
        time.sleep(stale)
        if not os.path.isfile(rollout):
            continue
        st = os.stat(rollout)
        size, age = st.st_size, time.time() - st.st_mtime
        with open(rollout, "r", errors="replace") as f:
            tokens = sum(len(USAGE_RE.findall(line)) for line in f)
        if age > stale and size == last_sz and tokens == last_tk:
            frozen += 1
        else:
            frozen = 0
        last_sz, last_tk = size, tokens
        if frozen >= 2:
            print(
                f"HEARTBEAT: rollout frozen {frozen}x{stale}s "
                f"(size={size} tokens={tokens}) — corroborate before any kill"
            )
            sys.exit(1)
    print(f"HEARTBEAT: watcher self-expired after {expire}s")


def cmd_sha(_args):
    here = os.path.dirname(os.path.abspath(__file__))
    for name in ("SKILL.md", "helpers.py", "verify.py"):
        path = os.path.join(here, name)
        try:
            digest = hashlib.sha256(open(path, "rb").read()).hexdigest()
            print(f"SKILL-SHA {digest[:12]} {path}")
        except OSError:
            print(f"SKILL-SHA missing {path}")


COMMANDS = {
    "telemetry": cmd_telemetry,
    "route": cmd_route,
    "watch": cmd_watch,
    "sha": cmd_sha,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        die("usage: helpers.py telemetry|route|watch|sha ...")
    COMMANDS[sys.argv[1]](sys.argv[2:])


if __name__ == "__main__":
    main()
