# Inbox drop — retail reference files, and a workflow to find the FGD (2026-08-29)

Two things, no deletions, nothing replaced.

    .github/workflows/csdk-fgd-check.yml    new workflow
    docs/reference/citadel/                 new directory, 22 files

## THE FINDING: citadel.fgd is not in a retail install

A helper sent their whole retail `game/citadel` folder. `find -iname '*.fgd'`
over 404 files returned NOTHING.

This is not their mistake. `gameinfo.gi` line 194 declares

    "fgd"   "citadel.fgd"   // NOTE: This is relative to the 'game' path.

so the game expects it at the game path and it still is not shipped there.
It is a tools-side file. That agrees with what CI already found from the
other direction — GameTracking ships no `.fgd` at all, and the compiler said
`Unable to find fgd file citadel.fgd!`.

**Do not ask a player for it again.** It is not on their disk.
`docs/one_file_please.md` and `docs/zip_citadel_folder.md` both send someone
looking for a file that is not there, and should be amended or retired.

## The workflow

`csdk-fgd-check` (`workflow_dispatch`) searches the ONE place nobody has
looked: the `csdk-12` release this repo already downloads on every compile
run. The FGD is a tools-side file and the CSDK is the tools. It may have been
sitting in the cache the whole time.

It reuses the `csdk-12-v1` cache key, so on a warm cache it is nearly free.
No compile, no wine, no timeout risk. Any FGDs found are uploaded as the
`csdk-fgds` artifact; the step sets `citadel=yes/no`.

**Read the listing even on a miss** — a differently-named FGD could still
carry the citadel entity definitions, so the job warns rather than passing
silently.

### The side question it also settles

While the tree is unpacked it counts `.vcs` and `.vfx`. SHIPPING.md asserts
the Reduced CSDK ships no shaders and that this is the sole reason CI cannot
compile — but that is read off community docs, and the only direct evidence
has ever been the compiler complaining about `complex.vfx`.

If a `complex.vcs` turns out to be present, the failure is a search-path
problem rather than a missing file, and **the depot pull may not be needed at
all**. Worth knowing before anyone spends an afternoon on DepotDownloader.

## What landed in docs/reference/citadel/

Trimmed 205 MB / 404 files down to 22. The keeper is `gameinfo.gi`:
SHIPPING.md says addon search paths plus an AddonRoot section are required
for a community-SDK map to load, and that a wrong brace gives
"Failed to parse KeyValues". This is the unmodified retail file to diff that
edit against. `SearchPaths` at line 64, `Game citadel` / `Game core` at 73-74.

Also `steam.inf` for build provenance, the 14 `citadel_*.cfg` mode configs
(the sandbox and dev-intro ones are the closest thing to a documented way to
boot into a map alone, which is the first-compile scenario), and four convar
schema/default files.

Dropped: the helper's personal data — `account_*.stats`, `cache_*.soc`, every
`user_convars_*` and `user_keys_*` slot, `video.txt`, and nine dated folders
of `rpt/` crash reports — plus 180 MB of CJK fonts, 35 localizations, and the
controller `.vdf` mappings. `maps/` and `bin/win64/` held no files at all.
The kept files were grepped for the account IDs; clean.

See `docs/reference/citadel/README.md` for the per-file rationale.

## Also settled this session, for whoever writes the next handoff

Titan is the SHRINE, confirmed on a second reading: it is the destroyable
building shielding the Patron, and destroyable_building is the class every
shrine in the plan already uses. The fixture proxy's four sub-objective slots
at lanes 1/3/4/6 are a FOUR-LANE ARTIFACT, not a count — dl_example is a
four-lane map, this one is three. That reconciles the tension that kept the
question open, and it also means two filled slots with an empty pair is the
expected shape rather than a gap.

`HANDOFF_20260829.md` still lists "whether titan means shrine or walker" as
unknown. It can move to the settled section.
