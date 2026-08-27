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

SIDE LANES ARE A MIRROR PAIR. With three lanes and 180 degree symmetry only
the MID lane can map to itself, because a route that does not pass through the
centre cannot be its own mirror. The two side lanes therefore map to EACH
OTHER: lane 3's far half is lane 6 reversed and mirrored, and lane 6's far
half is lane 3. So a side lane is authored as its own team-2 stretch and
completed from its PARTNER's, joined at the seam.

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

# Teams. 2 is amber, 3 is sapphire in Deadlock's own colour language, but
# dl_example names its entities REBELS and COMBINE, and every targetname in
# the fixture follows that. Matching it 2026-08-23 on the user's call, so a
# name read out of this map means the same thing as one read out of Valve's.
#
# THE TEAM WORD IS PART OF THE NAME, not a prefix bolted on. dl_example has
# rebels_t2_boss_orange and combine_t2_boss_orange as a pair, and no m_
# anywhere. This file still uses the m_ prefix for the PLAN-LEVEL entity
# name, because strip_previous and every batch script key on it, but the
# TARGETNAME - the thing the game and entity IO actually see - swaps the team
# word instead. Two namespaces, one bookkeeping and one real.
TEAM_WORD_A = "rebels"
TEAM_WORD_B = "combine"

# LANE COLOURS, read off dl_example's boss names: yellow is lane 1, orange
# lane 3, blue lane 4, purple lane 6. Lane 4 is listed for completeness even
# though this map has no such lane.
#
# NOTE the fixture's zipline color_tint does NOT agree with these on lane 3
# (red tint, orange name). The BOSS NAMES are followed here because they are
# what other entities reference.
LANE_COLOUR = {"1": "yellow", "3": "orange", "4": "blue", "6": "purple"}


def lane_colour(lane):
    return LANE_COLOUR.get(lane, "lane" + lane)


def team_swap(name):
    """Swap the team word in a targetname, for the mirrored copy.

    The word is not always at the front. dl_example puts it in the middle
    (shop_Sapphire_t1_lanecolor_shop, base_shop_teamname), so the swap is on
    the first occurrence ANYWHERE rather than on a prefix. A name with no team
    word in it is neutral and falls back to the m_ prefix, which is what the
    jungle and midboss entities use.
    """
    if not name:
        return name
    if TEAM_WORD_A in name:
        return name.replace(TEAM_WORD_A, TEAM_WORD_B, 1)
    if TEAM_WORD_B in name:
        return name.replace(TEAM_WORD_B, TEAM_WORD_A, 1)
    return PREFIX + name


TEAM_A = "2"
TEAM_B = "3"


# READ COORDINATES, 2026-08-23. Crosshair `copy pos` from the viewer, team-2
# half only; every one below is mirrored to the team-3 half by twin_of. The
# box each reading was taken on is recorded so a later re-survey knows what
# moved.
#
# LANE ASSIGNMENT is by x, not read: west is lane 3, mid lane 1, east lane 6,
# matching the LANES table. If the lane numbering itself is wrong, it is wrong
# consistently here and in the paths.
#
# WHAT IS STILL INVENTED. The ANGLES. No facing was surveyed, so each
# objective is turned to face the mirror point, which is the direction a
# defender looks down its own lane. That is a reasonable default and nothing
# more; a boss facing the wrong way is a cosmetic fault, not a structural one.
OBJECTIVE_READINGS = [
    # lane, kind, origin, box the reading was taken on
    ("3", "guardian", [-1753.0, 4750.0, 280.0], "axis_790"),
    ("1", "guardian", [425.0, 4126.0, 0.0], "axis_0"),
    ("6", "guardian", [3467.0, 4143.0, 213.0], "gapfill_50_34"),
    ("3", "walker", [-1208.0, 1143.0, 213.0], "merged_721"),
    ("1", "walker", [437.0, 1419.0, 213.0], "axis_125"),
    ("6", "walker", [2867.0, 2403.0, 213.0], "gapfill_42_27"),
]

# Guardian shops, one per lane. Same reading session.
SHOP_READINGS = [
    ("3", [-1623.0, 3200.0, 253.0], "axis_770"),
    ("1", [915.0, 3980.0, 0.0], "axis_0"),
    ("6", [3179.0, 3416.0, 213.0], "gapfill_50_34"),
]

