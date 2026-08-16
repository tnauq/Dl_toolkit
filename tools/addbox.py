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
    # Wall above the arcade, 2026-08-16, connecting axis_80 to axis_61.
    # axis_80 stops at y 3867.4 and axis_61 begins at 5067.6. Extending
    # axis_80 bodily in y would swallow the whole arcade, arch B included,
    # so this is the wall ABOVE the window band only: from the panel tops at
    # 933.5 up to 1280.3, axis_61's height. The heads axis_109, axis_111 and
    # axis_113 poke into its underside, which is harmless, and it overlaps
    # axis_371 over the last 160 of the run.
    {
        'name': 'gapfill_80_61',
        'origin': [653.5, 4467.5, 1106.9],
        'extents': [26.7, 1200.2, 346.8],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    # Wall above axis_68, 2026-08-16, bringing it to axis_61's height. Same
    # treatment: one box from the panel tops at 933.5 to 1280.3, running the
    # full length so the window bays are closed above their heads.
    {
        'name': 'axis_68_upper',
        'origin': [1480.3, 4254.3, 1106.9],
        'extents': [26.7, 1626.9, 346.8],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    # Windows in axis_68, 2026-08-16. Copies the pattern from the x 653.5
    # wall: solid panels separated by openings with a solid block below and
    # above. The three openings are lined up with the existing ones at
    # y 4187.6, 4454.2 and 4747.7, so the windows face their counterparts.
    #
    # The aperture is IDENTICAL to the source at 720.1 to 880.2, 160.1 tall.
    # Heads run 880.2 to 960.2 like axis_109, axis_111 and axis_113, so they
    # stand 26.7 proud of the panel tops exactly as those do.
    #
    # Below the aperture this uses a single block from 640.1 to 720.1 rather
    # than the source's two-part stack of axis_83's course at 640.1 to 666.9
    # plus a sill at 666.9 to 720.1, because axis_68 has no course under it
    # and the joint line would be invisible in a blockout.
    #
    # axis_68 itself is reshaped into the first panel in treefix.py; these
    # are the other three panels and the six blocks.
    {
        'name': 'axis_68_p2',
        'origin': [1480.3, 4347.5, 786.8],
        'extents': [26.7, 213.4, 293.4],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'axis_68_p3',
        'origin': [1480.3, 4627.6, 786.8],
        'extents': [26.7, 240.2, 293.4],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'axis_68_p4',
        'origin': [1480.3, 4934.3, 786.8],
        'extents': [26.7, 266.8, 293.4],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'axis_68_sill1',
        'origin': [1480.3, 4214.2, 680.1],
        'extents': [26.7, 53.2, 80.0],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'axis_68_head1',
        'origin': [1480.3, 4214.2, 920.2],
        'extents': [26.7, 53.2, 80.0],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'axis_68_sill2',
        'origin': [1480.3, 4480.9, 680.1],
        'extents': [26.7, 53.3, 80.0],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'axis_68_head2',
        'origin': [1480.3, 4480.9, 920.2],
        'extents': [26.7, 53.3, 80.0],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'axis_68_sill3',
        'origin': [1480.3, 4774.3, 680.1],
        'extents': [26.7, 53.2, 80.0],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'axis_68_head3',
        'origin': [1480.3, 4774.3, 920.2],
        'extents': [26.7, 53.2, 80.0],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    # Connector between merged_119 and axis_68, 2026-08-16. Both are the
    # same 26.7 wall plane at x 1467.0, stacked with 266.7 of nothing
    # between 373.4 and 640.1. This fills that over the 293.4 of y they
    # share. The volume was completely empty.
    {
        'name': 'gapfill_119_68',
        'origin': [1480.3, 3587.4, 506.8],
        'extents': [26.7, 293.4, 266.7],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    # Fill between axis_69 and merged_84, 2026-08-16. Unlike the seam these
    # two overlap in plan: merged_84 starts at y 3734.1 and axis_69 runs to
    # 3867.5, a 133.4 band, and the gap is the full 426.8 between the low
    # deck's top and the high deck's underside. It subsumes part of
    # gapfill_82_84 below, which is redundant but harmless, and it buries
    # axis_121.
    {
        'name': 'gapfill_69_84',
        'origin': [1327.0, 3800.8, 426.7],
        'extents': [1133.6, 133.4, 426.8],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
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
    # thick, and tops out flush with merged_84's underside. Extended west on
    # 2026-08-16 to meet axis_80's east face at 666.9.
    {
        'name': 'gapfill_82_84',
        'origin': [1067.0, 3734.1, 493.5],
        'extents': [800.1, 53.5, 293.3],
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
