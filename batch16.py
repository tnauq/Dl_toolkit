#!/usr/bin/env python3
"""batch16 - jungle camps, teleporters, sinners and the powerup, from readings.

RUNS LAST, after batch13/14/15. batch13 rebuilds the whole entity set from
scratch, so anything here that touched entities before it would be deleted
again; and batch15 wires shops, which this does not touch.

    SCRIPTS: batch13.py batch14.py batch15.py batch16.py

WHAT IT OWNS
    3   t1 camps        info_neutral_trooper_camp + creature spawns
    10  t2 camps
    6   t3 camps
    2   teleporters     POSITION ONLY - see UNKNOWN CLASSNAMES below
    2   single sinners  POSITION ONLY
    1   double sinner   POSITION ONLY
    1   powerup         citadel_item_powerup_spawner

All authored for the TEAM-2 HALF ONLY. Every one gets its mirrored twin the
same way batch13 does - proper rotation about (460.1, 6085.05) - and camps are
NEUTRAL, so teamnumber is not flipped and the CampName takes the m_ prefix
instead. Do not author the far half by hand.

FILL IN THE TABLE. Every row below starts as None. Paste the viewer's
`copy pos` in, one row at a time if you like: a row still at None is SKIPPED
with a line in the report, not an error, so this can be run half-filled and
rerun as more readings arrive.

RERUNNABLE, like every batch script here. It deletes everything carrying its
own mark and rebuilds. It ALSO deletes three of batch13's placeholders by
name, because this file supersedes them and leaving them in would put an
invented camp and an invented powerup on the map beside the real ones:

    camp_west_weak (+ its spawns), crate_west_1, bridge_buff_west, and m_ twins

That strip is by NAME and nothing else, the same narrow shape as batch13's
strip of the two legacy team spawns.

UNKNOWN CLASSNAMES. Neither a teleporter nor sinner's sacrifice appears
anywhere in this repo or in dl_example, so there is no classname to emit and a
guessed one would convert, verify and load while doing nothing. Their readings
are kept in the table and printed in the report; nothing is written into the
plan until EMIT_UNKNOWN is turned on and the two classnames below are real.
The positions are not lost, they are just not entities yet.

WHAT IS INVENTED HERE
  - subclass_name for the t2 and t3 camps. Only neutral_camp_weak is
    confirmed, off batch13's own camp. The other two are the obvious shape of
    the family and nothing more.
  - ENeutralTrooperType per tier.
  - creature count per camp and their offsets from the camp origin.
  - spawn timings.
  - the powerup carries NO keyvalues at all, which IS read from dl_example.

    python3 batch16.py [docs/plans/dust2_full.json]
"""

import json
import math
import sys

X_PLANE = 460.1
Y_PLANE = 12170.1 / 2.0     # 6085.05
PREFIX = "m_"
MARK = "_batch16"

# Turn on only when both classnames below are read off the shipped strings.
# SOLVED 2026-08-29, off deadlockmodding.pages.dev/entity-list - a dump of
# every class derived from CBaseEntity, made with CS2ServerGUI:
#
#     CCitadelTeleportTrigger     citadel_trigger_teleport
#     CCitadelTeleportLocation    info_teleport_location
#
# The trigger is the volume you walk into; the LOCATION is where you come
# out, and nobody had guessed there was a second entity at all. The name
# follows the same citadel_trigger_* convention as climb_rope, push,
# speed_boost and idol_return - which is why it was the first of the seven
# probe spellings, and why the LLM's trigger_citadel_teleport is not in the
# dump at all.
#
# The same dump confirms trigger_catapult (CCitadelCatapultTrigger),
# destroyable_building (CCitadel_Destroyable_Building) and every other
# classname this file emits.
EMIT_UNKNOWN = True
TELEPORTER_CLASS = "citadel_trigger_teleport"
TELEPORT_LOCATION_CLASS = "info_teleport_location"
SINNER_CLASS = "UNKNOWN"          # still: the sinner is a unit, not a class

# ---------------------------------------------------------------------------
# THE SPELLING PROBE. Two classnames came from an LLM search and BOTH invert
# a convention this project has actually read:
#
#     it said   trigger_citadel_teleport
#     but every Deadlock trigger in dl_example is citadel_trigger_* -
#     climb_rope, push, speed_boost, idol_return. None are trigger_citadel_*.
#
#     it said   citadel_sinners_sacrifice
#     but npc_units.vdata calls the unit neutral_sinners_sacrifice, next to
#     neutral_camp_* and neutral_trooper_*.
#
# Neither string appears in dl_example, in the vdata, or in any search that
# returned a game file. So they are NOT trusted - but they are free to test,
# and a compile answers in one run what no amount of searching has.
#
# With SPELLING_PROBE on, every candidate spelling is emitted at the SAME
# position, one entity each, named so the compile log names the spelling:
#
#     probe_tele_a__citadel_trigger_teleport
#     probe_tele_b__trigger_citadel_teleport      <- the LLM's
#     ...
#
# A compiler that rejects unknown classnames will name the ones it does not
# know, and whatever survives is the right spelling. A compiler that accepts
# anything tells you nothing, in which case load the map and see which one
# does something.
#
# THIS IS A DIAGNOSTIC, NOT CONTENT. Turn it off before anyone plays the
# map: it puts several overlapping entities at each teleporter and sinner.
# OFF. The teleporter is known, so there is nothing left to probe for. The
# tables below are kept because the same trick will be worth repeating the
# next time a classname is in doubt.
#
# SETTLED 2026-08-29 against citadel.fgd. The probe never needed to run: the
# FGD is the entity table the compiler itself validates against, and it names
# exactly one of the four teleporter candidates and none of the three sinner
# ones. Verdicts recorded per line below. Keep the tables as a worked example
# of the trick, not as live candidates.
SPELLING_PROBE = False
TELEPORTER_SPELLINGS = [
    "citadel_trigger_teleport",     # CORRECT - the only one in citadel.fgd
    "trigger_citadel_teleport",     # the LLM's answer. Not in the FGD.
    "citadel_teleport",             # not in the FGD
    "trigger_teleport",             # the Source 1 / generic name. Not in it.
]
# ALL THREE ARE WRONG. citadel.fgd has no class under any of these names.
# What it does have is `npc_neutral_sinners_sacrifice_hideout` - note the
# _hideout suffix, so that one is the Hideout mode's version and may not be
# what a lane map wants - and, separately, an ENeutralTrooperType of 6
# labelled "Sinner's Sacrifice" on info_neutral_trooper_camp. The camp route
# is the likelier one. See the SINNER'S SACRIFICE note in TIERS below: the
# FGD lists 6 (Sinner's) and 12 (Breakable Vault) as DIFFERENT types, which
# means sinner and vault are not the same thing after all.
SINNER_SPELLINGS = [
    "neutral_sinners_sacrifice",    # the unit name from the vdata. Not a class.
    "citadel_sinners_sacrifice",    # the LLM's answer. Not a class.
    "citadel_breakable_prop",       # a real class, but not the sinner
]

