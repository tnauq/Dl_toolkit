# Shipping this map — the desktop side

Everything here is READ off the community documentation
(deadlockmodding.pages.dev) and one mapper's write-up, 2026-08-29. None of it
has been done by anyone on this project, because none of it can be done from
a phone. It is written down so whoever has a desktop does not have to find it
again.

## Why CI could not do this

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

THE SHADERS ARRIVE AT STEP 3. That is the thing CI cannot have.

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
