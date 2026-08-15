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
