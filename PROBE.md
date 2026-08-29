# Probe: the classnames still missing

Everything below is blocked on a string that has to be read off the shipped
build. Nothing here is guessed into the plan, and nothing should be: a wrong
classname converts, packs and loads while doing nothing, which is the worst
failure mode available — it looks like it worked.

Two of the six things on the last list turned out to be answered already, by
reading batch13 rather than the game. Check this file's "already known"
section before probing anything.

---

## THE OBJECTIVE CHAIN — ANSWERED 2026-08-26

Settled by reading connection ownership correctly at the fourth attempt. An
entity lists its connections BEFORE its own properties, so the owner is the
NEXT classname in the file. Two earlier models looked backwards and were
confidently wrong; the first was believed for a while, which is the real cost.

    npc_boss_tier3                  fires OnBossKilled     <- GUARDIAN
    destroyable_building            fires OnDestroyed
    info_super_trooper_spawn        fires OnTrooperKilled
    logic_relay                     fires OnTrigger
    citadel_final_objective_proxy   fires FinalShielded, FinalExposed,
                                          SubObjective1/2 Destroyed and
                                          Revitilized

So the patron outputs belong to `citadel_final_objective_proxy` — a class
that was in the census from the first run and that I mapped to nothing. YOUR
2026-08-23 CALL STANDS: npc_boss_tier3 is the lane objective, and my case for
reversing it was wrong.

The proxy is wiring, not a body. It names its bodies in keyvalues:

    final_objective          125_rebels_building_final      the PATRON
    sub_objective_1..4       125_rebels_titan_<colour>      the TITANS
    sub_objective_lane_1..4  1, 3, 4, 6
    teamnumber               2 / 3

which answers the legend outright:

    Patron      a destroyable_building, the one named *_building_final
    Titan       four per team, one per lane, *_titan_<colour>
    Base Guard  npc_barrack_boss, most likely - not yet confirmed by output

TITAN IS NOT THE MIDBOSS. It is a per-lane objective between the walker and
the base. The midboss is the Rejuvenator, already placed.

WHAT THIS NEEDS FROM YOU: positions. A patron per team, four titans per team
(one per lane, so three on this map), and the base guards you mentioned
having. The proxy itself needs no reading — it is a logic entity that can sit
anywhere, and its links are keyvalues rather than connections, so unlike the
lid it CAN be expressed in the plan today.

## ANSWERED 2026-08-27 by npc_units.vdata

The file settles the objective chain outright. Model paths and health values,
read not inferred:

    npc_boss_tier1   boss_tier_01_brazier_guardian.vmdl   5500      GUARDIAN
    npc_boss_tier2   boss_tier_02_sun_walker.vmdl    6000/9000/12000  WALKER
    npc_boss_tier3   patron_amber.vmdl               12000 + phase2   PATRON
    destroyable_building   shrine_amber / shrine_sapphire            SHRINE
                     generator 5000, second 10000, final 8775
    neutral_sinners_sacrifice
                     props_gameplay/sinners_sacrifice_vault/...  500  SINNER
    npc_super_neutral      midboss.vmdl                             MIDBOSS

Consequences, in order of size:

1. THE PATRON IS npc_boss_tier3, with two phases, a transform sound and
   phase-1/phase-2 lasers. batch16 now emits it as that instead of a
   destroyable_building. My earlier case was right and the 2026-08-23 call
   was wrong.

2. batch13 THEREFORE PLACES SIX PATRONS where it means lane guardians. The
   lane guardian is npc_boss_tier1. That is one line in batch13's table, but
   it ripples into batch15's shop wiring, which fires off the guardian's
   OnBossKilled - so it wants doing deliberately, not folded into a drop
   about something else. NOT YET CHANGED.

3. The walker was right all along.

4. The shrine model is shrine_amber / shrine_sapphire, not the generator
   placeholder, and 5000 health matches m_iMaxHealthGenerator exactly - the
   wiki number was correct and dl_example's 8000 was not the relevant one.

5. THE SINNER'S MODEL PATH CONTAINS "vault":
   props_gameplay/sinners_sacrifice_vault/sinners_sacrifice.vmdl. That is
   independent support for your sinner = vault camp read, from a direction
   nobody was looking.

Still open after this file: whether neutral_camp_vaults is really the
container that spawns neutral_sinners_sacrifice. The teleporter was answered
separately, by the entity list - see above.

## CAN CI COMPILE THE MAP? NO - settled 2026-08-29

Seven runs of `compile dust2`. The answer is no, for one reason, and it is
not any of the reasons anyone expected.

WHAT WORKS, and this is more than was thought:

  - resourcecompiler RUNS on a GitHub runner, on the software rasterizer
    ('Microsoft Basic Render Driver'). The 2026-08-14 note saying it needs a
    GPU is wrong.
  - It never hung. Every "hang" was our own timeout. A stall watcher now
    kills it after 60 seconds of silence, so a failed run costs 90 seconds
    rather than 4.5 hours.
  - IT ACCEPTS THE MAP. Path split correctly, map named, Embree initialised.
    Valve's own compiler treats the emitter's output as a map.
  - Content compiling works: one material compiled in 0m:00s and failed with
    a proper named error.

