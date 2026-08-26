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
EMIT_UNKNOWN = False
TELEPORTER_CLASS = "UNKNOWN"
SINNER_CLASS = "UNKNOWN"

# Camp tiers. subclass_name and ENeutralTrooperType decide what spawns.
# neutral_camp_weak is READ, off the camp batch13 already carries. The other
# two are GUESSES with the shape of the family.
TIERS = {
    "t1": {"subclass": "neutral_camp_weak",   # read
           "trooper_type": "1",
           "creatures": 3,
           "initial_delay": "120", "interval": "120"},
    "t2": {"subclass": "neutral_camp_normal",  # GUESS
           "trooper_type": "2",
           "creatures": 4,
           "initial_delay": "150", "interval": "150"},
    "t3": {"subclass": "neutral_camp_strong",  # GUESS
           "trooper_type": "3",
           "creatures": 4,
           "initial_delay": "180", "interval": "180"},
}

# Creature offsets from the camp origin, by creature count. A ring, so a camp
# is not a stack of entities at one point. INVENTED: no real camp footprint
# was measured. RADIUS is deliberately smaller than the 240 u the scout used
# for a pocket, so the whole camp fits inside the room it was crosshaired in.
RING_RADIUS = 110.0


def ring(n):
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
    ("tele_2", [2107.1, 106.6, 213.4], "gapfill_39_8"),
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

# Placeholders this file supersedes. Deleted by name, with their m_ twins and,
# for the camp, its creature spawns.
SUPERSEDED = ["camp_west_weak", "crate_west_1", "bridge_buff_west"]

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
    for k in ("targetname", "CampName", "target", "parentname"):
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


def make_camp(name, origin, tier):
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
            "InitialSpawnDelayInSeconds": spec["initial_delay"],
            "SpawnIntervalInSeconds": spec["interval"],
        },
        MARK: True,
    }
    out.append(camp)
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
                "teamnumber": "0",
                "CampName": camp_name,
                "ENeutralTrooperType": spec["trooper_type"],
                "CoverGroupID": "",
                "HateCrateAttacker": "0",
            },
            MARK: True,
        }
        out.append(s)
        out.append(twin_of(s))
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
    have = {}
    new = []
    sites = []

    for tier, table in (("t1", CAMPS_T1), ("t2", CAMPS_T2), ("t3", CAMPS_T3)):
        filled = rows(table)
        have["camp_" + tier] = len(filled)
        for name, origin, note in filled:
            new += make_camp(name, origin, tier)
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
    for label, table, cls in (("teleporter", TELEPORTERS, TELEPORTER_CLASS),
                              ("sinner", SINNERS, SINNER_CLASS)):
        filled = rows(table)
        have[label] = len(filled)
        for name, origin, note in filled:
            sites.append((name, origin, note))
            if EMIT_UNKNOWN and cls != "UNKNOWN":
                new += make_point(name, origin, cls)
            else:
                held.append((name, label))

    plan.setdefault("entities", []).extend(new)

    # ---- checks -------------------------------------------------------
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
            (problems if name.startswith("camp_") else warnings).append(
                "%s has no box under it within 400 u" % name)
        d_twin = math.hypot(o[0] - (2 * X_PLANE - o[0]),
                            o[1] - (2 * Y_PLANE - o[1]))
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
