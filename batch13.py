#!/usr/bin/env python3
"""batch13 — objectives and lane paths into docs/plans/dust2_full.json.

THE FIRST BATCH THAT ADDS GAMEPLAY RATHER THAN GEOMETRY. Everything here is
entity and path data; no box is touched, so the 4,179 count does not move.

WHAT IT ADDS
    entities  guardians, walkers, trooper spawns          (team, mirrored)
    camps     info_neutral_trooper_camp + its spawns      (NEUTRAL, see below)
    breakables citadel_breakable_prop, item_crate_spawn   (NEUTRAL)
    brushes   trigger_item_shop and friends, with a volume
    paths     lane_marker_path, one per lane per LaneSlot
              citadel_zipline_path, same machinery

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

# NEUTRAL things still get a mirrored twin — the layout is rotationally
# symmetric, so a jungle camp on one half wants its opposite number — but
# teamnumber is NOT flipped, because there is nothing to flip. Camps and
# breakables belong to no one.


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
# ZIPLINES. Same CMapPath machinery as a lane: keyvalues say what it is, the
# node list says where it goes. Troopers ride one INTO the lane before they
# walk it, so a zipline route roughly parallels its lane at height.
#
# TODO: placeholder route.
# ---------------------------------------------------------------------------
ZIPLINES = [
    {
        "lane": "1",
        "route": [
            [25.0, -530.0, 900.0],
            [25.0, 2500.0, 900.0],
            [25.0, 5500.0, 900.0],
        ],
        "properties": {
            "targetname": "zip_lane1",
            "vscripts": "",
            "lane_number": "1",
            "radius": "2",
            "slack": "0",
            "particle_spacing": "512",
            "static_collision": "0",
            "color_tint": "255 216 0",
            "start_active": "1",
            "effect_name":
                "particles/entity/path_particle_cable_default.vpcf",
        },
    },
]


# ---------------------------------------------------------------------------
# NEUTRAL CAMPS. A camp is one info_neutral_trooper_camp plus N
# info_neutral_trooper_spawn, tied together by CampName — a plain string, like
# every other link in this map format. subclass_name picks the camp tier.
#
# TODO: placeholder origins.
# ---------------------------------------------------------------------------
CAMPS = [
    {
        "name": "camp_west_weak",
        "camp_name": "west_weak_neutrals",
        "origin": [-1200.0, 2400.0, 435.0],
        "subclass": "neutral_camp_weak",
        "trooper_type": "1",
        "initial_delay": "120",
        "interval": "120",
        # Offsets from the camp origin, one per creature.
        "spawns": [[-64.0, 0.0, 0.0], [64.0, 0.0, 0.0], [0.0, 96.0, 0.0]],
    },
]


# ---------------------------------------------------------------------------
# BREAKABLES. Point entities with a model. citadel_breakable_prop covers
# crates and the golden statues; item_crate_spawn is the soul crate.
#
# TODO: placeholder origins, and the model paths are UNCONFIRMED against the
# Deadlock tree — no run so far could have caught a bad one, because
# dmxconvert only moves the string.
# ---------------------------------------------------------------------------
BREAKABLES = [
    {
        "name": "crate_west_1",
        "classname": "citadel_breakable_prop",
        "origin": [-1400.0, 1800.0, 435.0],
        "properties": {"targetname": "", "vscripts": ""},
    },
]


# ---------------------------------------------------------------------------
# BRUSH ENTITIES. A volume, not a point: the entity carries a child mesh,
# emitted INLINE in its children exactly as dl_example does. `extents` is the
# size of the volume and `mesh_origin` its offset from the entity origin,
# normally zero.
#
# Do NOT set a `model` keyvalue here. In dl_example a brush entity has a child
# mesh and no model; a destroyable_building has a model and NO children. The
# maps\...\unnamed_*.vmdl values seen on some brush entities are written by
# the compiler on export, not authored.
#
# TODO: placeholder origin and size.
# ---------------------------------------------------------------------------
BRUSHES = [
    {
        "name": "shop_base",
        "classname": "trigger_item_shop",
        "origin": [400.0, -200.0, 435.0],
        "angles": [0.0, 0.0, 0.0],
        "extents": [256.0, 256.0, 192.0],
        "mesh_origin": [0.0, 0.0, 0.0],
        "properties": {
            "targetname": "amber_base_shop_item_trigger",
            "vscripts": "",
            "parentname": "",
            "StartDisabled": "0",
            "spawnflags": "4097",
            "teamnumber": TEAM_A,
            "AudioOffset": "-0.25 22 50",
        },
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


def twin_of(e, neutral=False):
    """The mirrored copy of an entity dict."""
    t = json.loads(json.dumps(e))
    t["name"] = PREFIX + e["name"]
    t["origin"] = mirror_point(e["origin"])
    t["angles"] = mirror_angles(e.get("angles", [0.0, 0.0, 0.0]))
    if e.get("mesh"):
        t["mesh"] = json.loads(json.dumps(e["mesh"]))
        t["mesh"]["angles"] = mirror_angles(e["mesh"].get("angles",
                                                          [0.0, 0.0, 0.0]))
    props = dict(e.get("properties", {}))
    if not neutral:
        props = flip_team(props)
    for k in ("targetname", "BossName", "CampName"):
        if props.get(k):
            props[k] = PREFIX + props[k]
    t["properties"] = props
    return t


def build_camps():
    """A camp and its creatures. CampName is the only link between them."""
    out = []
    for spec in CAMPS:
        camp = {
            "name": spec["name"],
            "classname": "info_neutral_trooper_camp",
            "origin": [round(v, 4) for v in spec["origin"]],
            "angles": [0.0, 0.0, 0.0],
            "properties": {
                "targetname": "",
                "vscripts": "",
                "CampName": spec["camp_name"],
                "ENeutralTrooperType": spec["trooper_type"],
                "subclass_name": spec["subclass"],
                "InitialSpawnDelayInSeconds": spec["initial_delay"],
                "SpawnIntervalInSeconds": spec["interval"],
            },
            MARK: True,
        }
        out.append(camp)
        out.append(twin_of(camp, neutral=True))

        for i, off in enumerate(spec["spawns"]):
            o = spec["origin"]
            spawn = {
                "name": "%s_spawn%d" % (spec["name"], i),
                "classname": "info_neutral_trooper_spawn",
                "origin": [round(o[0] + off[0], 4),
                           round(o[1] + off[1], 4),
                           round(o[2] + off[2], 4)],
                "angles": [0.0, 0.0, 0.0],
                "properties": {
                    "targetname": "",
                    "vscripts": "",
                    "teamnumber": "0",
                    "CampName": spec["camp_name"],
                    "ENeutralTrooperType": spec["trooper_type"],
                    "CoverGroupID": "",
                    "HateCrateAttacker": "0",
                },
                MARK: True,
            }
            out.append(spawn)
            out.append(twin_of(spawn, neutral=True))
    return out


def build_breakables():
    out = []
    for spec in BREAKABLES:
        e = {
            "name": spec["name"],
            "classname": spec["classname"],
            "origin": [round(v, 4) for v in spec["origin"]],
            "angles": list(spec.get("angles", [0.0, 0.0, 0.0])),
            "properties": dict(spec["properties"]),
            MARK: True,
        }
        out.append(e)
        out.append(twin_of(e, neutral=True))
    return out


def build_brushes():
    """Volumes. The child mesh rides along in `mesh` and the emitter puts it
    inline in the entity's children."""
    out = []
    for spec in BRUSHES:
        e = {
            "name": spec["name"],
            "classname": spec["classname"],
            "origin": [round(v, 4) for v in spec["origin"]],
            "angles": list(spec.get("angles", [0.0, 0.0, 0.0])),
            "properties": dict(spec["properties"]),
            "mesh": {
                "name": spec["name"] + "_vol",
                "origin": [round(v, 4) for v in spec.get("mesh_origin",
                                                         [0.0, 0.0, 0.0])],
                "extents": [round(v, 4) for v in spec["extents"]],
                "angles": [0.0, 0.0, 0.0],
            },
            MARK: True,
        }
        out.append(e)
        out.append(twin_of(e))
    return out


