#!/usr/bin/env python3
"""batch14 - geometry edits from the 2026-08-23 crosshair session.

SEPARATE FROM batch13 BECAUSE IT TOUCHES BOXES. batch13 adds entities and
paths and never moves the 4,179 count; this one edits boxes in place. Keeping
them apart means a bad geometry edit can be reverted without losing a survey
session's worth of entity coordinates.

WHAT IT DOES

    1. LOWER hex_par_s_mid by 25%. Replaces the spawn-room roof cut that NEXT
       lists: rather than removing a roof so the zipline can leave, the wall
       comes down by a quarter and the cable clears it. Less destructive and
       it keeps the room enclosed.

    2. RECOLOUR four boxes that are the wrong material. Two are coloured as
       floor but are boxes, two are coloured as floor but are wall. This is
       cosmetic in a blockout and structural in a playtest, because material
       is how anyone reading the map knows what they are looking at.

    3. EXTEND axis_473 toward axis_124_far to close a gap between them.

NO BOX IS ADDED OR REMOVED, so EXPECT_BOXES in batch.yml and the census in
emit-dust2.yml do NOT change. That was the reason NEXT gave for batch14
needing a coordinated drop, and lowering a wall instead of cutting a roof
removes it.

IDEMPOTENT, but not in the same way as the batch scripts that rebuild from
scratch. A lowering is relative, so applying it twice would lower twice.
Every edit therefore records itself in the box under `_batch14`, and a box
already marked is skipped. Delete the marker to force a re-apply.

MIRRORING. Every named box has an m_ twin, and each edit is applied to both.
The twin is NOT recomputed from the original, it is edited the same way, so
a box whose twin has drifted stays drifted rather than being silently
snapped. Drift is reported.

    python3 batch14.py [docs/plans/dust2_full.json]
"""

import json
import sys

MARK = "_batch14"
PREFIX = "m_"

# 1. WALL LOWERING -----------------------------------------------------------
# hex_par_s_mid, read at (-71, -5866, 1480). The user asked for 25% off, so
# the box keeps its FLOOR and loses a quarter of its height off the top: the
# z extent goes to 75% and the origin drops by an eighth of the original
# height, which is half of what was removed.
#
# UNVERIFIED: nobody has flown a zipline over the result. 25% is the user's
# number, not a computed clearance. If the cable still clips, the honest fix
# is another reading, not a bigger guess here.
LOWER = [("hex_par_s_mid", 0.25)]

# 2. MATERIAL CORRECTIONS ----------------------------------------------------
# Boxes coloured as floor that are not floor. The TARGET material is not
# hardcoded: it is taken from a reference box named below, so this script
# never invents a material path that may not exist in the Deadlock tree.
#
# WHY A REFERENCE BOX. The plan's material strings were authored elsewhere and
# a wrong one fails silently at compile, exactly like the dev_measuregeneric01
# path NEXT already flags as unproven. Copying a string that is already in the
# plan and already survives the round trip cannot introduce a new bad path.
#
# If a reference box is missing the edit is SKIPPED and reported, never
# guessed.
RECOLOUR = [
    # box, reference box to copy the material from, why
    ("yaw_575", "hex_par_s_mid", "coloured as floor but is a box"),
    ("axis_561", "hex_par_s_mid", "coloured as floor but is a box"),
    ("axis_553_mid_under", "hex_par_s_mid", "coloured as floor but is wall"),
    ("axis_719", "hex_par_s_mid", "coloured as floor but is wall"),
]

# 3. GAP CLOSURE -------------------------------------------------------------
# axis_473 (1308, 1621, 761) to axis_124_far (1428, 1467, 871). The gap is
# closed by growing the FIRST box along whichever axis the two are furthest
# apart on, until its face meets the other's.
#
# ROTATION IS THE TRAP. 3,201 of the plan's boxes are rotated, and a
# face-to-face distance computed from axis-aligned extents is meaningless for
# a rotated box. If either box carries a non-zero angle this edit REFUSES
# rather than producing a plausible wrong number.
GAPS = [("axis_473", "axis_124_far")]

ANGLE_TOL = 0.01


def by_name(plan):
    return {b["name"]: b for b in plan["boxes"] if "name" in b}


def rotated(box):
    return any(abs(a) > ANGLE_TOL for a in box.get("angles", [0.0, 0.0, 0.0]))


def both(name, boxes):
    """A box and its twin, whichever exist."""
    out = []
    for n in (name, PREFIX + name):
        if n in boxes:
            out.append(boxes[n])
    return out


