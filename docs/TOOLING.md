# TOOLING.md — tool specification

The design contract for everything in `tools/` and `harness/`. Written before
the code, deliberately. Read `AGENTS.md` first.

Status: **spec, not implementation.** Nothing here has been built or measured.
Anything describing performance is a target, not a result.

---

## 1. Architecture

Four layers. **Dependencies point downward only.** A layer never imports from
a layer above it, and never from a sibling.

```
  Deadlock.Harness     assertions, rendering, pass-fail reporting
  Deadlock.Tools       CLIs — one command, one job
  Deadlock.Transform   pure functions over parsed data. No I/O, no VRF.
  Deadlock.Format      binary in, plain data out. The only layer that knows KV3/VPK.
```

**Why the split matters.** `format/` is the layer most likely to be wrong,
because it rests on inference about file layouts we have not yet confirmed
against a fixture. Isolating it means a wrong guess costs one module, not the
toolkit. Everything above it should work on plain dicts and be testable with
hand-written data and no game files at all.

### Language: all C#

**Decided on optimisation and modularity grounds, with language fluency
treated as a non-factor.**

VRF is .NET, so C# makes the format layer an in-process library call. The
alternative considered and rejected was a hybrid — a C# format layer emitting
JSON to a Python toolkit above it.

Why the hybrid lost:

- **Its modularity benefit was illusory.** The composability in section 2 —
  pipeable tools, JSON envelope, independently replaceable components — comes
  from the *CLI contract*, not from the two halves being different languages.
  C# tools honour that contract identically. The hybrid paid a cost for
  something it was not actually providing.
- **The serialisation tax is on the hot path.** Every byte crossing the
  boundary is serialised and re-parsed, and the Python side is the slower one
  for precisely the bulk work — whole-VPK extraction, diffs across thousands
  of resources. Batching mitigates it; it does not remove it.
- **A language boundary is a rigid seam.** It forces the split at exactly one
  point and makes relocating it expensive. Assembly boundaries put seams where
  the design wants them.

What all-C# buys:

- In-process VRF: no spawn, no serialisation, no re-parse
- Spans over resource buffers — parse without copying
- Real threading for per-file parallelism, no GIL
- One toolchain, one dependency set, one build, one class of failure
- Static typing on `format/`, the layer most likely to be wrong

Costs accepted: rendering moves to SkiaSharp/ImageSharp rather than
PIL/matplotlib. Competent, less ergonomic. .NET is cross-platform, so nothing
is forced onto Windows runners — only `dl-pack` needs those, because the CSDK
compilers do.

### The risk this introduces, and the mitigation

A process boundary enforces modularity whether or not anyone is disciplined.
A single solution does not — it makes reaching across layers easy at exactly
the moment discipline is lowest.

So the layering in this section is **build-enforced, not conventional**:

- One assembly per layer: `Deadlock.Format`, `Deadlock.Transform`,
  `Deadlock.Tools`, `Deadlock.Harness`
- Project references encode the dependency direction. `Format` references
  nothing of ours; `Transform` references `Format` only; and so on upward.
- `Transform` must not reference VRF. If it needs something from a resource,
  `Format` exposes it as plain data.
- CI fails the build on a violation. Not a review comment — a red X.

### Registry pattern, not a switch statement

Asset types register handlers rather than appearing in a central dispatch:

```python
@handler("vdata")
def parse_vdata(raw): ...
```

Adding support for a new resource type is one file, no edits elsewhere.

---

## 2. Composability

Every tool reads JSON on stdin or a path, writes JSON to stdout. Tools compose
through pipes and never call each other in-process.

```bash
dl-extract --json fixtures/hero.vdata \
  | dl-patch --set 'abrams.max_health=800' \
  | dl-pack --out build/mod.vpk
```

Consequences to hold to:

- **No tool imports another tool.** Shared behaviour moves down into
  `transform/`.
- **stdout is the machine interface.** Diagnostics, progress and warnings go
  to stderr, always.
- A tool that cannot be usefully piped is probably doing two jobs.

---

## 3. CLI surface

| Command | Job |
|---|---|
| `dl-extract` | VPK/resource → JSON |
| `dl-diff` | two extracted trees → structural changeset |
| `dl-patch` | apply a changeset to extracted data |
| `dl-pack` | source assets → compiled VPK (shells out to CSDK) |
| `dl-fgd` | decompiled maps → reconstructed FGD |
| `dl-map` | layout description → `.vmap` (Phase 3b) |
| `dl-render` | map or layout → PNG artifact |
| `dl-verify` | run assertions, emit pass/fail |

Universal flags: `--json`, `--dry-run`, `--quiet`, `--fixture-root`.

Exit codes: `0` success · `1` expected failure (assertion failed, diff found
under `--check`) · `2` misuse · `3` missing fixture or dependency.

`3` is deliberately distinct: an agent should be able to tell "your input was
wrong" from "this machine isn't set up."

---

## 4. JSON envelope

Every tool emits the same outer shape, so consumers parse once:

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
  failure mode version-freezing exists to prevent, and it should be detectable
  from any single file.
