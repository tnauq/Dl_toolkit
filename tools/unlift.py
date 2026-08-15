"""Undo lifts applied to boxes that sit at the map's MAIN FLOOR level.

roofs.py lifts anything resting on a wall that doubled. That is right for
a roof and wrong for a floor plate: axis_199 is part of dust2's z=128
ground level (CS units), and it got carried 186 u into the air along with
the three boxes standing on it.

The rule: a box whose ORIGINAL bottom was at or below the main floor
(128 CS = 213 u) is ground, not roof. Restore it, and bring down whatever
was riding on it by the same amount.

Run AFTER roofs.py and archfix.py, BEFORE gapfill.py.
"""
import json, subprocess, sys

MAIN_FLOOR = 213.0     # 128 CS units at 1.667x
PAD = 8.0

cur = json.load(open('dust2_half.json'))
orig = json.load(open('orig_snapshot.json'))
O = {b['name']: b for b in orig['boxes']}
B = cur['boxes']
lo = lambda b,i: b['origin'][i]-b['extents'][i]/2
hi = lambda b,i: b['origin'][i]+b['extents'][i]/2

restored, deltas = [], {}
for b in B:
    o = O.get(b['name'])
    if o is None: continue
    ob, cb = lo(o,2), lo(b,2)
    if cb - ob < 1: continue                   # was not lifted
    if ob > MAIN_FLOOR + PAD: continue         # genuinely above the floor
    d = cb - ob
    b['origin'][2] = round(b['origin'][2] - d, 1)
    b['extents'][2] = o['extents'][2]          # undo any stretch too
    restored.append((b['name'], round(d)))
    deltas[b['name']] = d

print(f'restored {len(restored)} ground-level boxes')
for n,d in restored[:10]: print(f'  {n:20s} lowered {d} u')
if len(restored) > 10: print(f'  ... {len(restored)-10} more')

# bring down anything standing on a restored box
byname = {b['name']: b for b in B}
carried = 0
for _ in range(2):
    for b in B:
        if b['name'] in deltas: continue
        for n2, d in list(deltas.items()):
            s = byname[n2]
            if hi(b,0)<=lo(s,0) or lo(b,0)>=hi(s,0): continue
            if hi(b,1)<=lo(s,1) or lo(b,1)>=hi(s,1): continue
            if abs(lo(b,2) - (hi(s,2)+d)) <= PAD:
                b['origin'][2] = round(b['origin'][2] - d, 1)
                deltas[b['name']] = d; carried += 1
                break
print(f'carried down {carried} boxes that were standing on them')

json.dump(cur, open('dust2_half.json','w'), indent=1)
a = [x for x in B if x['name']=='axis_199'][0]
print(f"\naxis_199 now bottom={lo(a,2):.0f} top={hi(a,2):.0f} (target 187..213)")
