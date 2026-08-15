"""Targeted fix: raise the arch assembly to match its doubled wall.

The general classifier failed four times on this (per-box floor sampling
fragments an assembly; connectivity grouping misses pieces that do not
quite touch). Rather than keep generalising, fix the reported case: the
crosshair exists so specific spots can be named and fixed.

The assembly is the two piers plus the voussoir fan plus the crown slabs,
all sharing a plane at x = -227. The wall they pierce was scaled about its
base at z = 427, so the arch is scaled about the same datum. Same affine
transform, so the assembly cannot fragment.
"""
import json

DATUM = 427.0          # the wall's base, the datum its doubling used
X, XT = -227.0, 60.0
Y0, Y1 = -820.0, -300.0
Z0, Z1 = 400.0, 700.0

p = json.load(open('dust2_half.json'))
n = 0
for b in p['boxes']:
    o, e = b['origin'], b['extents']
    if abs(o[0]-X) > XT: continue
    if not (Y0 <= o[1] <= Y1): continue
    if not (Z0 <= o[2] <= Z1): continue
    bottom = o[2] - e[2]/2
    e[2] = round(e[2]*2, 1)
    o[2] = round(DATUM + (bottom-DATUM)*2 + e[2]/2, 1)
    n += 1
json.dump(p, open('dust2_half.json','w'), indent=1)
print(f'raised {n} boxes in the arch assembly about z={DATUM:.0f}')

U = 39.37
lo = lambda b,i: b['origin'][i]-b['extents'][i]/2
hi = lambda b,i: b['origin'][i]+b['extents'][i]/2
for nm in ['axis_480','axis_481','ramp-slab_861','ramp-slab_864','ramp-slab_872',
           'shallow_867','axis_482','axis_468']:
    q = [x for x in p['boxes'] if x['name']==nm]
    if q:
        b=q[0]
        print(f'  {nm:15s} bottom={lo(b,2):7.0f} top={hi(b,2):7.0f} ({hi(b,2)/U:5.1f} m)')
