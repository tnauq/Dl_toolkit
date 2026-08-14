# Inbox drop — the emitter (2026-08-14, second drop)

Unzip at repo root.

## NEW

    src/Deadlock.Format/Dmx/HalfEdgeMesh.cs
    src/Deadlock.Format/Dmx/MapEmitter.cs
    .github/workflows/emit-smoke.yml

## REPLACES files from the first drop today

    src/Deadlock.MapSmoke/Deadlock.MapSmoke.csproj   (adds Contracts ref)
    src/Deadlock.MapSmoke/Program.cs                 (adds `emit` mode)

Real extensions, because inbox needs to overwrite them.

## NOT COMPILED

Same caveat as the first drop, same mitigation. No dotnet in the authoring
sandbox. What WAS validated, before any C# was typed:

- The half-edge construction was ported to Python and asserted: 8 verts,
  12 edges, 24 half-edges, 6 faces; every face loop closes at length 4;
  every directed edge appears exactly once; **no -1 in edgeFaceIndices**
  (a sealed box, unlike the open quad in the fixture); and all six Newell
  normals point OUTWARD from the centre.
- Every structural value in `MapEmitter` was read off `dl_example.vmap`, not
  invented: the stream set and its `dataStateFlags`, the `CMapMesh` defaults,
  `CMapWorld`, `CMapRootElement`, and the text forms (`"element" ""` for a
  null reference, `"uint64" "0x0"`).

`emit-smoke` builds before it fetches the CSDK, so a typo costs seconds.

## No GUIDs, and why that is fragile

`keyvalues2_noids` writes an element id only where an element is referenced
MORE THAN ONCE. Everything the emitter produces is referenced exactly once,
so the document carries no ids at all.

Adding groups, selection sets, paths or entity connections breaks that and
reintroduces id generation. `docs/SCHEMA-mapplan.md` says the same thing;
this is the second place it is written down because it is the property most
likely to be lost by accident.

## What emit-smoke proves, and what it does not

    sealed-room.mapplan.json
      -> OUR emitter  -> keyvalues2_noids text
      -> dmxconvert   -> binary vmap 40      <-- Valve judges it
      -> dmxconvert   -> text
      -> OUR reader   -> census              <-- nothing lost

Green means **structurally valid and accepted by dmxconvert**. It does NOT
mean Hammer opens it, and it does not mean Deadlock loads it. The ceiling has
not moved. Tools say "structurally valid", never "works".

## Known soft spots

- **Texture axes and UVs are a first cut.** Projection axes are picked by
  dominant normal, texcoords are a 0.25 scale planar projection, tangents are
  derived from the U axis with w=-1. Plausible and consistent, but no fixture
  comparison was done for a BOX specifically — the fixture's smallest mesh is
  a quad. Expect to revisit once something renders it.
- **`smoothingAngle` is 180**, taken from the CMapMesh in the text dump. The
  binary sample read 40. Both appear in the file; 180 was chosen because it
  came from the fully-dumped element. Low confidence, easy to change.
- **`editorbuild 10169` / `editorversion 400`** are copied from an October
  2024 fixture. If Hammer or the compiler rejects the file, schema drift on
  these is hypothesis #1, per the settled decisions.
- **Rotated boxes are emitted but untested.** Geometry is local-space and
  placed by `angles`, so rotation should be free, but the example uses none.

## Next

1. Run `emit-smoke`.
2. The `resourcecompiler` map probe, warning-level: does a `.vmap` at
   `content/citadel_addons/<name>/` build headlessly? Still the only external
   judge beyond dmxconvert.
3. The HTML viewer. Needs no CI and no Windows.
