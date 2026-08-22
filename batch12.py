#!/usr/bin/env python3
"""batch12.py - nineteenth build step, run after batch11.py.

Removes xtun_big_n1 and its m_ twin.

WHY

The north wall of the xtun_big room runs x -2712.12..-2187.05.
xtun_big_n0 covers -2712.12..-2440.05, then the doorway runs
-2440.05..-2187.05 with xtun_big_n_sill beneath it. That doorway reaches
the room's east corner exactly, so the wall segment east of it has zero
length: -2187.05..-2187.05.

xtun_big_n1 is therefore not a thin wall, it is a correctly computed
empty remainder with x extent 0.00. A box with a zero extent has four
zero-area faces, which vbsp rejects as invalid planes, so it would break
the VMF export. Removing it changes nothing visually or in play; the
opening stays 253.00 wide and runs clean into the corner.

Idempotent: removals are skipped if the names are already gone.

Usage: python3 batch12.py docs/plans/dust2_full.json
"""

import json
import sys

REMOVE = ["xtun_big_n1"]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_full.json"
    with open(path) as f:
        plan = json.load(f)

    names = set()
    for n in REMOVE:
        names.add(n)
        names.add("m_" + n)

    present = {b["name"] for b in plan["boxes"]}
    gone = sorted(names & present)

    if not gone:
        print("removals already applied")
    else:
        for n in gone:
            box = next(b for b in plan["boxes"] if b["name"] == n)
            print("removing %s extents %s" % (n, box["extents"]))
        plan["boxes"] = [b for b in plan["boxes"] if b["name"] not in names]

    # Nothing else in the plan should have a zero extent. If one appears
    # later it will break the VMF export the same way, so it is worth
    # saying so here rather than discovering it at export time.
    bad = [b["name"] for b in plan["boxes"] if min(b["extents"]) <= 0.1]
    if bad:
        print("WARNING still zero or near-zero: " + ", ".join(bad))
    else:
        print("no remaining boxes with an extent at or under 0.1")

    with open(path, "w") as f:
        json.dump(plan, f, indent=1)

    print("boxes %d" % len(plan["boxes"]))


if __name__ == "__main__":
    main()
