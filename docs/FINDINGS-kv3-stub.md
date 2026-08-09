# FINDINGS stub — KV3 write path

Paste into `docs/FINDINGS.md` under a new `## KV3 writing` heading once the
`probe kv3` workflow has run. Fill the blanks from `probe-out/report.md` and
the artifact diff. **Do not mark anything `[V-CI]` without naming the run.**

---

## KV3 writing — `[ ]` STATUS PENDING, probe kv3 run #___

- VRF version probed: `ValveResourceFormat 12.0.0`
- Input file: `____________________` (____ bytes)
- Entry point used: `KeyValues3.ParseKVFile(path)` → `.ToString()`
  - If this was wrong, the correct names are in `kv3-surface.txt`: `________`
- Verdict: `IDENTICAL` / `REFORMATTED` / `LOSSY-SUSPECT` / `THREW`

**What it means for `dl-patch`:**

- [ ] `IDENTICAL` → wrap VRF. Unchanged-bytes assertion is available. v1 is small.
- [ ] `REFORMATTED` → VRF is usable for reading; CI compares parsed shape, not
      bytes. Decide separately whether the noisy diff is acceptable on mobile.
- [ ] `LOSSY` / `THREW` → we own a KV3 serializer. Scope it as its own tool
      under D8 before `dl-patch` v1 is designed.

**First divergence observed:**

```
____________________
```

**Not established by this probe** (do not let the result imply these):

- Whether the game LOADS either output. Still blocked on hardware — D7 stands.
- Whether other vdata files behave the same. One file was probed, not the set.
- Whether comments survive. Check the artifact by eye; the heuristic in the
  probe counts `=` signs and is `[?]` at best.
