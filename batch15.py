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

  1. LANE OBJECTIVES KILL THEIR OWN LANE'S SHOP. dl_example wires an
     info_super_trooper_spawn's OnTrooperKilled into the kill relay instead.
     Here the info_super_trooper_spawn that places the lane guardian does
     it directly, so a
     lane's shop dies with the objective that holds the lane.

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

# The same two namespaces batch13 uses: m_ for the PLAN-LEVEL entity name,
# which every script keys on, and a TEAM WORD swap for the targetname, which
# is what the game and entity IO see. dl_example names its pairs
# rebels_/combine_ with no prefix anywhere, and a relay network is nothing but
# names pointing at names, so getting this wrong would wire every mirrored
# relay back into the team-2 half while both halves verified green.
TEAM_WORD_A = "rebels"
TEAM_WORD_B = "combine"


def team_swap(name):
    """First occurrence anywhere; m_ prefix for names with no team word."""
    if not name:
        return name
    if TEAM_WORD_A in name:
        return name.replace(TEAM_WORD_A, TEAM_WORD_B, 1)
    if TEAM_WORD_B in name:
        return name.replace(TEAM_WORD_B, TEAM_WORD_A, 1)
    return PREFIX + name

# The 15 second wait before shops open, read off dl_example's
# logic_auto_citadel OnGameInProgress wire.
GAME_START_DELAY = 15.0

# CORRECTED 2026-08-29 by the connection probe, from OnBossKilled.
#
# All NINE guardian-closes-the-shop connections in dl_example are owned by
# info_super_trooper_spawn firing OnTrooperKilled -> <shop>_kill_relay .
# Trigger. Not one is owned by a boss NPC. The fixture's OnBossKilled wires
# belong to npc_boss_tier3 and go to a counter, not to a shop.
#
# citadel.fgd agrees: OnTrooperKilled is declared on exactly one class, and
# that class is info_super_trooper_spawn - which the FGD tool-names "Lane
# Guardian" and gives the brazier guardian editor model.
#
# batch13 now places guardians as info_super_trooper_spawn rather than
# npc_boss_tier1, so THIS CONSTANT AND THAT CLASS HAVE TO MATCH. A right
# output on a wrong entity and a wrong output on a right entity both fail
# the same silent way: the map emits, verifies, loads, and the shop simply
# never closes.
#
# The previous value was reasoned by analogy - tier1 and tier3 are both
# bosses, so presumably both fire OnBossKilled - and was recorded as an
# analogy rather than a reading. It is now a reading.
GUARDIAN_OUTPUT = "OnTrooperKilled"

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

# ---------------------------------------------------------------------------
# THE MIDBOSS CHAIN: the lid, and the night.
#
# ONE EVENT DRIVES BOTH, and we do not know its name. That is the whole
# blocker and it is worth stating precisely, because the shape of the problem
# has changed twice already.
#
# PROBE.md item 5 records the mechanism as "the midboss camp fires
# OnTrooperKilled -> lid Kill". THAT IS WRONG. The connection probe
# attributed OnTrooperKilled to exactly one class, info_super_trooper_spawn,
# and citadel.fgd declares it on exactly one class, the same one. Every
# midboss-related class - info_neutral_trooper_camp, info_mid_boss_spawn,
# info_neutral_trooper_spawn, trigger_midboss_shield and
# citadel_base_prop_midboss_indicator - declares NO OUTPUTS AND NO INPUTS AT
# ALL. Nothing on the map fires when the midboss dies.
#
# The route left is logic_gameevent_listener (citadel.fgd): a gameeventname
# in, OnEventFired out. Deadlock announces a midboss kill globally - there is
# a sound and a UI message - so the event exists; we just cannot read its
# name from any file we have. It is not in the retail folder (only UI strings
# like Objective_MidBoss), so it is in the vpk or the binaries.
#
# HOW TO GET IT: on a desktop, launch with the dev flags in SHIPPING.md and
# run `dumpgameevents` at the console. One command. Put the name below and
# everything in this section starts working.
#
# UNTIL THEN NOTHING HERE IS EMITTED. An empty or wrong gameeventname is the
# exact failure this project keeps hitting - it compiles, verifies, loads,
# and silently does nothing - so the block is gated rather than guessed.
MIDBOSS_EVENT = ""