def build_ziplines():
    out = []
    for spec in ZIPLINES:
        route = spec["route"]
        name = "zip_lane%s" % spec["lane"]
        p = {
            "name": name,
            "classname": "citadel_zipline_path",
            "origin": [round(v, 4) for v in route[0]],
            "angles": [0.0, 0.0, 0.0],
            "properties": dict(spec["properties"]),
            "interpolation_type": 1,
            "closed_loop": False,
            "nodes": [{"classname": "citadel_zipline_path_node",
                       "origin": [round(v, 4) for v in q],
                       "properties": {"teamnumber": TEAM_A,
                                      "enabled": "1",
                                      "corner_node": "0",
                                      "capturable": "0",
                                      "disable_zipping_to": "0"}}
                      for q in route],
            MARK: True,
        }
        out.append(p)

        m = json.loads(json.dumps(p))
        m["name"] = PREFIX + name
        m["origin"] = mirror_point(route[0])
        m["properties"]["targetname"] = PREFIX + p["properties"]["targetname"]
        for i, q in enumerate(route):
            m["nodes"][i]["origin"] = mirror_point(q)
            m["nodes"][i]["properties"]["teamnumber"] = TEAM_B
        out.append(m)
    return out


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
        out.append(twin_of(e))
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

    ents = (build_entities() + build_camps() + build_breakables()
            + build_brushes())
    paths = build_paths() + build_ziplines()
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
    brush = sum(1 for e in ents if e.get("mesh"))
    print("wrote %s" % path)
    print("  boxes    %d (untouched)" % len(plan["boxes"]))
    print("  entities %d (+%d, of which %d brush volumes)"
          % (len(plan["entities"]), len(ents), brush))
    print("  paths    %d (+%d), %d nodes" % (len(plan["paths"]), len(paths), nodes))
    print("\nEVERY COORDINATE IN THIS RUN IS A PLACEHOLDER. See the module")
    print("docstring. Replace with viewer `copy pos` readings before use.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else
                  "docs/plans/dust2_full.json"))
