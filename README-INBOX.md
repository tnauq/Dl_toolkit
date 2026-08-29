# Inbox drop — items 1, 2, 3 and 5 (2026-08-29)

    batch13.py    reinforcement spawns
    batch15.py    the midboss chain: lid kill + night, gated on one constant
    batch16.py    patron cover groups; the sun becomes env_global_light
    batch18.py    the lid becomes a func_brush entity
    PROBE.md      item 5 rewritten

All extracted byte-exact against `repo-manifest.md` before editing, all
parse, and `build_objectives()` was run in isolation.

## 1. The midboss chain — BUILT, BUT NOT EMITTED

The chain is written and complete: a `logic_gameevent_listener` fires
`night_relay.Trigger` and `midboss_lid.Kill` at delay 0, and
`day_relay.Trigger` at delay 300. Two relays hold the fan-out to the fog
controller and the global light, which is the fixture's own pattern — 39 of
dl_example's 89 connections are `logic_relay.OnTrigger`.

**It emits nothing, because `MIDBOSS_EVENT = ""`.** Nothing on the map fires
when the midboss dies: every midboss class in citadel.fgd declares no outputs
and no inputs at all, so PROBE.md item 5's "camp fires OnTrooperKilled" was
wrong. The only route is the game event, and its name isn't in any file we
hold — not in the retail folder, which has only UI strings like
`Objective_MidBoss`.

**One command gets it**: `dumpgameevents` at the console with the dev flags
from SHIPPING.md. Set the constant and the whole section switches on. Five
candidate names are listed in the code — do not pick one by eye. An empty or
wrong `gameeventname` compiles, verifies, loads and silently does nothing,
which is the failure this project keeps hitting, so the block is gated rather
than guessed.

The lid is now a `func_brush` entity (batch18, `LID_ENTITY`). `Kill` is on
base.fgd's `GameEntity` class, so every entity answers it. The brush class is
a **choice**, not a copy — dl_example's grate and ladder brushes are inside
prefabs and no targetname resolves to them.

The conversion happens at **write time**, after every geometry check has seen
the lid as a box. Moving it earlier would make the floor sampler report the
hole as open and fail a map that is correct.

## 2. Cover groups — the unbeatable warning is closed

Three groups of three `info_cover_point` around the patron: where it stands
and fights (r 220), where it moves to die (r 420), where it falls when it
becomes a core (r 120). Ids 4101/4102/4103.

**Cover ids are now per-team.** `twin_objective` adds an offset of 100 to
`CoverGroupID`, `dying_cover_id`, `vulnerable_cover_id` and `groupid`.
Without that both patrons would name group 4101 and share one set of cover
points on opposite sides of the map — and nothing would report it. The ids
resolve, the points exist, and the far patron walks the length of the map to
die.

Radii and point counts are invented. The FGD says to use cover groups; it
does not say how big one is.

## 3. Reinforcement spawns

One per lane, `ReinforcementsOnly 1`, empty BossName, at the lane's first
node — which is under its zipline by construction, since the ziplines are
built from the lane routes at height.

The FGD's last clause is the alarming one: "if they are not placed, troopers
will not spawn." If that's literal, this map had no troopers. It's also the
clause most worth doubting, since `info_trooper_spawn` is its own class and
dl_example carries 36 of them. Both are emitted.

## A correction found on the way: the sun was not a real class

`light_environment` is in **neither** citadel.fgd nor base.fgd. The only
mention anywhere is a comment inside base.fgd's fog volume. It may exist in
lights.fgd, which we don't have, but Deadlock's own global light is
`env_global_light` and citadel.fgd defines it outright.

It's also the only lighting entity with runtime inputs — `LightColor`,
`SetAngles`, `EnableShadows`, `Enable`/`Disable` — so the night mode needs
it. Switched, and given the targetname `global_light` that batch15 drives.

## 5. PROBE.md item 5

Rewritten. Both halves of the old blocker were wrong: the plan format has
expressed connections since `EXPECT_CONN` went to 56, and the output it names
belongs to a class that isn't the midboss. What's actually left is the event
name.

## Counts will move

Entities are up by roughly 40: 18 cover points with twins, 6 reinforcement
spawns with twins, and the lid moves from `boxes` to `entities`. Re-pin
`EXPECT_CLASSPROPS`, `EXPECT_PLUGLIST` and `EXPECT_ELEMENTS` from what the
run reports rather than from a guess here. `EXPECT_CONN` stays at 56 until
`MIDBOSS_EVENT` is set, then rises by 11.