# Candidates, for whoever runs dumpgameevents: the answer is probably one of
# these, but DO NOT pick one by eye. Confirm it against the dump.
MIDBOSS_EVENT_CANDIDATES = [
    "citadel_midboss_killed", "midboss_killed", "neutral_midboss_killed",
    "citadel_neutral_killed", "midboss_defeated",
]

# How long night lasts, in seconds. Fired as a DELAY on the same output that
# starts it, so no timer entity is needed - delay is a field on every
# connection.
NIGHT_SECONDS = 300.0

# The lid, built by batch18 as a func_brush named midboss_lid. Killing it
# opens the shaft to the bridge floor below; the deck under it is already
# cut, so nothing has to move.
LID_TARGET = "midboss_lid"

# THE SNAP IS DELIBERATE, decided 2026-08-29: the change is instant so it
# lands with the global midboss death sound. env_fog_controller has a lerp
# system (SetColorLerpTo and friends, then StartFogTransition) which is
# deliberately unused; if the cut ever reads as a glitch rather than an
# event, that is the fallback and it is a change of inputs, not structure.
#
# Values are INVENTED. Nothing was read for what this map should look like at
# night, and fog distances want checking against its actual extents.
FOG_NAME = "fog_controller"
LIGHT_NAME = "global_light"          # batch16's env_global_light
FOG_DAY = {"SetColor": "142 160 178", "SetStartDist": "1200",
           "SetEndDist": "9000", "SetFarZ": "18000"}
FOG_NIGHT = {"SetColor": "18 24 44", "SetStartDist": "400",
             "SetEndDist": "4200", "SetFarZ": "9000"}
LIGHT_DAY = {"LightColor": "228 184 134", "SetAngles": "-60 45 0"}
LIGHT_NIGHT = {"LightColor": "58 74 122", "SetAngles": "-24 200 0"}