WHAT STOPS IT:

    No valid vcs file found for shader complex.vfx

.vcs files are compiled shaders. The CSDK contains NONE - a scan of the
extracted SDK found zero .vcs, zero .vfx, and no shader directory at all.
Shaders ship with the GAME. No shaders, no materials; no materials, no map.

This is a missing licensed input, not a tuning problem. More cores, more
time and smaller maps all make no difference - a six box fixture stalls in
exactly the same place as the 4700 box map, which is how the size theory
was ruled out.

THE ROUTE THAT WORKS is a machine with Deadlock installed: a desktop, or a
cloud Windows VM at roughly two to five dollars for one attempt. Everything
else in the pipeline is ready for it.

## Two files that would close most of this

Neither is reachable from CI; both need a desktop or a clone.

**`citadel.fgd`** — `Deadlock/game/citadel/citadel.fgd`, declared by gameinfo
as `GameData "citadel.fgd"`. No public copy exists; it ships inside the
install only. Plain text, and it lists every entity class Hammer knows with
each keyvalue's name, type and DEFAULT. It would settle the teleporter
classname, whether the sinner is a class or a subclass, which keyvalues are
required rather than merely present in one gym map, the light_environment
defaults this project leaves to the compiler, and whether
func_conditional_collidable answers Kill.

**`npc_units.vdata`** — tracked publicly at
github.com/SteamDatabase/GameTracking-Deadlock, under
`game/citadel/pak01_dir/scripts/`. Defines the units themselves, which should
name the sinner, the midboss and the objective family outright.

WHAT THE INTERNET HAS ALREADY GIVEN, all UNVERIFIED and none of it from a
game file:

  - a console guide lists `neutral_sinners_sacrifice` as a spawnable unit -
    the sinner is a UNIT name, not a classname prefix, which is why no
    classname search ever found it
  - the same guide labels `npc_boss_tier3` as "throne" and lists Guardians as
    `npc_boss_tier1` and `npc_barrack_boss`, and `npc_super_neutral` as the
    mid-boss. This project uses tier3 as the lane objective on your
    2026-08-23 call and does not use tier1 at all.
  - an NPC reference describes the Titan as guarding the Patron and needing
    to die before the Patron can be damaged - the shrine's job, not the
    walker's

Treat all three as leads. `npc_create` unit names are not necessarily map
entity classnames; that distinction is exactly why `neutral_camp_weak` is a
subclass and not a class.

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

### 1. Teleporter — absent from the fixture, and the fixture is thorough

Rechecked 2026-08-26 against the full 54-classname census and every string
value in it. Nothing matching tele, port, warp, rift or gate. The nearest
things that DO exist:

    citadel_zipline_path / _node    ziplines, 8 paths and 270 nodes
    trigger_catapult                labelled "Fan Catapult" in the gym
    citadel_trigger_push            labelled as the MID BOSS VENT EXITS
    citadel_trigger_speed_boost     side exits of the base

That last pair is worth reading twice: dl_example says `citadel_trigger_push`
is "usually found on the side exits of the base or in the mid Boss Vent
Exits", with tuning 40 for base and 400 for midboss. So the VENTS are push
volumes, and the catapult is the fan.

The map's own header says it was made by pulling apart the current dev
shipped map, so a genuinely old asset should be here. Three readings of that:
the teleporter is not an entity at all, it is called something none of the
searched words cover, or the gym omits it. Nothing in CI can tell those
apart.

Old note:

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

### 2. Sinner's Sacrifice — treated as the vault camp, on your read

`neutral_camp_vaults` is a real subclass of `info_neutral_trooper_camp`, read
off dl_example. The pairing of "vault" to "sinner" is YOURS; the fixture does
not use the word sinner anywhere. All four are now emitted as vault camps
rather than held back, because the classname and subclass are both real.

ANSWERED 2026-08-26 by the per-entity dump: the vault camp carries an EMPTY
`ENeutralTrooperType` and 120/120 timings. The blank is deliberate — the gym
labels it "Neutral Trooper Type - None" — not missing data. batch16 matches.

Old note:

One field is still blank: `ENeutralTrooperType`. Two of the eleven camps in
the fixture leave it empty and one of those is plausibly the vault, but the
value census reports values per key, not per entity, so nothing pairs them.
The workflow now also writes `entities.md`, one row per entity, which settles
it in a single rerun. If the vault camp turns out to carry a type, put it in
TIERS and rerun the batch.

Original note, now superseded:

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

### 4. Camp tiers — ANSWERED 2026-08-26

The whole family, off dl_example's 11 camps:

    neutral_camp_weak      type 1
    neutral_camp_medium    type 2
    neutral_camp_strong    type 3
    neutral_camp_vaults    type ?
    neutral_camp_midboss   type 5

THERE IS NO `neutral_camp_normal`. That was the guess in batch16 for all ten
t2 camps and it was wrong; they are `neutral_camp_medium` now. The types 1/2/3
guess was right. Type 12 also appears, on spawns only.

Two more corrections came out of the same read, both of which had been sitting
wrong in batch16 since the camps went in:

