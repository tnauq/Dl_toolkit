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
  truncate on mobile.
- **Anything over one file goes as a ZIP** → repo root → run the `inbox`
  workflow. File cards download flat and lose directory structure.
- **CI is the permanent execution surface**, not a workaround.
- **Token cost is the binding constraint**, not the developer's hours.
- One tool at a time, CI-verified before the next is designed.

## Where things stand

**Built and green:**
- `Deadlock.Contracts` — JSON envelope, exit codes (net8.0)
- `Deadlock.Format` — `VpkIndex` (read), `VpkWriter` (synthetic fixtures)
- `Deadlock.Tools` — `dl-extract` (frozen, internal only)
- `Deadlock.MakeFixture` — `dl-mkfixture`
- **`Deadlock.Patch` — `dl-patch` v1. NEW, green 2026-08-09** (net9.0)
- `format-smoke.yml`, `inbox.yml`, `probe-compiler.yml`
- **`patch-smoke.yml` — NEW.** Patches a real hero vdata and asserts exactly
  one line changed
- `probe-kv3.yml` + `src/Deadlock.Probe.Kv3` — **throwaway, delete once the
  findings are absorbed**

**`dl-patch` v1 does:** `--set dotted.path=value` on source hero vdata, scalars
only, all-or-nothing, `--dry-run`, `--json` envelope. Refuses flagged values
(`resource_name:`), arrays, and lossy numeric conversions.

**Answered 2026-08-09:**
- **VRF round-trips source vdata without semantic loss** — 63,490 keys in and
  out. We do NOT need to write a KV3 serializer. Output is cosmetically
  reformatted (floats to 6dp, arrays exploded), so CI diffs against a **no-op
  baseline**, not the original.
- **VRF 12.x is net9.0 only.** The solution is otherwise net8.0. If a second
  shipping tool needs VRF, migrate everything rather than adding exceptions.
- `resourcecompiler.exe` runs headless on `windows-latest` (2026-08-09, earlier
  probe). Still needs a synthesized `gameinfo.gi` and `-game`.

**Still open, needs hardware:** whether the game loads vdata from an addon at
all, compiled or not, and whether it tolerates VRF's reformatting.

## THE NEXT THING

Three candidates, best first:

1. **Fold `Envelope.cs` into `Deadlock.Contracts`.** `dl-patch` carries a local
   copy because Contracts' type names had not been read. Small, removes a
   duplicate standard, forces the net8/net9 decision deliberately.
2. **Sweep the vdata tree for floats with >6 decimal places** — the one place
   VRF's reformatting could lose precision. Cheap; generalises the finding from
   one file to the corpus.
3. **`dl-patch batch`** — plan file, `expect` guards, atomic across files. Open
   questions are listed in `docs/TOOLING-dl-patch.md`; answer them before code.

## Settled decisions — do not relitigate

| | |
|---|---|
| **All C#**, one assembly per layer | VRF/ValvePak are .NET |
| **No version pinning** | Record the build id on artifacts instead |
| **Layering build-enforced** | CI fails on a violation |
| **Fixtures from GameTracking-Deadlock** | Public repo, no install, no credentials |
| **Structural validity is the ceiling** | Tools say "structurally valid", never "works" |
| **Parse-and-reserialize over surgical text edits** | Chosen deliberately: a full toolkit needs a real writer, and scalars-only is the cheap place to find its edges |

## Goal hierarchy

`dl-patch` (done, v1) → maps track → custom heroes (recombined abilities,
borrowed or AI art) → novel mechanics, private server, custom modes.

## Docs in the repo

`AGENTS.md` (root), then `docs/FINDINGS.md`,
`docs/FINDINGS-2026-08-09.md` (append into FINDINGS),
`docs/TOOLING-dl-patch.md`, `docs/PLAN.md`,
`docs/SESSION-2026-08-08.md`, `docs/SESSION-2026-08-09.md`.
Where they disagree, the newest session doc wins. `FINDINGS.md` marks `[V]`
sourced, `[V-CI]` proven by a run, `[I]` inferred, `[?]` assumption.

## Three process lessons worth carrying

1. **Survey before building.** A general VPK extractor was built before
   discovering Source2Viewer-CLI already does it.
2. **Cap the yak-shave.** Past two revisions, ask whether it is on the critical
   path.
3. **Probe the surface you will actually use.** Three compile failures came
   from writing against unread VRF signatures; the first surface dump filtered
   on the wrong type names and hid exactly the three types that mattered.
