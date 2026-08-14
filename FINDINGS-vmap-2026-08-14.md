# FINDINGS append — `.vmap` is DMX, not KV3 (2026-08-14)

Source: `dl_example.vmap`, community Deadlock dev map, 15,073,405 bytes,
mtime 2024-10-06. Parsed to completion by a throwaway Python probe.
**Every claim below is `[V-CI]`-grade in substance: it came from reading the
real file, and the parser consumed 15,073,405 of 15,073,405 bytes with no
slack.** Reimplement in C# before relying on it in the toolchain.

---

## 1. The correction

`FINDINGS` previously assumed map reading could reuse the vdata layer, because
compiled Source 2 resources are BinaryKV3. **That is wrong for map _source_.**

```
<!-- dmx encoding binary 9 format vmap 40 -->
```

`.vmap` is **DMX binary 9**, a different serialisation entirely. `Kv3Document`
and VRF's `Resource.Read` do not apply. The compiled `.vmap_c` is still KV3, but
it is the stub with the empty `DATA` block, so it is not a route to anything.

**Consequence for layering:** DMX is a new format concern. It belongs in
`Deadlock.Format` alongside ValvePak, as a sibling of the KV3 path, not inside
it. `Kv3Document` remains the only thing touching VRF; a new `DmxDocument`
becomes the only thing touching the DMX reader.

**Candidate library:** Datamodel.NET (Artfunkel) is the known C# binary-DMX
implementation. Not yet evaluated for binary 9 / net8. If it does not cover
v9, the format is small enough to implement directly, see section 2.

## 2. Binary 9 wire format, as actually observed

Confirmed by a parser that lands exactly on EOF. Order:

1. Header line, NUL-terminated.
2. `int32` prefix-element count (here `1`).
3. Per prefix element: `int32` attribute count, then attributes with
   **literal NUL-terminated names and literal string values** (no string
   table yet). Observed: `asset_preview_thumbnail` (binary, 51,781 B JPEG),
   `asset_preview_thumbnail_format` (`jpg`), `map_asset_references`
   (string array, 35 entries).
4. `int32` string-table count (here `1343`), then that many NUL-terminated
   strings.
5. `int32` element count (here `7071`), then per element:
   `int32` type-name index, `int32` name index, 16-byte GUID.
6. Element bodies in the same order: `int32` attribute count, then per
   attribute `int32` name index, `uint8` type, value.

**Type codes.** Scalars: 1 element-index(`int32`), 2 int, 3 float, 4 bool(u8),
5 string, 6 binary(`int32` length + bytes), 7 time, 8 colour(4 bytes),
9 vector2, 10 vector3, 11 vector4, 12 qangle(3 floats), 13 quaternion,
14 vmatrix, 15 uint64(8 bytes).

**Arrays are `scalar + 32`**, not `+15` as older DMX notes claim. Observed
live: 33 element-array, 34 int-array, 37 string-array, 41 vector2-array,
42 vector3-array, 43 vector4-array. An array is `int32` count then that many
values.

**Two traps that cost time here and will cost it again:**

- **Scalar strings in element bodies are string-table indices; strings inside
  an array are literal and NUL-terminated.** Same type code, two encodings.
- **Prefix-element strings are literal**, because they precede the table.

## 3. Element census (7,071 elements)

| count | type |
|---|---|
| 2482 | `CDmePolygonMeshDataStream` |
| 971 | `DmePlugList` |
| 969 | `EditGameClassProps` |
| 888 | `CDmePolygonMeshDataArray` |
| 598 | `CMapEntity` |
| 349 | `CMapPathNode` |
| 222 | `CMapMesh` |
| 222 | `CDmePolygonMesh` |
| 222 | `CDmePolygonMeshSubdivisionData` |
| 89 | `DmeConnectionData` |
| 24 | `CDmePolygonMeshSubdivisiondataBinding` |
| 21 | `CMapPath` |
| 2 each | `CMapSelectionSet`, `CMapInstance`, `CMapGroup` |
| 1 each | `CMapRootElement`, `CMapWorld`, `CMapVariableSet`, `CVisibilityMgr`, `CStoredCameras`, `CStoredCamera`, `CObjectSelectionSetDataElement`, `DmElement` |

