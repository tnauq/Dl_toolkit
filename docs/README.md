# deadlock-toolkit

Tooling for modding Deadlock on a pinned build with a private dedicated server.

**Start here:** `AGENTS.md`, then `FINDINGS.md`, then `TOOLING.md`.

## Status

Skeleton. The `Format` layer reads a VPK index; nothing else is implemented.
**None of this has been compiled** — it was written without a .NET toolchain
available. The first CI run is the first build.

## Layout

```
src/Deadlock.Contracts   JSON envelope, exit codes. Bottom of the graph.
src/Deadlock.Format      binary in, plain data out. Only layer that knows VPK/KV3.
src/Deadlock.Tools       CLIs.
fixtures/                real game data, read-only, committed from desktop.
docs/                    plan, findings, tool spec.
```

Dependencies point downward only, and CI fails the build on a violation.

## Smoke test

`.github/workflows/format-smoke.yml` validates the Format layer with **no
Deadlock files**: it builds, resolves ValvePak, checks the exit-code contract,
and verifies output is byte-identical across two runs.

Drop any Source-engine `*_dir.vpk` into `fixtures/` to exercise the read path.
For this test it should NOT be Deadlock's — the point is to prove the toolchain
before real fixtures exist.
