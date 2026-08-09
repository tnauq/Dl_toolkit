# TOOLING — `dl-patch`, including batch

Spec only. **Nothing here is built.** Kept so the single-edit v1 does not paint
batch into a corner, per D8: one tool at a time, but design the seams once.

Everything in this file is `[?]` until the KV3 write path is settled by the
`probe kv3` run.

---

## v1 — single edit, scalars only

```
dl-patch --in <file.vdata> --out <file.vdata> --set <dotted.path>=<value>
```

- `--set` may repeat. Repeats are applied in order, left to right.
- Scalars only: number, string, bool. Array indices and object insertion are
  out of scope and must produce a named error, not a partial write.
- `--dry-run` reports what would change and writes nothing.
- `--json` emits the envelope on stdout; diagnostics to stderr (D5).
- Exit codes: 0 ok, 2 misuse, 3 missing dependency, 4 input unreadable,
  5 path not found in document, 6 type mismatch at path.

### Why the seam matters now

v1 takes `--set` from argv. Batch takes it from a file. If v1's internals take
a `List<Edit>` rather than a string pair, batch is a new front end over the
same core and nothing is rewritten. **Do not let argv parsing reach into the
edit application code.**

---

## Batch — STUB, not built

```
dl-patch batch --plan <plan.json> [--root <dir>] [--out-root <dir>] [--dry-run]
```

One plan touches many files. Motivating case: a hero rebalance that spans
several vdata files and must land atomically or not at all.

### Plan shape — DRAFT

```json
{
  "version": 1,
  "description": "human note, echoed into the result",
  "edits": [
    {
      "file": "game/citadel/scripts/heroes.vdata",
      "set": [
        { "path": "hero_abrams.m_flMaxHealth", "value": 750 },
        { "path": "hero_abrams.m_bDisabled", "value": false }
      ]
    }
  ]
}
```

### Open questions — answer before building, do not guess

- **Atomicity.** All-or-nothing across files, or per-file best effort? Leaning
  all-or-nothing: a half-applied balance pass is worse than none. Requires
  staging to temp and moving on success.
- **Expected-value guards.** Should an edit be able to say
  `"expect": 600` and fail if the current value differs? This is what makes a
  plan survive a game patch instead of silently writing over changed values.
  Probably yes, and probably the single most valuable field here.
- **Path collisions.** Two edits to the same path in one plan: error, or
  last-wins? Leaning error.
- **Ordering.** Is plan order the contract, or is output sorted? D5 says
  deterministic ordering is a contract — decide which one.
- **Build id.** D2 says record the build id on every artifact rather than
  pinning. The result envelope should carry the GameTracking commit the input
  came from. Mechanism unspecified.

### Result envelope — DRAFT

```json
{
  "ok": true,
  "tool": "dl-patch",
  "version": "0.0.0",
  "sourceBuild": "gametracking-commit-sha",
  "files": [
    {
      "file": "game/citadel/scripts/heroes.vdata",
      "applied": 2,
      "skipped": 0,
      "edits": [
        { "path": "hero_abrams.m_flMaxHealth", "from": 600, "to": 750, "ok": true }
      ]
    }
  ]
}
```

`from` is what makes the output reviewable on a phone without opening the file,
and it is also the inverse of the plan — enough to generate an undo.

---

## Not in scope, recorded so it is not re-proposed

- Compiling to `.vdata_c`. Separate step, separate tool, needs the CSDK.
- Packing to a VPK addon. `Deadlock.Format` already writes archives; wiring is
  a later tool.
- Merging two plans. No use case yet.
