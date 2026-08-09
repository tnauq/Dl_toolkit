# HANDOFF — Deadlock toolkit, resume here

Paste this into a fresh conversation to pick up exactly where we stopped.

---

## What this is

A **personal** Deadlock modding toolkit for one developer, built so an AI agent
does 100% of the coding. Priorities, in order: **low friction, agent-friendly,
optimised and modular.**

Not a community product. Not a mod manager. Not an onboarding experience.
All three were explored and rejected — see `docs/SESSION-2026-08-08.md`
section 3, "Discarded", before proposing anything.

Repo: `github.com/tnauq/Dl_toolkit` (public).

## Working constraints — read first

- **Mobile-only (iOS) for months.** A Windows machine is coming, owned, no date.
- **ALWAYS give full file contents, never partial snippets.** Partial pastes
  truncate on mobile — this caused five CI failures in one session.
- **Multi-file delivery goes via zip** → repo root → run the `inbox` workflow.
  File cards download flat and lose directory structure.
- **CI is the permanent execution surface**, not a workaround. It is the only
  place the agent verifies its own work without the human couriering files.
- **Token cost is the binding constraint**, not the developer's hours.
- One tool at a time, CI-verified before the next is designed.

## Where things stand

**Built and green:**
- `Deadlock.Contracts` — JSON envelope, exit codes
- `Deadlock.Format` — `VpkIndex` (read), `VpkWriter` (synthetic fixtures)
- `Deadlock.Tools` — `dl-extract` (frozen, internal only)
- `Deadlock.MakeFixture` — `dl-mkfixture`
- `format-smoke.yml` — builds, layer boundaries, exit codes, determinism, and
  a VPK round trip proving `PackageEntry.CRC32` is the content checksum
- `inbox.yml` — unpacks zips dropped at repo root, uses `secrets.PAT`
- `probe-compiler.yml` — answered its question, see below

**Answered 2026-08-09:** `resourcecompiler.exe` **runs headless on
`windows-latest`**. Bare extracted CSDK, full usage printed, clean exit, no
tools or game install. The mobile compile path is viable. One gap remains: it
needs `-game <path>` pointing at a `game/citadel/gameinfo.gi`, which is small
text and synthesizable in CI.

**Still open, needs hardware:** whether the game loads *uncompiled* text vdata
from an addon. A real GameBanana mod was inspected and ships `.vdata_c`, but
that shows what modders do, not what the game accepts.

## THE NEXT THING TO BUILD

**`dl-patch` v1.** Hero vdata only. `--set dotted.path=value`. Reads real files
cloned from **SteamDB GameTracking-Deadlock** in CI. Emits **source vdata**,
not compiled. States the supported subset in the error when pointed elsewhere.

No CSDK, no Windows runner, no further probes needed. It is the first tool in
the project with no equivalent anywhere in the ecosystem — everything out there
reads; nothing writes back.

## Settled decisions — do not relitigate

| | |
|---|---|
| **All C#**, four assemblies | VRF/ValvePak are .NET; the CLI contract gives modularity, not a language split |
| **No version pinning** | Record the build id on artifacts instead |
| **Layering build-enforced** | CI fails on a violation, not a review comment |
| **Fixtures from GameTracking-Deadlock** | Public repo, no install, no Steam credentials — this is what unblocked mobile work |
| **Structural validity is the ceiling** | Tools say "structurally valid", never "works", until hardware exists |

## Goal hierarchy

First `dl-patch` → maps track → custom heroes (recombined abilities, borrowed
or AI art) → novel mechanics, private server, custom modes (needs binary work,
long-term).

## Docs in the repo

`AGENTS.md` (root), then `docs/FINDINGS.md`, `docs/TOOLING.md`,
`docs/PLAN.md`, `docs/SESSION-2026-08-08.md`. Where they disagree, the session
doc is newest. `FINDINGS.md` marks `[V]` sourced, `[V-CI]` proven by a run,
`[I]` inferred, `[?]` assumption — and has a corrections section so wrong
beliefs are not re-derived.

## Two process lessons worth carrying

1. **Survey before building.** A general VPK extractor was built before
   discovering Source2Viewer-CLI already does it. Check the ecosystem first.
2. **Cap the yak-shave.** One session spent seven workflow revisions on a probe
   that blocked nothing. Past two revisions, ask whether it is on the critical
   path.
