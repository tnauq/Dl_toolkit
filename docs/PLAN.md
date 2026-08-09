# Deadlock modding — project plan

Target: custom maps, custom game modes, and new mechanics on a pinned Deadlock
build with a private dedicated server.

Assumes hobby pace — roughly 8–10 hrs/week. Halve the calendar if you're at
20 hrs/week; the Hard phases don't compress proportionally because they're
gated on debugging, not typing.

## Difficulty scale

| Level | Means |
|---|---|
| **Easy** | Following known steps. Failure modes are documented somewhere. |
| **Moderate** | Normal software work. You'll write real code but the approach is clear. |
| **Hard** | Reverse engineering, undocumented internals, IDA. Timeline is a guess. |
| **Unknown** | Can't estimate until a probe lands. Treat estimates as fiction. |

## Confidence key

Marked on each phase, because several of these rest on inference rather than
anything I verified:

- **[V]** Verified — sourced, or a direct consequence of something sourced.
- **[I]** Inferred — reasonable from how Source 2 works generally, untested on Deadlock.
- **[?]** Assumption — could be wrong in a way that kills the phase.

---

## Cross-cutting — agent-friendly by design

**[I]** Not a phase. A constraint that runs through Phases 2, 3 and 6, so that
other users can hand a task to an agent and get a finished result rather than
a draft needing a human to check it.

Most of this is what makes tooling good anyway. Three things are genuinely
additive:

### 1. Machine-first interfaces (+1 week, folded into Phase 2)

Every CLI gets `--json`, meaningful exit codes, deterministic output ordering,
`--dry-run`, and no interactive prompts. Errors name the fix rather than
dumping a stack trace. An agent's only sensory channel is stdout — treat it
as the primary interface, not the debug one.

### 2. Headless verification harness (2–3 weeks, Moderate)

**The load-bearing piece.** One command that boots the pinned server, loads a
mod, runs scripted assertions, and returns pass/fail as JSON. Without it every
agent task ends in "I made the change, please check it." With it, agents
iterate unsupervised.

Slot it after Phase 2. Note you want this regardless of agents, so the
marginal cost is lower than it looks.

Assertions worth supporting from day one:

- Data: a stat reads the expected value after a vdata patch
- Runtime: an event fires, an ability applies the expected damage
- **Spatial:** a bot can path a route; traversal time between two points;
  sightline length distribution; symmetry check between lanes
- **Visual:** rendered PNG artifacts — plan views, sightline overlays,
  before/after diffs — reviewable on a phone alongside the pass/fail

That last group is what makes Phase 3 tractable for agents — see below.

### 3. Context artifacts (few days, Easy)

The machine-readable versions of the docs you'd write anyway: a schema doc for
the data model, a settled-findings file so agents don't re-derive things that
are already known, and an `AGENTS.md` at the repo root. Highest leverage per
hour in the whole plan, because it's what stops an agent confidently doing
the wrong thing.

### Where this genuinely doesn't help

- **Phases 4 and 5 are IDA work.** Don't scope them as agent-friendly; you'd
  build ceremony around a task agents can't do.
- **Final art pass and playtesting.** Rendered artifacts cover static layout
  review, but a map can satisfy every measurable constraint and still play
  like nothing. Metrics proxy fun badly.

---

## Working mode — mobile + GitHub Actions

**[I]** Added because the near-term constraint is an iOS client with no
desktop. This reorders the plan rather than shrinking it.

CI is the execution surface, same pattern as the API pipeline: push, let the
runner work, read the artifact. That is enough to make most of the asset track
viable without a desktop.

### Runs in CI today

- **Phase 2 in full.** VRF is .NET and cross-platform, so KV3 parsing, vdata
  diffing and FGD harvesting are ordinary headless jobs on `ubuntu-latest`.
- **Context artifacts and tool specs.** Pure writing — start here regardless,
  the plan already rates it highest leverage per hour.
- **Probe scripts,** written and committed now, fired the moment a desktop or
  a suitable runner exists.

### Probe first — could move a lot

**Do the CSDK compilers run on `windows-latest`?** They are CLI tools, so a
headless map compile in CI is plausible but unverified. If it works, Phase 3's
compile loop becomes phone-drivable and 3b's parametric emitter gets a real
feedback loop. If it doesn't, Phase 3 waits for hardware. Cheap to answer,
large consequence — treat it as probe 6.

