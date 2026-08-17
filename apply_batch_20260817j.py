#!/usr/bin/env python3
"""
Manual tail step: tenth batch from the 2026-08-17 crosshair session.
Runs after apply_batch_20260817i.py. Name-keyed and idempotent.

op 1: shrink axis_24_block footprint to one third per side. Height held,
      x centre held, north face held flat against axis_24.

Usage:  python3 apply_batch_20260817j.py docs/plans/dust2_half.json
"""
import json, sys

NAME = "axis_24_block"
PRE = 586.7          # current footprint, both axes
POST = 195.6         # one third per side
NORTH_Y = 3920.8     # axis_24 south face, held

def main(path):
    plan = json.load(open(path))
    boxes = plan["boxes"]
    idx = {b["name"]: i for i, b in enumerate(boxes)}
    log = []

    if NAME not in idx:
        log.append("skip resize %s (absent)" % NAME)
    else:
        b = boxes[idx[NAME]]
        e, o = b["extents"], b["origin"]
        if abs(e[0] - POST) < 0.1 and abs(e[1] - POST) < 0.1:
            log.append("skip resize %s (already %.1f)" % (NAME, POST))
        elif abs(e[0] - PRE) > 0.1 or abs(e[1] - PRE) > 0.1:
            log.append("FAIL resize %s: expected %.1f square, found %.1f x %.1f" % (NAME, PRE, e[0], e[1]))
        else:
            e[0] = POST
            e[1] = POST
            o[1] = round(NORTH_Y - POST / 2.0, 1)
            log.append("resize %s %.1f -> %.1f square, north face held at %.1f" % (NAME, PRE, POST, NORTH_Y))

    json.dump(plan, open(path, "w"), indent=1)
    for line in log:
        print(line)
    print("boxes: %d" % len(boxes))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_half.json")
