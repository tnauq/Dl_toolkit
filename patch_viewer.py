#!/usr/bin/env python3
"""patch_viewer.py - teaches the blockout walkthrough viewer to colour floors.

WHY THIS EXISTS
The viewer never reads the `material` field on a box. tileColor() returns
a fixed orange checker for every face of every solid, so setting
reflectivity_50 in the plan could not possibly change what is drawn. The
plan was right; the renderer was not looking.

WHAT IT CHANGES  (three edits, all inside the <script> block)

  1. prepare()   reads b.material and stores a boolean `floor` on the
                 prepared solid, true for dev_measure* or for
                 reflectivity_50, _70 or _90.
  2. tileColor() takes that flag and returns flat dev grey instead of the
                 orange checker. The checker survives as a 7-point
                 wobble, so the fill reads as one flat surface and the
                 grid line carries the scale, as on dev_measuregeneric.
  3. the call    passes sol.floor through, and puts it on the quad.
  4. the seam    goes light on grey and stays dark on orange. A dark seam
                 on a dark grey fill is invisible, which would have left
                 the floor a flat slab with no grid at all.

The viewer stays read-only on the plan: this adds a derived field on the
prepared copy, exactly like `rad` and `aabb` already are.

Idempotent: it checks for the patched text first and exits 0 if it is
already applied.

Usage:
  python3 patch_viewer.py                 # finds the viewer by content
  python3 patch_viewer.py path/to/x.html  # or point it at the file
"""

import os
import sys

# A v2 patch is identified by the seam-line edit, which only v2 has. The
# old marker was the tileColor signature, which v1 ALSO has, so a v1 file
# was reported as already patched and never upgraded. That is what left
# the viewer testing for reflectivity_50 after the material became
# dev_measuregeneric01: patched, reading the material, matching nothing.
MARK = "q.floor ? 'rgba(176,180,184,.42)'"

# v1 text -> the original text it replaced, so a v1 file can be put back
# to stock and then re-patched with the current EDITS below.
REVERTS = [
    (
        "    // Floors are told apart by material, set by floormat.py. Any of the\n"
        "    // brighter dev greys counts, so switching the constant in that script\n"
        "    // does not need a matching edit here.\n"
        "    const floor = typeof b.material === 'string' &&\n"
        "                  /reflectivity_(50|70|90)/.test(b.material);\n"
        "    return { i, name:b.name||('box['+i+']'), o, e, h, R, cell, rad, floor,",
        "    return { i, name:b.name||('box['+i+']'), o, e, h, R, cell, rad,",
    ),
    (
        "function tileColor(shade, gx, gy, floor){\n"
        "  const checker = ((gx + gy) & 1) === 0;\n"
        "  // Grey for anything a player stands on, orange for everything else.\n"
        "  const base = floor ? (checker ? [166,168,170] : [124,126,128])\n"
        "                     : (checker ? [198,101,42]  : [154,74,29]);",
        "function tileColor(shade, gx, gy){\n"
        "  const checker = ((gx + gy) & 1) === 0;\n"
        "  const base = checker ? [198,101,42] : [154,74,29];",
    ),
    (
        "                       col: tileColor(F.shade, iu, iv, sol.floor) });",
        "                       col: tileColor(F.shade, iu, iv) });",
    ),
]

EDITS = [
    (
        "    return { i, name:b.name||('box['+i+']'), o, e, h, R, cell, rad,",
        "    // Floors are told apart by material, set by floormat.py. Any of the\n"
        "    // brighter dev greys counts, so switching the constant in that script\n"
        "    // does not need a matching edit here.\n"
        "    const floor = typeof b.material === 'string' &&\n"
        "                  /measure|reflectivity_(50|70|90)/.test(b.material);\n"
        "    return { i, name:b.name||('box['+i+']'), o, e, h, R, cell, rad, floor,",
    ),
    (
        "function tileColor(shade, gx, gy){\n"
        "  const checker = ((gx + gy) & 1) === 0;\n"
        "  const base = checker ? [198,101,42] : [154,74,29];",
        "function tileColor(shade, gx, gy, floor){\n"
        "  const checker = ((gx + gy) & 1) === 0;\n"
        "  // Floors: flat dev grey with a barely-there checker, so the grid line\n"
        "  // does the work rather than the fill, matching dev_measuregeneric.\n"
        "  const base = floor ? (checker ? [62,59,57] : [55,52,50])\n"
        "                     : (checker ? [198,101,42] : [154,74,29]);",
    ),
    (
        "                       col: tileColor(F.shade, iu, iv) });",
        "                       col: tileColor(F.shade, iu, iv, sol.floor),\n"
        "                       floor: sol.floor });",
    ),
    (
        "      ctx.strokeStyle = 'rgba(40,18,6,.55)';",
        "      // On orange the seam is a dark shadow line; on dev grey it has to be\n"
        "      // LIGHTER than the fill or the grid disappears into the surface.\n"
        "      ctx.strokeStyle = q.floor ? 'rgba(176,180,184,.42)' : 'rgba(40,18,6,.55)';",
    ),
]


def find_viewer():
    hits = []
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules")]
        for fn in files:
            if not fn.endswith((".html", ".htm")):
                continue
            p = os.path.join(root, fn)
            try:
                with open(p, encoding="utf-8") as f:
                    t = f.read()
            except (OSError, UnicodeDecodeError):
                continue
            if "function tileColor(" in t and "blockout walkthrough" in t:
                hits.append(p)
    return hits


def main():
    if len(sys.argv) > 1:
        paths = sys.argv[1:]
    else:
        paths = find_viewer()
        if not paths:
            print("no viewer found: no .html here contains tileColor()")
            return 1
        print("found: " + ", ".join(paths))

    rc = 0
    for path in paths:
        with open(path, encoding="utf-8") as f:
            text = f.read()

        if MARK in text:
            print("%s already patched (current version)" % path)
            continue

        reverted = 0
        for old, orig in REVERTS:
            if old in text:
                text = text.replace(old, orig, 1)
                reverted += 1
        if reverted:
            print("%s had an older patch, reverting %d edits first"
                  % (path, reverted))

        missing = [old for old, _ in EDITS if text.count(old) != 1]
        if missing:
            print("%s NOT patched, these anchors did not match exactly once:" % path)
            for old in missing:
                print("  %r (%d matches)" % (old.splitlines()[0], text.count(old)))
            rc = 1
            continue

        for old, new in EDITS:
            text = text.replace(old, new, 1)

        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        print("%s patched, %d edits" % (path, len(EDITS)))

    return rc


if __name__ == "__main__":
    sys.exit(main())
