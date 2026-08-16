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
    # merged_97 and merged_98 were removed here on 2026-08-16 and put back
    # the same day: they are the panels between axis_80 / axis_109 and
    # axis_109 / axis_111, and were wanted after all. Left OUT of this list
    # rather than re-added under new names, so nothing in the pipeline
    # removes and recreates the same geometry on every run.
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
    # Batch, 2026-08-16. Four yawed plates at 320.0 to 346.8 and 613.4 to
    # 640.1, in two stacked pairs.
    'yaw_356',
    'yaw_357',
    'yaw_358',
    'yaw_359',
    # ramp-slab_92, one of the pair that flanked the removed stairs.
    # ramp-slab_90 is its twin at the same 229.5 to 282.8 and is left in.
    'ramp-slab_92',
    # Six angled blocks floating above axis_48, starting just over its top
    # at 1280.3 with nothing under them between 800 and 1280. Same cluster
    # as ramp-slab_181, removed earlier.
    'ramp-slab_147',
    'ramp-slab_149',
    'ramp-slab_169',
    'ramp-slab_182',
    'ramp-slab_184',
    'shallow_180',
    # Parapet above axis_335, 2026-08-16. 37 boxes on the single plane
    # y 1482.0, 27 thick, running the wall's full length from x 3198 to
    # 3734 and rising to 640.1: uprights, small ramps and caps.
    'axis_925',
    'axis_926',
    'axis_927',
    'axis_928',
    'axis_929',
    'axis_930',
    'axis_932',
    'axis_933',
    'axis_934',
    'axis_935',
    'axis_940',
    'axis_941',
    'axis_942',
    'axis_943',
    'axis_944',
    'axis_945',
    'axis_948',
    'axis_951',
    'axis_953',
    'axis_954',
    'axis_955',
    'axis_956',
    'axis_957',
    'axis_958',
    'axis_959',
    'axis_960',
    'ramp-slab_931',
    'ramp-slab_936',
    'ramp-slab_937',
    'ramp-slab_947',
    'ramp-slab_949',
    'ramp-slab_952',
    'ramp_938',
    'ramp_939',
    'ramp_946',
    'ramp_950',
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
