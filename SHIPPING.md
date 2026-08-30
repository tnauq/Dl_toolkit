# Shipping this map — the desktop side

Everything here is READ off the community documentation
(deadlockmodding.pages.dev) and one mapper's write-up, 2026-08-29. None of it
has been done by anyone on this project, because none of it can be done from
a phone. It is written down so whoever has a desktop does not have to find it
again.

## CORRECTION, 2026-08-30: the shaders were there all along

**The section below was wrong on its central claim, and it cost weeks.** Read
this first.

The reasoning was: the Reduced CSDK ships "without full game files", so it has
no shaders, so `No valid vcs file found for shader complex.vfx` is a missing
dependency, so a DepotDownloader pull is required. Every step of that follows
from the one before it. The first step was never checked.

It is false. **The Reduced CSDK contains plenty of `.vcs` files.** They are
inside VPKs that had not been unpacked, so the compiler — which resolves
loose files on a search path, not archive members — could not see them.

The 2026-08-28 compile log agrees in hindsight. Roughly ninety
`Failed loading resource` lines for `materials/dev/*` and `materials/tools/*`
sit alongside the missing shader, and I read those as two problems. They are
one: everything is still packed.

**So the depot pull in step 2 below is probably NOT required.** What is
required is finishing the export, which is steps 3 to 5 — and note step 4
deletes the VPKs deliberately, because with both the archive and the loose
files present the engine can resolve to either.

The order to try: do 3, 4 and 5 against the VPKs already present. Only if
something is genuinely absent after that does step 2 become necessary.

### The reasoning error, recorded because it will recur

"Not shipped with full game files" is a claim about game content. Shaders
were assumed to be game content. Nobody looked. The same shape has now caught
this project four times — `target` for `exitpoint`, `npc_boss_tier1`,
`light_environment`, and this — and the tell each time was a conclusion drawn
from a plausible premise that nothing had verified.

The old section, kept because the depot commands are still the fallback:

## Why CI could not do this (SUPERSEDED — see above)

Your repo's `csdk-12` release is the **Reduced** CSDK 12 — the community docs
say plainly it is "a stripped down version of the full CSDK 12 (without full
game files)". No game files means no shaders, and the compile dies on

    No valid vcs file found for shader complex.vfx

That is the whole story. Everything else in the pipeline works — see PROBE.md.

## Getting a full CSDK

The documented procedure, which needs Deadlock owned on Steam:

1. Download Reduced CSDK 12 and unpack it. NOT inside OneDrive-managed
   folders (Desktop, Documents) — the docs warn it breaks permissions.
2. Get DepotDownloader (github.com/SteamRE/DepotDownloader) and pull two
   depots into the CSDK root:

       DepotDownloader -app 1422450 -depot 1422451 -manifest 2639812037154209539 -qr -dir "...\Reduced_CSDK_12"
       DepotDownloader -app 1422450 -depot 1422456 -manifest 6378769520310560496 -qr -dir "...\Reduced_CSDK_12"

   If Steam 401s on the manifests — which it does for anyone who got access
   after those builds — the docs host a manifest archive to drop in first.
3. Open `game/citadel/pak01_dir.vpk` in Source 2 Viewer, right click,
   "Export as is", into `Reduced_CSDK_12/game/citadel`.
4. Delete `pak01_dir.vpk` and every `pak01_###.vpk` from `game/citadel` and
   `game/core`.
5. Re-extract the Reduced CSDK zip over the top, replacing files. The docs
   call this a necessary step.

THE SHADERS ARRIVE AT STEP 3 — and step 3 is an unpack, not a download. See
the correction at the top: they are already on disk, inside the VPKs. Step 2
is the fallback, not the prerequisite.

ALSO COPY THE FGDs IN. `gameinfo.gi` line 194 declares `"fgd" "citadel.fgd"`
relative to the GAME path, so `citadel.fgd` and `models_gamedata.fgd` belong
at `Reduced_CSDK_12/game/citadel/`. Both are committed under
`docs/reference/citadel/`. The 2026-08-28 compile could not find either, and
without them the compiler has no entity table — so it cannot report a bad
classname even when there is one, and a silent log is not a clean map.

AND RAISE THE TIMEOUT. That run ended in `exit: 124`, which is a timeout kill
rather than a compiler code, after an access violation. The crash is the
payload; do not let the wrapper kill it first.

## Compiling

Two routes, and the second is the one to use.

**GUIMapCompiler** — `Reduced_CSDK_12/GUIMapCompiler/CS2MapCompiler.exe`.
Needs the `bin_cs2` binaries, which the release already has. The docs say
this is the tool "needed in order to compile maps with lighting", without
the tools open. Point it at the emitted `.vmap`.

**Hammer** — open the `.vmap`, Full Compile, Compile. One mapper's note adds
that the custom compile path wants `deadlock.exe` from
`Reduced_CSDK_12\game\bin_cs2\win64`.

NOTE THE BINARY SETS, because they are not interchangeable:

    bin         regular tools. Compiles Animgraph1, crashes previewing
                some projected particles.
    bin_tools   the other tools set, and the one DeadPacker drives for
                compiling addon content.
    bin_cs2     ONLY for the GUI lighting compiler.
    bin_server  needs full game files; launches Deadlock in server mode.

## Packing

CSDK 12 ships CS2 Workshop Manager, from the Asset Browser's top bar.

1. Press **New**. Ignore every other button.
2. Any name, any description, any preview image, any visibility.
3. Press **Submit**. **THE SUBMIT WILL FAIL. That is expected and fine** —
   a VPK is created in `game/citadel_addons` anyway.
4. "Contents" shows what got packed, if you want to check.

2 GB limit per VPK. Multichunk Workshop Manager has no limit and splits into
chunks.

## Installing it

Rename the VPK `pak##_dir.vpk`, where ## is 01 to 99, and put it in
`Deadlock/game/citadel/addons` — create that folder if it is missing. Lower
numbers take priority when two mods collide.

`gameinfo.gi` needs the addon search paths for this to load at all; an
AddonRoot section is required for community SDKs. If the game says

    Application unable to load gameinfo.gi file from directory "citadel"
    Failed to parse KeyValues

then that edit has a brace wrong.

## Launching straight into it

    -dev -convars_visible_by_default -noassert -multiple -multirun
    -allowmultiple -no_prewarm_map +exec autoexec +map <mapname>

## Worth automating, if anyone iterates on this

**DeadPacker** — github.com/Artemon121/DeadPacker. TOML-driven: compile,
pack, copy into the Steam install, close Deadlock, relaunch with dev flags.
It is the desktop-side twin of this repo's batch scripts, and someone
building this map more than twice should be using it rather than clicking
through the Workshop Manager each time.

## The three questions a first compile answers

1. Does it compile at all? The patron's placeholder model is the likeliest
   first complaint.
2. Arc or blink on a `trigger_catapult`? Decides whether two rooms in this
   map are jump pads or teleporters.
3. Which of the seven probe spellings survives? With `citadel.fgd` present
   the compiler validates entities and names what it rejects — the thing CI
   could never do. TURN SPELLING_PROBE OFF in batch16 afterwards.
