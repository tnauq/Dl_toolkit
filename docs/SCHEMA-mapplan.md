# SCHEMA — `.mapplan.json`

The source of truth for a layout. Settled 2026-08-14.

The `.vmap` is a **regenerated build artifact**, not an editing surface. This
file is what a human, an agent, or the HTML viewer reads and writes.

**It goes stale by design.** The day Hammer opens an exported map on the
Windows machine, Hammer becomes the source and this file stops being
authoritative. That is the plan, not a problem to fix later.

Example: `examples/sealed-room.mapplan.json`.

---

## Top level

| key | type | notes |
|---|---|---|
| `version` | int | Schema version. Bump on breaking changes. Currently `1`. |
| `name` | string | Becomes the addon/map name on export. |
| `cell` | number | Grid spacing in Source units. Default `64`. |
| `boxes` | array | Axis-aligned solids. |
| `entities` | array | Point entities. |

**On `cell`.** 64 is the working assumption, taken from the floor height read
off `dl_example.vmap` — both a mesh origin and a spawn sit at z=64. It is
marked `[?]` in FINDINGS, not `[V]`. If it turns out wrong, every layout
authored before the correction needs a rescale, so it is worth confirming
early.

The grid **guides, it does not constrain**: origins are expected on the grid,
extents are free. A hard grid would fight ramps, ledges and diagonals, and
Deadlock is a verticality game.

## `boxes[]`

| key | type | notes |
|---|---|---|
| `name` | string? | Optional, for your own reference. |
| `origin` | `[x, y, z]` | **Centre** of the box. Expected to be a multiple of `cell`. |
| `extents` | `[x, y, z]` | **Full size** along each axis, not half-size. Free. |
| `angles` | `[p, y, r]` | Usually all zero for a blockout. |
| `material` | string | Defaults to a dev material. |

**Why centre-and-size rather than min-and-max.** `CMapMesh` carries `origin`,
`angles` and `scales`; `CDmePolygonMesh` carries only local geometry. So a box
is emitted as local-space vertices around zero, placed by the node transform.
A grid-derived box never needs world-space vertices, and rotation is free.

## `entities[]`

| key | type | notes |
|---|---|---|
| `classname` | string | e.g. `info_team_spawn`. |
| `origin` | `[x, y, z]` | |
| `angles` | `[p, y, r]` | |
| `properties` | object | **string to string**. |

`properties` is a flat string-to-string bag because that is exactly what
`EditGameClassProps` is in the file. Numeric-looking keys are stored as
strings there too — `lanenum`, `teamnumber` and `initialspawn` are all
`"1"`, not `1`. Write them as strings.

Classnames confirmed present in the fixture include `info_team_spawn`,
`info_trooper_spawn`, `info_super_trooper_spawn`, `info_neutral_trooper_camp`,
`info_cover_point`, `citadel_minimap_boundary`, `citadel_zipline_path`,
`citadel_trigger_push`, `npc_boss_tier2`, `npc_barrack_boss`,
`logic_auto_citadel`, `env_sky`, `light_environment`.

## Deliberately absent

Lighting, ziplines, bosses, paths, groups, selection sets, entity connections,
stored cameras, preview thumbnails.

Not an oversight, and not a backlog. Every one of them introduces **shared
elements**, and the emitter's whole simplification rests on nothing in its
scope being shared: `keyvalues2_noids` keeps element ids only where an element
is referenced more than once, so a plan containing only boxes and point
entities emits with **no GUIDs at all**.

Adding any of them means reintroducing id generation. Weigh that before
extending the schema, and if it has to happen, do it once and deliberately.

## Round trip

CI asserts that a plan exported to `.vmap` reads back to the same box list.
A green export is not a correct export.
