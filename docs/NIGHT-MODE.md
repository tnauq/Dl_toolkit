# Night mode on midboss death

Read off `base.fgd`, `postprocessing.fgd` and `citadel.fgd`, all committed
under `docs/reference/citadel/`. Supersedes the lighting half of
`docs/LID-DOORS-LIGHTING.md`.

## The transition is a SNAP, by choice

Decided 2026-08-29: the change is instant, timed to land with the global
midboss death sound. It is a rare event, and a hard cut reads as an event
rather than as weather.

This simplifies the design considerably, so it is worth being explicit about
what is NOT being used:

- `env_fog_controller`'s lerp system - `SetColorLerpTo`,
  `SetEndDistLerpTo`, `SetMaxDensityLerpTo`, `StartFogTransition`. Available,
  deliberately unused. If the snap turns out to read as a glitch rather than
  an event, this is the fallback and it is a change of inputs, not of
  structure.
- `post_processing_volume`'s `fadetime`, which should be set to **0** for the
  same reason. Its default is 1.0, so leaving it alone would give a
  one-second fade that fights the sound cue.

Everything below is the instant form.

## The three levers

**Fog** - `env_fog_controller` (base.fgd). Plain setters, no lerp:
`SetColor`, `SetColorSecondary`, `SetStartDist`, `SetEndDist`,
`SetMaxDensity`, `SetFarZ`, `TurnOn`/`TurnOff`. This carries most of the
effect. `env_volumetric_fog_controller` and `env_volumetric_fog_volume` are
there too if flat fog is not enough.

**Sun** - `env_global_light` (citadel.fgd). `LightColor`, `SetAngles`,
`SetFOV`, `EnableShadows`, plus `Enable`/`Disable` from its base. It has no
lerp at all, so it was always going to snap; the rest now matches it.

**Post-processing** - `post_processing_volume` (postprocessing.fgd). A solid
entity based on `Trigger`, so it takes `Enable`/`Disable`. Set `master` to 1
for an unbounded volume and `fadetime` to 0. Two of these, day and night, one
enabled at a time, is the cleanest switch in the design.

## THE SKY DOES NOT CHANGE

`env_sky` declares **no inputs**. `skyname`, `tint_color` and
`brightnessscale` are author-time only. The sky material is fixed for the
match, and night has to come from fog, sun and post-processing underneath an
unchanged sky.

If a visibly different sky matters, the only route is a second `env_sky` and
a `Kill` on the first - permanent, one-way, and it cannot come back for the
day state. Not recommended.

Incidental: `skyname(resource:material)` filtered to `materials/skybox/` is
exactly what batch16 already emits, so that key was right.

## Wiring

`logic_relay` (base.fgd): inputs `Trigger`, `Toggle`, `CancelPending`;
outputs `OnSpawn`, `OnTrigger`. `Kill` is on the `GameEntity` base, so every
entity answers it.

    midboss_camp  OnTrooperKilled -> night_relay . Trigger   delay 0
    midboss_camp  OnTrooperKilled -> day_relay   . Trigger   delay 300

`delay` is a field on every connection, so the X-minute revert needs no timer
entity. Each relay's `OnTrigger` then fans out to the fog controller, the
global light and the two post-processing volumes - roughly 8-10 connections
in total, every one of them a shape `batch15.wire()` already emits.

**The fixture backs this pattern**: it fires `OnTrooperKilled -> <relay> .
Trigger` nine times. A camp driving a relay is exactly what dl_example does.

## Open

- `FastRetrigger` on `logic_relay` - without it a relay waits for everything
  downstream to finish before it can fire again. With a 300 s gap that will
  not matter, but if night is ever shortened it might.
- Whether the midboss camp fires `OnTrooperKilled` here at all. The fixture's
  midboss camp carries both spawn timings at -1.
- What a sensible `.vpost` looks like, and whether one has to be authored.
