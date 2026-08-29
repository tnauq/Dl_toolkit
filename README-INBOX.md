# Inbox drop — the proxy goes back on (2026-08-29)

    batch16.py                                  MODIFIED - EMIT_PROXY = True
    docs/FINDINGS-connections-2026-08-29.md     NEW

The third probe run worked: 89 of 89 attributed, no disagreements, owners
varied and plausible.

## The headline: §13 was wrong, and the fixture says so

`citadel_final_objective_proxy` carries **sixteen** connections in
dl_example, despite citadel.fgd marking it "Unused. Do not use."

And two of them are `FinalShielded -> Trigger` and `FinalExposed ->
Trigger` — **the proxy's own outputs**. The proxy computes the shielding from
its sub-objectives and announces it. That is why `npc_boss_tier3` has no
input: nothing has to tell the patron it is exposed.

So the dead end in `FINDINGS-fgd-2026-08-29` §13 was an artifact of assuming
the chain had to be hand-wired. It doesn't. `EMIT_PROXY` is back to `True`
with the evidence recorded in the code, and the map has its win condition
again.

Only slots 1 and 2 are used, and the sub-objectives are named **left and
right** rather than by lane — which is the shape `PROXY_SUBS = ["w", "e"]`
with lane 0 already has.

## The lid: mechanism confirmed, class unavailable

Twelve `OnDestroyed -> Kill`, owned by `destroyable_building`, three per
shrine: a grate prop, a grate brush, a ladder brush.

All twelve targets are **unresolved**, and this time that is a finding rather
than a bug — other targets resolved fine. Every unresolved name carries a
`125_` prefix or is a grate/ladder, which is the signature of **prefab-scoped
entities**. They are not in dl_example.vmap, so the lid's brush class cannot
be read from it.

`base.fgd` settles the mechanism anyway: `Kill` is on the `GameEntity` base,
so every entity answers it. The brush class is now a choice — `func_brush` is
the obvious one — rather than something to copy.

## A correction that needs your call

The nine guardian-closes-the-shop connections are owned by
**`info_super_trooper_spawn`** firing `OnTrooperKilled`, not by a boss NPC
firing `OnBossKilled`. citadel.fgd is explicit that this class is what places
a lane guardian, via a `BossName` like `boss_rebel_t1_yellow`.

That makes two things wrong at once:

- `batch15.GUARDIAN_OUTPUT = "OnBossKilled"` should be `"OnTrooperKilled"`.
- Our guardians are `npc_boss_tier1`, a class that is **in neither
  citadel.fgd nor the fixture census** (17 `info_super_trooper_spawn`, zero
  `npc_boss_tier1`).

They have to change together — a wrong output on a right entity and a right
output on a wrong entity both fail silently — and the entity change is
batch13's, not batch16's. Not made here. See §3 of the findings.