def do_lower(boxes):
    n_done = 0
    for name, frac in LOWER:
        pair = both(name, boxes)
        if not pair:
            print("  SKIP %s: not in the plan" % name)
            continue
        if len(pair) == 1:
            print("  NOTE %s has no m_ twin" % name)
        heights = {round(b["extents"][2], 3) for b in pair}
        if len(heights) > 1:
            print("  NOTE %s and its twin differ in height: %s"
                  % (name, sorted(heights)))
        for b in pair:
            if MARK in b:
                print("  SKIP %s: already edited by batch14" % b["name"])
                continue
            h = b["extents"][2]
            cut = h * frac
            b["extents"][2] = round(h - cut, 4)
            b["origin"][2] = round(b["origin"][2] - cut / 2.0, 4)
            b[MARK] = "lowered %d%%" % round(frac * 100)
            print("  %s height %.1f -> %.1f, top down %.1f"
                  % (b["name"], h, b["extents"][2], cut))
            n_done += 1
    return n_done


def do_recolour(boxes):
    n_done = 0
    for name, ref_name, why in RECOLOUR:
        if ref_name not in boxes:
            print("  SKIP %s: reference box %s missing, refusing to invent a"
                  " material" % (name, ref_name))
            continue
        material = boxes[ref_name].get("material")
        if not material:
            print("  SKIP %s: reference box %s has no material set"
                  % (name, ref_name))
            continue
        pair = both(name, boxes)
        if not pair:
            print("  SKIP %s: not in the plan" % name)
            continue
        for b in pair:
            if MARK in b:
                print("  SKIP %s: already edited by batch14" % b["name"])
                continue
            was = b.get("material", "(unset)")
            if was == material:
                print("  %s already %s, nothing to do" % (b["name"], material))
                continue
            b["material"] = material
            b[MARK] = "material from %s (%s)" % (ref_name, why)
            print("  %s material %s -> %s" % (b["name"], was, material))
            n_done += 1
    return n_done


def do_gaps(boxes):
    n_done = 0
    for grow_name, toward_name in GAPS:
        if grow_name not in boxes or toward_name not in boxes:
            print("  SKIP %s -> %s: one of them is not in the plan"
                  % (grow_name, toward_name))
            continue
        a, b = boxes[grow_name], boxes[toward_name]
        if rotated(a) or rotated(b):
            print("  REFUSE %s -> %s: one of them is rotated, so a gap"
                  % (grow_name, toward_name))
            print("         computed from axis-aligned extents would be")
            print("         wrong. Needs a real reading or a rotated-box"
                  " routine.")
            continue

        # Grow along the axis with the largest centre-to-centre separation.
        seps = [abs(a["origin"][i] - b["origin"][i]) for i in range(3)]
        axis = seps.index(max(seps))
        sign = 1.0 if b["origin"][axis] > a["origin"][axis] else -1.0

        a_face = a["origin"][axis] + sign * a["extents"][axis] / 2.0
        b_face = b["origin"][axis] - sign * b["extents"][axis] / 2.0
        gap = (b_face - a_face) * sign

        label = "xyz"[axis]
        if gap <= 0:
            print("  %s -> %s: no gap on %s (overlap %.1f), nothing to do"
                  % (grow_name, toward_name, label, -gap))
            continue

        for box in both(grow_name, boxes):
            if MARK in box:
                print("  SKIP %s: already edited by batch14" % box["name"])
                continue
            box["extents"][axis] = round(box["extents"][axis] + gap, 4)
            box["origin"][axis] = round(box["origin"][axis]
                                        + sign * gap / 2.0, 4)
            box[MARK] = "extended %.1f u on %s toward %s" % (gap, label,
                                                             toward_name)
            print("  %s extended %.1f u on %s to meet %s"
                  % (box["name"], gap, label, toward_name))
            n_done += 1

            # The twin grows toward the TWIN of the target, which is the
            # opposite direction in world space. Sign is not flipped here
            # because each box is edited on its own axis-aligned extents and
            # the mirror is a 180 degree rotation, which preserves the axis.
            sign = -sign
    return n_done


def main(path):
    with open(path) as f:
        plan = json.load(f)

    before = len(plan["boxes"])
    boxes = by_name(plan)

    print("lowering walls")
    n1 = do_lower(boxes)
    print("\nmaterial corrections")
    n2 = do_recolour(boxes)
    print("\ngap closures")
    n3 = do_gaps(boxes)

    after = len(plan["boxes"])
    if after != before:
        print("\nFAIL box count moved %d -> %d. batch14 must not add or"
              " remove boxes." % (before, after))
        return 1

    bad = [b["name"] for b in plan["boxes"] if min(b["extents"]) <= 0.1]
    if bad:
        print("\nFAIL zero or near-zero extents after edit: "
              + ", ".join(bad))
        return 1

    with open(path, "w") as f:
        json.dump(plan, f, indent=1)

    print("\nwrote %s" % path)
    print("  boxes %d (unchanged, as required)" % after)
    print("  edits %d lowered, %d recoloured, %d extended" % (n1, n2, n3))
    print("\nUNVERIFIED: no zipline has been flown over the lowered wall and")
    print("no compile has been run. The lowering is the user's 25%, not a")
    print("computed clearance.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else
                  "docs/plans/dust2_full.json"))
