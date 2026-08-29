# Inbox drop — guardians become spawn markers (2026-08-29)

    batch13.py          MODIFIED - guardian class, BossName, explicit swaps
    batch15.py          MODIFIED - GUARDIAN_OUTPUT
    tools/minimap.py    MODIFIED - legend lookup

Option 1, taken in full. All three files round-tripped to a byte-exact sha1
match against `repo-manifest.md` before editing. All three parse, and
`build_objectives()` was run in isolation to check the result.

## What changed

The lane guardian is no longer placed as an NPC. It is placed as
`info_super_trooper_spawn`, a spawn marker carrying a `BossName`.

    guardian_l1   boss_rebel_t1_yellow   lane 1   team 2
    guardian_l3   boss_rebel_t1_orange   lane 3   team 2
    guardian_l6   boss_rebel_t1_purple   lane 6   team 2

and the mirrored half gets `boss_combine_t1_*`, verified through `team_swap`.

Three sources agree and none of them is the vdata:

- **citadel.fgd** tool-names the class "Lane Guardian", gives it the brazier
  guardian editor model, and says a guardian needs one of these placed on its
  lane with a unique BossName matching lane and team.
- **The connection probe**: all nine guardian-closes-the-shop wires are owned
  by this class firing `OnTrooperKilled`.
- **The fixture census**: 17 `info_super_trooper_spawn`, zero
  `npc_boss_tier1`.

`GUARDIAN_OUTPUT` in batch15 is now `"OnTrooperKilled"`. These two changes
had to land together — a right output on a wrong entity and a wrong output on
a right entity fail the same silent way, with the map emitting and verifying
green while the shop never closes.

## Three details worth knowing

**The key set shrank.** The old NPC carried ten keys; the marker takes seven,
and `vscripts`, `BackdoorProtectionTrigger`, `subclass_name`,
`dying_cover_id` and `vulnerable_cover_id` are gone because the class does
not have them. `SecondaryBoss` and `ReinforcementsOnly` are new, both 0.

**BossName is an enumeration, not a name we compose.** The FGD lists eight
values as `boss_<team>_t1_<colour>` using the SINGULAR "rebel". Our old
`rebels_t1_boss_orange` matched none of them. The generic rebels↔combine swap
cannot see "rebel", so batch13 now has an `EXPLICIT_SWAPS` table for the
pair, same as batch16 needed for the patron's BossName.

**The minimap would have gone quiet.** Its Guardian legend looked up
`npc_boss_tier1`, so after this change it would have drawn nothing and
reported "Guardian" missing on a map with three per team. Updated.

## Why npc_boss_tier1 looked right, recorded rather than deleted

The 2026-08-27 reasoning was not careless. `npc_units.vdata` really does
carry `npc_boss_tier1` with the brazier guardian model at 5500 health. But
that file lists **units**, not map entity classes. The unit is what gets
spawned; the marker is what you place. citadel.fgd draws the same distinction
of `npc_trooper_boss`: "creates a Tier1 boss directly. Use
`info_trooper_boss_spawn` instead."

`npc_boss_tier1` stays in batch13's `TEAM_SUBCLASS` table, unused, with a
note — the pairing is read and correct if the NPC is ever placed directly.

## Counts

Entity count is unchanged: one class swapped for another, and the two proxies
restored in the previous drop put `EXPECT_CLASSPROPS`/`EXPECT_PLUGLIST` back
at **611**. `EXPECT_ELEMENTS: 87916` may move, since the guardians carry
three fewer keyvalues each. Let the run report it rather than editing on a
guess.

## Still open, same block of batch13

citadel.fgd says reinforcement spawns are the SAME class with
`ReinforcementsOnly` set, one per four troopers under each zipline, and that
without them troopers will not spawn. We emit `info_trooper_spawn` instead.
Untouched here, but it now sits ten lines from code that knows the answer.
