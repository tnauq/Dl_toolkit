#!/usr/bin/env python3
"""batch15 - the shop relay network, and the wiring that drives it.

RUN AFTER batch13. It reads the entities batch13 wrote, generates the relay
network each shop needs, and wires the objectives into it. Kept separate
because batch13 is already the largest script here and because a wiring fault
should be revertable without losing a survey session's coordinates.

WHY A NETWORK AND NOT A WIRE. "The shop disables when its guardian falls"
sounds like one connection from a guardian to a shop. It is not how Deadlock
does it. Read out of dl_example.vmap 2026-08-23, all 89 connections: not one
is owned by an npc_barrack_boss, and every shop instead owns three relays and
two auto-triggers:

    <shop>_enable_relay        logic_relay          OnTrigger -> Enable
    <shop>_disable_relay       logic_relay          OnTrigger -> Disable
    <shop>_kill_relay          logic_relay          OnTrigger -> Kill
    <shop>_logic_auto_disable  logic_auto           OnMapSpawn, delay 0
    <shop>_logic_auto_enable   logic_auto_citadel   OnGameInProgress, delay 15

So a shop starts closed at map spawn, opens 15 seconds into the game, and
anything that wants to change its state TRIGGERS A RELAY rather than talking
to the shop. That indirection is what lets several unrelated things open or
close the same shop without knowing about each other.

Every keyvalue below is read from the fixture: logic_relay carries
StartDisabled 0 and NO spawnflags; logic_auto and logic_auto_citadel carry
spawnflags 1; the 15 second delay is on the OnGameInProgress wire.

WHAT IS A DESIGN DECISION AND NOT A READING. Two things, both the user's
2026-08-23 call, and both marked so they can be changed in one place:

  1. GUARDIANS KILL THEIR OWN LANE'S SHOP. dl_example wires an
     info_super_trooper_spawn's OnTrooperKilled into the kill relay instead,
     which suits a map where super troopers come from the barracks. Here the
     guardian does it directly, so a lane's shop dies with its guardian.

  2. SHRINES UPGRADE TROOPERS. Not implemented below, because there are no
     shrines in the plan yet and no super trooper spawns for them to enable.
     The table is present and empty, with the shape it will take.

WHAT IS AN OUTRIGHT GUESS. The guardian's OUTPUT NAME. dl_example contains no
connection owned by an npc_barrack_boss, so nothing in it says what a barrack
boss fires when it dies. npc_boss_tier3 fires OnBossKilled and
destroyable_building fires OnDestroyed, so GUARDIAN_OUTPUT is set to
OnBossKilled by analogy. A WRONG OUTPUT NAME FAILS SILENTLY: the map emits,
converts, verifies and loads, and the shop simply never closes. If shops stay
open after a guardian dies in game, this constant is the first thing to
change.

MIRRORING. Everything is authored for team 2 and mirrored, same rotation as
batch13. A connection's targetName is a NAME, so it takes the m_ prefix like
every other name-bearing field - without that, every mirrored relay points
back at the team-2 half and both halves verify green while half the map does
nothing.

RERUNNABLE. Deletes everything it previously added, by MARK, and strips the
connections it previously attached to entities it does not own, then rebuilds.

    python3 batch15.py [docs/plans/dust2_full.json]
"""

import json
import sys

X_PLANE = 460.1
Y_PLANE = 12170.1 / 2.0
PREFIX = "m_"
MARK = "_batch15"

TEAM_A = "2"
TEAM_B = "3"

# The 15 second wait before shops open, read off dl_example's
# logic_auto_citadel OnGameInProgress wire.
GAME_START_DELAY = 15.0

# UNVERIFIED, see the module docstring. Fails silently if wrong.
GUARDIAN_OUTPUT = "OnBossKilled"

# Which shops get a network, and which entity kills each one.
#
# Guardian shops only. The base shop and the secret shop are NOT wired: a base
# shop that closes when a guardian dies would punish the defending team twice,
# and the secret shop has no obvious owner. Both still get their auto-open, so
# they behave like dl_example's neutral shop.
SHOP_KILLERS = [
    # shop entity name (batch13's), guardian entity name (batch13's)
    ("shop_lane3", "guardian_l3"),
    ("shop_lane1", "guardian_l1"),
    ("shop_lane6", "guardian_l6"),
]

# Shops that get the network but nothing that kills them.
UNKILLED_SHOPS = ["shop_base", "shop_secret"]

