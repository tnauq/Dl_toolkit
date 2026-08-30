# The FGD set

Fifteen files, the complete `@include` closure of `citadel.fgd` plus the two
the compiler asks for by name. `tools/fgd_check.py` reads every `.fgd` in
this directory: **557 classes**.

    citadel.fgd                 the game's own entities        124
    base.fgd                    generic Source 2               323
    ai_basenpc.fgd                                              38
    ai_defaultnpc.fgd                                           17
    faceposer.fgd                                               33
    lights.fgd                  light_omni, light_spot,          8
                                env_cubemap, probe volumes
    lights2.fgd                 light_barn, light_rect,          4
                                light_omni2
    lights_base.fgd             light_environment                4
    markup_volumes.fgd                                           6
    postprocessing.fgd          post_processing_volume           1
    models_base_breakables.fgd                                   1
    workshop_addoninfo_base.fgd                                  1
    models_gamedata.fgd         asked for by the compiler        0
    models_base.fgd                                              0
    vdata_base.fgd                                               0

The three reporting 0 classes are not failures. They declare anim events,
model gamedata and vdata structs rather than map entities - `@AnimEvent`,
`@struct` and similar - which `fgd_check` does not parse because nothing in
the plan can reference them. `models_gamedata.fgd` is here because the
compiler names it three times in the 2026-08-28 log, not because this tool
needs it.

## Where these belong at compile time

**Not here.** `gameinfo.gi` line 194 declares `"fgd" "citadel.fgd"` relative
to the GAME path, so the compiler wants them in
`Reduced_CSDK_12/game/citadel/`. This directory is for `fgd_check` and for
reading. The 2026-08-28 compile failed to find `citadel.fgd` for exactly this
reason.

## Trust

Every one of these is annotated by hand in places - "//does this even work?
i think it should" - and READ ME FIRST credits `citadel.fgd` to
@NeoExperiences and @dirtkiller23, built from the CS2 FGD with entities
extracted by Source 2 Viewer. So:

- **A presence is strong evidence.** The compiler accepts what is in here.
- **An absence is weaker**, though much weaker than it was: the include
  closure is now complete, so an unknown classname is more likely to be
  wrong than to be missing. It is still not proof.
