# Inbox drop — the connection-ownership probe (2026-08-29)

    .github/workflows/connection-owner-probe.yml   NEW
    docs/LID-DOORS-LIGHTING.md                     NEW

Additive. Nothing existing is touched. Apply the FGD drop
(`inbox-20260829c-fgd`) first if it has not gone in yet — this one assumes
`docs/FINDINGS-fgd-2026-08-29.md` exists but does not depend on it.

## Why the last three attempts failed, and what changed

89 connections in dl_example, and no attempt has been able to say which
entity fires which. Nearest-classname-above said `light_omni2` fires
`OnTrooperKilled`. Brace depth said all 89 are unnested. The third dumped 80
lines of context around each and nobody has read 89 blocks.

**The cause was upstream of all three.** `entity-survey.yml` converts the
fixture with `-oe keyvalues2_noids`, and noids strips element ids. Without
ids there is nothing linking a connection back to its owner, so both
inference methods were guessing at a file the format had already stripped the
answer out of.

This workflow converts with `-oe keyvalues2`. Ownership becomes a lookup.

## How it avoids repeating the mistake

Two independent attribution methods — by reference id, and by containment —
run and are **cross-checked**. Agreement is a finding. Disagreement goes in
`out/disagreements.md` and neither answer is promoted. `out/structure.md` is
written before any parsing, so a run that attributes nothing still says why.

I tested the parser on a synthetic keyvalues2 sample covering both an inline
nested connection and one referenced by id from an element_array. It caught a
real bug in the process: descending two levels to find a classname makes the
ROOT element look like an entity, at which point it swallows every unnested
connection in the file — attempt 1's bug wearing a different hat. Descent is
one level, with a comment saying why widening it is not the fix.

## What it answers

- **THE LID.** `out/targets.md` resolves every `targetName` to the classname
  of the entity carrying it. The row whose input is `Kill` names the class of
  a killable brush outright — the single fact the lid has been blocked on.
- **DOORS ON GUARDIAN DEATH.** Reports what an `OnBossKilled` drives, and
  says so plainly if nothing matches.
- **THE SHRINE → PATRON CHAIN.** If dl_example's shrines carry connections,
  the input name citadel.fgd does not declare is in them. This is the only
  known place it can be.

## A correction worth propagating

`PROBE.md` item 5 says the plan format cannot express a connection. **It can,
and has for a while** — `batch15.py` has a `wire()` helper and
`emit-dust2.yml` pins `EXPECT_CONN: 56`, verified through dmxconvert. The lid
is not blocked on converter work. That paragraph in PROBE.md should go.

## On the night mode

`docs/LID-DOORS-LIGHTING.md` covers it. The short version: pre-baking two
lighting solutions and swapping them is not a thing Source 2 does — baked
lightmaps are baked once. What can change at runtime is the sun
(`env_global_light` takes `LightColor`, `SetAngles`, `EnableShadows` and
`Enable`/`Disable`), the fog (`SetFogColor`, `SetFogStrength`, `SetFarZ`),
and post-processing. Fog is where most of the effect lives.

The X-minute revert is free: `delay` is already a field on every connection,
so one output fires night at delay 0 and day at delay 300.

## NEXT ASK: five more FGD files

`citadel.fgd` line 7 onwards:

    @include "base.fgd"          @include "lights.fgd"
    @include "lights2.fgd"       @include "markup_volumes.fgd"
    @include "postprocessing.fgd"  @include "ai_defaultnpc.fgd"

**The entity table we have is incomplete by design.** `logic_relay`,
`logic_timer` and the `Kill` input itself all live in `base.fgd` — which is
why `Kill` appears in twelve fixture connections and nowhere in citadel.fgd.
`postprocessing.fgd` and `lights2.fgd` are the night-mode question.

They sit in the same folder as citadel.fgd. Since you have the full copy on
storage: those five, and `base.fgd` first.
