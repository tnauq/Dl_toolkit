# FINDINGS.md — settled findings, do not re-derive

Companion to `AGENTS.md`. Read both before starting work.

Every entry carries a confidence marker. **An unmarked claim is a bug.**

| Marker | Means |
|---|---|
| `[V]` | Verified — sourced from community documentation, or a direct consequence of something sourced |
| `[I]` | Inferred from how Source 2 works generally; untested on Deadlock |
| `[?]` | Assumption. Could be wrong in a way that breaks whatever rests on it |

**Most of this file has not been verified against a real Deadlock install or a
live server.** Where `[V]` means only *someone credible wrote it down*, it says
so. Entries proven by a CI run are marked **`[V-CI]`** and name the run.

## Rule zero

A cheap probe is the first thing you run against any unknown, before writing
anything substantial on top of it. This discipline is carried over from the
sibling API-pipeline project, where three versions were built on unverified
assumptions and all three silently produced nothing.

If a finding is here, do not re-establish it. If it is not here, establish it
and add it.

---

## Toolchain — `[V]`

- There is **no official Deadlock SDK**. The community route is a **Reduced
  CSDK**: a stripped CS2 SDK repackaged to target Deadlock.
- Releases: **CSDK 12 (Jan 2026)**, **CSDK 10 (Jan 2025)**. Distributed via
  the Hit Deadlock Modding Discord, not publicly.
- **Pin the client build to the CSDK release**, not newest-of-each. Map
  compile compatibility breaks silently on mismatch.
- Map compile path: Hammer → compile against `deadlock.exe` in
  `Reduced_CSDK_12\game\bin_cs2\win64` → package via the CS2 workshop manager
  to produce a `.vpk`.
- **Deadlock enforces a bounding box on maps.** Exact dimensions: `[?]` —
  not recorded anywhere we have read. Needs measuring off a decompiled
  official map.
- **ValveResourceFormat (VRF)** is .NET, open source, and the library under
  Source 2 Viewer. It provides VPK read and KV3 parsing as a dependency.
- **VRF reads far better than it writes.** Route anything non-trivial through
  the CSDK compilers from source assets rather than round-tripping compiled
  binaries.
- **Compiled lighting is a reported pain point** on Deadlock maps built with
  CS2 tools. Fullbright greybox is an acceptable early target.

## VPK access — `[V]`, from ValvePak documentation

- VPK reading is **ValvePak** (`SteamDatabase.ValvePak`), a separate library
  that VRF depends on. Archive work needs only ValvePak; VRF is required only
  to decode a resource once extracted.
- `Package.Read()` accepts a path **or a Stream**. It loads the directory;
  entry bodies are read individually via `ReadEntry`.
- Entries are enumerable by type from the index without touching bodies.
- **The index carries `CRC32` and `TotalLength` per entry.** Change detection
  across two builds is therefore an index-only operation — no body reads, no
  decode.
- **VPKs are uncompressed.** No decompression cost on read.
- `ReadEntry` returns a `byte[]`; the documented path wraps it in a
  `MemoryStream`. **There is no zero-copy / span surface.** Allocation per
  entry is the floor.
- Only `pak01_dir.vpk` is openable — numbered files such as `pak01_001.vpk`
  are data files, not archives.
- **`FindEntry` is a linear scan** unless `OptimizeEntriesForBinarySearch()` is
  called before `Read()`. Relevant to any lookup-heavy workload.

### Confirmed by CI — `[V-CI]`, format-smoke 2026-08-08

- **ValvePak 4.0.0.142 builds and runs on net8.0 / ubuntu-latest.** It requires
  `System.IO.Hashing >= 9.0.11`; pinning lower fails restore with NU1605.
- **`PackageEntry.CRC32` IS the CRC32 of file contents.** Five files written by
  `dl-mkfixture` with checksums computed independently via `System.IO.Hashing`
  matched ValvePak's reported values exactly on read-back. **This is what
  licenses index-only diffing** — it was an assumption, now it is a fact.
- `TotalLength`, `GetFullPath()` and `ArchiveIndex` behave as assumed.
- `ArchiveIndex` reads **32767** (0x7FFF) for entries stored in the dir file.
- **ValvePak can WRITE archives** — `AddFile()` then `Write()`. This is what
  makes fixture-free testing possible; no committed VPK is needed.
- `dl-extract` output is byte-identical across repeated runs.

## Scripting — `[V]` unless marked

- Source 2 ships a **Lua VScript VM that is present but disabled** in shipping
  titles.
- **LuaUnlocker** is a Metamod:Source plugin that re-enables Lua VScript on
  CS2. Precedent, not a Deadlock port.
- A Deadlock forum poster reported enabling Lua VScript via a `server.dll`
  addon and building custom HUD readouts with it. **Single unreplicated
  report** — treat as `[I]` until probe 5 lands.
- A **Source2 Schema Dumper** exists that lists Deadlock alongside Dota 2 and
  CS2 and references Metamod. This is evidence the loader path works on
  Deadlock; it is **not confirmation** for the server binary specifically.
- **Pulse** is Source 2's node-graph scripting layer and Deadlock uses it
  heavily for abilities. Reading Pulse graphs via VRF is tractable `[I]`.
  Authoring them without Valve's editor is a much larger lift `[I]`.