`CMapMesh` and `CDmePolygonMesh` are 1:1 at 222 each. `CMapMesh` is the scene
node (transform + render flags); `CDmePolygonMesh` under its `meshData`
attribute is the geometry.

## 4. The geometry floor, read from the smallest mesh in the file

The smallest `CDmePolygonMesh` is **a single quad**: 4 vertices, 8 half-edges,
1 face. This is effectively the one-box fixture we wanted, already present.

```
vertexEdgeIndices      [0, 2, 4, 6]
vertexDataIndices      [0, 1, 2, 3]
edgeVertexIndices      [1, 0, 2, 1, 3, 2, 0, 3]
edgeOppositeIndices    [1, 0, 3, 2, 5, 4, 7, 6]
edgeNextIndices        [2, 7, 4, 1, 6, 3, 0, 5]
edgeFaceIndices        [0, -1, 0, -1, 0, -1, 0, -1]
edgeDataIndices        [0, 0, 1, 1, 2, 2, 3, 3]
edgeVertexDataIndices  [0, 1, 2, 3, 4, 5, 6, 7]
faceEdgeIndices        [6]
faceDataIndices        [0]
materials              ['materials/effects/cosmic_veil.vmat']
vertexData / faceVertexData / edgeData / faceData / subdivisionData -> elements
```

**Rules this reveals.**

- Half-edges are stored in **opposite-pairs at adjacent indices**: edge `2k`
  and `2k+1` are twins. `edgeOppositeIndices` is therefore always
  `[1,0,3,2,5,4,...]` and is derivable, not free-form.
- `edgeFaceIndices` uses **`-1` for the outer/void side**. A single quad has
  one real face and four boundary half-edges. A sealed box will have a real
  face on both sides of every edge and no `-1` at all.
- `edgeDataIndices` pairs twins to one shared edge record (`[0,0,1,1,2,2,3,3]`),
  while `edgeVertexDataIndices` is per half-edge (`[0..7]`). Two different
  granularities, easy to conflate.
- `faceEdgeIndices` stores **one** starting half-edge per face; the rest of the
  loop is recovered through `edgeNextIndices`. Face loops are implicit.

### Data streams, per mesh

`CDmePolygonMeshDataArray` has `size` (element count) and `streams`. Each
`CDmePolygonMeshDataStream` carries `semanticName`, `semanticIndex`,
`dataStateFlags`, and `data`.

| array | size | streams (semanticName, type) | flags |
|---|---|---|---|
| `vertexData` | 4 | `position` vec3-array | 3 |
| `edgeData` | 4 | `flags` int-array | 3 |
| `faceVertexData` | 8 | `texcoord` vec2, `normal` vec3, `tangent` vec4 | 1 |
| `faceData` | 1 | `textureScale` vec2, `textureAxisU` vec4, `textureAxisV` vec4, `materialindex` int, `flags` int, `lightmapScaleBias` int | 0,0,0,8,3,1 |
| `subdivisionData` | — | `subdivisionLevels` int-array (all zeros), `streams` empty | — |

Note the sizes: `vertexData` and `edgeData` are indexed **per edge-pair /
per vertex** (4), `faceVertexData` is **per half-edge** (8), `faceData` is
**per face** (1). `textureAxisU`/`V` are 4-vectors: axis plus offset, the
Source UV projection, not per-vertex UVs. UVs still also appear per half-edge
as `texcoord`.

**Nothing here is optional-looking.** Emitting a box means producing all of it
consistently. The subdivision element exists even when unused, with a
zero-filled `subdivisionLevels` sized to the half-edge count.

## 5. `CMapMesh` node fields

Transform is on the node, not the geometry: `origin` (vec3), `angles` (qangle),
`scales` (vec3). Plus `nodeID` (int), `referenceID` (uint64),
`physicsType` (`default`), `smoothingAngle` (40.0), `tintColor`, `renderAmt`
(255), `bakelighting`, `renderToCubemaps`, `emissiveLightingEnabled`,
`emissiveLightingBoost`, `fademindist` (-1.0), `fademaxdist` (0.0), and empty
`children` / `variableNames` / `variableTargetKeys` arrays.