# Base room. hex_plat_s is the spawn shop, hex_plat_s_e the team spawn, and
# the regen covers the whole room, so the two readings are used as opposite
# reference points for its volume.
SPAWN_ORIGIN = [518.0, -6183.0, 1067.0]          # hex_plat_s_e
BASE_SHOP_ORIGIN = [17.0, -5926.0, 1067.0]       # hex_plat_s
SECRET_SHOP_ORIGIN = [-402.0, 2424.0, 654.0]     # axis_769
URN_ORIGIN = [-3688.0, 2908.0, 867.0]            # hex2_dais1_0

# INVENTED, all of them: no size was surveyed for any volume. A shop you
# cannot walk into is worse than one that is too big, so these err large.
# The regen is sized to span the two base-room readings plus a margin.
SHOP_EXTENTS = [256.0, 256.0, 192.0]
REGEN_MARGIN = 256.0
REGEN_HEIGHT = 256.0



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


# SUBCLASSES THAT ARE PER TEAM. Read off dl_example 2026-08-23: its team-2
# objectives use the plain subclass and its team-3 objectives the alt_ one,
# and the vdata shows the pair differing only in model and scale. So the
# mirror has to swap these the same way it swaps teamnumber - a twin left on
# the team-2 subclass renders in the wrong colours.
TEAM_SUBCLASS = {
    "npc_boss_tier1": "alt_npc_boss_tier1",
    "npc_boss_tier3": "alt_npc_boss_tier3",
    "npc_boss_tier2": "alt_npc_boss_tier2",
    "npc_boss_tier2_weak": "alt_npc_boss_tier2_weak",
}

# WALKER DIFFICULTY BY LANE. dl_example runs two strengths of npc_boss_tier2
# per team - the plain subclass and a _weak one - so lanes are deliberately
# not equal. User's call 2026-08-23: the SIDE lanes are the weak ones here,
# so the mid lane's walker is the full-strength body and 3 and 6 are weak.
#
# This is a subclass swap only. Position, keys and wiring are identical, and
# the difference lives entirely in npc_units.vdata.
#
# NOT READ FROM THE FIXTURE, and it could not be: dl_example is a four-lane
# map and puts its weak walkers on lanes 1 and 6, which says nothing about
# which lanes are "sides" on a three-lane map. This is a design decision.
WEAK_WALKER_LANES = {"3", "6"}


def flip_team(props):
    """Swap teamnumber, and any subclass that has a per-team variant."""
    out = dict(props)
    if out.get("teamnumber") == TEAM_A:
        out["teamnumber"] = TEAM_B
    elif out.get("teamnumber") == TEAM_B:
        out["teamnumber"] = TEAM_A

    sub = out.get("subclass_name")
    if sub in TEAM_SUBCLASS:
        out["subclass_name"] = TEAM_SUBCLASS[sub]
    else:
        for base, alt in TEAM_SUBCLASS.items():
            if sub == alt:
                out["subclass_name"] = base
                break
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

# Zipline node ownership. teamnumber 2 and 3 are the two ends; 4 is the
# NEUTRAL band in the middle, where the two trooper waves meet and neither
# side owns the cable. dl_example carries 38 nodes at 4 out of 270, about
# 14%, so the band is a real feature of the middle rather than a stray value.
#
# PROVISIONAL: the WIDTH is a guess. 2000 u either side of the mirror point
# is 50.8 m, chosen to be roughly a seventh of a 570 m lane and so land near
# dl_example's 14%. Nothing was measured. If it matters in play, the honest
# fix is to read the real band off a lane in game rather than tune it here.
ZIP_NEUTRAL_HALF_SPAN = 2000.0
TEAM_NEUTRAL = "4"