Second, longer shot: the dedicated server is headless and needs no GPU, so
some of the verification harness may run in CI against bots. Unverified, and
the 6-hour job ceiling caps what it could ever cover.

### Fixtures are the bottleneck

Runners need game files. The clean route is committing a fixture set **once**
from a desktop — representative vdata, a decompiled official map, a `cvarlist`
dump — after which the transformation work is pure data and fully mobile.

- **Public repo is fine.** Valve is permissive about modding and this is not a
  takedown risk. Public also means **unlimited free Actions minutes**, which
  removes any reason to ration compile jobs.
- Don't commit the CSDK binaries or full depots. Not a legal worry — a
  staleness one. Those are exactly the artifacts that drift out of sync and
  leave contributors on mismatched builds. Ship derived fixtures; let people
  bring their own game files.
- Avoid SteamCMD with stored credentials in CI. Steam Guard makes it awkward
  and secrets-plus-depot-downloads is not a risk worth taking for convenience.

### Visual review is not blocked

Rendered PNG artifacts are a working review channel on mobile — the tier-list
images already prove the pattern. Worth building into the harness from the
start:

- Orthographic plan view of a generated layout
- Sightline-length overlay and cover-density heatmap
- Lane symmetry diff, half against mirrored half
- Before/after renders on a geometry change

This strengthens 3b more than the assertions do on their own: an agent emits a
layout, and you review a picture rather than trusting a pass/fail.

### Still blocked

IDA work (Phases 4–5), and real-time feel — movement, pacing, whether a fight
in that space is any good. Static visual review covers more than assumed;
playtesting is the genuine remainder.

### Suggested near-term order

1. Context artifacts + `AGENTS.md`
2. Tool specs: CLI surface, JSON shapes, assertion vocabulary
3. Probe 6 (Windows runner compile)
4. One desktop session for fixtures — the single highest-value hour available
5. Phase 2 in CI

---

## Phase 0 — Freeze the stack

**1 week · Easy · [V]**

Nothing else is worth doing until the ground stops moving.

1. Pick the pinned client build. Match it to a CSDK release rather than
   choosing newest-of-each — CSDK 12 is dated Jan 2026, CSDK 10 Jan 2025.
   Map compile compatibility is the thing that breaks silently.
2. Archive everything to cold storage: client depot, dedicated server files,
   CSDK, and a hash manifest. You will rebuild your dev box at least once.
3. Stand up the dedicated server from the archived copy on a clean machine.
   Not the one you've been fiddling with.

**Gate:** clean-install server boots and accepts a client twice in a row.
**If it fails:** you don't have a reproducible base and every later phase
inherits the flakiness. Fix here, not later.

---

## Phase 1 — Recon probes

**1–2 weeks · Easy to Moderate · [I]**

This is the invalidation phase. Every probe below can kill or reshape a later
phase, and they're all cheap. Run them before writing anything substantial.
Same discipline as PROBES.md — record the result, don't re-run.

| # | Probe | Kills what if it fails |
|---|---|---|
| 1 | What does the server do without Valve's GC? Does a match start, do heroes populate, does the shop load? | Determines whether "game mode" is a server config or a rebuild-from-scratch |
| 2 | `cvarlist` dump on the pinned build, diffed against a recent build | Tells you how much dev affordance survives; feeds Phase 6 |
| 3 | Entity dump during a live match + decompile an official map | The gamerules entity surface — the whole of Phase 3's ceiling |
| 4 | Does Metamod:Source (Source 2 branch) load into Deadlock's server binary at all? | **Phases 4, 5, 6** |
| 5 | Does the Lua VM ship in the binary? String-search for `luaL_`, `lua_pcall`, `CScriptVM` | **Phase 5** |
| 6 | Do the CSDK compilers run headless on a `windows-latest` runner? | Decides whether Phase 3 is phone-drivable or waits for hardware |

Probe 4 is the single highest-leverage unknown in the whole plan. There is a
Source2 Schema Dumper that lists Deadlock alongside Dota 2 and CS2 and
references Metamod, which is decent evidence the loader path works — but that
is evidence, not confirmation, and I haven't seen it confirmed for Deadlock's
server binary specifically. **Run probe 4 first.**