## Data model — `[I]`

Everything in this section needs confirming against a fixture before code
depends on it.

- `.vmap` is KV3, therefore map geometry is data that can be emitted
  programmatically.
- Hero, item and ability definitions live in `vdata` (KV3), making stat and
  economy changes pure data edits.
- Deadlock's map is strongly rule-governed — bounded box, three lanes, heavy
  symmetry, dimensions pinned to movement mechanics. This makes blockout
  generation a constraint-satisfaction problem rather than an art problem.

## Version freeze — `[V]`

Pinning is what makes the project viable. A schema dump against a pinned build
stays valid permanently, which removes the per-patch re-dump cost that
otherwise dominates binary-level work.

Consequences accepted: no upstream fixes, no new heroes, steady divergence
from live Deadlock. Balance data from the live API pipeline **does not
transfer** to a pinned mod branch.

---

## Existing tools — surveyed 2026-08-08, scope reduced because of it

The canonical community tool list is **four items**: CSDK 12, CSDK 10,
Source 2 Viewer, Asset Browser. Beyond it:

| Exists | What it does |
|---|---|
| **Source2Viewer-CLI** | `--vpk_list`, `--vpk_dir`, filtered extract, `-d` decompile. **Covers general VPK extraction entirely.** |
| **Zehmosu/kv3parser** | Python KV3 → JSON, written for Deadlock analysis |
| **STmihan/deadlock-data-extractor** | automated heroes/items/abilities JSON + vdata + images |
| **Deadlock Mod Manager**, Grimoire | mod install/ordering |
| community server managers | dedicated server lifecycle |
| **`Deadlock_with_tools.exe`** | the game ships launchable Source 2 tools; Hammer opens from it |
| **`dl_example.vmap`** | community dev map containing all important map/gamemode entities |

**Consequences, all acted on:**

- `dl-extract` is **demoted to internal** — Source2Viewer-CLI already does it.
- Reading vdata is a solved problem. **Writing it back is not.**
- `dl_example.vmap` is a **partial answer to probe 3** and a better fixture than
  anything Valve-shipped. Get it early.
- The mod-manager and server-manager space is crowded. Stay out.

**VRF does not guarantee CLI stability** — argument names and output formats may
change between releases. That justifies building on the library for tools we
need anyway. It does **not** justify rebuilding a tool that exists.

**Still nothing exists for:** cross-build vdata diffing, patch-and-repack,
headless verification, parametric map generation, or any agent-oriented
interface. That is the whole of our remaining scope.

---

## Open probes — nothing downstream of these is settled

| # | Question | Blocks | Status |
|---|---|---|---|
| 1 | What does the server do without Valve's GC? Does a match start, heroes populate, shop load? | Shape of Phase 6 | open |
| 2 | `cvarlist` dump on the pinned build, diffed against a recent build | Which build to pin | open |
| 3 | Entity dump during a live match + decompile an official map | Phase 3 ceiling | **partly answered** — `dl_example.vmap` covers the entity surface |
| 4 | Does Metamod:Source (Source 2 branch) load into Deadlock's **server** binary? | Phases 4, 5, 6 | open |
| 5 | Does the Lua VM ship in the pinned binary? String-search `luaL_`, `lua_pcall`, `CScriptVM` | Phase 5 | open |
| 6 | Do the CSDK compilers run headless on a `windows-latest` runner? | Whether Phase 3 is phone-drivable | open |

**Probe 4 is the highest-leverage unknown in the project.** Run it first. If
it fails, the plan drops to the fallback track: maps plus vdata plus map
entity logic, with no binary access.

**Probe 6 is the cheapest and most immediately actionable**, because it needs
no desktop — only a workflow file and a fixture set.

---

## Known unknowns, not yet probes

- Exact Deadlock map bounding box dimensions. Measurable off `dl_example.vmap`.
- **Whether Source 2 Hammer needs an FGD for Deadlock at all**, or reads entity
  definitions from game files. Decides whether an FGD tool has any value.
- Whether the dedicated server can boot inside a CI runner against bots
  (headless, no GPU required — but the 6-hour job ceiling caps what it could
  ever cover).
- Which pinned build retains the most dev affordance. Probe 2 answers it.
- Whether constraint-satisfying generated layouts actually *play* well. Not
  answerable headlessly; needs playtesting.

---

## Corrections

Entries that turned out wrong go here rather than being deleted — knowing a
thing *used to* be believed is what stops it being re-derived.

**1. "Spans, not copies" — WITHDRAWN 2026-08-08.**
`TOOLING.md` originally specced parsing resource bodies out of a mapped buffer
with no per-entry allocation, given as a reason the format layer should be
native. ValvePak's public API returns a `byte[]` from `ReadEntry` and the
documented path wraps it in a `MemoryStream`. No zero-copy surface exists.
The optimisation was specced against a library API that had not been read.

Replacement: **read fewer entries** rather than reading them more cleverly —
diff from the index `CRC32` and pull bodies only for entries that moved.

Wider lesson, worth generalising: this spec contains other performance claims
written before the relevant library was read. Treat every one as `[?]` until
its API has actually been checked.