# Camp tiers. subclass_name and ENeutralTrooperType decide what spawns.
# neutral_camp_weak is READ, off the camp batch13 already carries. The other
# two are GUESSES with the shape of the family.
# READ 2026-08-26 off dl_example's own 11 camps, via the classname probe.
# The family is neutral_camp_weak / _medium / _strong / _vaults / _midboss.
# There is NO neutral_camp_normal - that was a guess and it was wrong.
# ENeutralTrooperType runs 1, 2, 3, 5 on camps (12 also appears on spawns).
#
# STILL INFERRED: which interval goes with which tier. The fixture uses
# InitialSpawnDelayInSeconds 120 on 9 of 11 camps, and SpawnIntervalInSeconds
# of 120, 300 and 360 - but the probe reports values per key, not per entity,
# so nothing here says the 360 belongs to the strong camp. The mapping below
# is the obvious one, not a reading.
TIERS = {
    "t1": {"subclass": "neutral_camp_weak",     # read
           "trooper_type": "1",                 # read
           "creatures": 3,
           # CONFIRMED per-entity 2026-08-26: weak 120/120, medium 120/300,
           # strong 120/360. Your shortest-to-longest ordering was right.
           "initial_delay": "120", "interval": "120"},
    "t2": {"subclass": "neutral_camp_medium",   # read
           "trooper_type": "2",                 # read
           "creatures": 4,
           "initial_delay": "120", "interval": "300"},
    "t3": {"subclass": "neutral_camp_strong",   # read
           "trooper_type": "3",                 # read
           "creatures": 4,
           "initial_delay": "120", "interval": "360"},
    # SINNER'S SACRIFICE, on your read that sinner = vault. The subclass
    # string is READ off dl_example; the pairing to "sinner" is YOURS, not
    # something the fixture says. ENeutralTrooperType is the one field still
    # unread: two of the eleven camps leave it empty and one of those is
    # probably this, but the probe reports values per key rather than per
    # entity, so nothing pairs them. Empty is what goes in until that is
    # settled - see PROBE.md.
    # READ per-entity 2026-08-26: the vault camp carries an EMPTY trooper
    # type and 120/120 timings. The blank is deliberate in the fixture, not
    # missing data - dl_example labels it "Neutral Trooper Type - None".
    # 2026-08-29, citadel.fgd: ENeutralTrooperType enumerates 6 as "Sinner's
    # Sacrifice" and 12 as "Breakable Vault" - SEPARATE VALUES. So sinner and
    # vault are not the same thing, and the pairing this entry was built on
    # does not hold. The entry itself is still a faithful read of the
    # fixture's vault camp; what is wrong is calling it the sinner.
    # UNCHANGED PENDING A DECISION: switching these four sites to type 6
    # needs a subclass to go with it, and the FGD names none. Left as-is
    # rather than guessed at.
    "vault": {"subclass": "neutral_camp_vaults",      # read
              "trooper_type": "",                     # read, genuinely empty
              "creatures": 3,
              "initial_delay": "120", "interval": "120"},
    # THE SINNER, split off from "vault" 2026-08-29 on your call. The FGD
    # lists 6 "Sinner's Sacrifice" and 12 "Breakable Vault" as separate
    # ENeutralTrooperType values, so the two are not the same camp.
    # The type is READ. The subclass is BORROWED from the vault camp,
    # because the FGD names no subclass for a sinner and neutral_camp_vaults
    # is the closest real one - it is the only camp family member that is
    # a static thing to break rather than a spawner of creatures. If the
    # sinner comes out looking like a vault, this pairing is why.
    # Timings copied from the vault camp, and inert either way (see the
    # emission note in make_camp).
    "sinner": {"subclass": "neutral_camp_vaults",     # borrowed, not read
               "trooper_type": "6",                   # read, citadel.fgd
               "creatures": 3,
               "initial_delay": "120", "interval": "120"},
    # THE MIDBOSS IS A CAMP: there is no npc_ classname for it. Both timings
    # at -1, so it does not respawn on a clock.
    "midboss": {"subclass": "neutral_camp_midboss",   # read
                "trooper_type": "5",                  # read
                "creatures": 1,
                "initial_delay": "-1", "interval": "-1"},  # read
}

# Creature offsets from the camp origin, by creature count. A ring, so a camp
# is not a stack of entities at one point. INVENTED: no real camp footprint
# was measured. RADIUS is deliberately smaller than the 240 u the scout used
# for a pocket, so the whole camp fits inside the room it was crosshaired in.
RING_RADIUS = 110.0


def ring(n):
    # A camp of one is the midboss: it stands ON the camp point, not on a
    # ring around it.
    if n == 1:
        return [[0.0, 0.0, 0.0]]
    return [[round(RING_RADIUS * math.cos(2 * math.pi * i / n), 2),
             round(RING_RADIUS * math.sin(2 * math.pi * i / n), 2),
             0.0] for i in range(n)]


# ---------------------------------------------------------------------------
# THE READINGS. Team-2 half only. Paste `copy pos` into origin and put the box
# name in note, so a later re-survey knows what moved.
#
#     ("camp_t2_4", [x, y, z], "axis_123"),
#
# A row left at None is skipped, reported, and costs nothing.
# ---------------------------------------------------------------------------
CAMPS_T1 = [
    ("camp_t1_1", [2133.0, 8449.0, 213.0], "m_merged_721"),
    ("camp_t1_2", [-1159.0, 9532.0, 213.0], "m_gapfill_38_26"),
    ("camp_t1_3", [-776.0, 8828.0, 373.0], "m_axis_77"),
]

CAMPS_T2 = [
    ("camp_t2_1", [-1590.0, 10421.0, 213.0], "m_axis_193"),
    ("camp_t2_2", [-2087.0, 10296.0, 213.0], "m_gapfill_47_23"),
    ("camp_t2_3", [-1398.0, 8845.0, 0.0], "m_axis_0"),
    ("camp_t2_4", [-4923.0, 7924.0, 213.0], "xtun_lo_room_g_floor"),
    ("camp_t2_5", [-1.0, 7352.0, 0.0], "m_axis_0"),
    ("camp_t2_6", [1110.0, 9288.0, 213.0], "m_axis_551_ext"),
    ("camp_t2_7", [933.0, 11536.0, 277.0], "m_ramp_479_down_a"),
    ("camp_t2_8", [3361.0, 8100.0, 907.0], "m_xtun_up_room_d_floor"),
    ("camp_t2_9", [4319.0, 7625.0, 213.0], "m_xtun_lo_room_e_floor"),
    ("camp_t2_10", [4259.0, 5370.0, 365.0], "m_xtun_up_room_a_floor"),
]

CAMPS_T3 = [
    ("camp_t3_1", [5133.0, 6799.0, 365.0], "m_xtun_up_tall_floor"),
    ("camp_t3_2", [2854.0, 9238.0, 720.0], "m_axis_761"),
    ("camp_t3_3", [-654.0, 10419.0, 761.0], "m_axis_473"),
    ("camp_t3_4", [-282.0, 10426.0, 761.0], "m_axis_473"),
    ("camp_t3_5", [-3533.0, 11288.0, 477.0], "m_bay_tun_landing1"),
    ("camp_t3_6", [-113.0, 11656.0, 213.0], "m_axis_125"),
]

# Position only until the classnames are known.
TELEPORTERS = [
    # centre of the batch17 room, computed not read: it is the
    # midpoint of the four faces, so it moves if the room does.
    ("tele_1", [-353.4, 506.75, 426.75], "axis_546_ext571"),
    ("tele_2", [2107.1, -80.0, 213.4], "gapfill_39_8_ext451"),
]

# Four sinner sites. The "double" is not one entity: in the game it is two
# ordinary sinners standing near each other, so sinner_3 and sinner_4 are the
# pair and carry no special classname or keyvalue. They are 691 u apart, which
# is under NEAR_WARN and will report as a near pair - that is expected here
# and is the one warning to ignore.
SINNERS = [
    ("sinner_1", [1721.0, 9719.0, 253.0], "m_axis_586"),
    ("sinner_2", [-1647.0, 6766.0, 0.0], "stitch_ground"),
    ("sinner_3", [324.0, 12027.0, 213.0], "m_axis_125"),
    ("sinner_4", [216.0, 11344.0, 213.0], "m_axis_125"),
]

