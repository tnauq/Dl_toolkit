"""Regenerate the example plans at Deadlock hero scale.

The old plans were sized against a 72-unit Source player. A Deadlock hero
is ~120 u (3.05 m), so every clearance was about 40% too tight and every
cover block read as full cover when it was meant to be partial.

Reference heights, in units, derived from 1 m = 39.37 u:
    hero            120   3.05 m
    eye              96   2.44 m
    partial cover    96   2.44 m   (breaks sightline on a crouched hero)
    full cover      192   4.88 m   (well above the tallest hero)
    min passage w   192   4.88 m   (two heroes abreast is ~256)
    min ceiling     256   6.50 m
Everything snaps to the 64 grid.
"""
import json

CELL = 64
U_PER_M = 39.37
def m(u): return u / U_PER_M

def box(name, o, e):
    return {"name": name, "origin": list(o), "extents": list(e)}

def spawn(cls, o, yaw, props):
    return {"classname": cls, "origin": list(o), "angles": [0, yaw, 0],
            "properties": props}

# ---------------------------------------------------------------- sealed room
# Interior 1536 x 1536 x 512 -> 39.0 x 39.0 x 13.0 m, about 4.3 heroes tall.
IN = 1536; H = 512; T = 64          # interior span, interior height, wall thickness
half = IN / 2
floor_top = 0                        # keep the floor surface at z=0 for sanity
sealed = {
    "version": 1, "name": "sealed_room", "cell": CELL,
    "boxes": [
        box("floor",   (0, 0, -T/2),        (IN + 2*T, IN + 2*T, T)),
        box("ceiling", (0, 0, H + T/2),     (IN + 2*T, IN + 2*T, T)),
        box("wall_-x", (-(half + T/2), 0, H/2), (T, IN, H)),
        box("wall_+x", ( (half + T/2), 0, H/2), (T, IN, H)),
        box("wall_-y", (0, -(half + T/2), H/2), (IN + 2*T, T, H)),
        box("wall_+y", (0,  (half + T/2), H/2), (IN + 2*T, T, H)),
    ],
    "entities": [
        spawn("info_team_spawn", (-384, 0, 0), 0,
              {"teamnumber": "2", "lanenum": "1", "initialspawn": "1"}),
        spawn("info_team_spawn", ( 384, 0, 0), 180,
              {"teamnumber": "3", "lanenum": "1", "initialspawn": "1"}),
    ],
}

# ------------------------------------------------------------------- two lane
# 5120 x 2560 -> 130 x 65 m. Divider down the middle, partial and full cover,
# and a ledge reachable by a step so step height gets exercised.
LX, LY, LH, T2 = 5120, 2560, 768, 64
hx, hy = LX/2, LY/2
two = {
    "version": 1, "name": "two_lane", "cell": CELL,
    "boxes": [
        box("floor",    (0, 0, -T2/2), (LX + 2*T2, LY + 2*T2, T2)),
        box("wall_-x",  (-(hx + T2/2), 0, LH/2), (T2, LY, LH)),
        box("wall_+x",  ( (hx + T2/2), 0, LH/2), (T2, LY, LH)),
        box("wall_-y",  (0, -(hy + T2/2), LH/2), (LX + 2*T2, T2, LH)),
        box("wall_+y",  (0,  (hy + T2/2), LH/2), (LX + 2*T2, T2, LH)),
        # Divider: full height, leaves a 640-unit (16.3 m) gap at each end.
        box("divider",  (0, 0, LH/2), (LX - 1280, 192, LH)),
        # Cover. Partial breaks a sightline without blocking movement over it.
        box("cover_partial_a", (-1088, -640, 48),  (448, 448, 96)),
        box("cover_partial_b", ( 1088,  640, 48),  (448, 448, 96)),
        box("cover_full_a",    (-1728,  704, 96),  (384, 384, 192)),
        box("cover_full_b",    ( 1728, -704, 96),  (384, 384, 192)),
        # Ledge with a step up to it: 192 total, reached via a 96 step.
        box("ledge",      (-1984, 832, 96),  (768, 768, 192)),
        box("ledge_step", (-1472, 832, 48),  (256, 768, 96)),
    ],
    "entities": [
        spawn("info_team_spawn", (-2240, 0, 0), 0,
              {"teamnumber": "2", "lanenum": "1", "initialspawn": "1"}),
        spawn("info_team_spawn", ( 2240, 0, 0), 180,
              {"teamnumber": "3", "lanenum": "1", "initialspawn": "1"}),
        spawn("info_trooper_spawn", (-2240, -768, 0), 0,
              {"teamnumber": "2", "lanenum": "1"}),
        spawn("info_trooper_spawn", ( 2240,  768, 0), 180,
              {"teamnumber": "3", "lanenum": "1"}),
    ],
}

for plan, path in ((sealed, 'docs/plans/sealed_room.json'),
                   (two,    'docs/plans/two_lane.json')):
    with open(path, 'w') as f:
        json.dump(plan, f, indent=2)
        f.write('\n')
    xs = [abs(b['origin'][0]) + b['extents'][0]/2 for b in plan['boxes']]
    zs = [b['origin'][2] + b['extents'][2]/2 for b in plan['boxes']]
    print(f"{plan['name']:12s} {len(plan['boxes'])} boxes  "
          f"span {2*max(xs):.0f}u / {m(2*max(xs)):.0f}m  "
          f"top {max(zs):.0f}u / {m(max(zs)):.1f}m")
