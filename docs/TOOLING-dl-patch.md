# TOOLING — `dl-patch`

Four modes, all CI-verified: `set` (default, no subcommand), `batch`, `diff`,
`pack`. One binary; `Program.cs` is a dispatcher.

| mode | status |
|---|---|
| `set` | green, patch-smoke 2026-08-09 |
| `batch` | green, batch-smoke 2026-08-12 |
| `diff` | green, diff-smoke 2026-08-12 |
| `pack` | green, loop 2026-08-12 |

---

## v1 — single edit, scalars only. SHIPPED.

```
dl-patch --in <file.vdata> --out <file.vdata> --set <dotted.path>=<value> [--set ...]
         [--dry-run] [--json]
```

- `--set` may repeat; applied in order, left to right.
- **Scalars only**: number, string, bool.
- `--dry-run` reports and writes nothing.
- `--json` puts the envelope on stdout; diagnostics to stderr (D5).
- Exit codes: 0 ok, 2 misuse, 3 missing dependency, 4 input unreadable,
  5 path not found, 6 type mismatch.

Takes **no subcommand**, so every existing invocation is unchanged by batch's
arrival. The implementation moved from `Program.cs` to `SetCommand.cs`
2026-08-12; behaviour, exit codes and error strings did not.

### Value inference — a contract, not an accident

```
true / false   -> bool
-12            -> integer
3.5            -> number
"1"            -> string   (quotes force string)
anything else  -> string
```

The quote escape exists so a numeric-looking value can still be written as a
string. Without it there is no way to set a key to the string `"1"`.

**Batch does not inherit this.** JSON is already typed, so a plan needs no
inference and no quote escape — a JSON string is a string.

### Rules that are enforced, each for a reason

- **The document's existing type wins.** A fractional value into an integer
  field is REFUSED, not rounded — silent rounding is how a vdata edit changes
  meaning invisibly.
- **Flagged values are refused by name.** `resource_name:`, `subclass:`,
  `panorama:` carry a `KVFlag`; writing one as a plain string would drop the
  prefix with no visible sign.
- **Arrays are refused.** Arrays are `KVObject` with `IsArray`, so without an
  explicit check they would look like traversable blocks.
- **All-or-nothing.** Any failed edit means nothing is written.
- **Source vdata in, source vdata out.** Compiling is a separate step.
- The tool says "structurally valid", never "works" (D7).

### What CI proves — and the trick that makes it work

VRF reformats on write (floats to 6dp, arrays exploded), so a byte-identical
assertion against the ORIGINAL is impossible. `patch-smoke` instead writes a
**no-op baseline** first, then diffs the patched file against the baseline.
Reformatting is constant on both sides, so the assertion reduces to *exactly
two changed lines, one `<` and one `>`*. `batch-smoke` reuses it.

### Known rough edge

The envelope's `from` uses `"R"` formatting, so a field reading `780.0` in the
file reports as `780`. Cosmetic — and it is precisely why batch guards compare
numerically after normalisation rather than as strings.

---

## Batch — GREEN 2026-08-12

```
dl-patch batch --plan <plan.json> --root <dir> --out-root <dir>
               --source-build <sha> [--dry-run] [--json] [--max-files N]
```

One plan touches many files. Motivating case: a rebalance spanning several
vdata files that must land atomically or not at all.

`batch` is a **subcommand**, not a flag, because the two modes take disjoint
arguments. One shared parser would have to police "never both `--plan` and
`--set`", a rule the shape expresses for free.

### Plan shape — v1

```json
{
  "version": 1,
  "description": "human note, echoed into the result",
  "edits": [
    {
      "file": "game/citadel/pak01_dir/scripts/heroes.vdata",
      "set": [
        { "path": "hero_base.m_mapStartingStats.EMaxHealth", "value": 750, "expect": 780 },
        { "path": "hero_base.m_bDisabled", "value": false, "expect": null }
      ]
    }
  ]
}
```

### The seam v1 already respected

`Edit` and `ScalarValue` are parsed from argv but **nothing in `Edit.cs`
reaches into argv**. Batch is a new front end producing the same `List<Edit>`.
`Kv3Document` gained a read path (`TryRead`, `Serialize`) so guards can be
evaluated before anything mutates; `Apply` is untouched.

### Settled decisions — answered 2026-08-12, do not relitigate. Each has a named assertion in `batch-smoke.yml`.

