#!/usr/bin/env python3
"""
Manual tail step: fourteenth batch from the 2026-08-17 crosshair session.
Runs after apply_batch_20260817m.py. Name-keyed and idempotent.

op 1: extend ceiling_80_68 south to the axis_80_cross north face.

Usage:  python3 apply_batch_20260817n.py docs/plans/dust2_half.json
"""
import json, sys

# name, axis, side, pre-edit value, post-edit value
GROW = [
    ("ceiling_80_68", 1, "min", 3867.4, 3467.4),
]

def main(path):
    plan = json.load(open(path))
    boxes = plan["boxes"]
    idx = {b["name"]: i for i, b in enumerate(boxes)}
    log = []

    for name, axis, side, pre, post in GROW:
        if name not in idx:
            log.append("skip grow %s (absent)" % name)
            continue
        b = boxes[idx[name]]
        o, e = b["origin"], b["extents"]
        lo, hi = o[axis] - e[axis] / 2.0, o[axis] + e[axis] / 2.0
        cur = hi if side == "max" else lo
        if abs(cur - post) < 0.1:
            log.append("skip grow %s (already %.1f)" % (name, post))
            continue
        if abs(cur - pre) > 0.1:
            log.append("FAIL grow %s: expected %.1f, found %.1f" % (name, pre, cur))
            continue
        if side == "max":
            hi = post
        else:
            lo = post
        o[axis] = round((lo + hi) / 2.0, 1)
        e[axis] = round(hi - lo, 1)
        log.append("grow %s axis%d %s %.1f -> %.1f" % (name, axis, side, cur, post))

    json.dump(plan, open(path, "w"), indent=1)
    for line in log:
        print(line)
    print("boxes: %d" % len(boxes))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_half.json")
