# Night mode, revised with base.fgd in hand

Supersedes the lighting half of `docs/LID-DOORS-LIGHTING.md`. Everything
below is read off `base.fgd` and `postprocessing.fgd`, now committed under
`docs/reference/citadel/`.

## The lever is fog, not the sun

`env_fog_controller` (base.fgd) is the strongest thing available, because it
has a **transition system built in**:

    SetColorLerpTo        SetColorSecondaryLerpTo
    SetStartDistLerpTo    SetEndDistLerpTo
    SetMaxDensityLerpTo   Set2DSkyboxFogFactorLerpTo
    StartFogTransition    <- fires the lerp

So: set every LerpTo value, then fire `StartFogTransition`, and the fog eases
from day to night rather than snapping. It also has plain `SetColor`,
`SetStartDist`, `SetEndDist`, `SetFarZ`, `SetMaxDensity`, `TurnOn`/`TurnOff`.

`env_volumetric_fog_controller` and `env_volumetric_fog_volume` exist too, if
the flat fog is not enough.

## The sun, second

`env_global_light` (citadel.fgd) takes `LightColor`, `SetAngles`, `SetFOV`,
`EnableShadows`, plus `Enable`/`Disable` from its base. Recolouring and
re-aiming it changes direct light and shadow direction. It has no lerp, so
any change here is instant — one reason fog carries the transition.

## Post-processing, third

`post_processing_volume` (postprocessing.fgd) is a **solid** entity based on
`Trigger`, so it takes `Enable`/`Disable`. It carries a `.vpost` resource
plus exposure controls and — the useful part —
**`fadetime`, "Time to transition to these postprocessing settings in
seconds"**. Set `master` to 1 for an unbounded volume covering the map.

Two of these, day and night, one enabled at a time, is the cleanest switch in
the whole design.

## THE SKY DOES NOT CHANGE

`env_sky` declares **no inputs at all**. `skyname`, `tint_color` and
`brightnessscale` are set at author time and stay. So the sky material is
fixed for the match and the night look has to come from fog, sun and
post-processing under an unchanged sky.

Incidental confirmation: `skyname(resource:material)` with an
`initial_filter_string` of `materials/skybox/` is exactly what batch16
already emits, so that key was right.

## The wiring, and the timer

`logic_relay` (base.fgd) is confirmed: inputs `Trigger`, `Toggle`,
`CancelPending`; outputs `OnSpawn`, `OnTrigger`. `logic_timer` exists as
well, and `logic_auto` for the initial state.

`Kill` is confirmed too, on the `GameEntity` base class, which is why it
appears in twelve fixture connections and nowhere in citadel.fgd. **Every
entity answers Kill.** That closes the lid's only open question in principle
— though which brush class to use is still worth reading off the probe.

The X-minute revert needs no timer entity, since `delay` is a field on every
connection:

    midboss_camp  OnTrooperKilled -> night_relay . Trigger   delay 0
    midboss_camp  OnTrooperKilled -> day_relay   . Trigger   delay 300

A relay per state keeps the wiring in one place: each relay's `OnTrigger`
fans out to the fog controller, the global light and the post-processing
volumes. Around 8-10 connections total, all of them shapes `batch15.wire()`
already emits.

## What is still unknown

- Whether the fog lerp inputs behave over a baked map in Deadlock
  specifically. base.fgd is the generic Source 2 table.
- What a sensible `.vpost` is, and whether one has to be authored.
- Whether the midboss camp fires `OnTrooperKilled` at all here — the fixture
  camp has both spawn timings at -1. The probe answers this.