| # | Decision | Reasoning |
|---|---|---|
| Q1 | **`expect` is MANDATORY.** Explicit `null` opts out | An unguarded edit inside a mostly-guarded plan is a silent hole, and it will be the one that overwrites a value Valve moved. Null makes the hole deliberate and greppable |
| Q2 | **Numbers compared after 6dp normalisation**; bool and string exactly | It matches what the file holds after VRF round-trips it. probe-floats found two literals over 6dp in `abilities.vdata`, so this is live, not hypothetical |
| Q3 | **All documents held in memory**, written only after all succeed | No temp-dir cleanup path, therefore no partial-cleanup failure mode. Bounded by the Q13 cap |
| Q4 | **`--out-root` required and separate.** Output is an **overlay** — only planned files are written | v1 already forces an explicit `--out`; batch must not be looser. An overlay is also exactly the shape an addon VPK wants. Plan paths must be relative and may not contain `..` |
| Q5 | **Duplicate path in one file: error** | Last-wins quietly commits to merge semantics nobody has designed. Merging is out of scope, and error keeps that door open |
| Q6 | **Apply in plan order; emit sorted by (file, path)** | Q5 makes edits independent, so application order is unobservable; plan order is what a human reading a diff expects. Sorted output makes two runs byte-identical |
| Q7 | **`--source-build` required**, carried in the envelope's `pinned_build` | D2. Optional-with-a-default means every forgotten flag yields an unlabelled artifact. The tool cannot derive it from a vdata file |
| Q8 | **Guard mismatch is exit 7**, a new code | It means something different in kind from 5 and 6: plan and file are both fine, the BUILD moved. Code 1 stays reserved for a future `--check` |
| Q9 | **A guarded path that has vanished is also 7** | Same event from the author's view. Code 5 then means only "you typed it wrong", which is a genuinely different signal |
| Q10 | **Unknown fields and unknown versions are refused** | A silently ignored typo is how a mandatory guard gets dropped, undoing Q1. Strict now is cheap; tightening later breaks plans in the wild |
| Q11 | **Same file twice: error** | The array-level form of Q5. One parsed document per plan entry, no reconciliation |
| Q12 | **`--dry-run` evaluates everything** — loads, guards, applies in memory, writes nothing | This is batch's most useful mode, not a courtesy flag: the pre-flight against a new build. Exit codes identical to a real run |
| Q13 | **File cap, default 32**, `--max-files` to raise | Makes the in-memory model fail with an error rather than an OOM |
| Q15 | **Every failure evaluated and reported**, never first-stop | A pre-flight that surfaces one problem at a time is a bad pre-flight |
| Q16 | **Every planned file appears in the envelope**, changed or not | Envelope shape then depends on the PLAN, never on tree content — so "files[] matches the plan" is assertable and two envelopes are diffable. No-ops count as `skipped` |
| Q17 | **Lives in `Deadlock.Patch`**, not a new assembly | A second assembly means a second net9.0 project and a second copy of the CLI conventions, for a tool sharing the whole document layer |

### Result envelope

Post-fold, this is `Envelope<BatchData>` from `Deadlock.Contracts`:

```json
{
  "tool": "dl-patch",
  "version": "0.2.0",
  "pinned_build": "0f32ac2411aa8e6832eb233b1db2d68800974714",
  "ok": true,
  "data": {
    "mode": "batch",
    "dry_run": false,
    "description": "human note",
    "files_total": 1,
    "applied": 2, "skipped": 0, "failed": 0,
    "files": [
      { "file": "game/citadel/pak01_dir/scripts/heroes.vdata",
        "applied": 2, "skipped": 0, "failed": 0, "written": true,
        "edits": [
          { "path": "hero_base.m_mapStartingStats.EMaxHealth",
            "from": "780", "to": "750", "expected": "780",
            "noop": false, "ok": true } ] } ]
  },
  "warnings": [],
  "errors": []
}
```

`from` makes the result reviewable on a phone without opening the file, and it
is the inverse of the plan — enough to generate an undo.

### Deferred, deliberately

- **`--emit-undo <path>`.** The envelope already carries everything needed.
  Building it now means designing undo semantics for guards (does the undo's
  `expect` become the value just written?) before the main path has run once.
  Obvious follow-up, not v1.
