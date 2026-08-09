# TOOLING.md — tool specification

The design contract for everything in `src/`. Read `AGENTS.md` first.

Status: **spec plus a working Format layer.** The VPK round trip is verified in
CI. Everything else is unbuilt.

---

## 0. Scope — what we build and what we do not

Scoped down 2026-08-08 after surveying the existing ecosystem (see
`FINDINGS.md`, "Existing tools"). The rule: **if it already exists and works,
use it.**

### Use, don't rebuild

| Need | Existing tool |
|---|---|
| Browse / extract / decompile a VPK | **Source2Viewer-CLI** (`--vpk_list`, `--vpk_dir`, `-e`, `-d`) |
| KV3 → JSON for analysis | Zehmosu/kv3parser, STmihan/deadlock-data-extractor |
| Hero / item / ability JSON dumps | deadlock-data-extractor, deadlock-api |
| Installing mods | Deadlock Mod Manager, Grimoire |
| Dedicated server lifecycle | community server managers |
| Hammer, compilers, asset browser | Reduced CSDK 12 + `Deadlock_with_tools.exe` |
| Map entity reference | community `dl_example.vmap` |

### Build — nothing equivalent exists

| Tool | Why it doesn't exist elsewhere |
|---|---|
| `dl-diff` | Nothing diffs vdata **across builds**. Existing tools extract a snapshot. |
| `dl-patch` | Everything out there **reads**. Nothing writes edits back into a mod VPK. |
| `dl-verify` | No headless verification harness exists for Deadlock in any form. |
| `dl-map` | No parametric `.vmap` emitter exists. |
| `dl-render` | No headless map-review renderer exists. |

**`dl-extract` is demoted.** It stays as an internal capability of
`Deadlock.Format` feeding `dl-diff`, not a general-purpose extractor. For
anything ad hoc, use Source2Viewer-CLI. Do not grow it.

### Why build on the library rather than shell out

VRF explicitly does not guarantee CLI argument or output stability. The library
API is the stabler surface, and `dl-patch`/`dl-verify` need in-process access
anyway. This is a real reason, but a narrow one — it justifies *how* we build
the tools above, never building a tool that already exists.

---

## 1. Architecture

Four layers. **Dependencies point downward only.**

```
  Deadlock.Harness     assertions, rendering, pass-fail reporting
  Deadlock.Tools       CLIs — one command, one job
  Deadlock.Transform   pure functions over parsed data. No I/O, no VRF.
  Deadlock.Format      binary in, plain data out. Only layer that knows KV3/VPK.
```

`Format` is the layer most likely to be wrong, so it is isolated: everything
above works on plain data and is testable with no game files.

### Language: all C#

Decided on optimisation and modularity grounds, fluency treated as a
non-factor. VRF and ValvePak are .NET, so C# makes the format layer an
in-process call. The rejected alternative was a C#/Python hybrid: its
modularity benefit came from the **CLI contract**, not the language split, so
it paid a serialisation tax for nothing.

Costs accepted: rendering is SkiaSharp/ImageSharp rather than PIL. .NET is
cross-platform, so only `dl-patch`'s compiler shell-out needs Windows.

### Layering is build-enforced

A single solution makes reaching across layers easy at 1am. So:

- One assembly per layer, project references encoding direction
- `Transform` must not reference VRF or ValvePak
- CI fails the build on a violation — not a review comment, a red X

### Registry pattern, not a switch statement

Asset types register handlers rather than appearing in central dispatch.
Adding a resource type is one file, no edits elsewhere.

---

## 2. Composability

Every tool reads JSON on stdin or a path, writes JSON to stdout. Tools compose
through pipes and never call each other in-process.

- **No tool imports another tool.** Shared behaviour moves down into `Transform`.
- **stdout is the machine interface.** Diagnostics go to stderr, always.
- A tool that cannot be usefully piped is probably doing two jobs.

---

## 3. CLI surface

