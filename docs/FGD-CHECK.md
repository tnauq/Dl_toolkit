# The FGD check

`tools/fgd_check.py`, run by `.github/workflows/fgd-check.yml` on every push
that touches the plan, a batch script, or an FGD.

## What it is for

Almost every fault found on 2026-08-29 was the same shape: a classname or a
keyvalue that looked right, emitted cleanly, verified green, and would have
done nothing in game.

    target                  should have been exitpoint
    light_environment       not a class in citadel.fgd or base.fgd
    npc_boss_tier1          not a class either - a unit in the vdata
    rebels_t1_boss_orange   not one of the eight legal BossName values

All four are detectable against `citadel.fgd`, which is the exact table the
compiler validates against. This does that check in seconds, with no CSDK, no
wine and no shaders — which matters precisely because we cannot compile yet.
It recovers most of what a compile would have told us.

## Severity, and why absence is not an error

    ERROR   the tables CONTRADICT it - a choices value outside its list
    WARN    not found in the tables we hold
    NOTE    found, with an annotation worth knowing - (Broken), Unused

citadel.fgd `@include`s six files and we hold two. An unknown class may
simply live in `lights.fgd`. Treating absence as failure would flag
`logic_relay`, which is real. So only errors fail the run; `--strict` also
fails on warnings, and is not used in CI.

## Two parsing traps, both hit and both fixed

**Do not scan for the first `=` in a class header.** Metadata blocks are full
of `entity_tool_name = "Lane Guardian"`, so a naive scan stops inside the
metadata. That cost 107 of citadel.fgd's 197 classes on the first run, and it
surfaced as `info_super_trooper_spawn` being "in none of the tables" — a
table failure wearing the costume of a finding. The class name is either
inline or on a later line that BEGINS with `=`; metadata lines never do.

**`vdata_model{my_key = "subclass_name"}` declares a keyvalue in the
header**, not the body. It is how an NPC class picks its model out of the
vdata. Without handling it, every `npc_boss_tier2` warns about
`subclass_name`, which is both real and required.

## Verified against

Real entities from `batch13.build_objectives()` plus four planted faults —
the four listed above. It caught all four and passed everything real.
