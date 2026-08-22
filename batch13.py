#!/usr/bin/env python3
"""batch13 — objectives and lane paths into docs/plans/dust2_full.json.

THE FIRST BATCH THAT ADDS GAMEPLAY RATHER THAN GEOMETRY. Everything here is
entity and path data; no box is touched, so the 4,179 count does not move.

WHAT IT ADDS
    entities  guardians, walkers, patrons, shrines, trooper spawns, shops
    paths     lane_marker_path, one per lane per LaneSlot

MIRRORING. Same proper rotation as mirror.py, about the vertical line through
(460.1, 6085.05):

    x' = 920.2   - x
    y' = 12170.1 - y
    z' = z
    yaw' = yaw + 180

Every entity and path below is authored ONCE, for team 2, and the team 3 half
is generated. Twins take the "m_" prefix, and teamnumber 2 becomes 3. Do not
author the far half by hand — that is what put the box plan out of symmetry
before.

RERUNNABLE, like every batch script here: it deletes everything it previously
added, by name prefix, and rebuilds. Names are the key, so editing a waypoint
below and rerunning is safe.

STATUS OF THE NUMBERS IN THIS FILE. The classnames and keyvalue sets are read
from dl_example.vmap and are correct. THE COORDINATES ARE NOT REAL. They are
placeholders derived from the two existing spawns so the file runs end to end
and the emitter can be exercised; every one is marked TODO. Replace them with
crosshair readings from the viewer's `copy pos` before believing anything the
game does with this map.

    python3 batch13.py [docs/plans/dust2_full.json]
"""

import json
import sys

X_PLANE = 460.1
Y_PLANE = 12170.1 / 2.0     # 6085.05
PREFIX = "m_"
MARK = "_batch13"

# Teams. 2 is amber, 3 is sapphire, following the plan's existing spawns.
TEAM_A = "2"
TEAM_B = "3"


def norm(a):
    while a > 180.0:
        a -= 360.0
    while a <= -180.0:
        a += 360.0
    return round(a, 4)


def mirror_point(p):
    return [round(2.0 * X_PLANE - p[0], 4),
            round(2.0 * Y_PLANE - p[1], 4),
            p[2]]


def mirror_angles(a):
    return [a[0], norm(a[1] + 180.0), a[2]]


def flip_team(props):
    """Swap teamnumber on the mirrored copy. Anything else is left alone."""
    out = dict(props)
    if out.get("teamnumber") == TEAM_A:
        out["teamnumber"] = TEAM_B
    elif out.get("teamnumber") == TEAM_B:
        out["teamnumber"] = TEAM_A
    return out


# ---------------------------------------------------------------------------
# LANES. One entry per lane. Nodes run from the team-2 base OUTWARD; the
# mirrored copy therefore runs from the team-3 base outward, and the two meet
# in the middle, which is what a lane is.
#
# SLOTS. dl_example carries LaneSlot 0, 1 and 2 per lane: three parallel files
# of troopers. Rather than author three routes by hand, one CENTRE route is
# given per lane and the slots are offset sideways by SLOT_OFFSET. That is an
# assumption about how Valve uses the slots, not a fact read from the file.
#
# TODO: every coordinate below is a placeholder.
# ---------------------------------------------------------------------------
SLOT_OFFSET = 96.0          # units between parallel trooper files
SLOTS = (0, 1, 2)

LANES = [
    {
        "lane": "1",
        # TODO placeholder route: straight north from the team-2 spawn.
        "route": [
            [25.0, -530.0, 435.0],
            [25.0, 1500.0, 435.0],
            [25.0, 3500.0, 435.0],
            [25.0, 5500.0, 435.0],
        ],
    },
]


# ---------------------------------------------------------------------------
# OBJECTIVES AND SPAWNS. Authored for team 2 only.
#
# Keyvalue sets are the ones dl_example actually uses. Empty strings are kept
# where dl_example keeps them, because a missing key and an empty key are not
# obviously the same thing to the game and the fixture is the only evidence.
#
# TODO: every origin below is a placeholder.
# ---------------------------------------------------------------------------
OBJECTIVES = [
    {
        "name": "guardian_l1",
        "classname": "npc_barrack_boss",
        "origin": [25.0, 2000.0, 435.0],
        "angles": [0.0, 90.0, 0.0],
        "properties": {
            "targetname": "amber_guardian_lane1",
            "vscripts": "",
            "teamnumber": TEAM_A,
            "lanenum": "1",
            "BackdoorProtectionTrigger": "",
            "CoverGroupID": "",
            "LaneSide": "0",
        },
    },
    {
        "name": "walker_l1",
        "classname": "npc_boss_tier2",
        "origin": [25.0, 3200.0, 435.0],
        "angles": [0.0, 90.0, 0.0],
        "properties": {
            "targetname": "amber_walker_lane1",
            "vscripts": "",
            "teamnumber": TEAM_A,
            "lanenum": "1",
            "BossName": "amber_walker_lane1",
            "CoverGroupID": "",
            "subclass_name": "npc_boss_tier2",
        },
    },
    {
        "name": "trooper_spawn_l1",
        "classname": "info_trooper_spawn",
        "origin": [25.0, -300.0, 435.0],
        "angles": [0.0, 90.0, 0.0],
        "properties": {
            "targetname": "",
            "vscripts": "",
            "teamnumber": TEAM_A,
            "lanenum": "1",
            "TrooperLevel": "4",
        },
    },
]