| Command | Job | State |
|---|---|---|
| `dl-diff` | two builds → structural changeset | next |
| `dl-patch` | apply a changeset, repack a mod VPK | after diff |
| `dl-verify` | run assertions, emit pass/fail | harness |
| `dl-render` | map or layout → PNG artifact | harness |
| `dl-map` | layout description → `.vmap` | Phase 3b |
| `dl-extract` | VPK index → JSON | internal, frozen |
| `dl-mkfixture` | synthetic VPK for testing | done |

Universal flags: `--json`, `--dry-run`, `--quiet`, `--fixture-root`.

Exit codes: `0` ok · `1` expected failure · `2` misuse · `3` missing fixture or
dependency. `3` is distinct so an agent can tell "your input was wrong" from
"this machine isn't set up."

---

## 4. JSON envelope

```json
{
  "tool": "dl-extract",
  "version": "0.1.0",
  "pinned_build": "<build id>",
  "ok": true,
  "data": {},
  "warnings": [],
  "errors": []
}
```

- `pinned_build` on **every** output. Mixing artifacts across builds is the
  failure mode version-freezing exists to prevent.
- `errors[]` carry `code`, `message`, `fix` — a concrete next action.
- **Deterministic ordering is mandatory:** sorted keys, stable record sort.
  Verified in CI by running twice and diffing.

---

## 5. Assertion vocabulary

`dl-verify` consumes a declarative assertion file. Four families:

| Family | Example | Needs |
|---|---|---|
| `data` | a stat reads the expected value after a patch | fixtures only |
| `runtime` | an event fires; an ability applies expected damage | live server |
| `spatial` | bot paths a route; traversal time; lane symmetry | live server |
| `visual` | rendered plan view, sightline overlay, before/after diff | renderer only |

`data` and `visual` run with fixtures alone — **build those first**, they are
what makes the toolkit useful before any hardware exists.

Every run emits a JSON report plus rendered PNGs as CI artifacts, so a failure
is reviewable on a phone.

---

## 6. Performance

Optimisation without measurement is guesswork. Split into decisions that are
architectural and tuning that waits for numbers.

### Architectural — decide now

- **Diff from the index, not the bodies.** `CRC32` and `TotalLength` are in the
  VPK directory. **VERIFIED in CI** — `CRC32` is the checksum of file contents,
  so change detection never decodes. This is the every-push hot path.
- **Content-addressed cache.** Key every parse by SHA-256 of input bytes plus
  parser version. Extraction is pure, so the cache cannot invalidate wrongly.
- **Stream, don't slurp.** ValvePak loads the directory and fetches bodies per
  entry; keep it that way.
- **Parse lazily.** Index eagerly, bodies on demand.
- **Parallelism at the file boundary only.** Merge in sorted order — parallelism
  must never be observable in output.
- **In-process composition** for multi-step operations: pass typed objects,
  serialise once at the end. The piped form must produce byte-identical output.
- ~~Spans, not copies.~~ **Withdrawn** — ValvePak returns `byte[]` per entry.
  Read fewer entries instead.
- **`OptimizeEntriesForBinarySearch()` before `Read()`** when the workload is
  lookup-heavy. `FindEntry` is otherwise a linear scan.

### Tuning — wait for measurement

A benchmark job records wall-clock and peak RSS per tool against a fixed
fixture and fails on regression. Optimise what the numbers show.

**Not optimising yet:** the KV3 parser, until a fixture shows it is hot;
anything shelling out to CSDK compilers, which we do not control.

---

## 7. Open questions

- Does Source 2 Hammer read an FGD for Deadlock, or source entity definitions
  from game files? **Decides whether an FGD tool is worth anything at all.**
  Cheap to answer once `dl_example.vmap` and the CSDK are in hand.
- Whether ValvePak's writer is byte-deterministic. CI warns rather than fails;
  if it is not, content-addressed caching keys on the manifest, not the archive.
- Assertion format: YAML or JSON. Leaning JSON — one format is easier for
  agents than two.
