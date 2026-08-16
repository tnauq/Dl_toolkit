"""Manual removals, batched.

Boxes named here are deleted from the plan. This is the list for things
found by eye in the viewer that no automated rule caught.

Run LAST in the pipeline, after gapfill.py.
"""
import json

REMOVE = [
    # Door leaves missed by doors.py: it shortlisted axis-aligned
    # door-shaped solids, and these are `compound` brushes (angled panels
    # reduced to bounding boxes), so they were never candidates. The wall
    # doubling then stretched them to 13.7 m.
    'compound_201',
    'compound_203',
    # Six more, same signature: paired leaves, 1-4 m wide, yawed, stretched
    # tall by the wall doubling. Long, mid and the B-side opening.
    'compound_196',
    'compound_197',
    'compound_118',
    'compound_117',
    'compound_374',
    'compound_375',
    # Gantry braces, 2026-08-16. Four facing pairs of 45 deg slabs with a
    # 53 x 53 cross section, flanking a pole that carries a platform
    # (ramp_818, ramp_837, ramp_840, ramp_843). Three of the four pairs sit
    # 72 to 125 u above the main floor, so with hero at 120 u they were
    # head-height clutter under an overhead structure. No other box in the
    # plan matches this signature.
    'ramp-slab_817',
    'ramp-slab_819',
    'ramp-slab_836',
    'ramp-slab_838',
    'ramp-slab_839',
    'ramp-slab_841',
    'ramp-slab_842',
    'ramp-slab_844',
    # Two flat plates at z 613 to 640, 26.7 thick, yawed 63.4 and 32.0.
    # Unlike the braces these were standable surface, so removing them
    # takes reachable cells out of the plan. Removed intentionally.
    'yaw_472',
    'yaw_474',
    # Flattened ramp and the fill above it, 2026-08-16. simplify.py reduced
    # this slope to a level plate (shallow_52, top 133.3) because it fell
    # under the 10 degree cutoff, while the other half of the same slope
    # survived as ramp-slab_53 at pitch 10.62. gapfill.py then filled the
    # void above the flat plate to 213.4. Rebuilt as ramp-slab_9052 in
    # addbox.py. shallow_52 is the only large shallow plate in the plan, so
    # this is a one-off, not a class.
    'shallow_52',
    'gapfill_38_45',
    # Angled wall, 2026-08-16. Full height, 0 to 640.2, 853.5 long and 26.7
    # thick at 26.6 degrees yaw. This is a route change, not clutter: the
    # whole span opens. merged_84, a 1160 x 1334 roof plate, rested on its
    # top at 653.5 and is left unsupported along that edge. Nothing opens
    # up, it just reads as floating from underneath.
    'yaw_21',
    # Batch, 2026-08-16.
    # merged_97 and merged_98: full-height walls, 346.7 to 933.5, beside
    # arch B.
    'merged_97',
    'merged_98',
    # yaw_353 and yaw_354: full-height yawed piers, 213.4 to 1067.0.
    'yaw_353',
    'yaw_354',
    # ramp_818: gantry platform. Its braces went earlier; axis_363 rested on
    # its top at 660.1 and is left floating, leaving axis_80 as the only
    # thing standing there.
    'ramp_818',
    'ramp-slab_181',
    # Four overlapping angled strips at 213.3 to 253.4, same 33.7 yaw
    # family, spanning the same run.
    'compound_589',
    'compound_590',
    'yaw_587',
    'yaw_588',
    # axis_355: 800 x 1520 plate at 826.9 to 853.6. It crossed axis_68's
    # footprint, which was the reference for that wall's trim; the trim
    # stands on its own and is unaffected.
    'axis_355',
    # Stairs, three treads rising to 266.6, 293.4 and 320.1. ramp-slab_90
    # and ramp-slab_92 flank them at 229.5 to 282.8 and are left in place.
    'axis_93',
    'axis_94',
    'axis_95',
]

p = json.load(open('dust2_half.json'))
before = len(p['boxes'])
gone = [b['name'] for b in p['boxes'] if b['name'] in REMOVE]
p['boxes'] = [b for b in p['boxes'] if b['name'] not in REMOVE]
json.dump(p, open('dust2_half.json','w'), indent=1)

missing = [n for n in REMOVE if n not in gone]
print(f'removed {len(gone)} of {len(REMOVE)} listed: {gone}')
if missing: print(f'NOT FOUND (already gone or renamed): {missing}')
print(f'plan {before} -> {len(p["boxes"])} boxes')