# citadel_item_powerup_spawner. ZERO keyvalues, read from dl_example: the
# position is the whole content. One here plus its twin is the two on the
# real map.
POWERUPS = [
    ("powerup_1", [-706.0, 5390.0, 640.0], "m_corner_plat_n"),
]

# ---------------------------------------------------------------------------
# BRUSH VOLUMES. Same shape batch13 emits: the child mesh rides in "mesh" and
# carries the extents. Both classnames here are READ - batch13 took them from
# dl_example - so unlike the teleporters and sinners these go straight in.
#
# A volume centred on the mirror point is NOT twinned, the same rule batch13
# applies: its twin would be itself, in the same place, doubled.
# ---------------------------------------------------------------------------
BRUSHES = [
    {
        # Moved up out of the old pit into the hexagon room. batch13 puts
        # this at the map centre but at z 435, which is now three floors
        # below the fight. Same classname and keys, new position and size.
        # The SIZE is invented: batch13's 1024 square was for a pit, and
        # this wants to cover the room's middle without reaching the walls,
        # so a team has to commit inside it.
        # NOT called midboss_shield. batch13 emits an entity of that name and
        # runs FIRST, so both existed at once and batch13 died on a duplicate
        # before batch16 could ever strip the placeholder. The rename breaks
        # that ordering trap; the strip below still removes batch13's.
        "name": "midboss_shield_hex",
        "classname": "trigger_midboss_shield",
        "origin": [460.1, 6085.05, 1707.1],
        "extents": [1600.0, 1600.0, 800.0],
        "properties": {"StartDisabled": "0", "spawnflags": "4097"},
    },
    {
        # Down the triangle hole beside hex3_blk_300. 640 tall, matching the
        # rope batch13 already carries, hung from the room floor at 1307.1 -
        # so it ends at 667.1, and merged_84's top is 666.9. That is luck
        # rather than design, but it lands.
        "name": "rope_tri_300",
        "classname": "citadel_trigger_climb_rope",
        "origin": [1111.55, 4956.7, 987.1],
        "extents": [96.0, 96.0, 640.0],
        "properties": {"targetname": "", "spawnflags": "4097"},
    },
    {
        # ---- jump pads ------------------------------------------------
        # trigger_catapult and its info_target_server_only landing marker
        # are both READ, off dl_example via batch13. `target` names the
        # marker, so the pair has to be authored together or the pad
        # launches at nothing.
        #
        # CONFIRMED 2026-08-29 against citadel.fgd, which describes the class
        # as "Bouncepad/Fan Trigger" and lists exactly two keys:
        # launch_speed (default 1000) and target ("Pair with a
        # info_target_server_only entity to launch entities at"). Both names
        # are right and this pairing is exactly what the FGD prescribes.
        #
        # THAT ALSO ANSWERS "ARC OR BLINK": a catapult LAUNCHES. These two
        # rooms are jump pads, not teleporters, and the separate
        # citadel_trigger_teleport pair below is the teleporter. The FGD's
        # default speed is 1000 against the 800 used here, which is another
        # reason the 800 wants testing.
        #
        # The pad's SIZE and launch_speed are invented - batch13's 128
        # square and 800 are the only precedent, and neither was measured.
        # The speed in particular is not derived from the distance to the
        # landing marker: whether 800 carries a player 1550 u is unknown
        # and wants testing in game.
        "name": "catapult_a",
        "classname": "trigger_catapult",
        "origin": [-574.0, 5259.0, 640.0],
        "extents": [128.0, 128.0, 64.0],
        "properties": {"targetname": "catapult_a",
                       "target": "catapult_a_land",
                       "launch_speed": "800", "spawnflags": "4097"},
    },
    {
        "name": "catapult_b",
        "classname": "trigger_catapult",
        "origin": [1795.0, 4052.0, 667.0],
        "extents": [128.0, 128.0, 64.0],
        "properties": {"targetname": "catapult_b",
                       "target": "catapult_b_land",
                       "launch_speed": "800", "spawnflags": "4097"},
    },
    {
        # Beside hex3_blk_240. Nothing under this one: the rope ends in air
        # at 667.1 and the drop below that is open to z 107 at best. Left
        # floating on purpose.
        "name": "rope_tri_240",
        "classname": "citadel_trigger_climb_rope",
        "origin": [-191.35, 4956.75, 987.1],
        "extents": [96.0, 96.0, 640.0],
        "properties": {"targetname": "", "spawnflags": "4097"},
    },
]

# The midboss, at the centre of the hexagon room, standing over the hole on
# whatever ends up being the lid. It is a camp, not an npc - see TIERS above.
# Sits on the mirror point, so it is not twinned.
MIDBOSS = ("midboss", [460.15, 6085.05, 1307.1], "the hexagon room floor")

# ---------------------------------------------------------------------------
# THE BASE OBJECTIVE CHAIN, from your readings on the m_ half. Authored on the
# BASE half as usual, so every number here is the mirror of what you sent.
#
# BASE GUARDS. Two per arch, three arches. The arch openings were MEASURED off
# the geometry rather than guessed: a ray sweep at head height finds the
# narrowest axis through each opening, which is the wall-to-wall direction,
# and the pair sits at the thirds of that span.
#
#   arch 1  shallow_869_d562, a wall arch    487 wide, floor 213.0
#   arch 2  hex_tun_n mouth                  385 wide, floor 426.8
#   arch 3  hex_tun_nw mouth                 444 wide, floor 426.8
#
# ARCH 3 IS COARSER THAN THE OTHER TWO. Its fine sweep did not finish in the
# time available, so its numbers come from a 2-degree pass rather than a
# 0.5-degree one. The pair may sit a few units off the opening's true centre
# line; worth an eyeball in the viewer before it matters.
#
# LANE ASSIGNMENT is by which arch, and it is a GUESS: arch 2 faces the mid
# lane and arches 1 and 3 the sides, so they take 1, 3 and 6 to match the
# LANES table. Nothing was read that says which arch belongs to which lane.
BASE_GUARDS = [
    # MEASURED off the jamb readings, which is why these are exact where the
    # first attempt's were not. A ray sweep was finding the wrong axis at two
    # of the three arches; two crosshaired jambs give the opening's width and
    # direction outright, and the pair sits at the thirds of it.
    #
    #   nw arch   340.4 wide, centre (-1199.5, -3101.0)
    #   n  arch   330.0 wide, centre (0.0, -2404.5)
    #   ne arch   330.9 wide, centre (1211.5, -3100.0)
    #
    # Floor is 426.8, the base hexagon's own. LANE ASSIGNMENT IS STILL A
    # GUESS: the n arch faces the mid lane and the other two the sides.
    ("guard_nw1", [-1228.7, -3149.7, 426.8], "3", "hex_wall_nw arch"),
    ("guard_nw2", [-1170.3, -3052.3, 426.8], "3", "hex_wall_nw arch"),
    ("guard_n1", [-55.0, -2404.0, 426.8], "1", "hex_wall_n arch"),
    ("guard_n2", [55.0, -2405.0, 426.8], "1", "hex_wall_n arch"),
    ("guard_ne1", [1184.3, -3052.0, 426.8], "6", "hex_wall_ne arch"),
    ("guard_ne2", [1238.7, -3148.0, 426.8], "6", "hex_wall_ne arch"),
]

