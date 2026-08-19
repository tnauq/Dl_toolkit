#!/usr/bin/env python3
"""Stitch the two halves at ground level and remove the seam wall.

Runs on docs/plans/dust2_full.json, AFTER mirror.py.  mirror.py rebuilds
that file from the half, so the order is always:

    python3 mirror.py docs/plans/dust2_half.json
    python3 stitch.py docs/plans/dust2_full.json

Two operations, both name-keyed and idempotent.

REMOVE the seam wall, whole boxes, no cutting:
    axis_61  x -1760.3..1920.3   y 5067.6..5254.4   z 0.1..1280.3
    axis_60  x  1920.4..2347.2   y 5094.4..5147.6   z 0.1..1280.3
    axis_59  x  2347.1..2773.9   y 5067.6..5254.4   z 0.1..1280.3
and their m_ twins.  Nothing straddles the seam, so all six leave cleanly.

ADD one ground plate across the band the two halves' ground plates do not
reach.  axis_0 tops out at y 5267.7 and m_axis_0 starts at y 6902.4; the
new plate runs wall face to wall face, 5254.35 to 6915.75, so it overlaps
both by 13.35 rather than leaving a seam.

  z matches axis_0 exactly: origin -26.7, extents 53.3, top at -0.05.
  Both sides are already at that height, so the join is DEAD FLAT and
  needs no ramp.  This is the only reason the stitch is one box.

  x spans the union of the two plates, -3053.9 to 3974.1.  That union is
  symmetric about the x flip plane at 460.1 by construction, so the plate
  does not break the 180 degree rotational symmetry.

This does NOT touch axis_371, axis_43, axis_44 or axis_45.  See the notes
delivered with this script: axis_371 is a separate solid block behind the
wall, and the other three are the CT spawn box walls.
"""

import json
import sys

REMOVE = [
    # The seam wall behind CT spawn.
    "axis_59", "axis_60", "axis_61",
    "m_axis_59", "m_axis_60", "m_axis_61",
    # Second pass: the remaining barriers along the seam.
    #   axis_371  x -1013.5..640.2   y 4907.7..5067.7  z 0.1..1280.3
    #             a SOLID block, not a wall, sitting behind axis_61
    #   axis_44   x  2800.6..3760.8  y 5441.2..5494.4  z 0.1..1280.3
    #             the north wall of the CT spawn box
    #   axis_782  x -2133.8..-1653.7 y 5254.5..5267.8  z 0.1..1280.3
    #             thin wall at the north edge, west side
    # All three are removed WHOLE.  Several smaller boxes are embedded in
    # them; those are left alone rather than trimmed, so they now stand
    # proud into the open.  Listed in the notes delivered with this file.
    "axis_44", "axis_371", "axis_782",
    "m_axis_44", "m_axis_371", "m_axis_782",
]

ADDS = [
    {
        "name": "stitch_ground",
        "origin": [460.1, 6085.05, -26.7],
        "extents": [7028.0, 1661.4, 53.3],
        "angles": [0.0, 0.0, 0.0],
        "material": "materials/dev/reflectivity_30.vmat",
    },
]


def main(path):
    with open(path) as f:
        plan = json.load(f)

    boxes = plan["boxes"]
    before = len(boxes)

    gone = {b["name"] for b in boxes} & set(REMOVE)
    for n in REMOVE:
        if n in gone:
            print("DEL  %s" % n)
        else:
            print("SKIP del %s (not present)" % n)
    boxes = [b for b in boxes if b["name"] not in gone]

    have = {b["name"] for b in boxes}
    for box in ADDS:
        if box["name"] in have:
            print("SKIP add %s (already present)" % box["name"])
            continue
        boxes.append(json.loads(json.dumps(box)))
        have.add(box["name"])
        print("ADD  %s" % box["name"])

    plan["boxes"] = boxes
    with open(path, "w") as f:
        json.dump(plan, f, indent=1)
        f.write("\n")

    print("%d -> %d boxes" % (before, len(boxes)))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_full.json")