# SHRINES UPGRADE TROOPERS. Empty until shrines exist in the plan. The shape,
# for when they do: a destroyable_building fires OnDestroyed into whatever
# spawns the upgraded wave. dl_example does the reverse - an
# info_super_trooper_spawn drives a shop's kill relay - so there is no
# fixture evidence for THIS direction and the input name will be a guess too.
#
#   ("shrine_west", "super_trooper_spawn_l3", "OnDestroyed", "Enable"),
SHRINE_UPGRADES = []

# Relay placement. Relays are point entities with no volume, so position is
# cosmetic; they are stacked above their shop so a human opening the map can
# see which shop they belong to.
RELAY_Z_STEP = 64.0
RELAY_Z_BASE = 128.0


def mirror_point(p):
    return [round(920.2 - p[0], 4), round(12170.1 - p[1], 4), round(p[2], 4)]


def mirror_angles(a):
    return [a[0], round((a[1] + 180.0) % 360.0, 4), a[2]]


def by_name(plan):
    return {e["name"]: e for e in plan["entities"] if "name" in e}


def strip_previous(plan):
    """Remove what a previous batch15 run added or attached."""
    before = len(plan["entities"])
    plan["entities"] = [e for e in plan["entities"] if not e.get(MARK)]
    removed = before - len(plan["entities"])

    # Connections attached to entities batch15 does NOT own - the guardians.
    # Each carries the mark so a hand-authored connection on the same entity
    # would survive.
    cleared = 0
    for e in plan["entities"]:
        conns = e.get("connections")
        if not conns:
            continue
        kept = [c for c in conns if not c.pop(MARK, False)]
        if len(kept) != len(conns):
            cleared += len(conns) - len(kept)
        if kept:
            e["connections"] = kept
        else:
            e.pop("connections", None)
    if removed or cleared:
        print("  stripped %d entity(s) and %d connection(s) from a previous run"
              % (removed, cleared))
    return removed, cleared


def wire(output, target, inp, delay=0.0):
    """One connection dict. Defaults match all 89 in dl_example."""
    return {
        "outputName": output,
        "targetType": 7,
        "targetName": target,
        "inputName": inp,
        "overrideParam": "",
        "delay": delay,
        "timesToFire": -1,
        MARK: True,
    }


def relay(name, origin, classname, props, conns, team):
    e = {
        "name": name,
        "classname": classname,
        "origin": [round(v, 4) for v in origin],
        "angles": [0.0, 0.0, 0.0],
        "properties": dict(props),
        "connections": conns,
        MARK: True,
    }
    if team:
        e["properties"]["teamnumber"] = team
    return e


def build_network(shop, killer_name):
    """The five entities and their wires for one shop.

    `shop` is batch13's shop entity. Its targetname is the anchor for every
    name here: amber_lane1_shop_item_trigger gives a base of
    amber_lane1_shop, exactly as dl_example derives its relay names.
    """
    trigger_name = shop["properties"].get("targetname", "")
    if not trigger_name.endswith("_item_trigger"):
        print("  SKIP %s: targetname %r does not end in _item_trigger, so the"
              % (shop["name"], trigger_name))
        print("       relay naming convention cannot be derived from it")
        return []
    base = trigger_name[: -len("_item_trigger")]
    team = shop["properties"].get("teamnumber")
    ox, oy, oz = shop["origin"]

    out = []
    z = oz + RELAY_Z_BASE

    out.append(relay(
        shop["name"] + "_enable_relay", [ox, oy, z],
        "logic_relay",
        {"targetname": base + "_enable_relay", "StartDisabled": "0"},
        [wire("OnTrigger", trigger_name, "Enable")], team))
    z += RELAY_Z_STEP

    out.append(relay(
        shop["name"] + "_disable_relay", [ox, oy, z],
        "logic_relay",
        {"targetname": base + "_disable_relay", "StartDisabled": "0"},
        [wire("OnTrigger", trigger_name, "Disable")], team))
    z += RELAY_Z_STEP

    out.append(relay(
        shop["name"] + "_kill_relay", [ox, oy, z],
        "logic_relay",
        {"targetname": base + "_kill_relay", "StartDisabled": "0"},
        [wire("OnTrigger", trigger_name, "Kill")], team))
    z += RELAY_Z_STEP

    # Closed at map spawn.
    out.append(relay(
        shop["name"] + "_logic_auto_disable", [ox, oy, z],
        "logic_auto",
        {"targetname": base + "_logic_auto_disable", "spawnflags": "1"},
        [wire("OnMapSpawn", base + "_disable_relay", "Trigger")], None))
    z += RELAY_Z_STEP

    # Open once the game actually starts.
    out.append(relay(
        shop["name"] + "_logic_auto_enable", [ox, oy, z],
        "logic_auto_citadel",
        {"targetname": base + "_logic_auto_enable", "spawnflags": "1"},
        [wire("OnGameInProgress", base + "_enable_relay", "Trigger",
              GAME_START_DELAY)], None))

    return out


