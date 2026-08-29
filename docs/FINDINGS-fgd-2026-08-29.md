# FINDINGS — citadel.fgd, 2026-08-29

The FGD arrived. It is committed at `docs/reference/citadel/citadel.fgd`:
114,917 bytes, 2,123 lines, 197 `@` class declarations, 120 named classes.

This is the file the compiler validates entities against, so it is the first
source in this project that gives **keyvalues** rather than classnames. Nearly
everything on the open list was keyvalue-shaped.

## What it is, and how much to trust it

It carries hand annotations — `//does this even work? i think it should`,
`//well this didn't work`, `//purely naming` — so it is an annotated or
partly reconstructed FGD rather than a pristine Valve artifact.

That asymmetry matters when reading it:

- **A presence is strong evidence.** A class or key that is in here is
  something the compiler will accept and something someone has used.
- **An absence is weak evidence.** `npc_boss_tier1` is not in this file, and
  yet dl_example — a shipped Valve map — is full of them. See §9.

Read every finding below with that split in mind.

## 1. The teleporter key is `exitpoint`, not `target` — FIXED

The single most valuable line in the file:

    exitpoint(target_destination) : "Remote Destination" : :
        "The entity specifying the point to which entities should be teleported."

We were emitting `target`, on the Source convention. It was flagged as a
guess in batch16 and the guess was wrong. A `target` on this class is simply
ignored: no compile error, no warning, you walk into the trigger and nothing
happens. This is exactly the failure mode that was going to eat a desktop
session.

Fixed in `batch16.py` (emission) and `tools/preflight.py` (reference check).
`tools/fix_exitpoint.py` migrates the committed plan.

The FGD also documents a local landmark mode: with one set, teleported
entities keep their offset from the landmark and their angles are left alone;
without one, angles are forced to the destination's. We use the latter, which
is right for two rooms that should face each other.

## 2. The mirror would have broken too — FIXED

`twin_of` prefixes every key that names another entity. Its list was
`targetname, CampName, target, parentname`. With the rename, `exitpoint`
would not have been prefixed, so **both** mirrored triggers would have
pointed at the original half's destination and dumped players on one side of
the map. Added to the list. This is the same silent-mirror bug class that
`LINK_KEYS` was written for.

## 3. `info_teleport_location` has more keys than we emit

It derives from `Targetname`, `TeamNumber` and `LaneNumber`, and adds:

    objective(integer) : "Objective? By default set to 3?" : 3

The question marks are the annotator's. We currently emit only `targetname`.
**Open** — see the questions at the bottom.

## 4. Jump pads are jump pads: arc, not blink — CONFIRMED

`trigger_catapult` is described as "Bouncepad/Fan Trigger" with exactly two
keys: `launch_speed` (default **1000**) and `target`, "Pair with a
info_target_server_only entity to launch entities at."

So the pads and the teleporters are different mechanisms and both spellings
we use are right. One of the three first-compile questions in SHIPPING.md is
answered without compiling. Note the FGD's default speed of 1000 against our
800 — another reason the 800 wants testing in game.

## 5. Probe spellings settled, probe unnecessary — RECORDED

Of the four teleporter candidates, **only `citadel_trigger_teleport` exists**.
`trigger_citadel_teleport`, `citadel_teleport` and `trigger_teleport` are
absent. The convention-following read was right and the LLM's answer was
wrong.

Of the three sinner candidates, **none exists**. See §7.

`SPELLING_PROBE` was already off. The tables stay as a worked example, with
each line's verdict recorded beside it.

## 6. Lane 0 was right, and four slots is a four-lane artifact — CONFIRMED

Each `sub_objective_lane_N` is a choices field:

    0 : "None"   1 : "Yellow"   3 : "Orange"   4 : "Blue"   6 : "Purple"

Three things fall out. **Zero is legal**, so the zeroes we guessed for the
non-lane shrines are a case the schema anticipates. **Blue is the lane that
went away**, which is why the fixture's proxy has four slots at 1/3/4/6.
And the outputs confirm the shape: the FGD declares
`SubObjective1Destroyed`/`Revitilized` and `SubObjective2Destroyed`/
`Revitilized` and **nothing at all for slots 3 and 4**. Only two are wired
for. Two filled slots plus an empty pair is correct for a three-lane map.

## 7. Sinner is NOT the vault

`ENeutralTrooperType` on `info_neutral_trooper_camp` enumerates:

    1 Weak   2 Medium   3 Strong   5 Mid Boss   6 Sinner's Sacrifice
    9 Sushibot (Gargoyle)   10 Cleanbot (Trashbug)   11 Punkbot (Whack-A-Ghost)
    12 Breakable Vault      "" None

**6 and 12 are different values.** The working assumption that sinner = vault
does not hold. The `vault` entry in `TIERS` is still a faithful read of
dl_example's vault camp — `neutral_camp_vaults`, empty trooper type, 120/120
— what is wrong is calling it the sinner.

