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

## Deliberately NOT changed

Four judgement calls were left alone rather than guessed at, with the reading
recorded beside each in the code: whether to emit `objective` / `TeamNumber` /
`LaneNumber` on `info_teleport_location`; whether to move the sinners to a
type-6 camp and under which subclass; whether to keep emitting the proxy; and
whether `npc_boss_tier3.BossName` must conform to its two-value enumeration.

Also unchanged: `npc_boss_tier1` is absent from this FGD, but dl_example is
full of them, so that is an FGD gap and not a fault in our plan. This file is
annotated by hand — its presences are strong evidence, its absences weak.
