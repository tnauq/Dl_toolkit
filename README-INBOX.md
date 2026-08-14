# Inbox drop — closing out before a fresh layout (2026-08-14)

Unzip at repo root, run `inbox`.

## NEW
    src/Deadlock.Format/Dmx/MapReader.cs
    .github/workflows/plan-roundtrip.yml
    docs/FIXTURES.md

## REPLACES
    src/Deadlock.MapSmoke/Program.cs     adds `verify`
    docs/SESSION-2026-08-14.md           the earlier version predates the
                                         compiler probes and is misleading

## What plan-roundtrip closes

Q16, agreed and never built. emit-smoke counts elements; a box emitted at
half size or a spawn that lost its teamnumber passes a census untouched.
`verify` compares the map BACK to the plan: every origin, extent, angle,
material and keyvalue.

Extents are RECOMPUTED from the vertex positions in the file, not read
from a field, so a geometry bug cannot hide behind matching metadata.
Comparison is to 0.1 u (2.5 mm) because values make a float round trip
through text twice.

It verifies twice: once on our own text before dmxconvert sees it, so an
emitter/reader disagreement is isolated from anything Valve does, and
again after the binary round trip.

## NOT COMPILED

Same as previous drops: no dotnet in the authoring sandbox. MapReader's
walk and its extents recovery WERE validated first — ported to Python and
run against a hand-written KV2 sample, recovering 8 verts, 6 faces,
extents from the position stream, material, classname and keyvalues.
plan-roundtrip builds before it fetches the CSDK.

## Still owed, needs the GitHub UI

`inbox` cannot delete. See section 5 of the session doc: three spent
compiler probes, the older probe-kv3 / probe-compiled / dump_contracts
leftovers, and the PLAN.md update.