def build_midboss_chain(plan, log):
    """The listener, the two relays and their wires. Nothing without an event.

    Returns a list of new entities. The lid and the global light are ATTACHED
    TO, not created here - batch18 and batch16 own those - so both are looked
    up and their absence is reported rather than papered over.
    """
    if not MIDBOSS_EVENT:
        log.append("")
        log.append("MIDBOSS CHAIN: not emitted. MIDBOSS_EVENT is unset, and")
        log.append("  no entity on this map fires anything when the midboss")
        log.append("  dies - every midboss class in citadel.fgd declares no")
        log.append("  outputs at all. Run `dumpgameevents` on a desktop and")
        log.append("  set MIDBOSS_EVENT. The lid stays solid until then, and")
        log.append("  the map has no night.")
        return []

    ents = by_name(plan)
    out = []
    missing = []
    if LID_TARGET not in ents:
        missing.append("%s (batch18, LID/LID_ENTITY)" % LID_TARGET)
    have_light = any(e.get("properties", {}).get("targetname") == LIGHT_NAME
                     for e in plan["entities"])
    if not have_light:
        missing.append("%s (batch16, env_global_light)" % LIGHT_NAME)
    have_fog = any(e.get("properties", {}).get("targetname") == FOG_NAME
                   for e in plan["entities"])

    # The fog controller is created HERE rather than in batch16, because it
    # exists only to be driven by this chain. If the chain is off there is no
    # fog controller and the map keeps whatever the compiler defaults to.
    if not have_fog:
        out.append(relay(FOG_NAME, [920.2 / 2, 12170.1 / 2, 2600.0],
                         "env_fog_controller", {
                             "targetname": FOG_NAME,
                             "fogenabled": "1",
                             "fogcolor": FOG_DAY["SetColor"],
                             "fogstart": FOG_DAY["SetStartDist"],
                             "fogend": FOG_DAY["SetEndDist"],
                             "farz": FOG_DAY["SetFarZ"],
                         }, [], None))

    # Two relays, each holding one state's whole fan-out. 39 of dl_example's
    # 89 connections are logic_relay.OnTrigger, so this is the fixture's own
    # pattern rather than an invention.
    for name, fog, light in (("night_relay", FOG_NIGHT, LIGHT_NIGHT),
                             ("day_relay", FOG_DAY, LIGHT_DAY)):
        conns = [wire("OnTrigger", FOG_NAME, k, 0.0) for k in fog]
        for i, (k, v) in enumerate(fog.items()):
            conns[i]["overrideParam"] = v
        for k, v in light.items():
            c = wire("OnTrigger", LIGHT_NAME, k, 0.0)
            c["overrideParam"] = v
            conns.append(c)
        out.append(relay(name, [920.2 / 2, 12170.1 / 2,
                                2600.0 + RELAY_Z_STEP], "logic_relay",
                         {"targetname": name, "TriggerOnce": "0",
                          "FastRetrigger": "0"}, conns, None))

    # The listener. One output, three consumers: night now, the lid now, day
    # in NIGHT_SECONDS.
    out.append(relay("midboss_listener", [920.2 / 2, 12170.1 / 2, 2600.0],
                     "logic_gameevent_listener",
                     {"targetname": "midboss_listener",
                      "gameeventname": MIDBOSS_EVENT,
                      "gameeventitem": "",
                      "StartDisabled": "0"},
                     [wire("OnEventFired", "night_relay", "Trigger", 0.0),
                      wire("OnEventFired", LID_TARGET, "Kill", 0.0),
                      wire("OnEventFired", "day_relay", "Trigger",
                           NIGHT_SECONDS)],
                     None))

    log.append("")
    log.append("MIDBOSS CHAIN on event %r: listener -> night_relay, %s.Kill, "
               "and day_relay after %.0fs" % (MIDBOSS_EVENT, LID_TARGET,
                                              NIGHT_SECONDS))
    for m in missing:
        log.append("  MISSING: %s - the wire will emit and resolve to "
                   "nothing" % m)
    return out


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
        props["targetname"] = team_swap(props["targetname"])
    t["properties"] = props

    # THE ONE THAT WOULD FAIL SILENTLY. targetName is a name like any other,
    # and a twin that keeps the original's target drives the team-2 half from
    # the team-3 side. Both halves verify green; half the map does nothing.
    conns = []
    for c in e.get("connections", []):
        c2 = dict(c)
        if c2.get("targetName"):
            c2["targetName"] = team_swap(c2["targetName"])
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

    # THE MIDBOSS CHAIN IS NOT MIRRORED. There is one midboss, one lid and
    # one sky, all on the mirror point, so a twin of any of this would be the
    # same entity in the same place - and two listeners on one event would
    # fire everything twice. Added after the twinning step for that reason.
    chain_log = []
    chain = build_midboss_chain(plan, chain_log)
    plan["entities"].extend(chain)
    for line in chain_log:
        print(line)

    ents = by_name(plan)
    for shop_name, killer in SHOP_KILLERS:
        mk = ents.get(PREFIX + killer)
        base_shop = ents.get(shop_name)
        if mk is None or base_shop is None:
            continue
        base = base_shop["properties"]["targetname"][: -len("_item_trigger")]
        mk.setdefault("connections", []).append(
            wire(GUARDIAN_OUTPUT, team_swap(base) + "_kill_relay", "Trigger"))

    conns = sum(len(e.get("connections", [])) for e in plan["entities"])
    with open(path, "w") as f:
        json.dump(plan, f, indent=1)

    print("\nwrote %s" % path)
    print("  entities %d (+%d, of which %d mirrored)"
          % (len(plan["entities"]), len(added) + len(twins), len(twins)))
    print("  connections %d" % conns)
    print("\nGUARDIAN_OUTPUT = %r, read off dl_example's own connections:"
          % GUARDIAN_OUTPUT)
    print("nine of them, all owned by info_super_trooper_spawn. This must")
    print("match the class batch13 places for a guardian.")
    print("Names follow dl_example: rebels_/combine_ pairs, lane colours")
    print("yellow/orange/purple for lanes 1/3/6, and no m_ prefix on any")
    print("targetname. The m_ prefix is plan bookkeeping only.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else
                  "docs/plans/dust2_full.json"))
