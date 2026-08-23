# NEXT — what is left, 2026-08-23

Companion to `HANDOFF_20260823.md`, which records what was LEARNED. This is
what remains to be DONE. Replaces the 2026-08-22 version, most of which is
now done.

**State of play: §2 of the old NEXT is empty.** Entity IO is built and gated,
trooper speed is read, the census is current, and batch.yml runs the whole
chain from one button. The plan carries real coordinates for everything
except the base room. What is missing is one survey session and one game.

---

## 1. The base room — blocked on the user

The only readings still needed. Send as `copy pos` with the box name, team-2
half only; everything mirrors.

- [ ] **patron** (`npc_boss_tier3`). Needs a **550 u radius pit** —
      `m_flPitRadius`, read from vdata. `hex_dais_0` was named as the
      location and still needs confirming as the entity origin
- [ ] **shrines** (`destroyable_building`), **two per team** in dl_example,
      named `<team>_t3_generator_<colour>`. The two readings taken on
      2026-08-23 predate the pit constraint and are expected to move
- [ ] **shrine guards** (`npc_barrack_boss`), the pair beside each shrine
- [ ] `func_regenerate` — currently spans the two base-room readings plus a
      256 u margin. A real pair of opposite corners would replace an
      invented size
- [ ] `trigger_tier3phase2_shield` — patron phase 2, centre plus size

**Shrine keyvalues that cannot be invented**: `model`, `skin`, `bodygroups`,
`building_health`, `final`, `add_attribute`, `add_modifier`. dl_example has
all seven on all four of its shrines.

**Barrack boss carries `BackdoorProtectionTrigger`** pointing at a trooper
detector entity (`amber_trooper_detector` / `sapphire_trooper_detector` in
the fixture). That entity does not exist in this map yet.

## 2. First in-game load — blocked on the user

**Nobody has loaded this map.** Every gate green proves it is structurally
valid and survives Valve's converter. It does not prove Deadlock opens it,
that troopers walk the lanes, that shops open 15 seconds in, or that
`dev_measuregeneric01.vmat` is a real content path — which now sits on most
of the floor boxes.

Do it EARLY with a rough map rather than late with a polished one. The base
room is not a prerequisite.

**What to watch for specifically**, since each fails silently:

- do shops close when a lane objective dies (`GUARDIAN_OUTPUT`, §4)
- do shops open at 15 s at all
- do troopers spawn on lanes 3 and 6 (lane numbering, §4)
- do the mirrored objectives render in the right team's colours

## 3. Content still at invented coordinates

None of it blocks a load. All of it is placeholder in the plan today.

- [ ] midboss: pit centre, and how big `trigger_midboss_shield` should be.
      It regenerates constantly and is a DPS check, so the volume wants to be
      tight enough that a team must commit inside it
- [ ] `info_neutral_trooper_camp` for the midboss, with its creature spawns
- [ ] jungle camp centres, plus creature offsets per camp
- [ ] breakables (`citadel_breakable_prop`) and crates (`item_crate_spawn`)
- [ ] bridge buffs (`citadel_item_powerup_spawner`) — 2 on the real map, zero
      keyvalues, position is everything
- [ ] climb ropes, jump pads (plus a landing marker each), fans
- [ ] `citadel_minimap_boundary` corners — without these the minimap has no
      frame
- [ ] **every volume SIZE in the plan.** Positions are real, extents are not

## 4. Unknowns that fail SILENTLY

- [ ] **`GUARDIAN_OUTPUT = "OnBossKilled"`.** Read from dl_example's
      `npc_boss_tier3`, so better than a guess, but no fixture connection is
      owned by a LANE objective specifically. Wrong name emits, converts,
      verifies and loads, and the shop never closes. One constant at the top
      of batch15
- [ ] **Lane numbering.** Using 1/3/6 from dl_example's 1/3/4/6. Against
      that: `client_strings` carries `BarrackBoss_Lane1` through `Lane4`,
      contiguous, so the game may number lanes 1..n. If troopers misbehave on
      3 and 6, try 1/2/3 first
- [ ] **The rift.** `citadel_capture_point` / `citadel_multi_capture_point`
      exist in the shipped strings with `CCitadelTriggerCapturePoint` behind
      them. The `CCitadelTrigger` prefix means it is a VOLUME and needs a
      mesh. dl_example predates the rift, so its absence proves nothing
- [ ] **`dev_measuregeneric01.vmat`** unconfirmed against the Deadlock tree
- [ ] **Shrine-upgrades-troopers direction.** dl_example wires the reverse —
      an `info_super_trooper_spawn` drives a shop's kill relay — so there is
      no fixture evidence for shrine → trooper upgrade and the input name
      will be a guess. `SHRINE_UPGRADES` in batch15 is an empty table with
      the shape it will take

## 5. Code — unblocked, no new information needed

- [ ] **Zipline tangents.** batch13 writes zeros, giving straight segments.
      dl_example's family B carries real in/out tangents. Only matters if the
      cable should sag or curve
- [ ] **Lane 4.** `LANE_COLOUR` carries blue for it and this map has no such
      lane. Harmless, listed for completeness
- [ ] **`ZIP_NEUTRAL_HALF_SPAN` and `ZIP_CAPTURABLE_HALF_SPAN`** are both
      guesses tuned to land near dl_example's ratios. Nothing was measured
- [ ] **Difficulty variants beyond `_weak`.** The fixture uses `_weak` on two
      lanes per team out of four. This map uses it on both side lanes

## 6. Suggested order

1. **Load the map.** Everything below is cheaper to do once with feedback
   than twice without it.
2. Base room readings, then wire the shrines.
3. Midboss, then the jungle.
4. Volume sizes, once something has been walked through.
5. Tangents and the rest of §5.