- **`--check` mode**, which is what `Contracts.Exit.ExpectedFailure = 1` is
  reserved for. Different question from dry-run: "would this change anything?"
  rather than "would this succeed?"

---

## Not in scope, recorded so it is not re-proposed

- Compiling to `.vdata_c`. Separate step, separate tool, needs the CSDK.
- Packing to a VPK addon. `Deadlock.Format` already writes archives.
- Merging two plans. No use case yet — and Q5/Q11 deliberately keep the door
  open by erroring rather than guessing.
- Array-element and object-insertion edits. Wait for a real need; they are what
  would force a genuine KV3 writer.


---

## diff — GREEN 2026-08-12

```
dl-patch diff --old <file.vdata> --new <file.vdata>
              [--json] [--max-entries N] [--paths-only]
```

**Why it exists.** Guards are mandatory and a guard fails when the build moved
underneath the plan. `--dry-run` says a plan HAS gone stale; diff says WHAT
moved, which is what you need to re-derive it.

### Decisions

| | |
|---|---|
| **Subcommand, not a new assembly** | `Kv3Document.cs` is the only file that touches VRF. A second assembly means duplicating that access or refactoring out a shared vdata layer |
| **Semantic, not textual** | Compares parsed values. Diffing a file against its own no-op round trip reports **zero** differences — verified at 35,443 paths |
| **Floats normalise to 6dp** | Same rule as batch guards (Q2) |
| **Arrays are opaque** | Length change registers, element edit does not. Array elements have no dotted path |
| **Exit 1 = differ** | `ExpectedFailure`, used for its stated meaning. `ok` stays true, `errors` empty: a difference is a RESULT |
| **`retyped` is its own change class** | A float becoming a string is drift a value-only diff would misreport |

Change classes: `added`, `removed`, `changed`, `retyped`. Results sorted by
path. `kind` currently reports the CLR type name (`Double`) — honest but it
leaks an implementation detail; map to KV3 vocabulary if anything branches on it.

---

## pack — GREEN 2026-08-12

```
dl-patch pack --in <dir> --out <pak01_dir.vpk> --source-build <sha>
              [--prefix <p>] [--json] [--verify]
```

The last link: compiled tree -> addon VPK.

### Decisions

| | |
|---|---|
| **Archive writing stays in `Deadlock.Format`** | CI enforces the layer boundary. pack is a front end over `VpkWriter.CreateFromDirectory` and touches no archive API |
| **Entries keyed relative to `--in`**, forward-slashed | `scripts/heroes.vdata_c`. `[I]` — consistent with gameinfo's mounts and the compiler's write path, unconfirmed against a running game. `--prefix` if it proves wrong |
| **`--source-build` required** | D2; a VPK is the most shippable artifact here |
| **`--verify` exit 8** | Re-reads and checks every CRC32 against the independently computed one. Distinct code because the tool worked and the RESULT is untrustworthy |

### PACK FROM A CURATED TREE

**Do not point `--in` at the compiler's output directory.** It holds
`gameinfo.gi` (game config, never mod content), and the compiler writes there,
so it may hold a stale artifact. The first green `loop` run shipped
`gameinfo.gi` plus the *unpatched* resource and every assertion passed. Stage
what you mean to ship.

### Install

A mod is a VPK at `Deadlock/game/citadel/addons/pak##_dir.vpk`, `##` 01-99,
**lower number = higher priority**. Requires a one-time `gameinfo.gi`
SearchPaths edit. Whether Deadlock accepts a modded vdata this way is
**unconfirmed** — needs hardware (D7).

---

## Compiling — no longer a gap

`resourcecompiler.exe` compiles source vdata headlessly on `windows-latest`.
See `FINDINGS-2026-08-12.md` for the three sub-gaps that were closed. In short:
`-game` names the directory holding `gameinfo.gi`, **the compiler must be run
from the directory containing `citadel/`** because `GAMEROOT` is the working
directory, `modtools.dll` is a loose release asset on `csdk-12`, and vdata must
declare `generic_data_type`.

`heroes.vdata` compiles from a bare content tree.

---

## Deferred, deliberately

- **`--emit-undo <path>`.** The envelope already carries `from` per edit.
  Building it now means designing undo semantics for guards before the main
  path has run in anger.
- **`--check` mode.** Code 1 is now spent on diff, so `--check` needs its own.
- **`pack --exclude <glob>`.** The curated-tree discipline covers it for now.
