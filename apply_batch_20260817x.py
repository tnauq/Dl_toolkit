#!/usr/bin/env python3
"""
Manual tail step: twenty-fourth batch from the 2026-08-17 crosshair session.
Runs after apply_batch_20260817w.py. Name-keyed and idempotent.

Heights measured from the axis_722 floor top at 213.3.
  axis_797 and axis_387 double, 106.8 -> 213.6
  axis_469 becomes half of that, 106.8, so its top lands on 320.1

Usage:  python3 apply_batch_20260817x.py docs/plans/dust2_half.json
"""
import json, sys

FLOOR = 213.3

# name, pre-edit z max, post-edit z max
RESIZE = [
    ("axis_797", 320.1, 426.9),
    ("axis_387", 320.1, 426.9),
    ("axis_469", 266.8, 320.1),
]

def main(path):
    plan = json.load(open(path))
    boxes = plan["boxes"]
    idx = {b["name"]: i for i, b in enumerate(boxes)}
    log = []

    for name, pre, post in RESIZE:
        if name not in idx:
            log.append("skip resize %s (absent)" % name)
            continue
        b = boxes[idx[name]]
        o, e = b["origin"], b["extents"]
        lo, hi = o[2] - e[2] / 2.0, o[2] + e[2] / 2.0
        if abs(hi - post) < 0.1:
            log.append("skip resize %s (already %.1f)" % (name, post))
            continue
        if abs(hi - pre) > 0.1:
            log.append("FAIL resize %s: expected z max %.1f, found %.1f" % (name, pre, hi))
            continue
        o[2] = round((lo + post) / 2.0, 1)
        e[2] = round(post - lo, 1)
        log.append("resize %s z max %.1f -> %.1f (%.1f above floor)" % (name, hi, post, post - FLOOR))

    json.dump(plan, open(path, "w"), indent=1)
    for line in log:
        print(line)
    print("boxes: %d" % len(boxes))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_half.json")
