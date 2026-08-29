# The lid, doors on guardian death, and a night mode

Written 2026-08-29, after reading `citadel.fgd`. Three related questions,
because all three are the same mechanism: an entity fires an output, another
entity does something.

## FIRST, A CORRECTION: the plan format CAN express connections

`PROBE.md` item 5 says:

> THE PLAN FORMAT CANNOT EXPRESS THE REAL MECHANISM YET. batch13 emits
> keyvalues only; no script here writes a connection, and the converter has
> never been asked to.

**That is stale.** `batch15.py` writes connections today — it has a `wire()`
helper emitting `outputName`, `targetType 7`, `targetName`, `inputName`,
`overrideParam`, `delay`, `timesToFire`, and `emit-dust2.yml` pins
`EXPECT_CONN: 56`, verified through `dmxconvert`'s own element census. The
shop networks and the guardian kill-relays are all wired that way.

So the lid is **not** blocked on converter work. It has not been blocked on
converter work for some time. What it is blocked on is one fact: which
classname a killable brush should be.

## 1. The lid

The mechanism, from PROBE.md item 5, read off the fixture:

    destroyable_building  OnDestroyed -> <named brush> . Kill   delay 0, timesToFire -1

twelve times, at targets named `*_grate_prop`, `*_grate_brush`,
`*_ladder_brush`. The geometry is not moved or toggled — a named entity is
destroyed and the hole is open from then on.

And the midboss version: the midboss is a camp, camps fire `OnTrooperKilled`,
so `midboss_camp OnTrooperKilled -> midboss_lid . Kill`.

**What is missing is the class of the lid brush.** `func_conditional_collidable`
is the candidate — the only brush-model non-trigger in the fixture — but
nothing confirms it answers `Kill`. `citadel.fgd` does not settle it either:
it describes `func_conditional_collidable` as a trigger applying collision
when conditions are met, and declares no inputs on it at all.

`connection-owner-probe` answers this directly. Its `out/targets.md`
resolves every `targetName` to the classname of the entity carrying that
targetname, so the row whose input is `Kill` names the class outright.

### How far it can be verified without a desktop

| claim | verifiable in CI? |
|---|---|
| the plan can carry the connection | YES — `EXPECT_CONN` rises by the number added |
| it survives the emitter and dmxconvert | YES — plan-roundtrip and emit-dust2 |
| every targetName resolves to a real entity | YES — preflight, once the key is in `REF_KEYS` |
| the classname is one the compiler accepts | YES, once a compile runs with the FGD present |
| **the lid actually opens when the midboss dies** | NO. Game only. |

That last row is the honest ceiling, and it is the same ceiling everything
else in this project has: green means structurally valid, never "it works".

## 2. Doors that open on guardian death

Mechanically identical, and if the lid works this works. One caution from the
FGD: **`npc_barrack_boss` declares no outputs at all**, and
`npc_boss_tier1` is not in the file. `OnBossKilled` is declared on
`npc_boss_tier2` and `npc_boss_tier3`; `OnTrooperKilled` on
`npc_trooper_boss`.

So "guardian death" may not have an output to hang a door on, depending on
which entity is your guardian. `batch15.py` already uses a `GUARDIAN_OUTPUT`
constant read off dl_example, so the fixture says something the FGD does not
— which is again the probe's job. Its "DOORS: what a boss death drives"
section reports exactly this, including the case where nothing matches.

Worth noting the design consequence: a killed door is **permanently** open.
That suits "guardian dies, this route opens for the rest of the match". It
cannot close again, so it is a one-way state change, not a door.

## 3. Day/night on midboss death

Three parts, and they are not equally possible.

### The part that does not work: pre-baking two setups

Source 2 bakes static lighting into lightmaps at compile time, one set per
map. There is no runtime switch between two baked solutions — the baked
component is simply what it is. Anything that changes at runtime has to be
the **dynamic** part of the lighting.

So "pre-bake a day set and a night set and swap" is not the shape this can
take. What can change is the sun, the fog and the post-processing, over a
baked-once world.

### The part that does work: env_global_light

From `citadel.fgd`, `env_global_light` derives from `Targetname` and
`EnableDisable` and declares:

    input LightColor(color255)     input SetAngles(string)
    input SetFOV(float)            input SetNearZDistance(float)
    input SetTexture(string)       input EnableShadows(bool)

That is a sun you can recolour and re-aim at runtime, plus `Enable`/`Disable`
from the base class. Its static keys include `color`, `lightscale`,
`ambientcolor1/2/3`, `ambientscale1/2`, `specularcolor`, `fow_darkness`.

There is also a fog entity carrying `SetFogStartDistance`, `SetFogEndDistance`,
`SetFogColor`, `SetFogStrength`, `SetFogMaxOpacity` and `SetFarZ` as inputs.
Fog is where a night mode gets most of its money: recolouring and thickening
fog reads as nightfall far more strongly than dimming a sun does.

### The timer, which is free

No timer entity is needed. `delay` is already a field on every connection, so
one output fires both halves:

    midboss_camp  OnTrooperKilled -> night_relay . Trigger   delay 0
    midboss_camp  OnTrooperKilled -> day_relay   . Trigger   delay 300

Five minutes of night from a single event, using only fields the emitter
already writes. `timesToFire -1` means unlimited, so it works on every
midboss respawn — though note the fixture's midboss camp has both spawn
timings at `-1`, so it may not respawn on a clock at all.

### What this needs before it can be written

`logic_relay` is **not in citadel.fgd**, though the fixture has ten of them.
It will be in `base.fgd`. Without that file we do not know its inputs
(`Trigger`, presumably) or whether a relay is even the right intermediary.
Firing the light entities directly from the camp would avoid the relay
entirely, at the cost of one connection per light per state.

Also unknown: whether `LightColor` and friends affect anything meaningful
over a baked map, or whether the effect is subtle enough not to be worth the
entities. That is a look-at-it-in-game question.

## THE ASK: five more FGD files

`citadel.fgd` opens with:

    @include "base.fgd"
    @include "lights.fgd"
    @include "lights2.fgd"
    @include "markup_volumes.fgd"
    @include "postprocessing.fgd"
    @include "ai_defaultnpc.fgd"

**So the entity table we have is deliberately incomplete.** Every generic
Source entity lives in those files: `logic_relay`, `logic_timer`,
`logic_auto`, `func_brush`, and — directly relevant — the `Kill` input
itself, which is why we could not find `Kill` declared anywhere in
citadel.fgd despite twelve connections using it.

`postprocessing.fgd` and `lights2.fgd` are exactly the night-mode question.
`base.fgd` is the lid question.

They will sit beside `citadel.fgd` in the same folder. If they are on your
storage, they are the next most valuable thing after the file we already
have.
