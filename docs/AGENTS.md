# AGENTS.md

Read this before doing anything in this repo. Then read `FINDINGS.md`.

## What this repo is

Tooling for modding Deadlock on a **pinned** game build with a private
dedicated server. Target output: custom maps, custom game modes, new mechanics.

Not a skin-modding repo. Not a mod manager. If a task is about cosmetics,
it belongs somewhere else.

## The three rules

1. **Do not re-derive what is already in `FINDINGS.md`.** If a fact is
   recorded there, use it. If it is not, establish it and add it — with a
   confidence marker and how you established it.
2. **Every factual claim carries a confidence marker.** `[V]` verified against
   a real file or run, `[I]` inferred from how Source 2 works generally,
   `[?]` assumption. An unmarked claim is a bug.
3. **Never bump the pinned version.** The entire project's viability rests on
   version freeze. Schema offsets, compiler compatibility and fixture validity
   are all pinned together. Changing one is changing all of them.

## Execution surface

CI (GitHub Actions) is where things run. There is no interactive desktop and
no one watching a screen.

- `ubuntu-latest` for all parsing, diffing and generation work
- `windows-latest` for anything invoking the CSDK compilers — **unverified**,
  see probe 6
- The repo is public, so Actions minutes are free. Do not optimise for them.

**You cannot verify anything in-game.** No agent task ends with "and I checked
it works in Deadlock." Tasks end at: assertions pass, artifacts render, or a
clearly-stated request for a human to verify on hardware.

## Working against fixtures

Real game files live in `fixtures/`. They are **read-only inputs**, committed
once from a desktop session. Treat them as ground truth.

- Never regenerate, "fix", or reformat a fixture.
- Never guess at a file format. Open the fixture and look. A confident wrong
  schema costs weeks; reading a sample file costs a minute.
- If a fixture you need does not exist, say so and stop. Do not synthesise a
  plausible substitute — the whole point of fixtures is that they are real.

## Do not commit

- CSDK binaries or game depots. Not a legal concern; they drift out of sync
  and leave people on mismatched builds. Ship derived fixtures only.
- Steam credentials, or any workflow that logs into Steam.

## Tool conventions

Every CLI in this repo:

- supports `--json` and emits nothing else to stdout in that mode
- returns meaningful exit codes (`0` success, `1` expected failure such as a
  failed assertion, `2` misuse)
- produces **deterministic output ordering** — sorted keys, stable sort on
  records, no dict iteration order dependence
- supports `--dry-run` wherever it writes
- never prompts interactively
- writes errors that name the fix, not a stack trace

Diagnostics go to stderr. stdout is a machine interface.

## Out of scope for agents

- Phases 4 and 5 (Metamod plugin, Lua unlock). These are IDA and C++ reverse
  engineering against a binary. Do not attempt; do not build scaffolding for
  attempting.
- Judgements about whether a map plays well. Rendered plan views and spatial
  assertions are review aids for a human, not a verdict you can issue.

## Where things live

```
fixtures/       real game data, read-only, committed from desktop
tools/          CLIs — parsing, diffing, generation
harness/        headless verification: assertions + rendered artifacts
probes/         probe scripts, one per open question in FINDINGS.md
docs/           plan, schema, findings
```
