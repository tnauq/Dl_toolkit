# Inbox drop — probe fix #2, and the night mode as a snap (2026-08-29)

    .github/workflows/connection-owner-probe.yml   REPLACES the previous version
    docs/NIGHT-MODE.md                             REPLACES the version in drop e

## Run 2 attributed all 89 — to the same entity. That was a bug.

`point_worldtext` firing `OnDestroyed -> Kill` twelve times is not a finding.
Ninety-nine percent of a 2.3M-line map cannot be owned by one point entity.

**The cause: brackets are not braces.** The parser popped the element stack
on `]` as well as `}`, but only ever pushed on `{`. Every array in the file
popped an element that was never pushed, the tree collapsed, and all 89
connections inherited whatever classname was left on the stack.

Fixed with a frame stack: each opener records whether it was an element `{`
or an array `[`, and only an element's closer pops the element stack.

**And a second guard.** If more than ten connections resolve to a single
distinct owner, that is now a hard error rather than a report. Run 2's
signature will never again be printed as a result. That is two guards from
two failures: one for zero parsed, one for all-identical.

## What run 2 got right, and it is a lot

`targets.md` resolves target classnames independently of ownership, and much
of it survived the bug:

- `*_shop_kill_relay` -> **`logic_relay`**, confirming relays are the fan-out
  pattern the fixture actually uses.
- `*_shop_item_trigger` -> `trigger_item_shop`, taking `Enable`, `Disable`
  and `Kill`.
- **The grate and ladder brushes resolved to nothing.** Six of them per team,
  all targets of `OnDestroyed -> Kill`. Either they are named on an element
  the collapsed tree hid, or they carry their targetname somewhere this probe
  does not look. The rerun will say which - and that is still the lid answer.

And the connection census is trustworthy even with owners wrong, because it
reads the blocks themselves:

    OnDestroyed -> Kill              x12    the lid mechanism
    OnTrooperKilled -> Trigger       x9     camps drive relays
    FinalShielded -> Trigger         x2
    FinalExposed -> Trigger          x2
    SubObjective1Destroyed -> StopPlayEndCap   x2
    SubObjective1Revitilized -> Start          x2
    SubObjective2Destroyed / Revitilized       x2 each

**Read those last six lines.** `FinalShielded`, `FinalExposed`,
`SubObjectiveNDestroyed` and `SubObjectiveNRevitilized` are outputs declared
on exactly one class: `citadel_final_objective_proxy` — the class citadel.fgd
marks *"Unused. Do not use."* **dl_example wires it anyway**, and only slots 1
and 2, exactly as the four-lane-artifact reading predicted.

That is a strong argument to put `EMIT_PROXY` back to `True`. The FGD
annotation is a mapper's note, and the shipped map disagrees with it. Worth
deciding once the rerun confirms which entity owns those wires — if it is the
proxy, the shrine→patron chain comes back and the §13 dead end closes.

## Night mode: snap confirmed

`docs/NIGHT-MODE.md` rewritten for an instant transition timed to the midboss
death sound. Two practical notes:

- `post_processing_volume.fadetime` defaults to **1.0** and must be set to
  **0**, or the post-processing will fade over a second while the fog and sun
  cut instantly.
- The lerp inputs on `env_fog_controller` are documented as the deliberate
  fallback rather than deleted, so switching to a fade later is a change of
  inputs and not of structure.

The fixture supports the wiring directly: `OnTrooperKilled -> <relay> .
Trigger` nine times over. A camp driving a relay is what dl_example does.
