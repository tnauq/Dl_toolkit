# Probe: the classnames still missing

Everything below is blocked on a string that has to be read off the shipped
build. Nothing here is guessed into the plan, and nothing should be: a wrong
classname converts, packs and loads while doing nothing, which is the worst
failure mode available — it looks like it worked.

Two of the six things on the last list turned out to be answered already, by
reading batch13 rather than the game. Check this file's "already known"
section before probing anything.

---

## Already known — do not probe these

| what | classname | where it came from |
|---|---|---|
| jump pad / air vent | `trigger_catapult` | batch13, read from dl_example |
| climbing rope | `citadel_trigger_climb_rope` | batch13, read from dl_example |
| midboss shield | `trigger_midboss_shield` | batch13, read from dl_example |
| powerup spawner | `citadel_item_powerup_spawner` | batch13, read from dl_example |
| directional push (fan) | `citadel_trigger_push` | batch13, read from dl_example |

**The jump pad is the thing described as an air vent.** `trigger_catapult`
takes a `target` naming a landing marker entity, plus `launch_speed`. Two
pads and their markers are now placed from readings, `catapult_a` and
`catapult_b`, with twins.

Two caveats remain, neither of them a classname probe:

- `trigger_catapult` is what dl_example uses. If the shipped vents are
  something else — a push volume aimed up, say — this is the wrong entity.
  Worth confirming against a shipped map.
- `launch_speed` is invented at 800, batch13's placeholder value. It is NOT
  derived from the distance to the marker, and the two pads throw 1939 u and
  1827 u. Whether 800 covers that is a question for the game, not the plan.
  If the pad undershoots, this is the number to change.

---

## Still unknown — the actual probe list

Ordered by what blocks the most work.

### 1. Teleporter
Blocks: 2 entities, positions already read and sitting in batch16 behind
`EMIT_UNKNOWN`. Two rooms are already built for them.
Search for: `teleport` as a substring of any classname; also `warp`, `portal`.
Expect a pair — an entrance and a destination, or one entity with a `target`
pointing at a marker, the way `trigger_catapult` does. Note which, because
the destination marker needs authoring too.

### 2. Sinner's Sacrifice
Blocks: 4 entities, positions already read and held in batch16.
Search for: `sinner`, `sacrifice`, `soul`, `idol`. May well not be an entity
at all — it could be a `citadel_breakable_prop` or similar with a specific
model and a keyvalue for the soul payout, in which case the model path
matters as much as the classname.

### 3. The midboss NPC
Blocks: the boss itself. Its shield volume is already placed in the hexagon
room, so this is the last piece of that fight.
Search for: `npc_` prefixed names near the ones batch13 already uses
(`npc_boss_tier2`, `npc_boss_tier3`, `npc_barrack_boss`). Also `midboss`,
`rejuv`, `patron`.
Wanted alongside the classname: the keyvalues. The tier bosses in batch13
carry `BossName`, `lanenum`, `teamnumber`, `CoverGroupID` and a set of
`*_cover_id` keys. A neutral midboss presumably drops the team and lane keys,
but that is an assumption, not a reading.

### 4. Camp tiers
Blocks: nothing — the camps are placed and working — but 16 of the 19 carry a
guessed `subclass_name`.
Confirmed: `neutral_camp_weak`, on the camp batch13 already had.
Guessed: `neutral_camp_normal`, `neutral_camp_strong`.
Also guessed: `ENeutralTrooperType` of `1`, `2`, `3` per tier. The weak camp's
real value is `1`; whether the family is 1/2/3 or something else entirely is
unread.
Search for: `neutral_camp` as a substring — the whole family should appear
together, which also settles the tier count.

### 5. The lid, and the crystal drop
Blocks: the whole midboss-over-the-hole idea.

Two separate unknowns, and the second is the harder one:

**a. A toggleable brush.** Something that is solid, covers the square hole,
and can be switched off. Search for: `func_brush`, `func_wall_toggle`, or
whatever Deadlock's equivalent is. A `destroyable_building` is probably NOT
it — that has a model and no children, per batch13's note, so it is a prop
that changes state rather than a piece of collision that goes away.

**b. What the midboss fires when it dies.** Search the shipped map's entity
outputs for anything on the boss or on a `destroyable_building`: `OnDestroyed`,
`OnKilled`, `OnDeath`, `OnBreak`. The shrine geometry change you remembered is
the precedent worth chasing — find the shrine in a shipped map and read what
its death output is wired to. If it targets a brush entity, that is the whole
mechanism and it transfers directly.

**If (b) comes back empty**, the fallback is worth knowing: if the dropped
crystal is a physics prop, no lid is needed at all — spawn the boss centred on
the hole and it falls on its own. The lid only exists to stop the *boss* from
falling through before it dies. So the question to answer first is actually
whether the boss's own collision would drop through a 266.7 square hole, which
is a test, not a probe: place the boss over the hole with no lid and watch.

---

## What to search

The rift was found by scanning shipped strings, so the same route applies.
For each item above the search is a substring match over the string table —
the classnames all follow visible conventions (`citadel_trigger_*`,
`trigger_*`, `npc_*`, `info_*`), so a scan for those four prefixes dumped to
an artifact would probably answer items 1 through 4 in one pass, and is
cheaper than four targeted scans.

Item 5b is different: it needs entity *outputs* from a real map, not the
string table, so it is a separate job and probably a separate tool.

## What to record

For each hit, the same three things the working entities have:

1. the exact classname string
2. its keyvalues, with the ones that are required and the ones that default
3. whether it is a point entity or a brush volume — batch13 emits those
   differently, brushes carrying their extents on a child mesh, and getting
   this wrong produces an entity with no size

Anything read this way should say so in the file that uses it, with the date,
the same way batch13's READ / DERIVED / INVENTED block does. The value of that
block is that six weeks from now nobody has to re-derive which numbers were
measured and which were made up.