There is also a class `npc_neutral_sinners_sacrifice_hideout`. Note the
suffix: that is the Hideout mode's version and may not be what a lane map
wants. The camp route with type 6 looks likelier.

**Open** — the four sinner sites are still held unemitted. Changing them to
type 6 needs a subclass to go with it and the FGD names none.

## 8. Camp spawn timings are inert

`InitialSpawnDelayInSeconds` and `SpawnIntervalInSeconds` are **commented out
in the FGD and annotated "Unused"**. The camp does not read them; timings
come from somewhere else, most likely the subclass.

So the tier-to-interval mapping that PROBE.md worried over — which of 120,
300, 360 belongs to which tier — does not matter. We still emit the keys:
they are what the fixture carries, they cost nothing, and "unused" is an
annotation rather than a promise.

## 9. Guardians: no conflict, but read carefully

`npc_boss_tier1` **is not in this FGD**. What is here:

| class | FGD says |
|---|---|
| `npc_barrack_boss` | "Barrack Guardians, there should be two per lane in each team" |
| `npc_trooper_boss` | "creates a Tier1 boss directly. Use `info_trooper_boss_spawn` instead" |
| `npc_boss_tier2` | "Sun Walkers, one per lane in each team" |
| `npc_boss_tier3` | "Tier3 Bosses/Titans/Patrons, one in each team" |

dl_example carries six `npc_boss_tier1` and sixteen `npc_barrack_boss`, so
both are real and they are different things — the lane objective and the
barrack pair. The handoff's reading stands. This is an FGD **absence**, and
absences here are weak (see the top of this file). Nothing changed.

## 10. Titan means Patron — the 2026-08-27 reading was wrong

`npc_boss_tier3` is tool-named **"Patron"**, tool-tipped "Spawn position for
Tier3 Boss/Titan/Patron", described as spawning "Tier3 Bosses/Titans/Patrons",
and its two BossName choices are labelled "T3 Boss/Titan/Patron".

Meanwhile `destroyable_building` is tool-named **"Base Shrine"** and described
as "used exclusively for base shrines".

So titan and patron are the same entity, and the shrine is a separate class.
The reasoning that led to titan = shrine (the destroyable thing shielding the
patron) correctly described the shrine; it just attached the wrong word.

**No code changes.** `tools/minimap.py` already labels `destroyable_building`
"Shrine" and `npc_boss_tier3` "Patron", which is right either way. batch16's
`PROXY_SUBS = ["w", "e"]` still points the sub-objectives at the shrines,
which is still what the proxy is for. Only stale comments were touched.

## 11. The patron may be unbeatable as authored

From the FGD, on `npc_boss_tier3`:

> "Make sure to use cover groups for each of the boss states, otherwise the
> game will be unbeatable."

We emit `CoverGroupID`, `dying_cover_id` and `vulnerable_cover_id` **all
empty**. `dying_cover_id` is where the patron moves before turning into a
core; `vulnerable_cover_id` is where it falls when it does.

This needs `info_cover_point` groups authored — real work, not a string to
fill in. Flagged loudly in the code. It belongs on the next handoff.

## 12. Smaller readings

- **`citadel_final_objective_proxy` is labelled "Final objective. Unused. Do
  not use."** Nothing else in the file is marked that way. It may be inert in
  the shipped game, in which case the shrine-shields-patron chain has to come
  from entity I/O — and the outputs exist for that on both
  `destroyable_building` and the patron. Emission unchanged; **open**.
- **`building_health` and `final` on the shrine are both marked "(Broken)".**
  Do not tune shrine health there and expect anything.
- **`npc_boss_tier3.BossName` is an enumeration**, only
  `boss_rebel_tier2_mid` and `boss_combine_tier2_mid` (the tier2 naming on the
  tier3 class is Valve's). We emit `rebels_patron`. On `npc_boss_tier2` the
  FGD annotates its BossName list "//purely naming"; on tier3 it does not, so
  the enumeration may be load bearing. **Open.**
- **`npc_barrack_boss.LaneSide`** is annotated "Unused property. Used as a way
  to index barrack guardians?" — our `"0"` is fine.
- **Team numbers confirmed**: 2 Amber/Rebels/North, 3 Sapphire/Combine/South,
  4 Neutral.

## Still open after this

1. `info_teleport_location`: emit `objective`, `TeamNumber`, `LaneNumber`?
2. Sinners: camp with type 6, and if so under which subclass?
3. The proxy: keep emitting a class the FGD says not to use?
4. `npc_boss_tier3.BossName`: conform to the enumeration?
5. Cover groups for the patron's states — §11, the biggest one.

None of these is blocking a compile. All of them are cheaper to answer with
the FGD in hand than they were yesterday.