- `errors[]` entries carry `code`, `message`, and `fix` — a concrete next
  action, not a restatement of the problem.
- **Deterministic ordering is mandatory:** sorted keys, stable record sort, no
  reliance on dict or filesystem iteration order. Byte-identical output for
  identical input is what makes `dl-diff` meaningful and CI caching safe.

---

## 5. Assertion vocabulary

`dl-verify` consumes a declarative assertion file. Four families:

| Family | Example | Needs |
|---|---|---|
| `data` | a stat reads the expected value after a patch | fixtures only |
| `runtime` | an event fires; an ability applies expected damage | live server |
| `spatial` | bot paths a route; traversal time; sightline distribution; lane symmetry | live server or geometry-only analysis |
| `visual` | rendered plan view, sightline overlay, before/after diff | renderer only |

```yaml
- id: abrams_health_patch
  family: data
  target: heroes.abrams.max_health
  expect: 800
```

`data` and `visual` assertions run today with fixtures alone. `runtime` and
`spatial` wait on a server. **Build the first two families first** — they are
what makes the toolkit useful before any hardware exists.

Every run emits a JSON report plus any rendered PNGs as CI artifacts, so a
failure is reviewable on a phone.

---

## 6. Performance

Optimisation without measurement is guesswork, and nothing here has been
measured. So this section is split into *decisions that must be made now
because they are architectural* and *tuning that waits for numbers*.

### Architectural — decide now, expensive to retrofit

- **Content-addressed cache.** Key every parse by SHA-256 of input bytes plus
  parser version. Extraction is pure, so the cache never invalidates
  incorrectly, and CI can restore it between runs. This is the single largest
  win available and it must be designed in, not bolted on.
- **Stream, don't slurp.** Iterate resource entries; never load a whole VPK
  into memory. VPKs are large enough that this decides whether a runner
  survives.
- **Parse lazily.** Extract the index eagerly, resource bodies on demand. Most
  tasks touch a handful of entries out of thousands.
- **Parallelism at the file boundary only.** Per-resource work is independent;
  keep it that way. Merge results in sorted order so output stays
  deterministic — parallelism must never be observable in the output.
- **Separate the hot path.** `dl-diff` and `dl-render` will run on every push.
  `dl-pack` runs rarely and can be slow. Do not let the rare-and-slow path
  dictate the design of the frequent one.
- **In-process composition for pipelines that would round-trip.** Piping tools
  is the interface, not the only path: a multi-step operation inside one
  process should pass typed objects and serialise **once**, at the end. Now
  that the toolkit is single-language this is available, and it is the main
  optimisation the all-C# decision bought. The piped form must still work
  identically — same output, byte for byte.
- **Diff from the index, not the bodies.** Every VPK entry carries `CRC32` and
  `TotalLength` in the directory. `dl-diff` compares those and reads bodies
  only for entries whose checksum moved. This is the every-push hot path and
  it costs almost nothing. Reading bodies to diff them is the wrong shape.
- ~~**Spans, not copies.**~~ **Withdrawn.** ValvePak's `ReadEntry` returns a
  `byte[]` per entry and the documented path wraps it in a `MemoryStream`.
  There is no zero-copy surface to build on. Allocation per entry is the
  floor unless `Format` reimplements the reader, which is not worth it.
  Mitigate by reading fewer entries, not by reading them more cleverly.

### Tuning — wait for measurement

Add a benchmark job that records wall-clock and peak RSS per tool against a
fixed fixture, and fails on regression beyond a threshold. Then optimise what
the numbers show, not what seems slow.

Rough budgets to design toward, to be replaced with real figures:

| Operation | Target |
|---|---|
| Full extract of one VPK | seconds, not minutes |
| Incremental diff, warm cache | under a second |
| Render one plan view | a few seconds |
| Full map compile | minutes; runs on its own workflow |

**Explicitly not optimising yet:** the KV3 parser, until a fixture shows it is
hot; anything in `dl-pack`, which is dominated by the CSDK compilers we do not
control.

---

## 7. Open questions in this spec

- ~~Is the C#/Python split right?~~ **Settled: all C#.** See section 1.
  Revisit only if VRF turns out to be unusable as a library, in which case the
  format layer is the only thing that changes.
- ~~Does VRF expose a streaming VPK reader?~~ **Answered.** VPK access is via
  **ValvePak**, a separate library VRF depends on. The index loads eagerly and
  bodies are fetched per entry, so the lazy-parse rule is native. `Read()`
  accepts a `Stream`. Body reads allocate a `byte[]` each — see the withdrawn
  spans rule in section 6.
- `Format` therefore takes **two** dependencies, ValvePak and VRF, not one.
  Worth noting because ValvePak alone covers archive work; VRF is only needed
  once a resource must be decoded.
- Whether the rendering stack should be SkiaSharp or ImageSharp. Deferred until
  `dl-render` has a real plan-view to draw; both are plausible.
- What assertion format — YAML as sketched, or JSON for consistency with
  every other interface? Leaning JSON, on the grounds that one format is
  easier for agents than two.
