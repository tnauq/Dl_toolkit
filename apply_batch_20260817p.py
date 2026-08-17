#!/usr/bin/env python3
"""
Manual tail step: sixteenth batch from the 2026-08-17 crosshair session.
Runs after apply_batch_20260817o.py. Name-keyed and idempotent.

Raise the remaining walls of the keyhole room to the full-map top so the
room matches the hall on the other side of axis_547. The corner fillers
from batch g are raised with them, otherwise the corners leak above 1067.

Usage:  python3 apply_batch_20260817p.py docs/plans/dust2_half.json
"""
import json, sys

TOP = 1280.3
PRE = 1067.0

RAISE = [
    "axis_565", "axis_568", "axis_571",
    "yaw_566", "yaw_569", "yaw_570",
    "gapfill_566_565", "gapfill_566_567",
    "gapfill_569_565", "gapfill_569_568",
    "gapfill_570_568", "gapfill_570_571",
    "gapfill_573_567", "gapfill_573_572",
]

def main(path):
    plan = json.load(open(path))
    boxes = plan["boxes"]
    idx = {b["name"]: i for i, b in enumerate(boxes)}
    log = []

    for name in RAISE:
        if name not in idx:
            log.append("skip raise %s (absent)" % name)
            continue
        b = boxes[idx[name]]
        o, e = b["origin"], b["extents"]
        lo, hi = o[2] - e[2] / 2.0, o[2] + e[2] / 2.0
        if abs(hi - TOP) < 0.1:
            log.append("skip raise %s (already %.1f)" % (name, TOP))
            continue
        if abs(hi - PRE) > 0.1:
            log.append("FAIL raise %s: expected z max %.1f, found %.1f" % (name, PRE, hi))
            continue
        o[2] = round((lo + TOP) / 2.0, 1)
        e[2] = round(TOP - lo, 1)
        log.append("raise %s z max %.1f -> %.1f" % (name, hi, TOP))

    json.dump(plan, open(path, "w"), indent=1)
    for line in log:
        print(line)
    print("boxes: %d" % len(boxes))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_half.json")
