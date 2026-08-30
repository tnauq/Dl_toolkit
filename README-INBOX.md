# Inbox drop — thirteen FGDs, and reading the compile log (2026-08-30)

    docs/reference/citadel/*.fgd        15 files - the complete set
    docs/reference/citadel/README-FGDS.md   what each one carries
    docs/logs/compile_20260828.md       NEW - the compile attempt, read

## Why fgd_check still found nothing

**The files have to be in the repo, not in your storage.** `fgd_check` reads
the working tree — it searches `docs/reference/citadel`, `docs/reference`,
`reference`, the repo root and `$FGD_DIR`, and nothing else. Uploading the
FGDs to a chat does not put them on the runner. This drop commits all
thirteen, so applying it is the fix.

With the full set the table goes from 447 classes to **557**, and the
`@include` closure of citadel.fgd is now complete - nothing it references is
missing.

`models_gamedata.fgd` and `lights_base.fgd` both arrived, so the two asks
from the last drop are closed. Three files report 0 classes
(`models_gamedata`, `models_base`, `vdata_base`); that is expected, they
declare anim events and vdata structs rather than map entities. See
`docs/reference/citadel/README-FGDS.md`.

## The compile log is the real news

It got further than CI ever has: it found `citadel\maps\dust2.vmap` and
initialised Embree. But it never compiled anything, and it names why.

**The CSDK has no game content.** Ninety-odd `Failed loading resource` lines,
starting with `materials/error.vmat_c`. That is READ ME FIRST step 3 — the
`pak01_dir.vpk` export — still not done. The access violation is very
probably a null resource handle downstream of that, not our map. `exit: 124`
is a timeout kill, not a compiler code; give the next run a longer one so the
crash reports itself.

**The FGDs must also go into the CSDK.** `gameinfo.gi` line 194 declares the
fgd path relative to the GAME path, so the compiler wants
`Reduced_CSDK_12/game/citadel/citadel.fgd`. The repo copies are for
`fgd_check` and for reading; they are on no search path the compiler uses.

**And there is no entity validation in that log.** No parse errors, no
unknown classnames — but with `citadel.fgd` unloaded the compiler had no
table to check against, so it could not have complained. Do not read the
silence as a clean map. That is precisely the gap `fgd_check` fills.

## One correction to yesterday, in our favour and against a conclusion I made

**`light_environment` is a real class.** I switched the sun off it on the
grounds that it appeared in neither citadel.fgd nor base.fgd. It lives in
`lights_base.fgd`, which is now here. That was an absence argument, and the
handoff's own trust rule says absences are weak — it was weaker than I
treated it.

**But the switch was right anyway, and now for a second reason.** Running
the validator against the complete set with the OLD sun restored:

    WARN  light_environment: key 'color' not declared on the class or its bases

`light_environment` takes `skycolor`, `skyintensity`, `skytexture`,
`brightnessscale`, `angulardiameter` and the shadow cascades. It has no
`color`, no `brightness`, no `castshadows` — three of the five keys the old
sun emitted were not on the class. So that entity was wrong in its keys as
well as arguably wrong in its class.

The primary reason still stands too: `env_global_light` is the only lighting
entity with runtime inputs (`LightColor`, `SetAngles`, `EnableShadows`,
`Enable`/`Disable`), and the night mode cannot work without them.

## Nothing further needed from storage

The include closure is complete. If a future compile names an FGD we do not
have, that is the moment to go back — otherwise the table is done.
