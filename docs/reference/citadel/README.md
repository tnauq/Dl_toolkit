# Retail `game/citadel` reference files

Extracted from a helper's retail Deadlock install, 2026-08-29. Trimmed from
404 files / 205 MB down to the 22 that are useful to this project.

## UPDATE, later the same day: we have the FGD

A copy turned up in the helper's own storage and is committed here as
`citadel.fgd` (114,917 bytes, 2,123 lines, 197 class declarations). Read
`docs/FINDINGS-fgd-2026-08-29.md` for what it answered.

The section below still stands and is still worth knowing: the file is NOT
part of a retail install, so this copy came from a tools or community
distribution. It carries hand annotations, which is why FINDINGS treats its
absences as weak evidence and its presences as strong.

## THE ORIGINAL HEADLINE: there is no citadel.fgd in a retail install

`find -iname '*.fgd'` over the whole retail `game/citadel` tree returned
NOTHING. This is not a mistake by whoever sent it.

`gameinfo.gi` line 194 declares:

    "fgd"   "citadel.fgd"   // NOTE: This is relative to the 'game' path.

So the game expects the file at the game path and it still is not shipped
there. It is a tools-side file. This agrees with what CI found from the other
direction: GameTracking ships no `.fgd` at all, and the compiler said
`Unable to find fgd file citadel.fgd!`.

Next place to look, cheapest first:

1. The `csdk-12` release assets already in this repo. See
   `.github/workflows/csdk-fgd-check.yml`, which does exactly this.
2. Failing that, step 3 of the full-CSDK procedure in SHIPPING.md — the
   Source 2 Viewer export of `game/citadel/pak01_dir.vpk`. The same step that
   supplies the shaders.

Do not ask the helper for it again. It is not on their disk.

## What IS here, and why

    gameinfo.gi                 The reason to keep any of this. SHIPPING.md
                                says addon search paths plus an AddonRoot
                                section are needed for a community-SDK map to
                                load, and that a wrong brace produces
                                "Failed to parse KeyValues". This is the
                                unmodified retail file to diff an edit
                                against. SearchPaths block at line 64,
                                `Game citadel` / `Game core` at 73-74.
    gameinfo_branchspecific.gi  Small companion, included for completeness.
    steam.inf                   Build number the above was taken from, so a
                                later diff knows what it is diffing against.
    cfg/citadel_*.cfg           Convar sets the game itself uses for sandbox,
                                botmatch, hideout and dev-intro modes. The
                                sandbox and dev-intro ones are the closest
                                thing to a documented way to boot into a map
                                alone, which is the first-compile scenario.
    cfg/citadel_server.cfg      Server-side counterpart.
    cfg/boot.vcfg
    cfg/configschema.vcfg       Convar schema and shipped defaults. Useful
    cfg/configdefaults.pc.vcfg  only as a lookup for what a convar is called
    cfg/machine_convars_default.vcfg  and what it defaults to.

## What was dropped, and why

Two categories.

PERSONAL DATA belonging to the helper, which should not be in a repo:
`account_*.stats`, `cache_*.soc`, every `user_convars_*` and `user_keys_*`
slot, `video.txt`, and nine dated folders of `rpt/` crash reports.

BULK with no bearing on the project: `panorama/fonts` (~180 MB of CJK
typefaces), `resource/localization` (35 languages), `resource/`, and the
controller-mapping `.vdf` files. `maps/` and `bin/win64/` contained no files
at all.

If more is ever needed from that install, ask for a specific path rather than
the folder — but note that the vpks, where nearly everything actually lives,
were not in the original zip either.
