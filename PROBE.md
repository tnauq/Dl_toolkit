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

### 1. Teleporter — not reachable from CI

Absent from dl_example, and the binary scan is worthless for this: the CS2
binaries contain no Deadlock entity strings at all. `citadel_` matched two
generic tokens, and `catapult` and `climb_rope` — both of which we KNOW are
real — matched nothing. So source B answers nothing about Deadlock, and a
negative there means nothing either way.

This one needs a desktop install, or a shipped map to survey.

Original note:
Blocks: 2 entities, positions already read and sitting in batch16 behind
`EMIT_UNKNOWN`. Two rooms are already built for them.
Search for: `teleport` as a substring of any classname; also `warp`, `portal`.
Expect a pair — an entrance and a destination, or one entity with a `target`
pointing at a marker, the way `trigger_catapult` does. Note which, because
the destination marker needs authoring too.

### 2. Sinner's Sacrifice — not reachable from CI, same reason as item 1

Worth noting `citadel_breakable_prop` takes a `subclass_name` (dl_example
uses `citadel_breakable_wooden_crate_03`), so if the sinner is a breakable
the answer may be a subclass string rather than a classname.

Original note:
Blocks: 4 entities, positions already read and held in batch16.
Search for: `sinner`, `sacrifice`, `soul`, `idol`. May well not be an entity
at all — it could be a `citadel_breakable_prop` or similar with a specific
model and a keyvalue for the soul payout, in which case the model path
matters as much as the classname.

### 3. The midboss NPC — ANSWERED 2026-08-26, and it is not an npc

There is no `npc_` classname for the midboss. IT IS A CAMP:

    info_neutral_trooper_camp
      subclass_name                neutral_camp_midboss
      ENeutralTrooperType          5
      CampName                     mid_boss_neutral
      InitialSpawnDelayInSeconds   -1
      SpawnIntervalInSeconds       -1

with one `info_neutral_trooper_spawn` carrying `teamnumber 4`,
`HateCrateAttacker 1` and a `CoverGroupID`. The -1 timings say it does not
respawn on a clock, which is the behaviour you would want and is a reading,
not an inference.

Placed in batch16 at the hexagon centre, standing over the hole.

### 4. Camp tiers — PARTLY ANSWERED

`neutral_camp_midboss` at type 5 is confirmed, which shows the family is
`neutral_camp_*` and that types run at least to 5. The 11 camps in the
fixture will name the rest, but the first probe run reported key NAMES and
not key VALUES, so the artifact says every camp has a `subclass_name`
without saying what they are. Fixed in the workflow; rerun answers it.

Original note:
Blocks: nothing — the camps are placed and working — but 16 of the 19 carry a
guessed `subclass_name`.
Confirmed: `neutral_camp_weak`, on the camp batch13 already had.
Guessed: `neutral_camp_normal`, `neutral_camp_strong`.
Also guessed: `ENeutralTrooperType` of `1`, `2`, `3` per tier. The weak camp's
real value is `1`; whether the family is 1/2/3 or something else entirely is
unread.
Search for: `neutral_camp` as a substring — the whole family should appear
together, which also settles the tier count.

### 5. The lid, and the crystal drop — a candidate, from the same run

`func_conditional_collidable` exists in the fixture, with `interactas` and
`interactwith` keys — dl_example sets `interactas` to
`blocklos, Citadel_Obscured`. That is collision that applies conditionally,
which is the shape the lid wants. It is a CANDIDATE, not an answer: nothing
yet says it can be toggled at runtime or what the condition list may contain.

`logic_relay` is also present with 10 instances, so the wiring half of the
mechanism exists.

The outputs question is still open, and for the same reason as item 4: the
first run could not see connections at all, because they do not live in
EditGameClassProps. The workflow now dumps every DmeConnectionData block
verbatim, so the rerun says what dl_example's `destroyable_building` fires
when it dies.
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

## The workflow that answers this

`.github/workflows/classname-probe.yml`, run by hand. It takes no needle list
on purpose - a search term cannot find a name nobody has thought of, which is
the failure mode for items 1, 2 and 5a. It pulls two things whole:

- every classname in `dl_example.vmap`, with its real keyvalues and how many
  instances set each one, plus one verbatim entity per classname
- every identifier-shaped token in every CSDK binary, grouped by prefix, with
  a histogram of EVERY prefix so an unfamiliar family is visible by reading
  down it

The fixture answers with certainty but only about what the gym map contains.
The binaries answer broadly but they are CS2's, not Deadlock's, so a hit
there is a lead and not a fact. If both are silent on an item, that is itself
the finding: the string is not reachable from CI and the answer has to come
off a desktop install.

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
