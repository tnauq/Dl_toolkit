# Inbox drop — citadel.fgd, and the fixes it forced (2026-08-29)

**This supersedes the earlier drop from the same day.** If that one was never
applied, this contains all of it plus the FGD work. If it was applied, this
overwrites the same files with newer content. Either way, apply this one.

    batch16.py                          MODIFIED - the exitpoint fix, + notes
    tools/preflight.py                  MODIFIED - exitpoint in REF_KEYS
    tools/fix_exitpoint.py              NEW - migrates the committed plan
    docs/FINDINGS-fgd-2026-08-29.md     NEW - the full reading
    docs/reference/citadel/citadel.fgd  NEW - the file itself
    docs/reference/citadel/             retail reference files + README
    .github/workflows/csdk-fgd-check.yml  NEW - now mainly a shader check

`batch16.py` and `tools/preflight.py` were taken from `repo-dump-4`, and both
round-tripped to a **byte-exact sha1 match against `repo-manifest.md`** before
being edited, so these are true modifications of the committed files rather
than reconstructions. Both parse.

## Run this after applying

    python3 tools/fix_exitpoint.py

`docs/plans/dust2_full.json` is a committed artifact built before the FGD
arrived, so its four teleport triggers still carry the old key. The tool is
idempotent, refuses to touch `trigger_catapult` (which uses `target`
correctly), and verifies every destination resolves before writing. Re-running
the whole batch chain would also work and is the more honest fix.

## THE BUG THIS CAUGHT

The teleporter's destination keyvalue is **`exitpoint`**, not `target`. We had
`target` — the Source convention, flagged in the code as a guess. It was
wrong, and it fails **silently**: no compile error, you walk into the trigger
and nothing happens. This was going to cost a desktop session.

It also would have broken the mirror. `twin_of` prefixes every key that names
another entity, and `exitpoint` was not in that list, so both mirrored
triggers would have pointed at the original half's destination. Fixed too.

## The other reversal: titan means PATRON

`npc_boss_tier3` is tool-named "Patron" and described as "Tier3 Bosses/Titans/
Patrons". `destroyable_building` is tool-named "Base Shrine". So this
morning's titan = shrine reading had the right entity and the wrong word.

**No code changed for this.** `minimap.py` already labels them Shrine and
Patron, and `PROXY_SUBS` still correctly points the sub-objectives at the
shrines. Only comments. But the next handoff should not repeat the claim.

## READ THIS BEFORE THE FIRST COMPILE

The FGD says of `npc_boss_tier3`: *"Make sure to use cover groups for each of
the boss states, otherwise the game will be unbeatable."* We emit
`CoverGroupID`, `dying_cover_id` and `vulnerable_cover_id` all **empty**.
That needs `info_cover_point` groups authored — real work, not a keyvalue.
It is flagged in the code and belongs at the top of the next handoff.

## Confirmed without needing a compile

- **Jump pads arc, they do not blink.** `trigger_catapult` is a
  "Bouncepad/Fan Trigger" with `launch_speed` (default 1000, we use 800) and
  `target` → `info_target_server_only`. One of SHIPPING.md's three
  first-compile questions, answered off the file.
- **Probe spellings.** `citadel_trigger_teleport` is the only teleporter
  candidate that exists; all three sinner candidates are absent. Verdicts
  recorded per line. `SPELLING_PROBE` was already off.
- **Lane 0 is legal** on the proxy's sub-objectives, so our zeroes were right,
  and the four slots are a four-lane artifact — the colour list still has
  Blue in it, and the FGD declares outputs for slots 1 and 2 only.

## Corrections to things we believed

- **Sinner is not the vault.** `ENeutralTrooperType` lists 6 "Sinner's
  Sacrifice" and 12 "Breakable Vault" as different values.
- **Camp spawn timings are inert** — both keys commented out and annotated
  "Unused" in the FGD. The tier-to-interval mapping does not matter.
- **`building_health` and `final` on the shrine are marked "(Broken)".**
- **`citadel_final_objective_proxy` is marked "Unused. Do not use."** Nothing
  else in the file is. Emission unchanged, but see the open questions.

## The four judgement calls, now decided

- **Teleport locations** emit `objective 3`, `teamnumber 0`, `lanenum 0`.
- **Sinners** are their own tier with `ENeutralTrooperType 6`, keeping
  `neutral_camp_vaults` as the subclass — borrowed, since the FGD names none.
- **Patron `BossName`** conforms to the enumeration: `boss_rebel_tier2_mid`,
  and `boss_combine_tier2_mid` on the twin via a new `EXPLICIT_SWAPS` table.
  The generic rebels↔combine rule matches neither (the FGD uses the singular
  "rebel") and would have produced `m_boss_rebel_tier2_mid`.
- **The proxy is dropped.** Read the next section before accepting this one.

## THE PROXY REPLACEMENT DOES NOT EXIST — READ THIS

Dropping `citadel_final_objective_proxy` was meant to be paired with wiring
shrine → patron by entity I/O. That half **cannot be done**: citadel.fgd
declares **no input on `npc_boss_tier3`** to fire. It has one output,
`OnBossKilled`, and no `SetVulnerable`, no `Enable`, nothing. All 35 inputs in
the entire file belong to fog, lighting, scenes, buoyancy, `EnableDisable`,
the speaking NPC, the sentry, or the lane test.

The shrine's side is fine — nine outputs including `OnDestroyed` and
`OnBecomeVulnerable`. Only the target is missing, and inventing an input name
would repeat the exact `target`/`exitpoint` mistake.

**So this plan now has no shrine-to-patron chain. The patron is vulnerable
from the first second.** That is a deliberate regression, taken over shipping
a class the FGD marks do-not-use. `EMIT_PROXY = False` in batch16 puts it
back in one line if you want the compile to tell you whether "Unused" means
inert.

The way out is dl_example's own connections. The entity survey found **89
`DmeConnectionData` blocks and could not attribute one of them to an owner**.
Reading who owns which wire is now the highest-value probe left.

## Counts will move

Dropping the proxy removes two entities (base and twin). `emit-dust2.yml`
pins `EXPECT_CLASSPROPS: 611`, `EXPECT_PLUGLIST: 611` and
`EXPECT_ELEMENTS: 87916`. The first two should become 609; the element delta
I did not try to predict. Let the run report and update from what it says —
those constants are deliberately not edited here on a guess.

## Also unchanged: `npc_boss_tier1` is absent from this FGD, but dl_example is
full of them, so that is an FGD gap and not a fault in our plan. This file is
annotated by hand — its presences are strong evidence, its absences weak.