# THE SHRINES. destroyable_building, CONFIRMED 2026-08-27 by npc_units.vdata:
#
#     m_sAmberModelName   models/npc/shrine_amber/shrine_amber.vmdl
#     m_sSapphModelName   models/npc/shrine_sapphire/shrine_sapphire.vmdl
#     m_iMaxHealthGenerator        5000
#     m_iMaxHealthGeneratorSecond 10000
#     m_iMaxHealthFinal            8775
#
# 5000 was the wiki number and it matches m_iMaxHealthGenerator exactly, so
# building_health stays. The model is now the real shrine rather than the
# generator placeholder.
#
# THE MODEL IS PER TEAM and the twin does not swap it. VData carries an amber
# and a sapphire name, so the entity may well pick for itself from teamnumber
# - in which case setting `model` at all is redundant. Both copies currently
# say amber. If the far shrine renders the wrong colour, that is why.
SHRINES = [
    ("shrine_w", [-732.5, -1982.2, 426.8], "shrine_w room"),
    ("shrine_e", [732.5, -1982.2, 426.8], "shrine_e room"),
]

# THE PATRON IS npc_boss_tier3, READ 2026-08-27 off npc_units.vdata:
#
#     npc_boss_tier3   models/npc/patron_amber/patron_amber.vmdl
#                      m_nMaxHealth 12000, m_nPhase2Health 12000
#                      m_PatronTransformStartSound "Patron.Phase1.Transform..."
#                      Phase1/Phase2 lasers, observer origins, dying sequence
#
# It is the patron, with two phases, and there is no ambiguity left. That
# means MY EARLIER CASE WAS RIGHT AND THE 2026-08-23 CALL WAS WRONG, and it
# also means batch13 currently places SIX PATRONS as lane objectives. The
# lane guardian is npc_boss_tier1:
#
#     npc_boss_tier1   models/npc/.../boss_tier_01_brazier_guardian.vmdl
#                      m_nMaxHealth 5500
#     npc_boss_tier2   models/npc/boss_tier_02_sun_walker/...
#                      6000 / 9000 / 12000 - the walker, which was right
#
# batch13 is not changed here; that is a one-line swap in ITS table and it
# ripples into batch15's shop wiring, so it wants doing deliberately rather
# than folded into this drop.
#
# THE PATRON, on the dais. A destroyable_building like the shrines, told apart
# from them by `final`, which is 1 here and 0 on every generator in
# dl_example. The name follows the fixture's own pattern, which the objective
# proxy below refers to by string.
#
# THE MODEL IS A PLACEHOLDER. No model for a patron has been read anywhere,
# and an EMPTY model path is a likely hard compile failure - preflight flags
# it as the single most probable thing to stop a build. So the patron borrows
# the shrines' generator model: obviously the wrong prop, obviously not
# finished, but it compiles and it is visible, and the POSITION - the part
# that came from a real reading - survives. Replace it when a real one turns
# up.
PATRON = ("patron", [-17.8, -3810.9, 533.0], "hex_dais_0")

# THE PROXY'S SUB-OBJECTIVES ARE THE SHRINES, changed 2026-08-27.
#
# They were wired to the WALKERS on the reading that titan = walker. Two
# independent signals now say otherwise:
#
#   - the wiki's objective chain: base guardians, then the shrine pair, then
#     the patron. Walkers are lane structures, not base ones.
#   - a Deadlock NPC reference describing the Titan as the thing that guards
#     the Patron and must be destroyed before the Patron can take damage -
#     which is the shrine's job. The same page describes the Walker
#     separately as front-line lane defence.
#
# Neither is a game file, so this is still a READ OFF THE INTERNET, not off
# the game. It is one line to put back: swap SHRINES for the walker names
# below. citadel.fgd or npc_units.vdata would settle it outright.
#
# The fixture's proxy has four sub-objective slots on lanes 1, 3, 4 and 6.
# This map has TWO shrines per team and they are not per-lane, so slots 3 and
# 4 are left empty and every lane field is 0 - dl_example's own team-3 proxy
# leaves its unused slots empty the same way.
#
# THE LANE-0 GUESS WAS RIGHT, and the four slots turned out to be a four-lane
# artifact rather than a count. citadel.fgd, 2026-08-29: 0 is "None" in the
# choices list, and only slots 1 and 2 have outputs declared.
#
# ALSO: THE PROXY IS NO LONGER EMITTED. See EMIT_PROXY in main - the FGD
# marks the class "Unused. Do not use." These readings are kept because they
# are correct and because putting the proxy back for one compile is a
# one-line change.
PROXY_SUBS = ["w", "e"]

# ---------------------------------------------------------------------------
# THE SKY AND THE SUN. READ off dl_example, which carries exactly one of each
# and wires them together: light_environment.skytexture names the env_sky's
# targetname, so the pair has to be authored as one thing.
#
# NEITHER IS A CEILING. env_sky is a point entity, not a lid - it does not cap
# the map and its elevation does not matter, which is why the roofline varying
# from 797.9 (median) to 2587.5 (the hexagon room's roof) is not a problem for
# it. What a varying roofline WOULD complicate is capping the map with
# sky-textured geometry, and nothing here does that. See the note in the
# handoff about whether the map wants a lid at all.
#
# Placed at the map centre and NOT twinned: one sky for both halves.
#
# The fixture's light_environment carries about forty keyvalues - cascades,
# shadow resolutions, occlusion tuning. Only the handful that were READ go in
# here; the rest are left for the compiler to default. That may look wrong
# without being broken, and is the first thing to tune if the map compiles
# dark or flat.
SKY_NAME = "sky_entity"
SKY = [
    {
        "name": "sky_entity",
        "classname": "env_sky",
        "origin": [X_PLANE, Y_PLANE, 2800.0],
        "properties": {
            "targetname": SKY_NAME,
            "skyname": "materials/skybox/light_test_psa_low_moon.vmat",
            "tint_color": "203 215 226",
            "StartDisabled": "0",
            "vscripts": "",
        },
    },
    {
        "name": "sun",
        "classname": "light_environment",
        "origin": [X_PLANE, Y_PLANE, 2800.0],
        # angles are INVENTED: nothing was read for the sun's direction, and
        # this is a plain overhead-ish angle rather than anything considered.
        "angles": [-60.0, 45.0, 0.0],
        "properties": {
            "targetname": "",
            "skytexture": SKY_NAME,      # names the env_sky above
            "color": "228 184 134",
            "brightness": "6",
            "enabled": "1",
            "castshadows": "1",
            "vscripts": "",
        },
    },
]

# Landing markers for the pads above. A point, not a volume, and the name
# must match the pad's `target` exactly - that string is the whole wiring.
LANDINGS = [
    ("catapult_a_land", [640.0, 3747.0, 667.0], "axis_363_slab_ns"),
    ("catapult_b_land", [3176.0, 5248.0, 401.0], "axis_42"),
]

# Placeholders this file supersedes. Deleted by name, with their m_ twins and,
# for the camp, its creature spawns.
SUPERSEDED = ["camp_west_weak", "crate_west_1", "bridge_buff_west",
              # batch13's midboss shield sits at the old pit height; the
              # one in BRUSHES above replaces it.
              "midboss_shield",
              # batch13's invented jump pad and its marker; the two real
              # pads above replace them.
              "catapult_west", "catapult_west_land"]

# Warn if a site and its own twin end up closer than this: on a rotationally
# symmetric map anything near the mirror point pairs with itself.
TWIN_WARN = 900.0
# Warn if two authored sites are closer than this.
NEAR_WARN = 700.0
# A site within this of the mirror of another site is the same site read
# twice, once from each end. Fatal: it would double the entity.
DUP_WARN = 300.0


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


