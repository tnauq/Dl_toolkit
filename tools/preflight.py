#!/usr/bin/env python3
"""preflight.py - what a compiler is likely to reject, checked before anyone
compiles.

    python3 tools/preflight.py [docs/plans/dust2_full.json]

Nothing here has ever been compiled, so nobody knows what resourcecompiler
will say. This file is a guess at the failures worth catching first, based on
what breaks Source maps generally. It is a SCREEN, not a guarantee: passing it
means the obvious faults are absent, not that the map builds.

WHAT IT CHECKS, and why each one is here.

1.  DUPLICATE NAMES. Two boxes with one name is how this project lost four
    boxes for three days: removal filters by name, so a duplicate takes two
    out where one went in.

2.  DUPLICATE TARGETNAMES. Two entities answering to the same targetname
    means an output fires at both. Legal, occasionally deliberate, usually a
    mistake - so this reports rather than fails.

3.  DANGLING REFERENCES. A `target`, `final_objective` or `sub_objective_N`
    naming something that does not exist. The pad that launches at nothing
    and the proxy wired to a walker that was renamed both look fine until
    the game does nothing at all.

4.  EMPTY MODEL on a classname that carries a model elsewhere in the plan.
    The patron is the known case. An empty model path is a likely hard
    failure and an easy one to miss, since the entity is otherwise complete.

5.  DEGENERATE AND ABSURD GEOMETRY. Zero or negative extents, non-finite
    numbers, coordinates far outside the map's own bounds. batch14 catches
    zero extents already; this catches the rest and catches them everywhere
    rather than only in the boxes batch14 edits.

6.  UNPAIRED MIRRORS. Every authored thing should have a twin unless it sits
    on the mirror point. A missing twin means one team has something the
    other does not, which is a gameplay bug no compiler will mention.

WHAT IT DOES NOT CHECK, and why.

    LEAKS. In Source 1 a map had to be sealed against the void or vbsp
    refused it - the classic `**** leaked ****` with an entity name and
    coordinates. Source 2 does not work that way, so an open-topped map is
    not automatically an error here. A hole in a wall is still a bug, but it
    is a GAMEPLAY bug, and the enclosure sampling in batch18 is the right
    place for it. Do not read a pass here as "no holes".

    MATERIALS AND MODEL PATHS. Whether a .vmat or .vmdl actually exists is a
    question about the game's content tree, which CI does not have. All this
    can say is which paths are referenced - printed at the end so they can be
    eyeballed against a real install.
"""

import json
import math
import sys
from collections import Counter, defaultdict

X_PLANE = 460.1
Y_PLANE = 6085.05
PREFIX = "m_"

REF_KEYS = ("target", "final_objective", "sub_objective_1",
            "sub_objective_2", "sub_objective_3", "sub_objective_4")

# Coordinates beyond this are almost certainly a units mistake rather than a
# real position. The map's own extent is about 11000 x 25000.
ABSURD = 100000.0