def strip_previous(plan):
    """Remove everything a previous run of this script added."""
    def mine(x):
        return x.get(MARK) is True

    before = (len(plan.get("entities", [])), len(plan.get("paths", [])))
    plan["entities"] = [e for e in plan.get("entities", []) if not mine(e)]
    plan["paths"] = [p for p in plan.get("paths", []) if not mine(p)]
    after = (len(plan["entities"]), len(plan["paths"]))
    if before != after:
        print("removed %d entities and %d paths from a previous run"
              % (before[0] - after[0], before[1] - after[1]))


def build_entities():
    out = []
    for spec in OBJECTIVES:
        e = {
            "name": spec["name"],
            "classname": spec["classname"],
            "origin": [round(v, 4) for v in spec["origin"]],
            "angles": list(spec["angles"]),
            "properties": dict(spec["properties"]),
            MARK: True,
        }
        out.append(e)

        t = json.loads(json.dumps(e))
        t["name"] = PREFIX + spec["name"]
        t["origin"] = mirror_point(spec["origin"])
        t["angles"] = mirror_angles(spec["angles"])
        t["properties"] = flip_team(spec["properties"])
        tn = t["properties"].get("targetname", "")
        if tn:
            t["properties"]["targetname"] = PREFIX + tn
        for k in ("BossName",):
            if t["properties"].get(k):
                t["properties"][k] = PREFIX + t["properties"][k]
        out.append(t)
    return out


def offset_route(route, slot):
    """Shift a route sideways for its LaneSlot.

    The offset is perpendicular to the segment the node sits on, in the XY
    plane, so a route that turns keeps its files parallel through the corner
    rather than crossing over. Straight routes get a plain sideways shift.
    """
    # Slots are centred on the authored route: with three slots the offsets
    # are -1, 0, +1 times SLOT_OFFSET, so the middle file walks the line you
    # actually drew and the route stays the centre of the lane.
    shift = (slot - (len(SLOTS) - 1) / 2.0) * SLOT_OFFSET
    if abs(shift) < 1e-9:
        return [list(p) for p in route]

    out = []
    n = len(route)
    for i, p in enumerate(route):
        a = route[max(0, i - 1)]
        b = route[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = (dx * dx + dy * dy) ** 0.5
        if length < 1e-6:
            out.append(list(p))
            continue
        # Left normal of the direction of travel.
        nx, ny = -dy / length, dx / length
        out.append([round(p[0] + nx * shift, 4),
                    round(p[1] + ny * shift, 4),
                    p[2]])
    return out


def make_path(name, lane, slot, route):
    return {
        "name": name,
        "classname": "lane_marker_path",
        "origin": [round(v, 4) for v in route[0]],
        "angles": [0.0, 0.0, 0.0],
        "properties": {
            "targetname": "",
            "vscripts": "",
            "lanenum": lane,
            "LaneSlot": str(slot),
        },
        "interpolation_type": 1,
        "closed_loop": False,
        "nodes": [{"classname": "path_node_generic",
                   "origin": [round(v, 4) for v in p]} for p in route],
        MARK: True,
    }


def build_paths():
    out = []
    for spec in LANES:
        lane = spec["lane"]
        for slot in SLOTS:
            route = offset_route(spec["route"], slot)
            name = "lane%s_slot%d" % (lane, slot)
            out.append(make_path(name, lane, slot, route))

            mirrored = [mirror_point(p) for p in route]
            out.append(make_path(PREFIX + name, lane, slot, mirrored))
    return out


def check(plan):
    """Cheap sanity, before anything expensive downstream."""
    bad = 0
    for p in plan["paths"]:
        if len(p["nodes"]) < 2:
            print("FAIL %s: %d node(s)" % (p["name"], len(p["nodes"])))
            bad += 1
    names = [e.get("name") for e in plan["entities"] if e.get("name")]
    names += [p.get("name") for p in plan["paths"]]
    dupes = {n for n in names if names.count(n) > 1}
    if dupes:
        print("FAIL duplicate names: %s" % sorted(dupes))
        bad += 1

    # Symmetry: every authored thing must have exactly one twin.
    for coll in ("entities", "paths"):
        mine = [x for x in plan[coll] if x.get(MARK)]
        half = {x["name"] for x in mine if not x["name"].startswith(PREFIX)}
        twin = {x["name"][len(PREFIX):] for x in mine
                if x["name"].startswith(PREFIX)}
        if half != twin:
            print("FAIL %s asymmetric: %s" % (coll, sorted(half ^ twin)))
            bad += 1
    return bad


def main(path):
    with open(path) as f:
        plan = json.load(f)

    plan.setdefault("entities", [])
    plan.setdefault("paths", [])
    strip_previous(plan)

    ents = build_entities()
    paths = build_paths()
    plan["entities"].extend(ents)
    plan["paths"].extend(paths)

    bad = check(plan)
    if bad:
        print("\n%d problem(s); nothing written" % bad)
        return 1

    with open(path, "w") as f:
        json.dump(plan, f, indent=1)
        f.write("\n")

    nodes = sum(len(p["nodes"]) for p in paths)
    print("wrote %s" % path)
    print("  boxes    %d (untouched)" % len(plan["boxes"]))
    print("  entities %d (+%d)" % (len(plan["entities"]), len(ents)))
    print("  paths    %d (+%d), %d nodes" % (len(plan["paths"]), len(paths), nodes))
    print("\nEVERY COORDINATE IN THIS RUN IS A PLACEHOLDER. See the module")
    print("docstring. Replace with viewer `copy pos` readings before use.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else
                  "docs/plans/dust2_full.json"))
