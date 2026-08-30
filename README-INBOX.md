# Inbox drop — SHIPPING correction, cleanups, handoff (2026-08-30)

    SHIPPING.md              MODIFIED - the shader claim was false
    HANDOFF_20260831.md      NEW
    tools/fgd_check.py       MODIFIED - stale-plan note
    batch15.py               MODIFIED - one misleading log line

`SHIPPING.md` and `batch15.py` were sha1-verified against the manifest before
editing. Both parse / render.

## The correction that matters

SHIPPING.md's central claim — the Reduced CSDK ships no shaders, so a
DepotDownloader pull is required — **is false**, and it has shaped the desktop
plan for weeks. The `.vcs` files are there, inside VPKs that were never
unpacked.

The old text is kept below the correction rather than deleted, because the
depot commands are still the fallback and because the reasoning is worth
seeing next to what was wrong with it.

Two things added to the compile section while I was there: **copy the FGDs
into `Reduced_CSDK_12/game/citadel/`** (the last compile found neither, so it
had no entity table and could not have reported a bad classname), and **raise
the timeout** (`exit: 124` was a kill, not a compiler code).

## The stale-plan note

Not a failure — a printed note when `docs/plans/dust2_full.json` is older
than any `batch*.py`. That exact confusion cost real time earlier today: a
fix was pushed, the check ran, and it reported the same four errors, because
the plan is a committed artifact and editing a script does not regenerate it.

Tested both ways: silent when the plan is current, and it names the offending
scripts when it is not.

## batch15's shrine line

It printed *"shrine upgrades: none. No shrines in the plan yet"* on a map with
four. batch15 runs before batch16, which creates them. Now says so, and says
what would have to change to wire them.

## The handoff

`HANDOFF_20260831.md`. The two things I would make sure survive into the next
session:

**dl_example is a template map** — 58 targetnames, none containing grate or
ladder, and names like `shop_Sapphire_t1_lanecolor_shop_kill_relay`. Its
connections are pre-wired to names a mapper is expected to create. That closes
the lid question: `func_brush` is the answer, not a placeholder, because the
example declines to specify one.

**Four faults this session shared one shape** — a conclusion from a plausible
premise nobody verified: `target` for `exitpoint`, `npc_boss_tier1`,
`light_environment`, the shaders. The handoff records the pattern, not just
the fixes.

## Not done, still on the list

`csdk-fgd-check` is obsolete — it reports confidently about a partial release
excerpt and its FGD question is closed. `one_file_please.md` and
`zip_citadel_folder.md` still send people hunting for a file that is not on a
retail disk. All three are prose-or-delete decisions I would rather you make.
