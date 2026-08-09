# TOOLING — `dl-patch`

v1 is **built and CI-verified** (patch-smoke 2026-08-09). Batch is spec only.

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

### Rules that are enforced, each for a reason

- **The document's existing type wins.** A fractional value into an integer
  field is REFUSED, not rounded — silent rounding is how a vdata edit changes
  meaning invisibly.
- **Flagged values are refused by name.** `resource_name:`, `subclass:`,
  `panorama:` carry a `KVFlag`; writing one as a plain string would drop the
  prefix with no visible sign.
- **Arrays are refused.** Arrays are `KVObject` with `IsArray`, so without an
  explicit check they would look like traversable blocks.
- **All-or-nothing.** Any failed edit means nothing is written. Established
  here because it is what batch needs.
- **Source vdata in, source vdata out.** Compiling is a separate step.
- The tool says "structurally valid", never "works" (D7).

### What CI proves — and the trick that makes it work

VRF reformats on write (floats to 6dp, arrays exploded), so a byte-identical
assertion against the ORIGINAL is impossible. `patch-smoke` instead writes a
**no-op baseline** first, then diffs the patched file against the baseline.
Reformatting is constant on both sides, so the assertion reduces to *exactly
two changed lines, one `<` and one `>`*.

Also asserted: re-parse, determinism across runs, all four exit codes, flagged
refusal, and that `--dry-run` leaves no file.

### Known rough edge

The envelope's `from` uses `"R"` formatting, so a field reading `780.0` in the
file reports as `780`. Cosmetic now; see the batch `expect` note below.

---

## Batch — STUB, not built

```
dl-patch batch --plan <plan.json> [--root <dir>] [--out-root <dir>] [--dry-run]
```

One plan touches many files. Motivating case: a rebalance spanning several
vdata files that must land atomically or not at all.

### Plan shape — DRAFT

```json
{
  "version": 1,
  "description": "human note, echoed into the result",
  "edits": [
    {
      "file": "game/citadel/pak01_dir/scripts/heroes.vdata",
      "set": [
        { "path": "hero_base.m_mapStartingStats.EMaxHealth", "value": 750, "expect": 780 },
        { "path": "hero_base.m_bDisabled", "value": false }
      ]
    }
  ]
}
```

### The seam v1 already respects

`Edit` and `ScalarValue` are parsed from argv but **nothing in `Edit.cs`
reaches into argv**. Batch is a new front end producing the same `List<Edit>`;
`Kv3Document` does not change.

### Open questions — answer before building

- **`expect` guards.** The field that makes a plan survive a game patch instead
  of overwriting values that moved underneath it. Probably the highest-value
  item here. **Comparison must be numeric, not string** — `780` vs `780.0`
  would fail a string compare (see the rough edge above).
- **Atomicity across files.** Leaning all-or-nothing, which needs staging to
  temp and moving on success.
- **Path collisions** — two edits to one path: error, or last-wins? Leaning
  error.
- **Ordering** — plan order, or sorted output? D5 makes deterministic ordering
  a contract; pick one and assert it.
- **Build id.** D2 says record the build on every artifact. The envelope should
  carry the GameTracking commit the input came from. `patch-smoke` already
  records it in `source-build.txt`; the tool itself does not.

### Result envelope — DRAFT

```json
{
  "ok": true,
  "tool": "dl-patch",
  "sourceBuild": "0f32ac2411aa8e6832eb233b1db2d68800974714",
  "files": [
    {
      "file": "game/citadel/pak01_dir/scripts/heroes.vdata",
      "applied": 2,
      "skipped": 0,
      "edits": [
        { "path": "hero_base.m_mapStartingStats.EMaxHealth",
          "from": 780, "to": 750, "ok": true }
      ]
    }
  ]
}
```

`from` makes the result reviewable on a phone without opening the file, and it
is the inverse of the plan — enough to generate an undo.

---

## Not in scope, recorded so it is not re-proposed

- Compiling to `.vdata_c`. Separate step, separate tool, needs the CSDK.
- Packing to a VPK addon. `Deadlock.Format` already writes archives.
- Merging two plans. No use case yet.
- Array-element and object-insertion edits. Wait for a real need; they are what
  would force a genuine KV3 writer.
