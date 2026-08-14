# Inbox drop — KV2 DMX layer + MapPlan schema (2026-08-14)

Unzip at repo root. Nothing here replaces an existing file; all new.

    src/Deadlock.Format/Dmx/DmxModel.cs
    src/Deadlock.Format/Dmx/Kv2Reader.cs
    src/Deadlock.Format/Dmx/Kv2Writer.cs
    src/Deadlock.Contracts/MapPlan.cs
    src/Deadlock.MapSmoke/Deadlock.MapSmoke.csproj
    src/Deadlock.MapSmoke/Program.cs
    .github/workflows/map-smoke.yml
    docs/SCHEMA-mapplan.md
    examples/sealed-room.mapplan.json

## NOT BUILT

There is no dotnet in the authoring sandbox and no network, so **the C# has
never been compiled**. The grammar it implements WAS validated: a reference
parser was written in Python and run against the real dmxconvert output for
both keyvalues2 and keyvalues2_noids before any C# was typed. So the risk is
concentrated in syntax and API details, not in the format.

`map-smoke` builds before it fetches the CSDK, so a typo costs seconds rather
than a full CSDK download.

## Layering

`Deadlock.Format` gains a `Dmx` namespace. It does NOT touch VRF —
`Kv3Document` remains the only thing that does. The layering rule holds:
KV3 and DMX are siblings, not nested.

`Deadlock.MapSmoke` is deliberately throwaway-shaped. It exists so map-smoke
can run without editing the `dl` CLI, which the settled decisions keep as ONE
binary. Folding this in as `dl map info` is a follow-up that needs the
existing CLI source; delete this project when that lands.

The new projects are referenced by path in the workflow, so **no solution file
edit is needed** to make CI work. Add them to the .sln at your leisure.

## What map-smoke proves

    dl_example.vmap (binary)
      -> dmxconvert -> text
      -> OUR reader + writer -> text2   (census across our own layer)
      -> dmxconvert -> binary           (Valve accepts it, or not)
      -> dmxconvert -> text3
      -> OUR reader                     (census end to end)

dmxconvert in the middle is the point. A reader and writer that shared a
misunderstanding of the grammar would cancel out in a plain read-write-read
check and pass. Valve's binary is the independent judge.

## Still open

- The EMITTER (MapPlan -> DMX) is not here. Next step, and the only remaining
  hard part: box to half-edge construction, plus the exact stream set a box
  must carry.
- `DmxReadResult` is a local result type. If Contracts already has a Result
  shape, merge them — failure kinds are values, per the settled convention,
  and `DmxFailure` follows `EditFailure`.
- Whether Hammer READS a text-encoded .vmap. Unaffected by anything here,
  since export goes through dmxconvert to binary either way.