- every one of the 32 spawns carries `teamnumber 4`, not 0
- every one carries `HateCrateAttacker 1`, not 0

CONFIRMED 2026-08-26, per entity: weak 120/120, medium 120/300, strong
120/360, midboss -1/-1, vaults 120/120. Shortest to longest by size, as you
said. batch16 already matched and now says so.

Old note:

Still inferred: WHICH interval belongs to which tier. Camps use
InitialSpawnDelay 120 (9 of 11) and intervals of 120, 300 and 360, but the
probe reports values per key rather than per entity, so nothing pairs a 360
with the strong camp. batch16 uses the obvious mapping and says so.

`neutral_camp_vaults` is a fifth kind nobody has asked about yet.

Original note:

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

### 5. The lid — ANSWERED 2026-08-26. It is a brush that gets killed.

The shrine mechanism you remembered is real and it is simpler than expected.
`destroyable_building` fires:

    OnDestroyed -> <named brush> . Kill    delay 0, timesToFire -1

twelve times in the fixture, against targets named `*_grate_prop`,
`*_grate_brush` and `*_ladder_brush`. Geometry does not move or toggle: a
named entity is destroyed outright, and the hole it was blocking is open from
then on. That transfers to the lid directly.

Two more outputs matter here, both read from the same dump:

    OnBossKilled     -> counter . Add 1
    OnTrooperKilled  x9

`OnTrooperKilled` is fired by neutral camps — and the midboss IS a camp — so
the wiring is: midboss camp `OnTrooperKilled` -> lid `Kill`. Every string in
that sentence is now read rather than guessed.

WHAT IS STILL UNKNOWN is which classname the lid brush should be.
`func_conditional_collidable` is the only brush-model non-trigger in the
fixture (it carries `interactas` / `interactwith` and a mesh), so it is the
candidate, but nothing yet confirms it answers `Kill`. The fixture's own
`*_grate_brush` entities would say, except their targetnames do not appear in
the census — worth a look in `entities.md` on the next run.

SHELVED 2026-08-26. The lid is in as SOLID GEOMETRY - `midboss_lid`, a slab
flush with the room floor, built by batch18 behind a `LID` switch. The
midboss now stands on it. The deck below stays cut, so on the day the lid
becomes killable the shaft is already open to the bridge floor and nothing
has to be recut. Flip `LID` to False and the square opens again.

UNSHELVED 2026-08-29, and both halves of the old blocker were wrong.

THE PLAN FORMAT HAS EXPRESSED CONNECTIONS FOR SOME TIME. batch15 has a
`wire()` helper writing exactly the fields listed above, and `emit-dust2.yml`
pins `EXPECT_CONN: 56`, verified through dmxconvert's own element census. The
shop networks and guardian kill-relays are all wired that way. This paragraph
outlived the thing it described.

AND THE OUTPUT NAMED HERE DOES NOT EXIST. The sentence above says a neutral
camp fires `OnTrooperKilled`. The connection probe attributed that output to
exactly one class, `info_super_trooper_spawn`, and citadel.fgd declares it on
exactly one class, the same one. Every midboss-related class -
`info_neutral_trooper_camp`, `info_mid_boss_spawn`,
`info_neutral_trooper_spawn`, `trigger_midboss_shield` and
`citadel_base_prop_midboss_indicator` - declares NO OUTPUTS AND NO INPUTS AT
ALL. Nothing on the map fires when the midboss dies.

WHAT IS ACTUALLY LEFT is the event name. `logic_gameevent_listener` takes a
`gameeventname` and fires `OnEventFired`; Deadlock announces a midboss kill
globally, so the event exists, but its name is not in any file we hold. Run
`dumpgameevents` at the console with the dev flags from SHIPPING.md and set
`MIDBOSS_EVENT` in batch15. Everything downstream is built and waiting.

The lid is now a `func_brush` entity named `midboss_lid` (batch18,
`LID_ENTITY`), because base.fgd puts `Kill` on the `GameEntity` base class,
so every entity answers it. The brush class is a CHOICE, not a copy:
dl_example's own grate and ladder brushes live inside prefabs and no
targetname in the map resolves to them.

Old note:

`func_conditional_collidable` exists in the fixture, with `interactas` and
`interactwith` keys — dl_example sets `interactas` to
`blocklos, Citadel_Obscured`. That is collision that applies conditionally,
which is the shape the lid wants. It is a CANDIDATE, not an answer: nothing
yet says it can be toggled at runtime or what the condition list may contain.

`logic_relay` is also present with 10 instances, so the wiring half of the
mechanism exists.

The outputs question is still open, and the second run did not answer it
either — for a reason worth recording. It found 89 connection blocks and
reported every field as `?`, because it looked for `m_outputName`,
`m_targetName` and `m_inputName`: field names nobody had read. That is the
same mistake this workflow exists to avoid, made inside the workflow itself.

The third version names nothing. It censuses whatever fields the blocks turn
out to have, lists their values, and dumps all 89 blocks verbatim. The
connections ARE there — 89 of them — so this should answer what
`destroyable_building` fires on death, which is the precedent for the lid.
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
