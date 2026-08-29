# FINDINGS — who owns the 89 connections

Third run of `connection-owner-probe`. 89 connections, 89 attributed, 0
disagreements, and the owners are plausible and varied - which the first two
runs were not (0 parsed, then 89 x `point_worldtext`).

## The census

| owner | n | fires |
|---|---|---|
| `logic_relay` | 39 | `OnTrigger` -> skins, animations, Enable/Disable/Kill/Trigger |
| `citadel_final_objective_proxy` | 16 | BecomeActive, SubObjective1/2 Destroyed/Revitilized, FinalShielded, FinalExposed |
| `destroyable_building` | 12 | `OnDestroyed -> Kill` |
| `info_super_trooper_spawn` | 9 | `OnTrooperKilled -> Trigger` |
| `logic_auto` | 4 | `OnMapSpawn -> Trigger` |
| `logic_auto_citadel` | 3 | `OnGameInProgress -> Trigger` |
| `npc_boss_tier3` | 2 | `OnBossKilled -> Add` (a counter) |
| `trigger_item_shop_safe_zone` | 2 | OnContested / OnNotContested |
| `trigger_catapult` | 1 | `OnStartTouch -> StartSound` |
| `trigger_multiple` | 1 | `OnStartTouch -> Speak` |

## 1. The proxy is used, and it IS the shrine-to-patron chain

`citadel_final_objective_proxy` carries sixteen connections, eight per team,
despite citadel.fgd marking it "Unused. Do not use."

The decisive pair:

    FinalShielded -> <relay> . Trigger
    FinalExposed  -> <relay> . Trigger

Those are the proxy's **own outputs**. The proxy computes shielding from the
state of its sub-objectives and announces it. **That is why npc_boss_tier3
needs no input** — nothing has to tell the patron it is exposed.

`FINDINGS-fgd-2026-08-29` §13 concluded the chain could not be built because
the FGD declares no patron input. That conclusion was right about the FGD and
wrong about the problem: the chain was never meant to be hand-wired.
`EMIT_PROXY` is back to `True`.

Only slots 1 and 2 are used, as the four-lane-artifact reading predicted, and
the two sub-objectives are named **left and right**, not by lane. Our
`PROXY_SUBS = ["w", "e"]` with lane 0 matches that shape.

## 2. The lid mechanism is confirmed, the lid CLASS is not

Twelve `OnDestroyed -> Kill`, all owned by `destroyable_building`, four
shrines firing three each:

    rebels_t3_generator_yellow  -> rebels_yellow_grate_prop   . Kill
                                -> rebels_yellow_grate_brush  . Kill
                                -> rebels_yellow_ladder_brush . Kill

and the same for purple, both teams. Shrine dies, a grate prop, a grate brush
and a ladder brush are all destroyed outright.

**Every one of those twelve targets is unresolved** — nothing in dl_example
carries those targetnames. That is not a probe failure this time, because
plenty of other targets resolved cleanly (`trigger_item_shop`,
`logic_relay`). See §4.

## 3. GUARDIANS ARE `info_super_trooper_spawn`, and this affects batch15

The nine `OnTrooperKilled -> <shop>_kill_relay . Trigger` connections — the
guardian-closes-the-shop wiring — are owned by **`info_super_trooper_spawn`**,
not by any boss NPC.

citadel.fgd agrees, and is specific: the class "marks the start point for
Guardians and Reinforcement Troopers... For Lane Guardians, one of these
needs to be placed on their respective lane with an unique BossName that
matches their lane and team." Its BossName enumeration is
`boss_rebel_t1_yellow` and friends. It declares `OnTrooperKilled`, and it is
the only class in citadel.fgd that does.

**Two consequences.**

`batch15.GUARDIAN_OUTPUT = "OnBossKilled"` is wrong. The fixture's
`OnBossKilled` connections belong to `npc_boss_tier3` and go to a counter,
not a shop. The guardian output is `OnTrooperKilled`.

And the entity is wrong upstream of that. The fixture census has **17
`info_super_trooper_spawn` and no `npc_boss_tier1` at all** — consistent with
citadel.fgd, which has no `npc_boss_tier1` either. Our plan places
`npc_boss_tier1` for guardians. Both need changing together, and that is a
batch13 change, so it has not been made here.

## 4. The unresolved targets are PREFAB-SCOPED, and that is the pattern

Everything unresolved shares a signature: a `125_` numeric prefix
(`125_combine_left_objective_particle`, `125_rebels_final_shielded_relay`) or
a grate/ladder name. Everything that resolved has no prefix.

A numeric prefix on an instance's entities is how Source keeps prefab names
unique. So these entities live **inside prefabs**, not in dl_example's own
entity list, which is why no targetname matches and why the entity survey
could never find `*_grate_brush` in its census either.

This also explains the older note that the proxy's `sub_objective_1` reads
`125_rebels_titan_yellow` while the shrines are named
`rebels_t3_generator_yellow` — different names for prefab-internal and
map-level entities, and a caution against reading too much into "titan"
appearing there.

**Consequence for the lid**: the class of a killable brush cannot be read
from dl_example.vmap alone. It is in a prefab file. `base.fgd` already
settles the mechanism — `Kill` is on the `GameEntity` base, so every entity
answers it — but which brush class to use is a choice we now have to make
rather than copy. `func_brush` (base.fgd) is the obvious candidate and is
what the rest of Source uses for exactly this.

## 5. Relays are the fan-out pattern

39 of 89 connections are `logic_relay.OnTrigger`. One event drives a relay,
the relay drives everything else. That is precisely the night-mode wiring in
`docs/NIGHT-MODE.md`, and it is what the fixture does throughout.

`logic_auto` (4) and `logic_auto_citadel` (3) set the initial state at map
spawn — which is how the day lighting should be established.