Probe 5 has a real precedent: LuaUnlocker is a Metamod plugin that enables Lua
VScript on CS2, and a Deadlock forum poster reported enabling Lua vscript via a
server.dll addon and building custom HUD readouts with it. So the VM is
probably present and disabled rather than absent.

**Gate:** probes 4 and 5 both answered.
**If probe 4 fails:** drop to the Fallback Track at the bottom. It's a smaller
project but far from a dead one.

---

## Phase 2 — Asset toolchain

**1–3 weeks · Easy to Moderate · [V]** *(reduced 2026-08-08)*

Independent of everything above. **Scope cut after surveying what exists** —
see `FINDINGS.md`, "Existing tools". Extraction and KV3 reading are solved
several times over; use Source2Viewer-CLI and stop.

Remaining deliverables, in order of value:

1. **Patch differ (`dl-diff`).** Two builds in, structural changeset out.
   Nothing does this. Cheap now that CI has confirmed VPK `CRC32` is a content
   checksum, so change detection reads the index only.
2. **Patch and repack (`dl-patch`).** Apply a changeset to vdata and write a
   mod VPK. Every existing tool reads; **none writes back**. This is the loop
   you'll run hundreds of times.
3. ~~Reconstructed Deadlock FGD.~~ **Demoted to a probe.** Source 2 Hammer may
   read entity definitions from game files rather than an FGD, and
   `dl_example.vmap` already documents the entity surface. Confirm before
   spending a week on it.

**Gate:** change a hero stat in vdata, repack, load it on the pinned server,
observe the change in game.

**Note:** writing *compiled* Source 2 resources is where VRF is weak — it reads
far better than it writes. Route anything non-trivial through the CSDK
compilers from source assets rather than trying to round-trip binaries.

---

## Phase 3 — Map pipeline

**6–10 weeks · Moderate · [V]**

Gated only on Phase 0. The most predictable phase in the plan — this is the one
part of Deadlock modding with a real community track record.

1. Install the latest CSDK package, launch `Deadlock_with_tools.exe`, open
   Hammer from it. Compile against `deadlock.exe` in
   `Reduced_CSDK_12\game\bin_cs2\win64`, package via the CS2 workshop manager.
2. Respect the bounding box Deadlock enforces on maps.
3. **Start from the community `dl_example.vmap`**, which contains all the
   important map and gamemode entities. Do not rediscover the entity surface.
4. Greybox target: a single-lane map that actually spawns troopers,
   objectives, and both team spawns. Art later, never first.
4. Then push on entity I/O. `logic_*` chains are a genuine scripting language
   and they work with zero binary access — this is where Fallback-Track game
   modes live.

### 3b — Parametric geometry layer (+3–4 weeks, Moderate)

The unlock for agent-authored maps, and worth building regardless.

`.vmap` is KV3, so geometry is data that can be emitted programmatically. Build
a DSL or Python layer that takes a layout description — lane paths, widths,
cover placement, verticality, zipline routes — and emits a compilable `.vmap`.
Agents author the description, not the Hammer output.

This is more tractable in Deadlock than in most games because the map is
heavily rule-governed:

- Hard bounding box, so the solution space is closed
- Three lanes with strong symmetry — generate half, mirror it
- Dimensions pinned to movement mechanics (jump height, dash distance,
  zipline clearance), which are numeric constraints, therefore checkable
- Blockout doesn't need art, and art is the part that needs a human

Pair it with the spatial assertions in the harness — bot pathing, traversal
symmetry, sightline distribution — and an agent gets a real feedback loop
instead of guessing. Constraint satisfaction, verified headlessly.

**Correction to an earlier draft of this plan:** I previously wrote that map
geometry isn't agent-authorable. That conflated blockout with the art pass.
Blockout is generatable and verifiable; the art pass and the taste calls are
what still need eyes.

**Gate:** custom greybox map, loaded on your server, playable end to end with
working objectives. Then: same map produced from a parametric description,
passing spatial assertions.

**Watch for:** compiled lighting has historically been the reported pain point
on Deadlock maps built with CS2 tools. Budget a week for it and don't be
surprised if the answer is "fullbright greybox is fine for now."

---

## Phase 4 — Server plugin base

**4–8 weeks · Hard · [?]**

Gated on probe 4. The riskiest phase, and the one where the estimate is
weakest — if the loader needs work, this is 4 weeks; if it needs porting, it's
much more.

