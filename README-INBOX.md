# Inbox drop — probe fix, base.fgd, postprocessing.fgd (2026-08-29)

    .github/workflows/connection-owner-probe.yml   REPLACES the broken version
    docs/reference/citadel/base.fgd                NEW (414 KB)
    docs/reference/citadel/postprocessing.fgd      NEW
    docs/NIGHT-MODE.md                             NEW

## The probe run found 0 connections. Here is why, and it is fixed

The conversion worked — 51 MB of keyvalues2, exit 0, and `structure.md`
counted **89 lines mentioning DmeConnectionData**. The parser then reported
**0 connection elements** and exited green.

The cause is visible in `structure.md`'s verbatim dump, which is the one part
of the run that did its job. Element headers in this file are **quoted**, and
there are two forms:

    "connectionsData" "element_array"
    [
        "DmeConnectionData"          <- type alone, inside an array
        {

    "relayPlugData" "DmePlugList"    <- key + type, under a key
    {

The parser expected BARE type names, so `"DmeConnectionData"` fell through to
the array-reference branch and every connection was filed as a reference to
an id that does not exist. Nothing crashed. It just reported zero.

A quoted line is a header only if the next non-blank line opens a brace, so
the fix is a **lookahead**, not a tighter regex — the distinction cannot be
made from the line alone.

**And a guard.** The run compared nothing against nothing: 89 mentions and 0
elements were both printed, in different files, and never compared. They are
compared now, and a mismatch is a hard error. A total parse failure will
never again look like a clean result.

I tested the new parser against the exact syntax from your run — nested
connections inside `connectionsData`, `DmePlugList` under a key,
`EditGameClassProps` siblings — and it attributes owners and resolves target
classnames correctly.

Worth noting the connections turn out to be **nested inside their owners**,
not referenced by id. So the containment method is the one that will answer,
and the id method will report 0 — that is expected, not a second failure.
The `keyvalues2` conversion is still what made this legible.

## base.fgd answers three things outright

- **`Kill` is on the `GameEntity` base class.** Every entity answers it.
  That is why it appears in twelve fixture connections and nowhere in
  citadel.fgd, and it means the lid mechanism is sound in principle.
- **`logic_relay` confirmed**: `Trigger`, `Toggle`, `CancelPending` in;
  `OnSpawn`, `OnTrigger` out. `logic_timer` and `logic_auto` are there too.
- **`env_fog_controller` has a lerp system** — `SetColorLerpTo`,
  `SetEndDistLerpTo`, `SetMaxDensityLerpTo`, then `StartFogTransition`. Fog
  is where the night mode should live, because it is the only part that can
  transition rather than snap.

`postprocessing.fgd` adds `post_processing_volume`, with `master` for an
unbounded volume and `fadetime` for a smooth swap.

**`env_sky` has no inputs**, so the sky cannot change at runtime. Night has
to come from fog, sun and post-processing under a fixed sky. Incidentally it
confirms `skyname` is the right key, which is what batch16 already emits.

See `docs/NIGHT-MODE.md`, which supersedes the lighting half of
`docs/LID-DOORS-LIGHTING.md`.
