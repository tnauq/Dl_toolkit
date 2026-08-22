#!/usr/bin/env python3
"""batch13 — objectives and lane paths into docs/plans/dust2_full.json.

THE FIRST BATCH THAT ADDS GAMEPLAY RATHER THAN GEOMETRY. Everything here is
entity and path data; no box is touched, so the 4,179 count does not move.

WHAT IT ADDS
    entities  guardians, walkers, trooper spawns          (team, mirrored)
    camps     info_neutral_trooper_camp + its spawns      (NEUTRAL, see below)
    breakables citadel_breakable_prop, item_crate_spawn   (NEUTRAL)
    volumes   every trigger_* and func_*: shops, shields, urn dropoffs,
              ropes, catapults, pushes, zap and speed-boost zipline volumes,
              spawn regen. All carry an inline child mesh.
    points    citadel_item_powerup_spawner (bridge buff),
              citadel_minimap_boundary. Both carry NO keyvalues at all.
    paths     lane_marker_path, one per lane per LaneSlot
              citadel_zipline_path, same machinery

LANE ROUTES ARE AUTHORED HALF-LENGTH. The map is rotationally symmetric, so
only the run from the team-2 base to the mirror point is authored; the far
half is that polyline mirrored and reversed, appended. That guarantees the
two halves are exactly equal length, which authoring both by hand would not.
The joining node is dropped if the last authored point lands on the mirror
point, or the path would carry two coincident nodes there.

LANE PATHS ARE NOT MIRRORED AS ENTITIES. Read out of dl_example 2026-08-22: its 16
lane_marker_path are 4 lanes x 4 slots, each (lanenum, LaneSlot) pair exactly
ONCE, and the class carries no teamnumber while every team-owned entity in the
map carries one. One path spans the WHOLE lane and both teams walk it in
opposite directions. So a lane route is authored base to base, not base to
middle, and mirroring it would lay a second full-length route on top of the
first. Ziplines ARE per team (2 per lane in dl_example) and do mirror.

MIRRORING, for everything else. Same proper rotation as mirror.py, about the
vertical line through (460.1, 6085.05):

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
# Height of a zipline above the lane floor, in units. The transit line runs
# overhead, not along the ground, and without this a zip that follows the
# trooper route inherits the route's floor z.
#
# 300 u is 7.6 m. PROVISIONAL: chosen to clear the 98 u figure with room to
# spare, not read from anything. Applied only to points taken from the lane
# route; points authored explicitly in ZIPLINES keep their own z, so a
# doorway passage can be given real readings later without changing this.
ZIP_HEIGHT = 300.0

SLOT_OFFSET = 96.0          # units between parallel trooper files
# FOUR slots, read from dl_example, not three. A wave is 4 troopers.
# Offsets are centred on the authored route: -1.5, -0.5, +0.5, +1.5 x
# SLOT_OFFSET, so the drawn line is the centre of the lane and no file
# walks exactly on it.
SLOTS = (0, 1, 2, 3)
# Slots are PARALLEL FILES, confirmed by the user 2026-08-22: one route per
# lane, offset sideways, not four independently shaped routes. 4 slots at 96
# is 288 u across, about 7.3 m — drop SLOT_OFFSET if the lanes are narrower
# than that after the rescale.

LANES = [
    # `half_route` runs from the team-2 base TO THE MIRROR POINT only. The
    # far half is generated by mirroring and reversing it, so the two halves
    # are exactly equal length by construction. Use as many nodes as the
    # shape needs — a real lane_marker_path in dl_example carries 17 — and
    # put the last one ON (460.1, 6085.05).
    #
    # Lane numbers 1, 3 and 6, chosen from dl_example's 1/3/4/6. No shipped
    # table of lane numbering exists anywhere (see the handoff), so these are
    # the only values observed working in a real map.
    #
    # MID LANE IS REAL. Crosshair readings, 2026-08-22, with the box each
    # point was taken on. The last one is SNAPPED to the mirror point: the
    # raw reading was (461, 6180, 0) on stitch_ground, 95 u past the middle,
    # which would have put a 190 u dogleg in the most contested spot on the
    # map once the far half was generated.
    {
        "lane": "1",
        "half_route": [
            [-4.0, -2630.0, 427.0],       # hex_floor_0, trooper spawn
            [34.0, -525.0, 427.0],        # axis_470
            [1627.0, -248.0, 213.0],      # axis_125
            [1618.0, 1272.0, 213.0],      # axis_125
            [396.0, 1354.0, 213.0],       # axis_125
            [446.0, 3608.0, 0.0],         # axis_0
            [X_PLANE, Y_PLANE, 0.0],      # snapped from stitch_ground
        ],
    },
    # WEST SIDE LANE. Crosshair readings 2026-08-22. The last two raw
    # readings, (-1467, 6131) on m_t3_ramp3 and (-2241, 6159) on m_t3_pad1,
    # were PAST the mirror point and on m_ boxes, i.e. the far half — an
    # overshoot. They are dropped and the route is closed on the mirror
    # point instead. Under a 180 degree rotation only the centre maps to
    # itself, so a half route that ends anywhere else generates a straight
    # jump from that point to its mirror: ending on (-2241, 6159) would have
    # put a 5,400 u line straight across the map.
    {
        "lane": "3",
        "half_route": [
            [-1016.0, -3206.0, 427.0],    # hex_floor_1, trooper spawn
            [-1476.0, -2828.0, 427.0],    # hex_tun_nw_floor
            [-1596.0, -676.0, 427.0],     # axis_470
            [-1701.0, 711.0, 213.0],      # merged_721
            [-1350.0, 1493.0, 213.0],     # merged_721
            [-1311.0, 2916.0, 253.0],     # axis_771
            [-1870.0, 2892.0, 253.0],     # axis_720
        ],
        # INCOMPLETE: the run from axis_720 to the middle is not surveyed.
        # Nothing is invented to close it — a straight line across 3,900 u
        # of unsurveyed lane would have been the wrong shape AND would have
        # made the length figure look authoritative. The far half is not
        # generated for an incomplete route either, because the completion
        # only works from a route that ends on the mirror point.
        "complete": False,
    },
    {
        "lane": "6",
        "half_route": [
            [1500.0, -530.0, 435.0],
            [1500.0, 3000.0, 435.0],
            [X_PLANE, Y_PLANE, 435.0],
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
    # Per team, so these DO mirror. Troopers ride one in before they walk.
    #
    # From the user 2026-08-22: the first point is the spawn shop room on
    # hex_plat_s and is shared by all three lanes; the second point differs
    # per lane (hex_floor_0 for mid, hex_dais_0 for the two side lanes);
    # from the third point on, the zipline follows the trooper route, so
    # those points are the lane's own half_route.
    #
    # NOTE the height: the spawn point is at z 1067 and the route runs at
    # 427 and below, so the zipline descends into the lane. Points taken
    # from the lane route are lifted by ZIP_HEIGHT; the two authored points
    # below keep the z they were read at.
    {
        "lane": "1",
        "route": [
            [3.0, -5955.0, 1067.0],       # hex_plat_s, spawn shop room
            [-4.0, -2630.0, 427.0],       # hex_floor_0
        ],
        # Everything after the second point is the lane route itself.
        "follow_lane": True,
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
    {
        "lane": "3",
        "route": [
            [3.0, -5955.0, 1067.0],       # hex_plat_s
            [3.0, -3770.0, 533.0],        # hex_dais_0, also the patron
        ],
        "follow_lane": True,
        "properties": {
            "targetname": "zip_lane3", "vscripts": "", "lane_number": "3",
            "radius": "2", "slack": "0", "particle_spacing": "512",
            "static_collision": "0", "color_tint": "0 25 255",
            "start_active": "1",
            "effect_name":
                "particles/entity/path_particle_cable_default.vpcf",
        },
    },
    {
        "lane": "6",
        "route": [
            [3.0, -5955.0, 1067.0],       # hex_plat_s
            [3.0, -3770.0, 533.0],        # hex_dais_0
        ],
        "follow_lane": True,
        "properties": {
            "targetname": "zip_lane6", "vscripts": "", "lane_number": "6",
            "radius": "2", "slack": "0", "particle_spacing": "512",
            "static_collision": "0", "color_tint": "0 200 0",
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
    # ---- per team, mirrored ------------------------------------------
    {
        "name": "shop_base",
        "classname": "trigger_item_shop",
        "origin": [400.0, -200.0, 435.0],
        "extents": [256.0, 256.0, 192.0],
        "properties": {
            "targetname": "amber_base_shop_item_trigger",
            "teamnumber": TEAM_A,
            "spawnflags": "4097",
            "AudioOffset": "-0.25 22 50",
        },
    },
    {
        # Urn dropoff AND spawn; the two alternate, so this is one entity
        # that does both jobs and its twin is the other end.
        "name": "urn_return",
        "classname": "citadel_trigger_idol_return",
        "origin": [200.0, 400.0, 435.0],
        "extents": [192.0, 192.0, 192.0],
        "properties": {"targetname": "amber_idol_return",
                       "teamnumber": TEAM_A, "spawnflags": "4097"},
    },
    {
        "name": "spawn_regen",
        "classname": "func_regenerate",
        "origin": [25.0, -700.0, 435.0],
        "extents": [512.0, 384.0, 256.0],
        "properties": {"targetname": "amber_spawn_regen",
                       "teamnumber": TEAM_A, "spawnflags": "4097"},
    },
    {
        # Patron phase 2. No targetname in dl_example either.
        "name": "patron_phase2_shield",
        "classname": "trigger_tier3phase2_shield",
        "origin": [25.0, -900.0, 435.0],
        "extents": [768.0, 768.0, 512.0],
        "properties": {"spawnflags": "4097"},
    },
    {
        # Shot off the zipline. A volume that damages the WRONG team, so it
        # runs along the enemy-side stretch of a zipline, not the whole run.
        # PercentMaxHealthDamage and the two timings are real tuning, copied
        # in shape from dl_example but with placeholder values.
        "name": "zip_zap_l1",
        "classname": "citadel_zap_trigger",
        "origin": [25.0, 4000.0, 900.0],
        "extents": [256.0, 3000.0, 256.0],
        "properties": {
            "targetname": "amber_zip_zap_lane1",
            "teamnumber": TEAM_A,
            "spawnflags": "4097",
            "PercentMaxHealthDamage": "5",
            "TimeBetweenShots": "1",
            "ShootAfterEnteringTime": "1",
            "ShootFromEntity": "",
        },
    },
    {
        "name": "zip_boost_l1",
        "classname": "citadel_trigger_speed_boost",
        "origin": [25.0, 1000.0, 900.0],
        "extents": [256.0, 1500.0, 256.0],
        "properties": {"targetname": "amber_zip_boost_lane1",
                       "spawnflags": "4097"},
    },

    # ---- neutral, mirrored -------------------------------------------
    {
        # The midboss pit shield. Only 4 keys in dl_example: no targetname
        # and no teamnumber, so it is presumably found by proximity to the
        # camp rather than wired by name. It regenerates constantly and is a
        # DPS CHECK — chip damage is meant to achieve nothing — which means
        # the volume wants to enclose the pit tightly enough that a team has
        # to commit inside it.
        "name": "midboss_shield",
        "classname": "trigger_midboss_shield",
        "origin": [460.1, 6085.05, 435.0],
        "extents": [1024.0, 1024.0, 512.0],
        "neutral": True,
        "properties": {"StartDisabled": "0", "spawnflags": "4097"},
    },
    {
        "name": "rope_west",
        "classname": "citadel_trigger_climb_rope",
        "origin": [-1600.0, 3000.0, 435.0],
        "extents": [96.0, 96.0, 640.0],
        "neutral": True,
        "properties": {"targetname": "", "spawnflags": "4097"},
    },
    {
        # Jump pad. `target` names the entity it launches you AT, so a
        # landing marker has to exist under that name — see POINTS below.
        "name": "catapult_west",
        "classname": "trigger_catapult",
        "origin": [-1800.0, 4000.0, 435.0],
        "extents": [128.0, 128.0, 64.0],
        "neutral": True,
        "properties": {"targetname": "catapult_west",
                       "target": "catapult_west_land",
                       "launch_speed": "800", "spawnflags": "4097"},
    },
    {
        # Directional push (a fan), not a teleporter: pushdir + speed.
        "name": "push_west",
        "classname": "citadel_trigger_push",
        "origin": [-2000.0, 5000.0, 435.0],
        "extents": [192.0, 192.0, 256.0],
        "neutral": True,
        "properties": {"targetname": "", "pushdir": "0 90 0",
                       "speed": "500", "spawnflags": "4097"},
    },
]


# ---------------------------------------------------------------------------
# POINT ENTITIES WITH NO KEYVALUES. Both of these carry nothing but a
# classname in dl_example — the position IS the whole content, like a
# path_node_generic.
#
#   citadel_item_powerup_spawner  the bridge buff. Rolls one of four buffs,
#                                 so the roll is not authored. TWO on the
#                                 real map, i.e. one here plus its twin.
#   citadel_minimap_boundary      2 of them; without these the minimap has
#                                 no frame.
#
# info_target_server_only is here too, as the landing marker a
# trigger_catapult aims at by name.
#
# TODO: placeholder origins.
# ---------------------------------------------------------------------------
POINTS = [
    {
        "name": "bridge_buff_west",
        "classname": "citadel_item_powerup_spawner",
        "origin": [-1500.0, 5200.0, 700.0],
        "neutral": True,
        "properties": {},
    },
    {
        "name": "minimap_corner",
        "classname": "citadel_minimap_boundary",
        "origin": [-5200.0, -6500.0, 0.0],
        "neutral": True,
        "properties": {},
    },
    {
        "name": "catapult_west_land",
        "classname": "info_target_server_only",
        "origin": [-1800.0, 5200.0, 900.0],
        "neutral": True,
        "properties": {"targetname": "catapult_west_land"},
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


ON_AXIS_TOL = 1.0


def on_mirror_point(origin):
    """True if this sits ON the mirror point, so its twin would be itself.

    Exactly the stitch_ground case from the box plan: the mirror maps the
    point onto itself, and emitting a twin puts two coincident entities in
    the same place. The midboss shield is the obvious one — the pit is in
    the middle of the map by definition.
    """
    return (abs(origin[0] - X_PLANE) <= ON_AXIS_TOL
            and abs(origin[1] - Y_PLANE) <= ON_AXIS_TOL)


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
    # Every key that NAMES another entity has to be prefixed too, or the
    # twin points back at the original half. Caught by the target check:
    # the mirrored catapult was launching players at the un-mirrored
    # landing marker, i.e. across the whole map.
    for k in ("targetname", "BossName", "CampName", "target",
              "ShootFromEntity", "BackdoorProtectionTrigger", "parentname",
              "filtername"):
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
        if not on_mirror_point(e["origin"]):
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
        if not on_mirror_point(e["origin"]):
            out.append(twin_of(e, neutral=spec.get("neutral", False)))
    return out


def build_points():
    """Entities that are nothing but a position."""
    out = []
    for spec in POINTS:
        e = {
            "name": spec["name"],
            "classname": spec["classname"],
            "origin": [round(v, 4) for v in spec["origin"]],
            "angles": list(spec.get("angles", [0.0, 0.0, 0.0])),
            "properties": dict(spec.get("properties", {})),
            MARK: True,
        }
        out.append(e)
        if not on_mirror_point(e["origin"]):
            out.append(twin_of(e, neutral=spec.get("neutral", False)))
    return out


def lane_half(lane):
    for spec in LANES:
        if spec["lane"] == lane:
            return spec["half_route"]
    raise KeyError("no lane %s" % lane)


def build_ziplines():
    out = []
    for spec in ZIPLINES:
        route = [list(p) for p in spec["route"]]

        # A zipline runs to the middle only: it is a per-team entity and the
        # far half belongs to the other team's zipline, which is this one's
        # mirrored twin. So it follows the lane's HALF route, not the
        # completed one.
        if spec.get("follow_lane"):
            lift = spec.get("height", ZIP_HEIGHT)
            for p in lane_half(spec["lane"]):
                q = [p[0], p[1], p[2] + lift]
                if route and all(abs(q[i] - route[-1][i]) <= 1.0
                                 for i in range(3)):
                    continue          # already there, do not duplicate
                # An authored point at the same x,y wins: it was given
                # explicitly, so its height is deliberate.
                if route and all(abs(p[i] - route[-1][i]) <= 1.0
                                 for i in range(2)):
                    continue
                route.append(q)
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


def complete_route(half):
    """Base-to-middle in, base-to-base out.

    The far half is the authored polyline mirrored and REVERSED, so the
    result runs continuously from one base to the other. If the last
    authored point sits on the mirror point its mirror is itself, so that
    duplicate is dropped rather than emitted as two coincident nodes.
    """
    if len(half) < 2:
        raise ValueError("a half route needs at least 2 points")

    # Only the centre maps to itself under a 180 degree rotation. A route
    # that ends anywhere else generates a straight jump from its last point
    # to that point's mirror — for a side lane that is thousands of units
    # across the map. Refuse rather than emit it.
    if not on_mirror_point(half[-1]):
        raise ValueError(
            "route ends at %s, not on the mirror point (%.2f, %.2f). "
            "Either finish the survey or set \"complete\": False."
            % (half[-1][:2], X_PLANE, Y_PLANE))

    far = [mirror_point(p) for p in reversed(half)]
    a, b = half[-1], far[0]
    same = all(abs(a[i] - b[i]) <= 1.0 for i in range(3))
    if same:
        far = far[1:]
    return [list(p) for p in half] + far


def build_paths():
    """One path per lane per slot. NOT mirrored — see the docstring."""
    out = []
    for spec in LANES:
        lane = spec["lane"]
        if spec.get("complete", True):
            full = complete_route(spec["half_route"])
        else:
            full = [list(p) for p in spec["half_route"]]
        for slot in SLOTS:
            route = offset_route(full, slot)
            out.append(make_path("lane%s_slot%d" % (lane, slot),
                                 lane, slot, route))
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

    # Symmetry: every authored thing must have exactly one twin, EXCEPT the
    # shared lane paths, which are single by design.
    for coll in ("entities", "paths"):
        mine = [x for x in plan[coll] if x.get(MARK)
                and x.get("classname") != "lane_marker_path"
                and not on_mirror_point(x.get("origin", [0, 0, 0]))]
        half = {x["name"] for x in mine if not x["name"].startswith(PREFIX)}
        twin = {x["name"][len(PREFIX):] for x in mine
                if x["name"].startswith(PREFIX)}
        if half != twin:
            print("FAIL %s asymmetric: %s" % (coll, sorted(half ^ twin)))
            bad += 1

    # Name wiring: anything referenced by `target` must actually exist, on
    # both halves. A dangling name fails silently in game.
    names = {e["properties"].get("targetname")
             for e in plan["entities"] if e.get("properties")}
    for e in plan["entities"]:
        want = (e.get("properties") or {}).get("target")
        if want and want not in names:
            print("FAIL %s: target '%s' names nothing" % (e["name"], want))
            bad += 1

    # A shared lane path must not have acquired a twin.
    for p in plan["paths"]:
        if p.get("classname") == "lane_marker_path" and \
                p["name"].startswith(PREFIX):
            print("FAIL %s: lane paths are shared and must not be mirrored"
                  % p["name"])
            bad += 1
    return bad


# Trooper ground speed, in units per second. UNVERIFIED: not found in the
# vdata searched so far, so this is a placeholder used only to turn lane
# lengths into a rough time. The LENGTHS are exact; the times are not.
TROOPER_SPEED = 0.0          # set from npc_units.vdata when known
UNITS_PER_M = 39.37


def route_length(route):
    total = 0.0
    for a, b in zip(route, route[1:]):
        dx, dy, dz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        total += (dx * dx + dy * dy + dz * dz) ** 0.5
    return total


INCOMPLETE = {spec["lane"] for spec in LANES
              if not spec.get("complete", True)}


def report_lengths(paths):
    """Lane lengths, and the distance to the mirror point.

    Troopers from both sides walk the SAME path in opposite directions, so
    the waves meet near the middle. The number that matters for lane parity
    is the distance from each base to the mirror point: if the three lanes
    differ there, one lane's wave arrives before the others and the map is
    unfair in a way no amount of geometry symmetry fixes.
    """
    print("\nlane lengths")
    for p in paths:
        if p.get("classname") != "lane_marker_path":
            continue
        route = [n["origin"] for n in p["nodes"]]
        total = route_length(route)

        # Split at the node nearest the mirror point.
        best, at = None, 0
        for i, q in enumerate(route):
            d = ((q[0] - X_PLANE) ** 2 + (q[1] - Y_PLANE) ** 2) ** 0.5
            if best is None or d < best:
                best, at = d, i
        first = route_length(route[:at + 1])
        second = total - first

        lane = p["properties"].get("lanenum", "")
        if lane in INCOMPLETE:
            print("  %-16s %8.1f u (%6.1f m)   INCOMPLETE, not comparable"
                  % (p["name"], total, total / UNITS_PER_M))
            continue

        line = ("  %-16s %8.1f u (%6.1f m)   to midpoint %7.1f / %7.1f"
                % (p["name"], total, total / UNITS_PER_M, first, second))
        if TROOPER_SPEED > 0:
            line += "   %5.1f s" % (first / TROOPER_SPEED)
        print(line)
        if best is not None and best > 500.0:
            print("    NOTE nearest node is %.0f u from the mirror point; the"
                  % best)
            print("    split above is approximate. Add a node near the middle.")
    if TROOPER_SPEED <= 0:
        print("  (no trooper speed known, so no times — see TROOPER_SPEED)")


def main(path):
    with open(path) as f:
        plan = json.load(f)

    plan.setdefault("entities", [])
    plan.setdefault("paths", [])
    strip_previous(plan)

    ents = (build_entities() + build_camps() + build_breakables()
            + build_brushes() + build_points())
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
    report_lengths(paths)
    print("\nEVERY COORDINATE IN THIS RUN IS A PLACEHOLDER. See the module")
    print("docstring. Replace with viewer `copy pos` readings before use.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else
                  "docs/plans/dust2_full.json"))
