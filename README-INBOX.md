# Inbox drop — the FGD check, the prefab probe, and housekeeping (2026-08-30)

    tools/fgd_check.py                        NEW - the main event
    .github/workflows/fgd-check.yml           NEW
    .github/workflows/prefab-probe.yml        NEW
    .github/workflows/entity-survey.yml       MODIFIED - keyvalues2
    batch16.py                                MODIFIED - two comment-level fixes
    docs/FGD-CHECK.md                         NEW

`entity-survey.yml` and `batch16.py` were sha1-verified against the manifest
before editing. Everything parses; the validator was tested end to end.

## 1. The FGD check is the valuable one

It validates every entity in the plan against `citadel.fgd` and `base.fgd` —
the exact table the compiler uses. All four of yesterday's silent faults are
statically detectable this way, and it runs in seconds with no CSDK.

Tested against real entities from `batch13.build_objectives()` with four
faults planted. It caught all four:

    ERROR  BossName='rebels_t1_boss_orange' is not one of boss_rebel_t1_*
    WARN   classname 'light_environment' is in none of the tables
    WARN   key 'target' not declared on citadel_trigger_teleport
    NOTE   'building_health' and 'final' are marked (Broken)

Errors fail the run; warnings do not, because citadel.fgd `@include`s six
files and we hold two — an unknown class may live in `lights.fgd`. See
`docs/FGD-CHECK.md`, including the two parsing traps that cost 107 of 197
classes on the first attempt.

**Expect warnings on the first real run.** Anything the plan emits that lives
in a file we do not have will show up. Read them before deciding any are
noise.

## 2. The prefab probe

The twelve unresolved `Kill` targets are prefab-scoped — they carry a `125_`
prefix or a grate/ladder name, and nothing else unresolved. This follows the
prefab references out of the map, converts any prefab file present on disk,
and reads targetname → classname out of it. That turns the lid's brush class
from a reasoned choice into a copy.

If every referenced prefab turns out to be in the game vpk, it says so
plainly and `func_brush` stands. Its first report also lists the numeric name
prefixes found — if `125` appears, the link to the unresolved targets is
confirmed rather than inferred.

## 3. entity-survey now converts with ids

`-oe keyvalues2_noids` → `-oe keyvalues2`. That flag was upstream of all
three failed attempts to attribute the 89 connections: noids strips element
ids, and without ids nothing can be linked to its referrer. The text is
larger (51 MB) and every downstream step was written against the noids shape,
so if a step starts reporting differently, that line is the first suspect.

## 4. Two corrections in batch16, both comment-level

**The patron's placeholder model was already resolved.** That block emits no
`model` key at all. citadel.fgd declares `npc_boss_tier3` with
`vdata_model{my_key = "subclass_name" vdata_key = "m_sModelName"}`, so the
class takes its model from the vdata via `subclass_name` — which is set, and
which npc_units.vdata maps to `patron_amber.vmdl`. Setting `model` would
override the thing that already works. The open item can come off the list.

**Sub-objective lanes are now a named constant.** `PROXY_LANES` defaults to
`["0", "0"]`, unchanged. But dl_example names its shrines per lane —
`_yellow` and `_purple`, the outer pair — and never uses the None value. If
the game routes sub-objective state by lane, 0 means nothing gets shielded
while resolving perfectly cleanly. One line to switch to `["1", "6"]`.

## Not done

`docs/one_file_please.md` and `docs/zip_citadel_folder.md` still send someone
hunting for an FGD that is not on a retail disk. Both want retiring, but they
are prose files and `inbox` overwrites wholesale, so I would rather rewrite
them deliberately than reconstruct them from a dump.
