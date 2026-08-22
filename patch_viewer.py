#!/usr/bin/env python3
"""patch_viewer.py - teaches the blockout walkthrough viewer to colour floors.

WHY THIS EXISTS
The viewer never reads the `material` field on a box. tileColor() returns
a fixed orange checker for every face of every solid, so setting
reflectivity_50 in the plan could not possibly change what is drawn. The
plan was right; the renderer was not looking.

WHAT IT CHANGES  (three edits, all inside the <script> block)

  1. prepare()   reads b.material and stores a boolean `floor` on the
                 prepared solid, true when the material name ends in
                 reflectivity_50, _70 or _90.
  2. tileColor() takes that flag and returns a grey checker instead of
                 the orange one. Same checker, same shading, so the LOD
                 banding and the face shading still read as before.
  3. the call    passes sol.floor through.

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

MARK = "function tileColor(shade, gx, gy, floor)"

EDITS = [
    (
        "    return { i, name:b.name||('box['+i+']'), o, e, h, R, cell, rad,",
        "    // Floors are told apart by material, set by floormat.py. Any of the\n"
        "    // brighter dev greys counts, so switching the constant in that script\n"
        "    // does not need a matching edit here.\n"
        "    const floor = typeof b.material === 'string' &&\n"
        "                  /reflectivity_(50|70|90)/.test(b.material);\n"
        "    return { i, name:b.name||('box['+i+']'), o, e, h, R, cell, rad, floor,",
    ),
    (
        "function tileColor(shade, gx, gy){\n"
        "  const checker = ((gx + gy) & 1) === 0;\n"
        "  const base = checker ? [198,101,42] : [154,74,29];",
        "function tileColor(shade, gx, gy, floor){\n"
        "  const checker = ((gx + gy) & 1) === 0;\n"
        "  // Grey for anything a player stands on, orange for everything else.\n"
        "  const base = floor ? (checker ? [166,168,170] : [124,126,128])\n"
        "                     : (checker ? [198,101,42]  : [154,74,29]);",
    ),
    (
        "                       col: tileColor(F.shade, iu, iv) });",
        "                       col: tileColor(F.shade, iu, iv, sol.floor) });",
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
            print("%s already patched" % path)
            continue

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
        print("%s patched, 3 edits" % path)

    return rc


if __name__ == "__main__":
    sys.exit(main())
