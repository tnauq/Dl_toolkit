# Inbox drop — prefab-probe run 2 (2026-08-30)

    .github/workflows/prefab-probe.yml   MODIFIED

## Run 1 answered the structural question, in the negative

    Paths that look like maps or prefabs (0)
    CMapInstance x2, CMapGroup x2
    125_ x22   2399_ x4   1456_ x3   2150_ x2

**Zero external prefab paths.** So the instances are EMBEDDED, not file
references — there is no second file to fetch, and nothing is hiding in the
game vpk. The grate and ladder entities have been inside `dl_example.vmap`
the whole time.

**And the prefix theory is confirmed outright.** Four instances, four numeric
prefixes, `125_` twenty-two times. A connection says
`125_rebels_titan_yellow`; the entity inside the instance is named
`rebels_titan_yellow`, with the prefix stamped on at instance time. Matching
a decorated name against an undecorated one fails every time — that is the
entire reason twelve targets came back unresolved, and it was never a missing
file.

That also retires the worry in the last handoff that the lid's class could
only come from the depot pull. It cannot be far away.

## What run 2 does instead

The file-fetching steps are kept but demoted; the new step does a **full
targetname census** — every `CMapEntity` in the file, by targetname and
classname, matched crudely by regex rather than by tree walk, because pairs
are all this needs. Plus:

- `out/census.md` — every targetname in the file, with the grate/ladder/lid
  rows pulled to the top. **That table is the lid answer.**
- `out/instances.md` — the two `CMapInstance` elements verbatim, since what
  an embedded instance points at is the one thing run 1 could not show.

## If the census comes back empty

The step says so explicitly rather than shrugging. An empty grate/ladder
table would mean those names are not entity targetnames at all — they would
be group names, mesh names, or instance-local names the text form does not
carry — and `out/instances.md` becomes the thing to read. That is a real
possible outcome and it is worth knowing which of the two it is.

`func_brush` stands either way: `base.fgd` puts `Kill` on the `GameEntity`
base, so the mechanism works regardless of what Valve chose.

## Unrelated, from the batch log

The run is consistent: boxes 4745, entities 384, connections 56, and batch16
reports `final_objective_proxy EMITTED`. The earlier `emit.txt` showing
4746/391 was from a stale run — the numbers in this one are the ones to pin.

One line in batch15 is now misleading: *"shrine upgrades: none. No shrines in
the plan yet."* There are four shrines; batch15 simply runs before batch16
creates them. Harmless, but it reads like a missing feature. Worth a comment
fix in the next cleanup pass rather than a drop of its own.
