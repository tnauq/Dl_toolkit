#!/usr/bin/env python3
"""preclean - remove batch16's entities before batch13 rebuilds its own.

RUNS FIRST, before everything.

    SCRIPTS: preclean.py batch13.py batch17.py batch18.py batch14.py
             batch15.py batch16.py

WHY THIS EXISTS. batch13 rebuilds its entity set from scratch and fails on a
duplicate name. batch16 strips its own work and rebuilds it too - but batch16
runs LAST, so on any run where the two would collide, batch13 dies first and
batch16 never executes. The plan then keeps the stale entity forever and
every subsequent run dies in the same place: the script that would clean up
is behind the failure.

That happened with `midboss_shield`. Renaming batch16's copy fixed the
collision for new runs but could not fix the committed one, because the
committed one is still sitting there when batch13 looks.

So: strip anything carrying batch16's mark up front. batch16 recreates all of
it from its own tables at the end of the same run, which is exactly what it
does anyway on a rerun - this only moves the strip earlier, where it can do
some good.

This also removes the ordering trap for good. Any future name batch16 shares
with batch13 now resolves in batch13's favour during the run, and batch16
puts its own back afterwards.

NOT TOUCHED: batch17's and batch18's marks. Those two scripts remove existing
BOXES and stash the originals to restore, so stripping their work from
outside would skip the restore and quietly shrink the map.

    python3 preclean.py [docs/plans/dust2_full.json]
"""

import json
import sys

MARK = "_batch16"


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_full.json"
    with open(path) as f:
        plan = json.load(f)

    ents = plan.get("entities", [])
    before = len(ents)
    kept = [e for e in ents if not e.get(MARK)]
    dropped = before - len(kept)

    boxes = len(plan.get("boxes", []))
    plan["entities"] = kept

    if dropped:
        names = sorted(e.get("name", "?") for e in ents if e.get(MARK))
        print("preclean: removed %d entity(ies) marked %s" % (dropped, MARK))
        print("  %s" % ", ".join(names[:12]))
        if len(names) > 12:
            print("  ... and %d more" % (len(names) - 12))
        print("  batch16 rebuilds all of these at the end of this run")
    else:
        print("preclean: nothing marked %s in the plan; nothing to do" % MARK)

    if len(plan.get("boxes", [])) != boxes:
        print("::error::preclean touched the box list")
        sys.exit(1)
    print("preclean: entities %d -> %d, boxes %d unchanged"
          % (before, len(kept), boxes))

    with open(path, "w") as f:
        json.dump(plan, f, indent=1)


if __name__ == "__main__":
    main()
