# Fixtures

## `dl_example.vmap`

**Location:** repo root (committed there by accident on 2026-08-14; nothing
depends on the path, and moving it costs a UI operation for no gain).

**Size:** 15,073,405 bytes. **Mtime:** 2024-10-06.
**CRC per resourcecompiler:** `0xA01748CD`.

**What it is:** a community-made Deadlock dev map, described by its author
as containing examples of the entities a map or gamemode needs to work.

**Where it came from:** a pixeldrain link published in Rayth's Deadlock
mapping guide on Steam. Downloaded 2026-08-14.

**Licence: none found.** No licence file, no stated terms, no named author
beyond the guide. It is committed here as a test fixture for a personal
toolkit on the reasoning that it is a shared community asset and that a
fixture CI cannot fetch reproducibly is a fixture that rots. That is a
practical judgement, not a legal one, and "testing and education" is a
description of intent rather than a grant of rights. If the author asks,
remove it: nothing in the toolchain needs it except tests, and those can
run against a derived minimal fixture instead.

**Why it is committed whole rather than fetched:** considered and
rejected. The CSDK is already fetched from a release asset and that path
works, so the history-bloat argument had merit. But 15 MB is well inside
GitHub's limits and a checkout is one fewer moving part in every workflow
that needs it. Accepted cost: it is in git history permanently and
`inbox` cannot remove it.

**Do NOT publish it.** The repo is public and GitHub Pages serves from
`docs/`, which is why the viewer lives there. A Pages deploy from the repo
root would republish this file.

### What it is used for

| workflow | use |
|---|---|
| `probe-dmxconvert` | binary <-> keyvalues2 round trip |
| `probe-dmx-noids` | binary <-> keyvalues2_noids, census intact |
| `map-smoke` | the KV2 reader and writer, against 7,071 real elements |

### Census, measured 2026-08-14

7,071 elements, 769 roots, 1,343 strings in the binary string table.

    222 CDmePolygonMesh     222 CMapMesh      222 CDmePolygonMeshSubdivisionData
    888 CDmePolygonMeshDataArray            2482 CDmePolygonMeshDataStream
    598 CMapEntity          969 EditGameClassProps   971 DmePlugList
    349 CMapPathNode         89 DmeConnectionData     24 subdivision bindings
     21 CMapPath              2 each CMapGroup / CMapInstance / CMapSelectionSet
      1 each CMapRootElement / CMapWorld / CMapVariableSet / CVisibilityMgr /
             CStoredCameras / CStoredCamera / CObjectSelectionSetDataElement /
             DmElement

**These numbers are asserted in CI.** If the fixture is ever replaced they
must be RE-MEASURED, never carried over. A stale floor that happens to
pass is worse than no floor.

### It is MAXIMAL, not minimal

It contains bosses, ziplines, breakables, powerups, full lighting and an
embedded JPEG preview thumbnail. It answers "what is available" and cannot
answer "what is required". The document floor — which of
`CMapRootElement`, `CMapWorld`, `CVisibilityMgr`, `CMapVariableSet`,
`CStoredCameras`, `CObjectSelectionSetDataElement` a `.vmap` must have —
is still open, and this file cannot close it.

### Version drift

`editorbuild 10169`, `editorversion 400`, October 2024. Deadlock has moved
on. Accepted rather than chased: hunting a newer fixture is an unbounded
search for a problem that may not exist. **But if Hammer or the compiler
ever rejects an emitted map, schema drift on these is hypothesis #1**,
before anyone debugs half-edge code for a day.