# How far from the middle a node is still CAPTURABLE. Read off dl_example
# 2026-08-22: every one of its 38 teamnumber-4 nodes is capturable, while the
# 232 owned nodes split roughly 60/40 not-capturable to capturable. So
# capturable is not ownership — it marks the stretch that can change hands as
# a wave pushes, which is why a winning team ends up zipping most of the map.
# Nodes near a base are fixed; the middle and its approaches are not.
#
# 6000 u is 152 m, three times the neutral half-span. PROVISIONAL: chosen so
# roughly half the owned nodes come out capturable, matching dl_example's
# split. Not measured.
ZIP_CAPTURABLE_HALF_SPAN = 6000.0

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
    # WEST SIDE LANE. Crosshair readings 2026-08-22, running past the middle
    # onto the mirrored east geometry (m_t3_ramp3, m_t3_pad1) — which is
    # correct, not an overshoot: this lane continues into what is the east
    # side of the far half. Completed from lane 6, its mirror partner.
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
            [-1467.0, 6131.0, 343.0],     # m_t3_ramp3
            [-2241.0, 6159.0, 365.0],     # m_t3_pad1
        ],
        "pair": "6",
    },
    {
        # EAST SIDE LANE. Completed from lane 3.
        "lane": "6",
        "half_route": [
            [1002.0, -3207.0, 427.0],     # hex_floor_2, trooper spawn
            [1461.0, -2939.0, 427.0],     # hex_tun_ne_stub_floor
            [1591.0, -690.0, 213.0],      # axis_125
            [1731.0, 18.0, 213.0],        # axis_125
            [2100.0, 1134.0, 213.0],      # gapfill_39_9
            [2120.0, 2327.0, 213.0],      # gapfill_38_26
            [3438.0, 2512.0, 213.0],      # gapfill_51_28
            [3468.0, 6015.0, 365.0],      # t1_ramp1
        ],
        "pair": "3",
    }
]


