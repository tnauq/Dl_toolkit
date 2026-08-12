#!/usr/bin/env python3
"""
pick_target.py — find a real, patchable float in a source vdata file and emit a
batch plan that guards on its current value.

The smoke test needs a target that is true by construction: hardcoding a path
means the test breaks whenever Valve moves the value, which is noise rather
than signal. An earlier version pattern-matched `m_fl*` at exactly two tabs and
failed on the real file — this walks the block structure instead of guessing at
indentation depth.

    python3 tools/pick_target.py <source.vdata> <relative-path> [--delta 1.0]

Writes a version-1 plan to stdout. Exit 3 if no suitable target exists.

What counts as suitable:
  - a plain float scalar (a decimal point, no type prefix, not quoted)
  - reachable by a dotted path of plain identifiers
  - NOT inside an array, since v1 refuses array traversal
  - shallow first, so the resulting path is short and legible in a log
"""

import argparse
import json
import re
import sys

# key = value, where value is a bare decimal number
FLOAT_LINE = re.compile(r'^(\t*)([A-Za-z_]\w*)\s*=\s*(-?\d+\.\d+)\s*$')
# key = (block or array opens on this line or the next)
OPEN_LINE = re.compile(r'^(\t*)([A-Za-z_]\w*)\s*=\s*([\{\[])?\s*$')
BARE_OPEN = re.compile(r'^(\t*)([\{\[])\s*$')
CLOSE_LINE = re.compile(r'^(\t*)([\}\]])')


def candidates(text):
    """Yield (depth, dotted_path, value) for every plain float outside arrays."""
    stack = []          # list of (name, is_array)
    pending = None      # a key awaiting its opening brace on the next line

    for raw in text.split("\n"):
        line = raw.rstrip("\r")

        if pending is not None:
            m = BARE_OPEN.match(line)
            if m:
                stack.append((pending, m.group(2) == "["))
                pending = None
                continue
            # key wasn't a block after all
            pending = None

        m = CLOSE_LINE.match(line)
        if m:
            if stack:
                stack.pop()
            continue

        m = FLOAT_LINE.match(line)
        if m:
            key, value = m.group(2), float(m.group(3))
            if not any(is_array for _, is_array in stack):
                path = ".".join([name for name, _ in stack] + [key])
                yield len(stack), path, value
            continue

        m = OPEN_LINE.match(line)
        if m:
            opener = m.group(3)
            if opener:
                stack.append((m.group(2), opener == "["))
            else:
                pending = m.group(2)
            continue


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("relative")
    ap.add_argument("--delta", type=float, default=1.0)
    args = ap.parse_args()

    try:
        text = open(args.source, encoding="utf-8", errors="replace").read()
    except OSError as e:
        print("cannot read %s: %s" % (args.source, e), file=sys.stderr)
        return 3

    found = list(candidates(text))
    if not found:
        print("no plain float scalar found in %s" % args.source, file=sys.stderr)
        return 3

    # Shallowest first, then alphabetical, so the choice is deterministic
    # across runs — the envelope determinism assertion depends on it.
    found.sort(key=lambda t: (t[0], t[1]))
    depth, path, value = found[0]

    plan = {
        "version": 1,
        "description": "batch-smoke",
        "edits": [{
            "file": args.relative,
            "set": [{
                "path": path,
                "value": value + args.delta,
                "expect": value
            }]
        }]
    }
    print(json.dumps(plan, indent=2))
    print("picked %s = %s (depth %d, %d candidates)"
          % (path, value, depth, len(found)), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
