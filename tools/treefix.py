"""Manual height corrections, batched.

Boxes named here are moved in z to a stated target. This is the list for
lift faults found by eye in the viewer: things roofs.py carried up that
should not have moved, and things it left behind that should have.

Each entry records the height the box is expected to be at BEFORE the fix.
A box that is not at that height is skipped, not moved, so a rerun is a
no-op and an upstream change is reported rather than silently compounded.

Run LAST in the pipeline, after remove.py.
"""
import json

TOL = 1.0  # a box must be within this of `was` to be moved

# name: (was, now)  -- both are origin z
FIXES = {
    # Tree canopy near T spawn, 2026-08-16. The trunk (angled-wall_488..506)
    # is a stack of 53 x 53 x 40 blocks based at 213.4, the main floor.
    # roofs.py read the stack as a wall, doubled it, and carried the canopy
    # resting on it up by one datum of 213.4. ramp-slab_503 took the lift
    # twice. Lowered back onto the trunk top at 693.5.
    'ramp-slab_499': (880.8, 667.4),
    'ramp-slab_501': (890.0, 676.6),
    'ramp-slab_503': (1129.6, 702.8),
    'ramp-slab_507': (890.3, 676.9),
    'ramp-slab_510': (890.3, 676.9),
    'ramp-slab_512': (892.0, 678.6),
    'ramp-slab_515': (893.8, 680.4),
    'ramp-slab_526': (891.3, 677.9),
    'ramp-slab_529': (868.8, 655.4),
    'ramp-slab_531': (889.0, 675.6),
    'ramp-slab_534': (892.0, 678.6),
    'ramp-slab_538': (859.2, 645.8),
    'ramp-slab_539': (843.7, 630.3),
    'ramp-slab_540': (888.5, 675.1),
    'ramp-slab_541': (855.2, 641.8),
    'ramp-slab_542': (890.7, 677.3),
    'ramp-slab_543': (871.2, 657.8),
    'ramp-slab_544': (858.0, 644.6),
    'shallow_504': (922.0, 708.6),
    'shallow_521': (922.3, 708.9),
    'shallow_525': (922.7, 709.3),
    'shallow_532': (921.1, 707.7),

    # Gantry crossbeams, 2026-08-16. Four identical 320 x 53 x 40 beams
    # spanning the walls axis_192 and axis_195, in a row along y at
    # y = 1293.6, 1480.3, 1653.7, 1827.0. axis_348 sits at 713.5; the other
    # three sit 186.7 lower, which is 112 CS x 1.667, so they missed a
    # doubling the fourth received. Raised to match axis_348. Both walls run
    # z 0.1 to 1280.3 and their y spans cover all four beams, so nothing is
    # left behind by the move.
    'axis_345': (526.8, 713.5),
    'axis_346': (526.8, 713.5),
    'axis_347': (526.8, 713.5),
}

p = json.load(open('dust2_half.json'))
by_name = {b['name']: b for b in p['boxes']}

moved, skipped, missing = [], [], []
for name, (was, now) in FIXES.items():
    box = by_name.get(name)
    if box is None:
        missing.append(name)
        continue
    z = box['origin'][2]
    if abs(z - was) > TOL:
        skipped.append((name, z, was))
        continue
    box['origin'][2] = now
    moved.append(name)

json.dump(p, open('dust2_half.json', 'w'), indent=1)

print(f'moved {len(moved)} of {len(FIXES)} listed')
for name, z, was in skipped:
    print(f'  skipped {name}: z={z}, expected {was}')
for name in missing:
    print(f'  NOT FOUND (already gone or renamed): {name}')
