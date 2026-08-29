#!/usr/bin/env python3
"""Rename `target` to `exitpoint` on citadel_trigger_teleport entities.

WHY THIS EXISTS. batch16 now emits `exitpoint`, which is what citadel.fgd
says the class actually reads. But docs/plans/dust2_full.json is a COMMITTED
ARTIFACT, built by a run of the batch scripts that happened before the FGD
arrived, and it still carries four teleport triggers keyed on `target`. Two
ways to correct that:

  1. Re-run the whole chain - preclean.py batch13 batch17 batch18 batch14
     batch15 batch16 - and commit the new plan.
  2. Run this, which touches only the four entities that are wrong.

Option 1 is the honest one and should be done eventually. This exists because
it is small, reviewable, and does not risk a 4746-box plan changing in ways
nobody asked for on the way to fixing one keyvalue.

SAFE TO RUN TWICE. An entity that already has `exitpoint` is left alone, and
one carrying BOTH keys is reported as a problem rather than silently picked
between.

DELIBERATELY NARROW. Only citadel_trigger_teleport is touched.
trigger_catapult also uses `target` and that is CORRECT there - the FGD
confirms the catapult pairs with an info_target_server_only via `target`.
Renaming that would break the jump pads.

    python3 tools/fix_exitpoint.py [path/to/plan.json]

Exits 0 if the plan is correct at the end, 1 if something needs a human.
"""

import json
import sys

CLASS = "citadel_trigger_teleport"
OLD = "target"
NEW = "exitpoint"


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_full.json"
    with open(path) as f:
        plan = json.load(f)

    ents = plan.get("entities", [])
    hits = [e for e in ents if e.get("classname") == CLASS]
    if not hits:
        print("no %s in %s - nothing to do" % (CLASS, path))
        return 0

    renamed, already, problems = 0, 0, []
    for e in hits:
        props = e.get("properties") or {}
        name = e.get("name", "?")
        has_old, has_new = OLD in props, NEW in props

        if has_old and has_new:
            problems.append(
                "%s carries BOTH %s=%r and %s=%r. Cannot choose between them."
                % (name, OLD, props[OLD], NEW, props[NEW]))
            continue
        if has_new:
            already += 1
            print("  %-20s already on %s -> %s" % (name, NEW, props[NEW]))
            continue
        if not has_old:
            problems.append("%s has neither %s nor %s - it teleports nowhere"
                            % (name, OLD, NEW))
            continue

        # Rebuild the dict rather than pop-and-insert, so the key lands in
        # the same position and the diff stays readable.
        e["properties"] = {(NEW if k == OLD else k): v
                           for k, v in props.items()}
        renamed += 1
        print("  %-20s %s -> %s = %s" % (name, OLD, NEW, props[OLD]))

    # Every destination must exist, or the rename has quietly created a
    # dangling reference that preflight would catch later and further away.
    known = {(e.get("properties") or {}).get("targetname", "") for e in ents}
    known |= {e.get("name", "") for e in ents}
    known.discard("")
    for e in hits:
        dest = (e.get("properties") or {}).get(NEW, "")
        if dest and dest not in known:
            problems.append("%s points at %s, which nothing defines"
                            % (e.get("name", "?"), dest))

    print("\n%d renamed, %d already correct, %d teleport trigger(s) total"
          % (renamed, already, len(hits)))

    if problems:
        print("\nPROBLEMS - plan NOT written:")
        for p in problems:
            print("  " + p)
        return 1

    if renamed:
        with open(path, "w") as f:
            json.dump(plan, f, indent=1)
            f.write("\n")
        print("wrote %s" % path)
        print("\nNow re-run preflight, and expect the teleporter pair to "
              "still resolve - REF_KEYS knows about exitpoint.")
    else:
        print("plan already correct, not rewritten")
    return 0


if __name__ == "__main__":
    sys.exit(main())