def twin_of(e):
    t = json.loads(json.dumps(e))
    t["name"] = PREFIX + e["name"]
    t["origin"] = mirror_point(e["origin"])
    t["angles"] = mirror_angles(e.get("angles", [0.0, 0.0, 0.0]))
    props = dict(e.get("properties", {}))
    if props.get("teamnumber") == TEAM_A:
        props["teamnumber"] = TEAM_B
    elif props.get("teamnumber") == TEAM_B:
        props["teamnumber"] = TEAM_A
    if props.get("targetname"):
        props["targetname"] = PREFIX + props["targetname"]
    t["properties"] = props

    # THE ONE THAT WOULD FAIL SILENTLY. targetName is a name like any other,
    # and a twin that keeps the original's target drives the team-2 half from
    # the team-3 side. Both halves verify green; half the map does nothing.
    conns = []
    for c in e.get("connections", []):
        c2 = dict(c)
        if c2.get("targetName"):
            c2["targetName"] = PREFIX + c2["targetName"]
        conns.append(c2)
    if conns:
        t["connections"] = conns
    return t


def main(path):
    with open(path) as f:
        plan = json.load(f)

    plan.setdefault("entities", [])
    strip_previous(plan)

    ents = by_name(plan)
    added = []

    print("shop networks")
    for shop_name, killer in ([(s, k) for s, k in SHOP_KILLERS]
                              + [(s, None) for s in UNKILLED_SHOPS]):
        shop = ents.get(shop_name)
        if shop is None:
            print("  SKIP %s: not in the plan. Run batch13 first." % shop_name)
            continue
        net = build_network(shop, killer)
        if not net:
            continue
        added.extend(net)
        base = shop["properties"]["targetname"][: -len("_item_trigger")]
        print("  %-14s %d relay(s), base name %s"
              % (shop_name, len(net), base))

        if killer is None:
            continue
        k = ents.get(killer)
        if k is None:
            print("    SKIP kill wire: %s not in the plan" % killer)
            continue
        k.setdefault("connections", []).append(
            wire(GUARDIAN_OUTPUT, base + "_kill_relay", "Trigger"))
        print("    %s %s -> Trigger %s_kill_relay"
              % (killer, GUARDIAN_OUTPUT, base))

    if SHRINE_UPGRADES:
        print("\nshrine upgrades")
        for shrine, target, out_name, in_name in SHRINE_UPGRADES:
            s = ents.get(shrine)
            if s is None:
                print("  SKIP %s: not in the plan" % shrine)
                continue
            s.setdefault("connections", []).append(
                wire(out_name, target, in_name))
            print("  %s %s -> %s %s" % (shrine, out_name, in_name, target))
    else:
        print("\nshrine upgrades: none. No shrines in the plan yet; see")
        print("  SHRINE_UPGRADES in this file for the shape they will take.")

    # Mirror everything added, and the twins of the entities we attached to
    # are batch13's problem - it already generated them, and their m_ copies
    # were made BEFORE this run attached anything, so the twin guardians need
    # their wire attaching here too.
    twins = [twin_of(e) for e in added]
    plan["entities"].extend(added)
    plan["entities"].extend(twins)

    ents = by_name(plan)
    for shop_name, killer in SHOP_KILLERS:
        mk = ents.get(PREFIX + killer)
        base_shop = ents.get(shop_name)
        if mk is None or base_shop is None:
            continue
        base = base_shop["properties"]["targetname"][: -len("_item_trigger")]
        mk.setdefault("connections", []).append(
            wire(GUARDIAN_OUTPUT, PREFIX + base + "_kill_relay", "Trigger"))

    conns = sum(len(e.get("connections", [])) for e in plan["entities"])
    with open(path, "w") as f:
        json.dump(plan, f, indent=1)

    print("\nwrote %s" % path)
    print("  entities %d (+%d, of which %d mirrored)"
          % (len(plan["entities"]), len(added) + len(twins), len(twins)))
    print("  connections %d" % conns)
    print("\nUNVERIFIED: GUARDIAN_OUTPUT = %r. No connection in dl_example is"
          % GUARDIAN_OUTPUT)
    print("owned by an npc_barrack_boss, so nothing says what one fires when")
    print("it dies. A wrong name emits, converts and verifies clean, and the")
    print("shop simply never closes.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else
                  "docs/plans/dust2_full.json"))