1. Get Metamod:Source (Source 2 branch) loading into the pinned server.
2. Run the schema dumper against your pinned build. **Once.** Pinning means the
   output is permanently valid — this is the single biggest payoff of freezing
   the version, and it's why this plan is viable at all.
3. Hook one function and log one event. That's the milestone. Something
   trivial — player spawn, damage applied.
4. Only then build an abstraction layer over the hooks.

**Gate:** plugin loads on server start, hooks a gameplay event, logs it.

**Skills needed:** C++, and enough IDA to resolve a signature when the dumper
misses one. If you don't have the second, budget an extra month or find
someone in the Hit Deadlock Modding Discord who does.

---

## Phase 5 — Lua unlock

**2–6 weeks · Hard · [I]**

Gated on Phases 4 and probe 5. Port the LuaUnlocker approach to your pinned
Deadlock build: flip the VM on, expose bindings, get a script executing
server-side.

Wide range because it's either "the same patch works" or "the offsets differ
and you're back in IDA." Pinning helps enormously — you solve it once.

**Gate:** a Lua script running server-side that reads and modifies game state.

**Why it matters:** this is the boundary between *tweaking data* and *writing
game rules*. Everything genuinely novel sits behind it.

---

## Phase 6 — Mechanics and game modes

**Open-ended · Hard · [I]**

Now it's ordinary game development, which is to say it never ends.

Suggested first target: something with clearly defined win conditions and no
new art. A round-based single-lane variant is a good shape — Valve's own
Street Brawl proves the engine expresses single-lane, round-based, item-draft
rules, so you're following a path the game already supports rather than
fighting it.

Sequence: win condition → spawn rules → economy → new abilities. Abilities last,
because they're the part that needs both Lua and asset work.

---

## Fallback track — if probe 4 fails

**6–10 weeks total · Moderate · [V]**

No binary access. Still a real project:

- Phase 2 asset toolchain (unaffected)
- Phase 3 maps (unaffected)
- Game rules expressed through map entity logic and vdata edits only
- Server-side authority means these actually hold, unlike the client-only
  situation for people without private servers

You lose: new abilities, custom UI, anything needing per-frame logic or novel
state. You keep: custom maps, modified economy, altered hero stats, and
rule variants expressible as entity graphs. That is most of a custom game mode.

---

## Timeline summary

| Track | To first playable result |
|---|---|
| Maps only (0→2→3), agent-ready | **10–16 weeks** |
| Fallback track (no binary access) | **12–18 weeks**, lower ceiling |
| Full stack (0→1→2→3→4→5→6) | **5–9 months** to a custom mode with novel mechanics |

Agent-friendliness adds ~3–4 weeks (CLI hardening, harness, context docs) and
the parametric geometry layer another 3–4. Both are on the asset/map track;
the plugin track is unchanged. Scope reduction 2026-08-08 took ~2 weeks off
Phase 2 by deleting work the ecosystem already does.

**The differentiated core is: `dl-diff`, `dl-patch`, the verification harness,
and parametric geometry.** Nothing comparable exists for any of the four.

Phases 2 and 3 are parallel with 4 and 5. If you're working alone, run the
asset/map track as the default and drop into the plugin track when you have
appetite for a hard debugging session — that keeps something shipping while
the risky part stalls.

---

## Things I'd flag as genuinely uncertain

- **Metamod on Deadlock's server binary.** Inferred from the schema dumper's
  Deadlock support. Not confirmed. Probe 4 exists because of this.
- **What the GC does when absent.** I don't know how much of match setup,
  hero availability, and shop config lives server-side vs in Valve's
  coordinator. This could reshape Phase 6 substantially.
- **Which pinned build is best.** Older builds plausibly retain more dev
  affordances, but I don't know Deadlock's version history well enough to name
  one. Probe 2 answers it empirically.
- **Phase 4 and 5 estimates.** These are the weakest numbers here. Hard phases
  in RE work routinely run 3x over.
- **How far parametric geometry actually gets.** Emitting valid `.vmap` is
  clearly doable; whether generated layouts *play well* under constraint
  satisfaction alone is untested. The 3–4 week estimate covers the emitter and
  the assertions, not the tuning loop that makes output good.

Anything in this plan downstream of an unrun probe should be read as
provisional.