# ---------------------------------------------------------------------------
# ZIPLINES. Same CMapPath machinery as a lane: keyvalues say what it is, the
# node list says where it goes. Troopers ride one INTO the lane before they
# walk it, so a zipline route roughly parallels its lane at height.
#
# TODO: placeholder route.
# ---------------------------------------------------------------------------
ZIPLINES = [
    # ONE PER LANE, BASE TO BASE. The cable spans the whole lane and who owns
    # a stretch of it is decided at runtime by trooper position, not by there
    # being two entities. So a zipline is completed exactly like a lane route
    # — mirrored for mid, paired for the side lanes — and gets NO m_ twin.
    #
    # DISCREPANCY, unresolved: dl_example has 8 citadel_zipline_path for 4
    # lanes, i.e. TWO per lane, and its nodes carry teamnumber 2, 3 and 4.
    # If those two are the two directions rather than the two halves, this
    # emits half as many as the real map. Worth checking before a load.
    #
    # COLOURS AND max_simulation_time are dl_example's own, read off its
    # family A paths 2026-08-22: lane 1 orange 255 106 0, lane 3 red
    # 255 0 0, lane 4 blue 0 25 255, lane 6 purple 139 0 139. The minimap
    # uses these, so they are not free choices.
    #
    # Node teamnumber is assigned by position: 2 on the team-2 side, 3 on
    # the far side, and 4 across a neutral band in the middle — the shape the
    # node teamnumbers take in dl_example, where 4 accounts for 38 of 270.
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
            "max_simulation_time": "0.2",
            "radius": "2",
            "slack": "0",
            "particle_spacing": "512",
            "static_collision": "0",
            "color_tint": "255 106 0",
            "start_active": "1",
            "effect_name":
                "particles/entity/path_particle_cable_default.vpcf",
        },
    },
    {
        # The zip FOLLOWS THE WALKING ROUTE, lifted. An earlier version sent
        # it up through the second level on its own points (axis_766 / _761 /
        # _762 / _790, z 720 down to 280); that is reverted, because troopers
        # dropping off a cable onto the second level can get stuck there.
        # Same line, first level, is the safe version. The second-level
        # readings are kept in the handoff if it is ever wanted back.
        "lane": "3",
        "route": [
            [3.0, -5955.0, 1067.0],       # hex_plat_s
            [3.0, -3770.0, 533.0],        # hex_dais_0, also the patron
        ],
        "follow_lane": True,
        "properties": {
            "targetname": "zip_lane3", "vscripts": "", "lane_number": "3",
            "max_simulation_time": "0.2",
            "max_simulation_time": "0.2",
            "radius": "2", "slack": "0", "particle_spacing": "512",
            "static_collision": "0", "color_tint": "255 0 0",
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
            "max_simulation_time": "0.2",
            "max_simulation_time": "0.2",
            "radius": "2", "slack": "0", "particle_spacing": "512",
            "static_collision": "0", "color_tint": "139 0 139",
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
        # READ 2026-08-23 on hex_plat_s, the spawn shop room.
        "origin": list(BASE_SHOP_ORIGIN),
        "extents": list(SHOP_EXTENTS),
        "properties": {
            "targetname": "base_shop_%s_item_trigger" % TEAM_WORD_A,
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
        # READ 2026-08-23 on hex2_dais1_0.
        "origin": list(URN_ORIGIN),
        "extents": [192.0, 192.0, 192.0],
        "properties": {"targetname": "%s_idol_return" % TEAM_WORD_A,
                       "teamnumber": TEAM_A, "spawnflags": "4097"},
    },
    {
        "name": "spawn_regen",
        "classname": "func_regenerate",
        # The WHOLE spawn room, per the user: the two base-room readings are
        # used as opposite reference points and the volume spans both plus a
        # margin. The room's true walls were not surveyed, so the SIZE is
        # invented even though both reference points are real.
        "origin": [round((SPAWN_ORIGIN[i] + BASE_SHOP_ORIGIN[i]) / 2.0, 4)
                   for i in range(3)],
        "extents": [round(abs(SPAWN_ORIGIN[0] - BASE_SHOP_ORIGIN[0])
                          + 2 * REGEN_MARGIN, 4),
                    round(abs(SPAWN_ORIGIN[1] - BASE_SHOP_ORIGIN[1])
                          + 2 * REGEN_MARGIN, 4),
                    REGEN_HEIGHT],
        "properties": {"targetname": "%s_spawn_regen" % TEAM_WORD_A,
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
            "targetname": "%s_zip_zap_%s" % (TEAM_WORD_A, lane_colour("1")),
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
        "properties": {"targetname": "%s_zip_boost_%s" % (TEAM_WORD_A, lane_colour("1")),
                       "spawnflags": "4097"},
    },

    # ---- guardian shops, READ 2026-08-23 -----------------------------
    # One per lane, beside its guardian. Origins are real; EXTENTS are not,
    # so a shop that turns out to sit inside a wall is a size fault, not a
    # position fault.
    {
        "name": "shop_lane3",
        "classname": "trigger_item_shop",
        "origin": [-1623.0, 3200.0, 253.0],       # axis_770
        "extents": list(SHOP_EXTENTS),
        "properties": {"targetname": "shop_%s_t1_%s_shop_item_trigger" % (TEAM_WORD_A, lane_colour("3")),
                       "teamnumber": TEAM_A, "spawnflags": "4097",
                       "AudioOffset": "-0.25 22 50"},
    },
    {
        "name": "shop_lane1",
        "classname": "trigger_item_shop",
        "origin": [915.0, 3980.0, 0.0],           # axis_0
        "extents": list(SHOP_EXTENTS),
        "properties": {"targetname": "shop_%s_t1_%s_shop_item_trigger" % (TEAM_WORD_A, lane_colour("1")),
                       "teamnumber": TEAM_A, "spawnflags": "4097",
                       "AudioOffset": "-0.25 22 50"},
    },
    {
        "name": "shop_lane6",
        "classname": "trigger_item_shop",
        "origin": [3179.0, 3416.0, 213.0],        # gapfill_50_34
        "extents": list(SHOP_EXTENTS),
        "properties": {"targetname": "shop_%s_t1_%s_shop_item_trigger" % (TEAM_WORD_A, lane_colour("6")),
                       "teamnumber": TEAM_A, "spawnflags": "4097",
                       "AudioOffset": "-0.25 22 50"},
    },
    {
        # SECRET SHOP. Authored per team like every other shop, so the twin
        # sits on the mirrored half. If the real map has ONE secret shop
        # rather than one per side, delete the twin rather than moving this.
        "name": "shop_secret",
        "classname": "trigger_item_shop",
        "origin": list(SECRET_SHOP_ORIGIN),       # axis_769
        "extents": list(SHOP_EXTENTS),
        "properties": {"targetname": "secret_shop_%s_item_trigger" % TEAM_WORD_A,
                       "teamnumber": TEAM_A, "spawnflags": "4097",
                       "AudioOffset": "-0.25 22 50"},
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
def face_centre(origin):
    """Yaw turning this entity toward the mirror point.

    Not surveyed. A guardian looks up its own lane toward the middle, which
    is where everything it cares about comes from, so this is the sane
    default rather than a measured fact.
    """
    import math
    return [0.0, round(math.degrees(math.atan2(Y_PLANE - origin[1],
                                               X_PLANE - origin[0])), 2), 0.0]


def build_objectives():
    """The objective table, from the readings above.

    Trooper spawns are NOT in the readings: none was surveyed. Each is
    DERIVED from the first node of its own lane route, which is the point
    troopers walk away from by definition. Derived, not read, and marked so.
    """
    out = []
    for lane, kind, origin, box in OBJECTIVE_READINGS:
        if kind == "guardian":
            out.append({
                "name": "guardian_l%s" % lane,
                # CORRECTED AGAIN 2026-08-27, from npc_units.vdata itself:
                #
                #   npc_boss_tier1  boss_tier_01_brazier_guardian.vmdl   5500
                #   npc_boss_tier3  patron_amber.vmdl   12000, m_nPhase2Health,
                #                   Patron.Phase1.Transform.Start, phase 1 and
                #                   phase 2 lasers, a dying sequence
                #
                # npc_boss_tier3 IS THE PATRON. Using it here put six patrons
                # on the map, one per lane per team. The lane objective - the
                # brazier guardian - is npc_boss_tier1.
                #
                # The 2026-08-23 note this replaces was reasoned from the
                # fixture: tier3 was the only objective class dl_example wired
                # an output on. That was true and still is; it just does not
                # mean tier3 is the guardian. The gym contains one of each
                # thing, and its tier3 is its patron.
                #
                # npc_barrack_boss is unchanged and still not this: it is the
                # pair guarding a shrine in the base.
                "classname": "npc_boss_tier1",
                "origin": list(origin),
                "angles": face_centre(origin),
                "surveyed_on": box,
                # KEY SET READ 2026-08-23, not copied. dl_example's two
                # npc_boss_tier3 carry exactly ten keys and all ten are here.
                # Three were missing from the earlier tier2-shaped guess:
                # BackdoorProtectionTrigger, dying_cover_id and
                # vulnerable_cover_id.
                #
                # TARGETNAME IS EMPTY in both of dl_example's, which use
                # BossName as the identity instead. That is followed here,
                # because BossName is what the fixture keys on and an
                # invented targetname could collide with something the game
                # looks up. NOTE that this makes the objective unaddressable
                # by entity IO from anything except its own outputs, which is
                # fine: it drives the shop relay rather than being driven.
                #
                # SUBCLASS_NAME IS PER TEAM: npc_boss_tier1 for team 2 and
                # alt_npc_boss_tier1 for team 3. The vdata shows the two are
                # identical in every value that matters - same model, same
                # 5500 health, same scale - so the split is bookkeeping, but
                # it is what the fixture does. flip_team does not touch
                # subclass_name, so the twin is corrected in
                # build_objectives' mirror step below.
                #
                # The cover ids are UNSET rather than invented. dl_example
                # carries real values (CoverGroupID 4321 / 1234), which look
                # like references into cover groups this map does not have.
                "properties": {
                    "targetname": "",
                    "vscripts": "",
                    "teamnumber": TEAM_A,
                    "lanenum": lane,
                    "BackdoorProtectionTrigger": "",
                    "BossName": "%s_t1_boss_%s" % (TEAM_WORD_A, lane_colour(lane)),
                    "subclass_name": "npc_boss_tier1",
                    "CoverGroupID": "",
                    "dying_cover_id": "",
                    "vulnerable_cover_id": "",
                },
            })
        else:
            out.append({
                "name": "walker_l%s" % lane,
                "classname": "npc_boss_tier2",
                "origin": list(origin),
                "angles": face_centre(origin),
                "surveyed_on": box,
                # KEY SET CONFIRMED 2026-08-23 against dl_example's eight
                # npc_boss_tier2: seven keys, exactly these. Unlike tier3,
                # this class DOES carry a real targetname in the fixture, and
                # it matches its BossName.
                #
                # SUBCLASS_NAME IS PER TEAM here too: npc_boss_tier2 for
                # team 2, alt_npc_boss_tier2 for team 3, and flip_team swaps
                # them. It is also PER LANE: the side lanes take the _weak
                # variant, see WEAK_LANES.
                "properties": {
                    "targetname": "%s_t2_boss_%s" % (TEAM_WORD_A, lane_colour(lane)),
                    "vscripts": "",
                    "teamnumber": TEAM_A,
                    "lanenum": lane,
                    "BossName": "%s_t2_boss_%s" % (TEAM_WORD_A, lane_colour(lane)),
                    "CoverGroupID": "",
                    "subclass_name": ("npc_boss_tier2_weak"
                                      if lane in WEAK_WALKER_LANES
                                      else "npc_boss_tier2"),
                },
            })
    # TEAM SPAWN, read on hex_plat_s_e. Authored here for the first time:
    # the plan already carried two info_team_spawn from an earlier session,
    # unnamed, at placeholder coordinates, and NOT mirror-symmetric with each
    # other. Those are removed by strip_legacy_spawns and replaced by this
    # one plus its generated twin, so the pair is symmetric by construction
    # like everything else in this file.
    out.append({
        "name": "team_spawn",
        "classname": "info_team_spawn",
        "origin": list(SPAWN_ORIGIN),
        "angles": face_centre(SPAWN_ORIGIN),
        "surveyed_on": "hex_plat_s_e",
        "properties": {
            "teamnumber": TEAM_A,
            "lanenum": "1",
            "initialspawn": "1",
        },
    })
    for spec in LANES:
        lane = spec["lane"]
        first = list(spec["half_route"][0])
        out.append({
            "name": "trooper_spawn_l%s" % lane,
            "classname": "info_trooper_spawn",
            "origin": [round(v, 4) for v in first],
            "angles": face_centre(first),
            "surveyed_on": "DERIVED from lane %s first node" % lane,
            "properties": {
                "targetname": "",
                "vscripts": "",
                "teamnumber": TEAM_A,
                "lanenum": lane,
                "TrooperLevel": "4",
            },
        })
    return out


OBJECTIVES = build_objectives()


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
            # team_swap turns rebels_ into combine_ where the fixture's
            # convention applies, and falls back to the m_ prefix for
            # anything neutral, which has no team word to swap.
            props[k] = team_swap(props[k])
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


def build_ziplines():
    """One full-length cable per lane. No twin — see the ZIPLINES comment."""
    out = []
    for spec in ZIPLINES:
        lane = spec["lane"]
        route = [list(p) for p in spec["route"]]

        if spec.get("follow_lane"):
            lift = spec.get("height", ZIP_HEIGHT)
            for p in lane_route(lane):
                q = [p[0], p[1], p[2] + lift]
                if route and all(abs(q[i] - route[-1][i]) <= 1.0
                                 for i in range(3)):
                    continue
                if route and all(abs(p[i] - route[-1][i]) <= 1.0
                                 for i in range(2)):
                    continue
                route.append(q)

        for p2 in spec.get("then", []):
            route.append([round(v, 4) for v in p2])

        # The far end: the shared start points of the OTHER base, mirrored,
        # so the cable finishes in the enemy spawn room the way it started in
        # ours. Without this it stops wherever the walking route ends.
        tail = [mirror_point(p) for p in reversed(spec["route"])]
        for t in tail:
            if route and all(abs(t[i] - route[-1][i]) <= 1.0 for i in range(3)):
                continue
            route.append(t)

        nodes = []
        for q in route:
            # Team by side of the mirror point, with a neutral band across
            # the middle where the waves meet.
            dy = q[1] - Y_PLANE
            if abs(dy) <= ZIP_NEUTRAL_HALF_SPAN:
                team = TEAM_NEUTRAL
            else:
                team = TEAM_A if dy < 0 else TEAM_B
            cap = "1" if abs(dy) <= ZIP_CAPTURABLE_HALF_SPAN else "0"
            nodes.append({"classname": "citadel_zipline_path_node",
                          "origin": [round(v, 4) for v in q],
                          "properties": {"teamnumber": team,
                                         "enabled": "1",
                                         # corner_node marks turn geometry.
                                         # In dl_example disable_zipping_to
                                         # is 1 only where corner_node is 1:
                                         # you pass through a corner, you do
                                         # not zip TO it. Left at 0 until
                                         # the corners here are identified.
                                         "corner_node": "0",
                                         "capturable": cap,
                                         "disable_zipping_to": "0"}})

        out.append({
            "name": "zip_lane%s" % lane,
            "classname": "citadel_zipline_path",
            "origin": [round(v, 4) for v in route[0]],
            "angles": [0.0, 0.0, 0.0],
            "properties": dict(spec["properties"]),
            "interpolation_type": 1,
            "closed_loop": False,
            "nodes": nodes,
            MARK: True,
        })
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


def lane_route(lane):
    """The completed base-to-base route for a lane, as build_paths sees it."""
    for spec in LANES:
        if spec["lane"] != lane:
            continue
        if spec.get("pair"):
            return complete_paired(spec["half_route"],
                                   lane_half(spec["pair"]),
                                   lane, spec["pair"], quiet=True)
        if spec.get("complete", True):
            return complete_route(spec["half_route"])
        return [list(p) for p in spec["half_route"]]
    raise KeyError("no lane %s" % lane)


def lane_half(lane):
    for spec in LANES:
        if spec["lane"] == lane:
            return spec["half_route"]
    raise KeyError("no lane %s" % lane)


# How far apart the two halves of a paired lane may be at the seam before it
# is treated as an error rather than crosshair slop. 500 u is 12.7 m.
SEAM_SNAP = 500.0


def complete_paired(half, partner_half, lane, partner, quiet=False):
    """Join a side lane to its mirror partner.

    The far half is the PARTNER's authored stretch, mirrored and reversed.
    The seam is where this lane's last point meets the partner's mirrored
    last point; they are two independent crosshair readings of the same
    place, so they will not match exactly. Within SEAM_SNAP the partner's
    point is dropped and this lane's reading wins — one reading, not an
    average, so the seam sits on a real surface someone actually stood on.
    """
    far = [mirror_point(p) for p in reversed(partner_half)]
    a, b = half[-1], far[0]
    gap = ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5

    if gap <= SEAM_SNAP:
        if not quiet:
            print("  lane %s seam: %.1f u to lane %s, snapped"
                  % (lane, gap, partner))
        far = far[1:]
    elif quiet:
        pass
    else:
        print("  lane %s seam: %.1f u to lane %s, TOO FAR to snap — the two"
              % (lane, gap, partner))
        print("    halves are joined by a straight line of that length. Either")
        print("    survey the gap or move an endpoint.")
    return [list(p) for p in half] + far


def build_paths():
    """One path per lane per slot. NOT mirrored — see the docstring."""
    out = []
    for spec in LANES:
        lane = spec["lane"]
        if spec.get("pair"):
            full = complete_paired(spec["half_route"],
                                   lane_half(spec["pair"]),
                                   lane, spec["pair"])
        elif spec.get("complete", True):
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
                and x.get("classname") not in ("lane_marker_path",
                                               "citadel_zipline_path")
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


# Trooper ground speed, in units per second. READ from npc_units.vdata,
# subclass trooper_normal, npc-probe round four: m_flWalkSpeed = 248,
# m_flRunSpeed = 512, m_flAcceleration = 200. Lane troopers WALK, so the walk
# speed is the one that sets wave timing. The run speed is what a trooper
# uses when it is chasing something, which is not what a lane length measures.
#
# WHAT IS STILL UNVERIFIED. Nobody has watched a trooper walk this map, so the
# times below assume a trooper is at full walk speed for the whole route with
# no acceleration ramp, no pathing overshoot on corners and no stopping to
# shoot. Real waves do all three, so treat every time as a FLOOR. The lengths
# remain exact; only the times carry the assumption.
TROOPER_SPEED = 248.0        # m_flWalkSpeed, trooper_normal
TROOPER_RUN_SPEED = 512.0    # m_flRunSpeed, for reference, not used below
UNITS_PER_M = 39.37


def route_length(route):
    total = 0.0
    for a, b in zip(route, route[1:]):
        dx, dy, dz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        total += (dx * dx + dy * dy + dz * dz) ** 0.5
    return total


INCOMPLETE = {spec["lane"] for spec in LANES
              if not spec.get("complete", True) and not spec.get("pair")}


def report_lengths(paths):
    """Lane lengths, and the distance to the mirror point.

    Troopers from both sides walk the SAME path in opposite directions, so
    the waves meet near the middle. The number that matters for lane parity
    is the distance from each base to the mirror point: if the three lanes
    differ there, one lane's wave arrives before the others and the map is
    unfair in a way no amount of geometry symmetry fixes.
    """
    print("\nlane lengths")
    lengths = []
    approx = 0
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
        lengths.append(total)
        # The midpoint split is printed for interest only. It is taken at
        # whichever node falls nearest the centre, so on a lane that passes
        # the middle without stopping near it the two halves are a sampling
        # artefact rather than a measurement. Not a defect, and no longer
        # worth a warning per slot.
        if best is not None and best > 500.0:
            approx += 1
    if approx:
        print("  (%d slot(s) have no node within 500 u of the centre, so their"
              % approx)
        print("   midpoint split above is approximate. Lengths are exact.)")
    if TROOPER_SPEED <= 0:
        print("  (no trooper speed known, so no times, see TROOPER_SPEED)")
        return

    # LANE PARITY, measured on TOTAL LENGTH rather than time to the middle.
    #
    # An earlier version of this report compared base-to-midpoint times and
    # warned when they differed by more than three seconds. That check is
    # gone, on the user's call 2026-08-23, and the reasoning is worth keeping:
    # waves do not have to meet at the geometric centre, and on a rotationally
    # symmetric map they will meet somewhere sensible regardless, because both
    # halves of a lane are the same polyline. What actually has to match is
    # the LENGTH of one lane against another, since that is what decides
    # whether all three lanes are contested on a similar cadence.
    #
    # The old check was also measuring the wrong thing. The split is taken at
    # whichever node happens to fall nearest the middle, and on the side lanes
    # that node is 1,800 to 2,000 u away, so it reported a 7 s spread on
    # routes whose totals differ by 2%. It was reporting sampling error.
    if len(lengths) > 1:
        lo, hi = min(lengths), max(lengths)
        print("\nlane parity, by total route length")
        print("  shortest %8.1f u (%.1f m)" % (lo, lo / UNITS_PER_M))
        print("  longest  %8.1f u (%.1f m)" % (hi, hi / UNITS_PER_M))
        spread = (hi - lo) / lo * 100.0
        print("  spread   %8.1f u (%.1f%%)" % (hi - lo, spread))
        if TROOPER_SPEED > 0:
            print("  at %.0f u/s that is %.1f s between the shortest and"
                  " longest lane" % (TROOPER_SPEED, (hi - lo) / TROOPER_SPEED))
        if spread > 5.0:
            print("  OVER 5%%. One lane is meaningfully longer than another.")
        else:
            print("  within 5%, lanes are comparable.")


LEGACY_SPAWN_CLASSES = ("info_team_spawn",)


def strip_legacy_spawns(plan):
    """Remove UNNAMED team spawns this script did not write.

    THIS DELETES SOMETHING BATCH13 DID NOT CREATE, which no other batch script
    does, so the rule is deliberately narrow: only info_team_spawn, only where
    the entity has no `name`, and only where it is not already marked as
    batch13's own. Everything batch13 writes carries a name, so a named spawn
    is either mine and rebuilt anyway or somebody else's and left alone.

    WHY AT ALL. The plan carried two of these from an earlier session, at
    placeholder coordinates, and they were not mirrors of each other:
    (25, -530, 435) mirrors to (895.2, 12700.1, 435), while the second sat at
    (1494, 4854, 3). Leaving them would mean two spawn pairs, one symmetric
    and one not, and the emitted map would have four spawn points.
    """
    before = len(plan["entities"])
    kept = []
    for e in plan["entities"]:
        if (e.get("classname") in LEGACY_SPAWN_CLASSES
                and not e.get("name")
                and not e.get(MARK)):
            print("  removing legacy %s at %s (unnamed, not batch13's)"
                  % (e["classname"], [round(v) for v in e["origin"]]))
            continue
        kept.append(e)
    plan["entities"] = kept
    n = before - len(kept)
    if n:
        print("  removed %d legacy spawn(s)" % n)
    return n


def main(path):
    with open(path) as f:
        plan = json.load(f)

    plan.setdefault("entities", [])
    plan.setdefault("paths", [])
    strip_previous(plan)
    strip_legacy_spawns(plan)

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
    print("\nWHAT IN THIS RUN IS REAL, 2026-08-23")
    print("  READ      lane routes, guardians, walkers, guardian shops,")
    print("            secret shop, urn dropoff, base shop, spawn room,")
    print("            team spawn")
    print("  DERIVED   trooper spawns, from each lane's first node")
    print("  INVENTED  every volume SIZE, all angles, camps, breakables,")
    print("            bridge buffs, minimap corners, ziplines, zap and")
    print("            boost volumes, midboss")
    print("  ABSENT    shrines (destroyable_building), the barrack")
    print("            bosses guarding them, patron. Readings pending.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else
                  "docs/plans/dust2_full.json"))