def finite(v):
    return isinstance(v, (int, float)) and math.isfinite(v)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_full.json"
    with open(path) as f:
        plan = json.load(f)

    boxes = plan.get("boxes", [])
    ents = plan.get("entities", [])
    fail = []
    warn = []
    log = []

    log.append("preflight on %s" % path)
    log.append("  %d boxes, %d entities, %d paths"
               % (len(boxes), len(ents), len(plan.get("paths", []))))
    log.append("")

    # 1. duplicate names
    for label, items in (("box", boxes), ("entity", ents)):
        counts = Counter(b.get("name", "") for b in items)
        dupes = {n: c for n, c in counts.items() if c > 1 and n}
        if dupes:
            fail.append("%d duplicate %s name(s): %s"
                        % (len(dupes), label,
                           ", ".join(sorted(dupes))[:200]))
        else:
            log.append("no duplicate %s names" % label)

    # 2. duplicate targetnames
    tn = Counter()
    for e in ents:
        t = (e.get("properties") or {}).get("targetname", "")
        if t:
            tn[t] += 1
    shared = {n: c for n, c in tn.items() if c > 1}
    if shared:
        warn.append("targetname(s) used by more than one entity: %s"
                    % ", ".join("%s x%d" % (n, c)
                                for n, c in sorted(shared.items()))[:200])
    else:
        log.append("no shared targetnames")

    # 3. dangling references
    known = {(e.get("properties") or {}).get("targetname", "")
             for e in ents}
    known |= {e.get("name", "") for e in ents}
    known.discard("")
    dangling = []
    for e in ents:
        props = e.get("properties") or {}
        for k in REF_KEYS:
            v = props.get(k, "")
            if v and v not in known:
                dangling.append("%s.%s -> %s" % (e.get("name", "?"), k, v))
    if dangling:
        fail.append("%d reference(s) to entities that do not exist: %s"
                    % (len(dangling), "; ".join(sorted(dangling))[:240]))
    else:
        log.append("every target, final_objective and sub_objective "
                   "resolves")

    # 4. empty model where the class uses one
    models = defaultdict(set)
    for e in ents:
        props = e.get("properties") or {}
        if "model" in props:
            models[e["classname"]].add(props["model"])
    for e in ents:
        props = e.get("properties") or {}
        if "model" in props and not props["model"]:
            others = {m for m in models[e["classname"]] if m}
            if others:
                fail.append("%s (%s) has no model, but other %s entities use "
                            "%s" % (e.get("name", "?"), e["classname"],
                                    e["classname"], sorted(others)[0]))
            else:
                warn.append("%s (%s) has no model, and no entity of that "
                            "class in the plan sets one"
                            % (e.get("name", "?"), e["classname"]))

    # 5. degenerate and absurd geometry
    bad_ext = []
    bad_num = []
    for b in boxes:
        e = b.get("extents", [])
        o = b.get("origin", [])
        if len(e) != 3 or min(e) <= 0.05:
            bad_ext.append(b.get("name", "?"))
        if not all(finite(v) for v in list(e) + list(o)):
            bad_num.append(b.get("name", "?"))
        elif max(abs(v) for v in o) > ABSURD:
            bad_num.append(b.get("name", "?"))
    for e in ents:
        o = e.get("origin", [])
        if not o or not all(finite(v) for v in o):
            bad_num.append(e.get("name", "?"))
        m = e.get("mesh")
        if m and min(m.get("extents", [1, 1, 1])) <= 0.05:
            bad_ext.append(e.get("name", "?") + " (mesh)")
    if bad_ext:
        fail.append("%d zero or near-zero extent(s): %s"
                    % (len(bad_ext), ", ".join(sorted(bad_ext))[:200]))
    if bad_num:
        fail.append("%d non-finite or absurd coordinate(s): %s"
                    % (len(bad_num), ", ".join(sorted(bad_num))[:200]))
    if not bad_ext and not bad_num:
        log.append("no degenerate extents or absurd coordinates")

    # 6. unpaired mirrors
    def on_plane(o):
        return (abs(o[0] - X_PLANE) < 2.0 and abs(o[1] - Y_PLANE) < 2.0)

    for label, items in (("box", boxes), ("entity", ents)):
        names = {b.get("name", "") for b in items}
        at = set()
        for b in items:
            o = b.get("origin", [])
            if len(o) == 3 and all(finite(v) for v in o):
                at.add((round(o[0], 0), round(o[1], 0), round(o[2], 0)))
        lonely = []
        for b in items:
            n = b.get("name", "")
            if not n or n.startswith(PREFIX):
                continue
            o = b.get("origin", [0, 0, 0])
            if len(o) == 3 and on_plane(o):
                continue
            # A twin is m_<name>, a team-word swap, OR simply something
            # sitting at the mirrored position under another name. The
            # hexagon room is the reason for that last case: it is centred
            # on the mirror point and its pieces reflect onto EACH OTHER, so
            # a name-only test called 63 of them orphans when the room is
            # perfectly symmetric.
            if PREFIX + n in names:
                continue
            if any(w in n for w in ("rebels", "combine")):
                sw = (n.replace("rebels", "combine") if "rebels" in n
                      else n.replace("combine", "rebels"))
                if sw in names:
                    continue
            if len(o) == 3:
                key = (round(2 * X_PLANE - o[0], 0),
                       round(2 * Y_PLANE - o[1], 0), round(o[2], 0))
                if key in at:
                    continue
            lonely.append(n)
        if lonely:
            warn.append("%d %s(es) with no mirror twin: %s"
                        % (len(lonely), label, ", ".join(sorted(lonely))[:240]))
        else:
            log.append("every off-centre %s has a twin" % label)

    # references, for eyeballing against a real install
    mats = Counter(b.get("material", "") for b in boxes)
    mdls = Counter((e.get("properties") or {}).get("model", "")
                   for e in ents
                   if (e.get("properties") or {}).get("model"))
    log.append("")
    log.append("materials referenced (existence NOT checked):")
    for m, c in mats.most_common():
        log.append("  %-52s %d" % (m or "(none)", c))
    if mdls:
        log.append("models referenced (existence NOT checked):")
        for m, c in mdls.most_common():
            log.append("  %-52s %d" % (m, c))

    classes = Counter(e.get("classname", "?") for e in ents)
    log.append("")
    log.append("entity classes:")
    for c, n in sorted(classes.items()):
        log.append("  %-40s %d" % (c, n))

    print("\n".join(log))
    if warn:
        print("")
        print("WARNINGS, worth a look, not blocking:")
        for w in warn:
            print("  " + w)
    if fail:
        print("")
        for f in fail:
            print("::error::preflight: " + f)
        print("")
        print("%d problem(s). These are the ones most likely to stop a "
              "compile." % len(fail))
        sys.exit(1)
    print("")
    print("preflight clean. THIS IS NOT A COMPILE - it means the obvious")
    print("faults are absent, nothing more.")


if __name__ == "__main__":
    main()
