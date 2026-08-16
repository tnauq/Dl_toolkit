"""Manual additions, batched.

Boxes defined here are appended to the plan. This is the list for geometry
that had to be rebuilt by hand because an automated rule produced the wrong
shape and deleting the result is not enough on its own.

Run after remove.py, before treefix.py.
"""
import json

ADD = [
    # Replaces shallow_52 and gapfill_38_45, 2026-08-16.
    #
    # shallow_52 was a ramp that simplify.py flattened to a level plate with
    # its top at 133.3. ramp-slab_53 is the same physical slope and survived
    # at pitch 10.62, so one ramp was split either side of the 10 degree
    # cutoff and half of it became terrain. gapfill.py then filled the void
    # above the flat plate to 213.4, which is the platform you could stand
    # on. Both are removed in remove.py.
    #
    # This slab runs west to east from z 0 at x 1920 up to z 132.9 at
    # x 2772, which is the west edge of ramp-slab_53's top face once its
    # 10.62 pitch is applied. Grade is 8.87 degrees against ramp-slab_53's
    # 10.62. Not a constant grade across the pair, but continuous at the
    # join, which is what the two ends actually are.
    #
    # Thickness is 160, matching the plate it replaces. That is enough that
    # the underside stays below ground level along the whole run (-161.9 at
    # the west end, -29.0 at the east), so the space under the ramp is
    # sealed without re-running gapfill.
    # Fill under axis_82, 2026-08-16. axis_69's deck tops out at 213.3 and
    # axis_82 starts at 320.0 directly above it, leaving a 106.7 void.
    # Filled across axis_82's whole footprint. It engulfs the thin walls
    # axis_80 and merged_119 that pass through, and buries ramp-slab_90,
    # the leftover stair stringer.
    {
        'name': 'gapfill_69_82',
        'origin': [1066.9, 3640.7, 266.7],
        'extents': [800.2, 186.7, 106.7],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    # Riser at the merged_84 seam, 2026-08-16. axis_82 ends at y 3734.0 and
    # merged_84 begins at 3734.1, so the two decks meet edge to edge with an
    # open face between 346.8 and 640.1. This straddles the seam at 53.5
    # thick, across the 706.8 the two decks share in x, and tops out flush
    # with merged_84's underside.
    {
        'name': 'gapfill_82_84',
        'origin': [1113.6, 3734.1, 493.5],
        'extents': [706.8, 53.5, 293.3],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_9052',
        'origin': [2346.0, 4280.9, -14.5],
        'extents': [862.3, 667.0, 160.0],
        'angles': [8.866, 180.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
]

p = json.load(open('dust2_half.json'))
before = len(p['boxes'])
existing = {b['name'] for b in p['boxes']}

added, clash = [], []
for box in ADD:
    if box['name'] in existing:
        clash.append(box['name'])
        continue
    p['boxes'].append(box)
    added.append(box['name'])

json.dump(p, open('dust2_half.json', 'w'), indent=1)

print(f'added {len(added)} of {len(ADD)} listed: {added}')
if clash:
    print(f'ALREADY PRESENT (not added again): {clash}')
print(f'plan {before} -> {len(p["boxes"])} boxes')