def twin_of(e):
    """The mirrored copy. NEUTRAL only, so no team is flipped.

    Every key that names another entity is prefixed too, or the twin points
    back at the original half - which for a camp means both halves' creatures
    answering to one CampName.
    """
    t = json.loads(json.dumps(e))
    t["name"] = PREFIX + e["name"]
    t["origin"] = mirror_point(e["origin"])
    t["angles"] = mirror_angles(e.get("angles", [0.0, 0.0, 0.0]))
    props = dict(e.get("properties", {}))
    # `exitpoint` added 2026-08-29 with the FGD. Without it the mirrored
    # teleporter would have pointed at the ORIGINAL half's destination, so
    # both trigger pairs would have dumped players on the same side of the
    # map. The same class of silent mirror bug LINK_KEYS was written for.
    for k in ("targetname", "CampName", "target", "exitpoint", "parentname"):
        if props.get(k):
            props[k] = PREFIX + props[k]
    t["properties"] = props
    return t


def rot(angles):
    p, y, r = [math.radians(v) for v in angles]
    cy, sy = math.cos(y), math.sin(y)
    cp, sp = math.cos(p), math.sin(p)
    cr, sr = math.cos(r), math.sin(r)
    return [
        [cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
        [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
        [-sp, cp * sr, cp * cr],
    ]


def floor_under(plan, p, reach=400.0):
    """Name and top height of the highest box top at or below a reading.

    A pure geometry check with no walkability model: it answers "is there
    anything under this point", which is the fault a mistyped reading
    actually produces. Oriented, so a ramp is handled.
    """
    best = None
    for b in plan["boxes"]:
        o = b["origin"]
        e = b["extents"]
        if abs(p[0] - o[0]) > sum(e) or abs(p[1] - o[1]) > sum(e):
            continue
        R = rot(b.get("angles", [0.0, 0.0, 0.0]))
        # walk down from the reading looking for the first solid sample
        z = p[2] + 8.0
        while z > p[2] - reach:
            d = [p[0] - o[0], p[1] - o[1], z - o[2]]
            inside = True
            for k in range(3):
                local = sum(d[i] * R[i][k] for i in range(3))
                if abs(local) > e[k] / 2.0 + 1e-6:
                    inside = False
                    break
            if inside:
                if best is None or z > best[1]:
                    best = (b["name"], z)
                break
            z -= 13.3
    return best


def rows(table):
    return [(n, o, note) for n, o, note in table if o is not None]


# READ: every one of dl_example's 32 trooper spawns carries teamnumber 4 and
# HateCrateAttacker 1, midboss and jungle camps alike. Both were 0 here.
SPAWN_TEAM = "4"
# Objectives belong to a real team, unlike neutral camps. TEAM_A in batch13.
SPAWN_TEAM_OBJ = "2"
TEAM_WORD = "rebels"
# batch13's own lane -> colour map, needed to name the walkers the proxy
# points at. If batch13's changes, this must change with it.
# READ off batch13, not guessed: yellow is lane 1, orange lane 3, purple
# lane 6. An earlier draft here had these rotated, which would have pointed
# the proxy at walkers that do not exist.
LANE_COLOUR = {"1": "yellow", "3": "orange", "4": "blue", "6": "purple"}
SPAWN_HATE = "1"


def make_camp(name, origin, tier, team=SPAWN_TEAM):
    spec = TIERS[tier]
    camp_name = name + "_neutrals"
    out = []
    camp = {
        "name": name,
        "classname": "info_neutral_trooper_camp",
        "origin": [round(v, 4) for v in origin],
        "angles": [0.0, 0.0, 0.0],
        "properties": {
            "targetname": "",
            "vscripts": "",
            "CampName": camp_name,
            "ENeutralTrooperType": spec["trooper_type"],
            "subclass_name": spec["subclass"],
            # THESE TWO ARE INERT. citadel.fgd carries both keys COMMENTED
            # OUT and annotated "Unused", so the camp does not read them and
            # the timings come from elsewhere (the subclass, most likely).
            # Kept because they are a faithful copy of what dl_example's own
            # camps carry, they cost nothing, and if the annotation is wrong
            # the values are the right ones anyway. The upshot is that the
            # tier-to-interval mapping worried over above does not matter.
            "InitialSpawnDelayInSeconds": spec["initial_delay"],
            "SpawnIntervalInSeconds": spec["interval"],
        },
        MARK: True,
    }
    out.append(camp)
    if not on_mirror_point(origin):
        out.append(twin_of(camp))
    for i, off in enumerate(ring(spec["creatures"])):
        s = {
            "name": "%s_spawn%d" % (name, i),
            "classname": "info_neutral_trooper_spawn",
            "origin": [round(origin[0] + off[0], 4),
                       round(origin[1] + off[1], 4),
                       round(origin[2] + off[2], 4)],
            "angles": [0.0, 0.0, 0.0],
            "properties": {
                "targetname": "",
                "vscripts": "",
                "teamnumber": team,
                "CampName": camp_name,
                "ENeutralTrooperType": spec["trooper_type"],
                "CoverGroupID": "",
                "HateCrateAttacker": SPAWN_HATE,
            },
            MARK: True,
        }
        out.append(s)
        if not on_mirror_point(origin):
            out.append(twin_of(s))
    return out


TEAM_WORD_B = "combine"
TEAM_B = "3"
# Keys whose VALUE names another entity by targetname. On an objective twin
# these have to be swapped too, or the mirrored proxy wires itself to the
# base half's walkers - which it did, silently, on the first attempt.
# BossName belongs here too. Without it the far patron came out as
# rebels_patron on team 3 - a name that says one team and a teamnumber that
# says the other.
LINK_KEYS = ("final_objective", "sub_objective_1", "sub_objective_2",
             "sub_objective_3", "sub_objective_4", "targetname", "BossName")


# Names that are NOT ours to build and cannot be swapped by the rebels <->
# combine rule below. citadel.fgd enumerates npc_boss_tier3.BossName as
# exactly two values, and they use the SINGULAR "rebel" - so the generic rule
# matches neither, falls through, and would prefix the twin's to
# "m_boss_rebel_tier2_mid": off the enumeration, and pointing at the wrong
# team besides. (The "tier2" inside a tier3 name is Valve's, not a typo.)
EXPLICIT_SWAPS = {
    "boss_rebel_tier2_mid": "boss_combine_tier2_mid",
    "boss_combine_tier2_mid": "boss_rebel_tier2_mid",
}

# The base half is the rebels/north/amber side, so it takes the rebel value.
PATRON_BOSSNAME = "boss_rebel_tier2_mid"


def team_swap(name):
    """rebels <-> combine, anywhere in the string. batch13's own rule."""
    if name in EXPLICIT_SWAPS:
        return EXPLICIT_SWAPS[name]
    if TEAM_WORD in name:
        return name.replace(TEAM_WORD, TEAM_WORD_B, 1)
    if TEAM_WORD_B in name:
        return name.replace(TEAM_WORD_B, TEAM_WORD, 1)
    return PREFIX + name if name else name


def twin_objective(e):
    """The mirrored copy of a TEAM entity, not a neutral one.

    twin_of leaves teamnumber alone, which is right for camps and wrong for
    everything in the base: the far patron belongs to the other team and its
    proxy must name the other team's walkers. Both are swapped here.
    """
    t = json.loads(json.dumps(e))
    t["name"] = PREFIX + e["name"]
    t["origin"] = mirror_point(e["origin"])
    t["angles"] = mirror_angles(e.get("angles", [0.0, 0.0, 0.0]))
    props = dict(e.get("properties", {}))
    if props.get("teamnumber") == SPAWN_TEAM_OBJ:
        props["teamnumber"] = TEAM_B
    for k in LINK_KEYS:
        if props.get(k):
            props[k] = team_swap(props[k])
    t["properties"] = props
    return t


def make_objective(name, origin, classname, props):
    e = {
        "name": name,
        "classname": classname,
        "origin": [round(v, 4) for v in origin],
        "angles": [0.0, 0.0, 0.0],
        "properties": dict(props),
        MARK: True,
    }
    return [e, twin_objective(e)]


def on_mirror_point(o, tol=1.0):
    return (abs(o[0] - X_PLANE) < tol and abs(o[1] - Y_PLANE) < tol)


def make_brush(spec):
    """A volume, in the shape batch13 emits: extents live on a child mesh."""
    e = {
        "name": spec["name"],
        "classname": spec["classname"],
        "origin": [round(v, 4) for v in spec["origin"]],
        "angles": list(spec.get("angles", [0.0, 0.0, 0.0])),
        "properties": dict(spec["properties"]),
        "mesh": {
            "name": spec["name"] + "_vol",
            "origin": [0.0, 0.0, 0.0],
            "extents": [round(v, 4) for v in spec["extents"]],
            "angles": [0.0, 0.0, 0.0],
        },
        MARK: True,
    }
    out = [e]
    if not on_mirror_point(e["origin"]):
        out.append(twin_of(e))
    return out


def make_point(name, origin, classname, props=None):
    e = {
        "name": name,
        "classname": classname,
        "origin": [round(v, 4) for v in origin],
        "angles": [0.0, 0.0, 0.0],
        "properties": dict(props or {}),
        MARK: True,
    }
    return [e, twin_of(e)]


def strip_previous(plan, log):
    ents = plan.get("entities", [])
    before = len(ents)
    kept = [e for e in ents if not e.get(MARK)]
    log.append("stripped %d entities from a previous batch16 run"
               % (before - len(kept)))

    gone = []
    dead = set()
    for n in SUPERSEDED:
        dead.add(n)
        dead.add(PREFIX + n)
    out = []
    for e in kept:
        nm = e.get("name", "")
        base = nm.split("_spawn")[0]
        if nm in dead or base in dead:
            gone.append(nm)
            continue
        out.append(e)
    plan["entities"] = out
    if gone:
        log.append("superseded batch13 placeholders removed: %s"
                   % ", ".join(sorted(gone)))
    else:
        log.append("no batch13 placeholders present to supersede")
    return out


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_full.json"
    with open(path) as f:
        plan = json.load(f)

    log = []
    boxes_before = len(plan["boxes"])
    strip_previous(plan, log)

    wanted = {"camp_t1": 3, "camp_t2": 10, "camp_t3": 6, "teleporter": 2,
              "sinner": 4, "powerup": 1}
    # SINNERS is consumed above as camps, so it must not be walked again
    # below or every one would be emitted twice.
    have = {}
    new = []
    sites = []

    for tier, table in (("t1", CAMPS_T1), ("t2", CAMPS_T2), ("t3", CAMPS_T3)):
        filled = rows(table)
        have["camp_" + tier] = len(filled)
        for name, origin, note in filled:
            new += make_camp(name, origin, tier)
            sites.append((name, origin, note))

    # Volumes are NOT added to `sites`. Every check that runs over sites -
    # what is underneath it, how close it is to its own twin, whether it is
    # the mirror of another - is a check about a point on the floor, and a
    # volume hanging in the air fails all three for no reason. They get
    # their own checks below.
    brushes = []
    for spec in BRUSHES:
        made = make_brush(spec)
        new += made
        brushes.append((spec, len(made)))

    tier, origin, note = MIDBOSS
    # teamnumber 4 on the spawn, read off dl_example's own midboss camp.
    new += make_camp("midboss", origin, tier)
    sites.append(("midboss", origin, note))

    # base guards
    for name, origin, lane, note in BASE_GUARDS:
        new += make_objective(name, origin, "npc_barrack_boss", {
            "targetname": "",
            "vscripts": "",
            "teamnumber": SPAWN_TEAM_OBJ,
            "lanenum": lane,
            "LaneSide": "0",
            "CoverGroupID": "0",
            "BackdoorProtectionTrigger": "",
        })
        sites.append((name, origin, note))

    for nm2, o2, note2 in SHRINES:
        new += make_objective(nm2, o2, "destroyable_building", {
            "targetname": "%s_%s_shrine" % (TEAM_WORD, nm2.split("_")[1]),
            "vscripts": "",
            "model": "models/npc/shrine_amber/shrine_amber.vmdl",   # read
            "skin": "default",
            "bodygroups": "",
            "disableshadows": "0",
            "add_attribute": "",
            "add_modifier": "",
            "teamnumber": SPAWN_TEAM_OBJ,
            "lanenum": "1",
            "BackdoorProtectionTrigger": "",
            # BOTH OF THESE ARE MARKED "(Broken)" IN citadel.fgd. The shrine
            # will not take its health from building_health and will not
            # honour `final`. Left in place - they are harmless, they are
            # what the fixture carries, and "broken" is an annotation rather
            # than a promise. But do not tune shrine health here and expect
            # it to do anything.
            "building_health": "5000",
            "final": "0",
        })
        # CLASS CONFIRMED 2026-08-29. citadel.fgd tool-names
        # destroyable_building "Base Shrine" and describes it as "used
        # exclusively for base shrines", which is as direct as this gets.
        sites.append((nm2, o2, note2))

    # the patron, and the proxy that binds it to the walkers
    name, origin, note = PATRON
    new += make_objective(name, origin, "npc_boss_tier3", {
        "targetname": "%s_building_final" % TEAM_WORD,
        "vscripts": "",
        "teamnumber": SPAWN_TEAM_OBJ,
        "lanenum": "3",              # the fixture's own tier3 carries lane 3
        # BossName IS NOT A FREE STRING HERE. citadel.fgd enumerates exactly
        # two values, boss_rebel_tier2_mid and boss_combine_tier2_mid (the
        # tier2 naming on the tier3 class is Valve's, not a typo of ours).
        # On npc_boss_tier2 the FGD annotates its BossName list "//purely
        # naming"; on THIS class it does not, so the enumeration may be load
        # bearing. UNCHANGED pending a decision - see the FGD findings doc.
        # CONFORMED TO THE ENUMERATION 2026-08-29. Was "rebels_patron", a
        # name of our own. citadel.fgd allows exactly two values here and
        # npc_boss_tier2's list is annotated "//purely naming" while this
        # one is NOT, so the enumeration is treated as load bearing. The
        # twin's value comes from EXPLICIT_SWAPS, not the generic rule.
        "BossName": PATRON_BOSSNAME,
        "subclass_name": "npc_boss_tier3",
        # READ THIS BEFORE THE FIRST COMPILE. citadel.fgd on this class:
        # "Make sure to use cover groups for each of the boss states,
        # otherwise the game will be unbeatable." All three cover ids below
        # are EMPTY. dying_cover_id is where the patron moves before turning
        # into a core; vulnerable_cover_id is where it falls when it does.
        # With neither set, the second phase has nowhere to go, and the
        # FGD's word for that outcome is unbeatable. This needs
        # info_cover_point groups authoring - work nobody has started, and
        # not a keyvalue that can be filled in from a string.
        "CoverGroupID": "",
        "dying_cover_id": "",
        "vulnerable_cover_id": "",
        "BackdoorProtectionTrigger": "",
    })
    sites.append((name, origin, note))

    # ---- the shrine -> patron chain -----------------------------------
    #
    # THE PROXY IS NO LONGER EMITTED, decided 2026-08-29. citadel.fgd calls
    # citadel_final_objective_proxy "Final objective. Unused. Do not use."
    # Nothing else in the file is labelled that way, and shipping a class the
    # entity table itself tells you not to use is a poor bet when the whole
    # win condition hangs off it.
    #
    # AND THE REPLACEMENT DOES NOT EXIST YET. Wiring shrine -> patron by
    # entity I/O needs an INPUT on the patron to fire, and citadel.fgd
    # declares none: npc_boss_tier3 has BackdoorProtectionTrigger, BossName,
    # subclass_name, three cover ids and one output, OnBossKilled. No
    # SetVulnerable, no Enable, nothing. The whole file has 35 inputs and
    # every one belongs to fog, lighting, scenes, buoyancy, EnableDisable,
    # the speaking NPC, the defense sentry or the lane test.
    #
    # The outputs on the shrine are real and rich - OnDestroyed,
    # OnBecomeVulnerable, OnBecomeInvulnerable, OnRevitilized and five more -
    # so the SOURCE half of the wire is known and only the target is missing.
    # Inventing an input name is exactly the mistake `target` was: it would
    # emit clean, verify green, and do nothing.
    #
    # So this map currently has NO shrine-to-patron chain, by choice, rather
    # than a chain built on a class marked do-not-use. That is a REGRESSION
    # in behaviour and a deliberate one. To close it, one of:
    #
    #   1. Find the input. dl_example is the place to look - if its shrines
    #      carry connections, the input name is sitting in them. The entity
    #      survey reported 89 DmeConnectionData blocks and NO OWNER COLUMN,
    #      so nobody has yet seen which entity owns which wire. That is the
    #      single highest-value probe left.
    #   2. Compile with the proxy and see whether "Unused" means inert or
    #      just undocumented. Set EMIT_PROXY back to True for that run.
    #   3. Accept that the patron is always vulnerable, which is what this
    #      emits today.
    #
    # PROXY_SUBS, the lane readings and the slot-count findings are all kept
    # below the flag, because if 2 is the answer they are needed intact.
    EMIT_PROXY = False

    if EMIT_PROXY:
        proxy = {
            "targetname": "",
            "final_objective": "%s_building_final" % TEAM_WORD,
            "teamnumber": SPAWN_TEAM_OBJ,
        }
        # LANE 0 IS LEGAL, confirmed 2026-08-29. citadel.fgd makes each
        # sub_objective_lane_N a choices field and lists 0 : "None" alongside
        # 1 : "Yellow", 3 : "Orange", 4 : "Blue", 6 : "Purple". The zeroes
        # were a guess and the guess was right - a non-lane sub-objective is
        # a case the schema anticipates.
        #
        # AND THE FOUR SLOTS ARE A FOUR-LANE ARTIFACT, not a count. Those
        # colour names are the four lanes of the old layout, Blue being the
        # one that went away. Two filled slots plus an empty pair is the
        # correct shape for a three-lane map, which the outputs corroborate:
        # the FGD declares SubObjective1Destroyed/Revitilized and
        # SubObjective2Destroyed/Revitilized and NOTHING for slots 3 and 4.
        for i, side in enumerate(PROXY_SUBS, start=1):
            proxy["sub_objective_%d" % i] = "%s_%s_shrine" % (TEAM_WORD, side)
            proxy["sub_objective_lane_%d" % i] = "0"
        for i in range(len(PROXY_SUBS) + 1, 5):
            proxy["sub_objective_%d" % i] = ""
            proxy["sub_objective_lane_%d" % i] = "0"
        # A logic entity with no body. It sits on the patron so it mirrors
        # with it and is findable in the viewer; nothing depends on where.
        new += make_objective("final_objective_proxy", origin,
                              "citadel_final_objective_proxy", proxy)
        log.append("final_objective_proxy EMITTED - the FGD marks this class "
                   "'Unused. Do not use.'")
    else:
        log.append("")
        log.append("NO SHRINE -> PATRON CHAIN IN THIS PLAN.")
        log.append("  the proxy is dropped (citadel.fgd: 'Unused. Do not "
                   "use.') and entity I/O cannot replace it yet - the FGD")
        log.append("  declares no input on npc_boss_tier3 to fire. The "
                   "patron is vulnerable from the first second.")
        log.append("  To find the input: look for connections on "
                   "dl_example's own shrines. See the note in this file.")

    for spec in SKY:
        e = {
            "name": spec["name"],
            "classname": spec["classname"],
            "origin": [round(v, 4) for v in spec["origin"]],
            "angles": list(spec.get("angles", [0.0, 0.0, 0.0])),
            "properties": dict(spec["properties"]),
            MARK: True,
        }
        new.append(e)          # one sky for the whole map, never twinned
        log.append("%-16s %-24s at %.1f, %.1f, %.1f"
                   % (spec["name"], spec["classname"], *spec["origin"]))

    for name, origin, note in LANDINGS:
        new += make_point(name, origin, "info_target_server_only",
                          {"targetname": name})
        sites.append((name, origin, note))

    filled = rows(POWERUPS)
    have["powerup"] = len(filled)
    for name, origin, note in filled:
        new += make_point(name, origin, "citadel_item_powerup_spawner")
        sites.append((name, origin, note))

    # POSITION ONLY. Held back until the classnames are real; the readings
    # are still checked and reported so a bad one is caught now rather than
    # on the day the classname turns up.
    held = []
    # Sinners are emitted as camps. They were "vault" camps until
    # 2026-08-29; they are now their own tier carrying
    # ENeutralTrooperType 6, which citadel.fgd labels "Sinner's Sacrifice".
    # The subclass is still the vault's - see TIERS.
    filled = rows(SINNERS)
    have["sinner"] = len(filled)
    for name, origin, note in filled:
        new += make_camp(name, origin, "sinner")
        sites.append((name, origin, note))

    if SPELLING_PROBE:
        n_probe = 0
        for name, origin, note in rows(TELEPORTERS):
            for cn in TELEPORTER_SPELLINGS:
                new += make_point("probe_%s__%s" % (name, cn), origin, cn,
                                  {"targetname": ""})
                n_probe += 1
        for name, origin, note in rows(SINNERS):
            for cn in SINNER_SPELLINGS:
                props = {"targetname": ""}
                if cn == "citadel_breakable_prop":
                    # the one candidate that certainly needs a subclass
                    props["subclass_name"] = "neutral_sinners_sacrifice"
                new += make_point("probe_%s__%s" % (name, cn), origin, cn,
                                  props)
                n_probe += 1
        log.append("")
        log.append("SPELLING PROBE ON: %d extra entities counting twins, %d "
                   "spellings at each teleporter and %d at each sinner. "
                   "Diagnostic only - turn SPELLING_PROBE off before anyone "
                   "plays this."
                   % (n_probe * 2, len(TELEPORTER_SPELLINGS),
                      len(SINNER_SPELLINGS)))
        log.append("   whatever the compiler does not complain about is the "
                   "right spelling; the name after __ is the candidate.")

    for label, table, cls in (("teleporter", TELEPORTERS, TELEPORTER_CLASS),):
        filled = rows(table)
        have[label] = len(filled)
        for name, origin, note in filled:
            sites.append((name, origin, note))
            if EMIT_UNKNOWN and cls != "UNKNOWN":
                # THE TRIGGER AND ITS DESTINATION. A teleporter is two
                # entities: the volume you enter, and an
                # info_teleport_location you come out at. Each of the two
                # rooms sends to the OTHER, so tele_1's trigger targets
                # tele_2's location.
                #
                # THE KEYVALUE IS `exitpoint`, READ off citadel.fgd
                # 2026-08-29. It was `target` until then - the Source
                # convention, and a guess. The FGD's own text: "Remote
                # Destination ... The entity specifying the point to which
                # entities should be teleported." A `target` on this class
                # would have been ignored and walking in would have done
                # nothing, with no compile error to say why.
                #
                # The FGD also documents an optional local landmark: with one
                # set, entities keep their offset from it and their angles are
                # left alone. Not used here - without it, angles are forced to
                # the destination's, which is what two facing rooms want.
                other = "tele_2" if name == "tele_1" else "tele_1"
                new += make_point(name, origin, cls, {
                    "targetname": "%s_trigger" % name,
                    "exitpoint": "%s_dest" % other,
                    "StartDisabled": "0",
                })
                # THE DESTINATION'S OWN KEYS, added 2026-08-29 from the FGD.
                # info_teleport_location derives from Targetname, TeamNumber
                # and LaneNumber and adds objective(integer), default 3 -
                # annotated in the FGD itself as 'Objective? By default set
                # to 3?', question marks and all, so nobody knows what it
                # selects. 3 is what the file says the default is, so 3 is
                # what goes in.
                #
                # teamnumber 0 is "None" in the FGD's own TeamNumber list.
                # These two rooms are neutral map furniture, not base
                # infrastructure, so neither team owns them; a 2 or 3 here
                # would be a claim nothing supports. lanenum 0 for the same
                # reason - the rooms are not on a lane.
                new += make_point("%s_dest" % name, origin,
                                  TELEPORT_LOCATION_CLASS, {
                                      "targetname": "%s_dest" % name,
                                      "teamnumber": "0",
                                      "lanenum": "0",
                                      "objective": "3",
                                  })
            else:
                held.append((name, label))

    plan.setdefault("entities", []).extend(new)

    # ---- checks -------------------------------------------------------
    log.append("")
    for spec, n_made in brushes:
        e = spec["extents"]
        o = spec["origin"]
        log.append("%-16s %-30s %8.1f %9.1f  z %.1f..%.1f%s"
                   % (spec["name"], spec["classname"], o[0], o[1],
                      o[2] - e[2] / 2.0, o[2] + e[2] / 2.0,
                      "  (on the mirror point, not twinned)"
                      if n_made == 1 else ""))
    # A rope wants its top at the floor you step off, and the shield wants
    # its bottom on the floor the fight happens on. Both are 1307.1 now.
    ROOM_FLOOR = 1307.1
    for spec, _ in brushes:
        top = spec["origin"][2] + spec["extents"][2] / 2.0
        bot = spec["origin"][2] - spec["extents"][2] / 2.0
        if spec["classname"] == "citadel_trigger_climb_rope":
            if abs(top - ROOM_FLOOR) > 1.0:
                problems.append("%s's top is %.1f, not the room floor %.1f"
                                % (spec["name"], top, ROOM_FLOOR))
        if spec["classname"] == "trigger_midboss_shield":
            if abs(bot - ROOM_FLOOR) > 1.0:
                problems.append("%s's base is %.1f, not the room floor %.1f"
                                % (spec["name"], bot, ROOM_FLOOR))

    marks = {n: o for n, o, _ in LANDINGS}
    for spec, _ in brushes:
        tgt = spec["properties"].get("target")
        if not tgt:
            continue
        if tgt not in marks:
            problems.append("%s launches at %s, which nothing defines"
                            % (spec["name"], tgt))
            continue
        o, m = spec["origin"], marks[tgt]
        log.append("%-16s throws %.0f u out and %+.0f u up, to %s"
                   % (spec["name"], math.hypot(m[0] - o[0], m[1] - o[1]),
                      m[2] - o[2], tgt))

    log.append("")
    log.append("%-18s %10s %10s %9s  %s  %-22s %s"
               % ("name", "x", "y", "z", "side", "stands on", "note"))
    problems = []
    warnings = []
    for name, o, note in sites:
        f = floor_under(plan, o)
        stands = "%s @%.1f" % (f[0], f[1]) if f else "NOTHING UNDER IT"
        if not f:
            # Fatal for a camp: neutrals stand and path there, and a camp in
            # the air is a typed coordinate. Only a warning for a powerup,
            # which may be deliberately off the floor.
            # The midboss stands over the square hole on purpose: whatever
            # covers that hole does not exist yet, so no floor under it is
            # the expected state, not a fault.
            note_txt = "%s has no box under it within 400 u" % name
            (problems if name.startswith("camp_") else warnings).append(note_txt)
        d_twin = math.hypot(o[0] - (2 * X_PLANE - o[0]),
                            o[1] - (2 * Y_PLANE - o[1]))
        if on_mirror_point(o, 2.0):
            d_twin = 1e9        # it IS the mirror point; it is not twinned
        if d_twin < TWIN_WARN:
            warnings.append("%s is %.0f u from its own twin - too near the "
                            "mirror point" % (name, d_twin))
        # Which side of the seam a reading came from is INFORMATION, not a
        # fault. The mirror is an involution, so authoring on either half
        # produces the same pair; and the halves interleave anyway - the
        # powerup reading sits south of the plane on a box named m_. What
        # WOULD be a fault is reading both ends of a pair, which the
        # duplicate check below catches.
        side = "n" if o[1] > Y_PLANE else "s"
        log.append("%-18s %10.1f %10.1f %9.1f  %s  %-22s %s"
                   % (name, o[0], o[1], o[2], side, stands, note))

    for i in range(len(sites)):
        for j in range(i + 1, len(sites)):
            a, b = sites[i][1], sites[j][1]
            d = math.hypot(a[0] - b[0], a[1] - b[1])
            if d < NEAR_WARN:
                warnings.append("%s and %s are %.0f u apart"
                                % (sites[i][0], sites[j][0], d))
            # Reading BOTH ends of a pair authors four entities where two
            # were meant. Compares each site against the mirror of every
            # other, which is what a duplicate actually looks like.
            m = mirror_point(b)
            if math.hypot(a[0] - m[0], a[1] - m[1]) < DUP_WARN:
                problems.append(
                    "%s is the mirror of %s - only author one end of a "
                    "pair, the twin is generated" % (sites[i][0], sites[j][0]))

    log.append("")
    for k in ("camp_t1", "camp_t2", "camp_t3", "teleporter",
              "sinner", "powerup"):
        n, w = have.get(k, 0), wanted[k]
        log.append("%-14s %2d of %2d filled%s"
                   % (k, n, w, "" if n == w else "   <-- STILL TO READ"))

    if held:
        log.append("")
        log.append("HELD BACK, position recorded but no entity written:")
        for name, label in held:
            log.append("  %-18s %s classname is UNKNOWN" % (name, label))
        log.append("Set EMIT_UNKNOWN and the two classnames once they are")
        log.append("read off the shipped strings. Nothing is lost meanwhile.")

    if warnings:
        log.append("")
        log.append("WARNINGS, the run continues:")
        for w in warnings:
            log.append("  " + w)

    if problems:
        log.append("")
        log.append("PROBLEMS, nothing written:")
        for p in problems:
            log.append("  " + p)

    log.append("")
    log.append("entities now %d, added %d (each authored site plus its twin)"
               % (len(plan["entities"]), len(new)))

    if len(plan["boxes"]) != boxes_before:
        print("::error::box count moved: %d -> %d"
              % (boxes_before, len(plan["boxes"])))
        sys.exit(1)
    log.append("boxes %d, unchanged" % len(plan["boxes"]))

    # THE PLAN IS WRITTEN ONLY IF THE CHECKS PASS. A fatal fault means a
    # mistyped reading, and half-writing it would leave the next script in
    # the chain editing a file nobody meant to create. An unfilled row is
    # not a fault.
    if problems:
        print("\n".join(log))
        print("::error::batch16: %d problem(s), plan not written" % len(problems))
        sys.exit(1)

    with open(path, "w") as f:
        json.dump(plan, f, indent=1)
    print("\n".join(log))


if __name__ == "__main__":
    main()
