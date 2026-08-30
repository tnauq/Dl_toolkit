# Inbox drop — acting on the first real fgd_check run (2026-08-30)

    tools/fgd_check.py    MODIFIED - two parser faults, one noise filter
    batch16.py            MODIFIED - the teamnumber error
    batch15.py            MODIFIED - teamnumber off logic_relay

The check earned its keep on the first run against the real plan: 384
entities, 4 errors, 127 warnings, 20 notes. Triage below. **Two of the four
findings are real bugs and two were the checker's own fault.**

## REAL: teamnumber=0 on the teleport destinations (the 4 errors)

Mine, from yesterday. The reasoning was right and the value was wrong.

Those rooms ARE neutral — but citadel.fgd's `TeamNumber` base enumerates
only 2 (Rebels/North/Amber), 3 (Combine/South/Sapphire) and 4 (**Neutral**),
and defaults to 4. There is no 0. I took "0 is None" from the PROXY's
`sub_objective_lane` fields, which do list 0, and carried it across to a
different base class where it does not hold.

Now 4. `lanenum` 0 stays — `LaneNumber` is a different base and does list 0.

## REAL: 30 relays carried a teamnumber that logic_relay does not have

`logic_relay` derives from Targetname and EnableDisable and declares
`TriggerOnce` and `FastRetrigger`. No TeamNumber base, no teamnumber key.

Harmless in that an undeclared keyvalue is ignored — but it was also doing
nothing, and the twin swap was dutifully rewriting a value the entity cannot
represent. If anything ever reads teamnumber off a relay to decide ownership
it would read the twin's swapped value and be wrong silently. Now gated by a
`TEAM_KEY_CLASSES` table.

I did **not** add `logic_auto` to that table even though it looks similar.
fgd_check did not warn about it, so guessing would be changing behaviour on
no evidence.

## CHECKER'S FAULT: `skyname` on env_sky

`base.fgd` line 7217 declares `skyname(resource:material)`. The key regex
only accepted `[A-Za-z_0-9]+` as a type, so **every resource-typed key was
invisible** and a correct entity was reported as wrong.

That is the worst failure mode a validator has — a false positive sends
someone to "fix" working code. Fixed, and worth remembering when reading
future warnings.

## CHECKER'S FAULT: `Input SetTeam (integer)` listed as a legal team value

The input line sits inside the choices block and matched the choice pattern.
It did not change any verdict but it made the error message nonsense. Input
and output lines are now skipped.

## NOISE, now filtered: 94 camp-timing warnings

`InitialSpawnDelayInSeconds` and `SpawnIntervalInSeconds` are commented out
in citadel.fgd and annotated Unused. We emit them deliberately — they are a
faithful copy of dl_example's own camps. 94 repetitions of two lines buried
everything else, so they are now in an `EXPECTED_UNDECLARED` allowlist with
the reason attached. **Not deleted: entries there are decisions, and the list
is meant to be read.**

## LEFT ALONE, deliberately

**`citadel_minimap_boundary` is in none of the tables** (2 entities). It came
from batch13's read of dl_example, so the fixture says it is real and the FGD
does not mention it. That is the FGD trust rule working exactly as written:
presences are strong, absences weak, and the fixture outranks the FGD. No
change — but worth watching for in the next compile log, since the compiler
now has a table and can complain.

**20 notes are informational** — `LaneSide` annotated Unused on the twelve
barrack guardians, and `building_health`/`final` marked (Broken) on the four
shrines. Both already documented in the code. Nothing to do.

## After this the check should be: 0 errors, 3 warnings

The two `citadel_minimap_boundary` lines and nothing else. If more appear,
they are new.