**Emitter implication: geometry can be authored in local space at the origin
and placed by `origin`/`angles`.** A grid-derived box does not need world-space
vertices. That is a large simplification for a voxel front end.

## 6. Entities

`CMapEntity` holds transform plus `entity_properties` pointing at an
`EditGameClassProps` element, which is a flat **string-to-string** bag. Also
`relayPlugData` (a `DmePlugList`), `connectionsData`, `hitNormal`,
`isProceduralEntity`.

Observed `info_team_spawn`:

```
classname     info_team_spawn
targetname    (empty)
vscripts      (empty)
lanenum       1
initialspawn  0
teamnumber    3
```

Note `lanenum`, `initialspawn`, `teamnumber` are **strings**, not ints, even
though they are numeric. `EditGameClassProps` appears 969 times against 598
`CMapEntity`, so the type is shared with other holders.

### Deadlock entity vocabulary present in the file

`info_team_spawn`, `info_trooper_spawn`, `info_super_trooper_spawn`,
`info_neutral_trooper_camp`, `info_neutral_trooper_spawn`, `info_cover_point`,
`info_target_server_only`, `info_particle_system`,
`citadel_minimap_boundary`, `citadel_final_objective_proxy`,
`citadel_zipline_path`, `citadel_zipline_path_node`,
`citadel_trigger_push`, `citadel_trigger_climb_rope`,
`citadel_trigger_idol_return`, `citadel_trigger_speed_boost`,
`citadel_zap_trigger`, `citadel_item_powerup_spawner`,
`citadel_herotest_orbspawner`, `citadel_point_talker`,
`citadel_breakable_prop` and variants,
`npc_barrack_boss`, `npc_boss_tier2`, `npc_boss_tier2_weak`, `npc_boss_tier3`,
`func_nav_markup`, `func_regenerate`, `func_conditional_collidable`,
`logic_auto_citadel`, `logic_auto`, `logic_relay`,
`env_sky`, `light_environment`, `light_omni2`, `light_barn`, `light_style`,
`path_node_generic`.

## 7. Scale calibration

The single-quad mesh sits at `origin [-11916.0, 1101.5, 63.99976]`, a spawn at
`[-12478.5, 832.0, 64.009]`. Floor height reads as **z = 64** in both, and the
map spans five figures in X. Grid cell size for any voxel front end should be
chosen against these, not invented. `[?]` The usual Source unit is 1/16 ft;
not yet confirmed for Deadlock.

## 8. What this file still does not answer

`dl_example.vmap` is a **maximal** reference, not a floor. It contains bosses,
ziplines, breakables, powerups, full lighting and an embedded preview
thumbnail. It shows what is *available*. It does not show what a `.vmap` must
contain for Hammer to open it or `resourcecompiler` to accept it.

**The one-box question is still open**, and it is the one that scopes the
emitter. The geometry floor in section 4 is a real answer for a *mesh*; the
document floor (which of `CMapRootElement`, `CMapWorld`, `CVisibilityMgr`,
`CMapVariableSet`, `CStoredCameras`, `CObjectSelectionSetDataElement` are
mandatory) is not.

## 9. Next, in order

1. **`dl map info` reads DMX source**, not compiled `.vmap_c`. Cheaper, and we
   have a real fixture. Report element census, entity classnames, mesh count,
   world bounds.
2. **Round-trip before emit.** Parse and reserialise `dl_example.vmap` and
   diff. The vdata layer earned its confidence this way (35,443 paths); do the
   same here. State the floor first: assert element count > 7000, per lesson 5.
3. **Then the probe that gates everything:** does `resourcecompiler` build a
   `.vmap` headlessly on `windows-latest`? Map source at
   `content/citadel_addons/<name>/`.
4. **Only then the emitter**, box-at-a-time, local space, placed by
   `origin`/`angles`.

## 10. Process note

The Python probe was written against the real bytes and reached EOF exactly.
Three wrong assumptions died in the first ten minutes: KV3 (it is DMX), array
base 15 (it is 32), and uniform string encoding (indices in bodies, literals in
arrays and the prefix). Lesson 4 again, and cheaply this time.
