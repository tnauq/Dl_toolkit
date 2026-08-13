# FINDINGS — maps, 2026-08-13

Established by inspecting a real published Deadlock map mod from GameBanana
(`pak01_dir.vpk`, 107 MB, 71 entries, map name `deadrun`). Inspected locally
only — **the map is another modder's work and was never committed**. Per the
project's existing practice with GameTracking: ship derived facts, not files.

Everything here is `[V]` — read out of a shipping artifact — unless marked.

---

## 1. Addon VPK entry paths — CONFIRMED, was `[I]`

`dl pack` keys entries relative to the pack root, forward-slashed, with no
`citadel/` prefix. That was inferred from how `gameinfo.gi` mounts `citadel`
and marked `[I]` in `PackCommand`. **A real shipping addon does exactly this:**

```
README.txt
maps/deadrun.vpk
soundevents/soundevents_from_tools.vsndevts_c
maps/materials/bricks.vmat_c
maps/models/door/doorwhite.vmdl_c
maps/sounds/kidcheer.vsnd_c
```

Relative, forward-slashed, rooted at the game directory. **Promote the note in
`PackCommand.CreateFromDirectory` from `[I]` to `[V]`, and `--prefix` is
confirmed unnecessary for the default case.**

Also confirmed: everything sits at `ArchiveIndex 32767`, i.e. inline in the
dir file, matching what `format-smoke` established for our own writes.

---

## 2. A map ships as a NESTED VPK — the biggest structural finding

A map is **not** loose `.vmap_c` files in the addon. The addon contains a
second, complete VPK:

```
maps/deadrun.vpk        8,547,961 bytes    <- a whole VPK inside the addon
```

Inside that nested VPK, 70 entries:

| entry | bytes | what it is |
|---|---|---|
| `maps/deadrun.vmap_c` | 7,760 | **a stub — see below** |
| `maps/deadrun/world.vwrld_c` | 2,065 | world definition |
| `maps/deadrun/world_visibility.vvis_c` | 4,496,894 | visibility, the largest single file |
| `maps/deadrun/world_physics.vmdl_c` | 41,572 | collision |
| `maps/deadrun/entities/default_ents.vents_c` | 11,802 | the entity lump |
| `maps/deadrun/worldnodes/n0_lr0_*.vmdl_c` | 5-48 KB | baked geometry per node |
| `maps/deadrun/lightmaps/*.vtex_c` | 0.5-1 MB each | **baked lighting, six channels** |
| `maps/deadrun/entities/<name>_<id>.vmdl_c` | ~6 KB each | per-entity meshes |

Consequences for the maps track:

- Producing a loadable map means producing **this whole tree**, then packing it
  into a nested VPK, then packing that into an addon. `dl pack` handles the
  outer step and, unchanged, the inner one too — it packs a directory, and this
  is a directory.
- **Baked lighting is present and worked for this modder.** FINDINGS lists
  compiled lighting as a reported pain point; here are six lightmap channels
  in a shipping community map, so it is not a blocker in practice.
- `world_visibility.vvis_c` is 4.5 MB of the 8.5 MB map. Vis is the expensive
  part of a compile, which is worth knowing before timing a CI map build.

---

## 3. There is NO source `.vmap` in a published map — Q7 answered

`maps/deadrun.vmap_c` is 7,760 bytes and its block table is:

```
RERL  5,028 bytes   (external resource references)
RED2  2,663 bytes   (editor/source metadata)
DATA      0 bytes   <- EMPTY
```

The `DATA` block is **empty**. The `.vmap_c` is a stub that references the
compiled children; it carries no geometry and no recoverable source.

**Therefore a published map cannot be turned back into an editable `.vmap`
from the addon alone.** Decompiling would mean reconstructing source geometry
from `worldnodes/*.vmdl_c`, which is a different and much larger problem.

Consequence for the plan: the parametric emitter (Phase 3b) is not optional
convenience, it is **the only route to map source we control**. We cannot start
from someone else's map and edit it.

---

## 4. Map source lives at `content/citadel_addons/<name>/` — `[V]`

RED2 retains the compile-time input dependencies, including:

```
m_RelativeFilename  lightmaptexturearg.txt
m_SearchPath        citadel_addons/deadrun
```

So the content root for a map addon is `content/citadel_addons/<mapname>/`,
**not** `content/citadel/` where vdata lives. The original `probe-compiler`
draft used `content/citadel_addons/probe/` and that was changed to
`content/citadel/` for the vdata probe — correct for vdata, and the map probe
must change it back.

RED2 also lists the compiler's own parameter vocabulary — `bakedlighting`,
`visgeo`, `dumptris`, `noProbeVolumes`, `skipauxfiles`, `vrad3LargeBlockSize`,
`MaxResolution`, `hueShiftFixup`, `keep_vertices`, `ChartPackIterations` and
others. That is a map-compile flag surface to read properly before designing a
build step.

---

## 5. Compiled resources are compressed KV3 with a string table — `[I]`

Naive byte scanning of `.vents_c` returns fragments (`m_childLumps`,
`steamaudio_customdata_occlu'`, `height_above_floor)`, `[PR#]deadrun`) with
strings running together and truncating. That is the signature of a
dictionary-compressed KV3 payload, not plain text.

**Do not hand-parse compiled resources.** Route them through VRF, which is what
`Kv3Document` already wraps. Whether `Kv3Document.Load` opens a `.vents_c` or
`.vwrld_c` as-is remains **unprobed** — it has only ever been pointed at
uncompiled source vdata (Q9, still open).

---

## 6. Map assets sit BESIDE the map, not inside it

Materials, models and sounds used by the map are in the **outer** addon under
`maps/materials/`, `maps/models/`, `maps/sounds/` — not inside the nested map
VPK. Texture entries carry a content hash in the name:

```
maps/materials/red_brick_diff_2k_png_12b13c82.vtex_c
maps/models/door/doorwhite_vmat_g_tambientocclusion_9782fd5c.vtex_c
```

The `_<hash>` suffix is compiler-generated, so asset filenames in an addon are
not stable across recompiles — **never hardcode one**.

This map also ships obviously borrowed art (a `maxresdefault (2).jpg`, a
profile image) which compiled fine, confirming the art bar for a working map is
"any texture at all".

---

## What this changes in the plan

1. **`dl pack` needs no change** for maps. Packing a directory into a VPK is
   the operation at both levels.
2. **The emitter is on the critical path**, not a nice-to-have — there is no
   route from a published map back to editable source (§3).
3. **The map compile probe must use `content/citadel_addons/<name>/`** (§4).
4. **Q9 is still open** and is now the next cheap probe: can VRF read a
   compiled `.vents_c` / `.vwrld_c`? That decides whether map *reading* tools
   reuse the vdata layer.
5. **Baked lighting is not a blocker** (§2), contradicting the caution in
   FINDINGS. Downgrade that warning.
