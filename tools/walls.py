"""Double the height of WALLS and CEILINGS only.

Floors, ledges, ramps and cover keep their elevation, so terrain stays
walkable and the floorplan does not move. Rooms get twice the free height.

Classification, all in Deadlock units (1 m = 39.37 u, hero = 120 u):

  ramp     pitched -> untouched, doubling it would steepen the gradient
  cover    z extent < 192 u (under ~1.6 heroes) -> untouched; a crate is
           not a wall and a 2 m box should not become 4 m
  ceiling  a broad flat slab with standable-height clearance under it ->
           its BOTTOM is raised so the gap below doubles
  wall     everything else with z extent >= 192 u -> bottom stays put, the
           extent doubles upward
"""
import json, collections

HERO = 120
WALL_MIN = 192          # >= this tall counts as a wall, not cover
SLAB_MAX = 96           # <= this thick and broad counts as a plate

p = json.load(open('dust2_half.json'))
B = p['boxes']

def lo_(b,i): return b['origin'][i]-b['extents'][i]/2
def hi_(b,i): return b['origin'][i]+b['extents'][i]/2

# support height: the highest thing under each box that overlaps it in XY
tops = []
for b in B:
    tops.append((lo_(b,0),hi_(b,0),lo_(b,1),hi_(b,1),hi_(b,2)))

def support(b):
    bz = lo_(b,2)
    best = None
    x0,x1,y0,y1 = lo_(b,0),hi_(b,0),lo_(b,1),hi_(b,1)
    for (ox0,ox1,oy0,oy1,otop) in tops:
        if otop > bz + 1: continue
        if ox1 <= x0 or ox0 >= x1 or oy1 <= y0 or oy0 >= y1: continue
        if best is None or otop > best: best = otop
    return best

counts = collections.Counter()
out = []
for b in B:
    e, o, a = b['extents'][:], b['origin'][:], b.get('angles',[0,0,0])
    kind = None
    if abs(a[0]) > 0.01:
        kind = 'ramp (untouched)'
    elif e[2] < WALL_MIN and not (e[2] <= SLAB_MAX and min(e[0],e[1]) > 256):
        kind = 'cover (untouched)'
    elif e[2] <= SLAB_MAX and min(e[0],e[1]) > 256:
        s = support(b)
        gap = None if s is None else lo_(b,2) - s
        if gap is not None and gap >= HERO:
            newbottom = s + gap*2
            o[2] = newbottom + e[2]/2
            kind = 'ceiling (raised)'
        else:
            kind = 'floor (untouched)'
    else:
        bottom = lo_(b,2)
        e[2] = round(e[2]*2, 1)
        o[2] = round(bottom + e[2]/2, 1)
        kind = 'wall (doubled)'
    counts[kind] += 1
    nb = dict(b); nb['origin'] = [round(x,1) for x in o]; nb['extents'] = [round(x,1) for x in e]
    out.append(nb)

p['boxes'] = out
json.dump(p, open('dust2_half.json','w'), indent=1)

U = 39.37
for k,v in counts.most_common(): print(f'  {v:5d}  {k}')
zs=[hi_(b,2) for b in out]
print(f'\ntallest point now {max(zs):.0f} u = {max(zs)/U:.1f} m')
print(f'ramp pitches unchanged: max '
      f'{max((abs(b["angles"][0]) for b in out if abs(b["angles"][0])>0.01), default=0):.1f} deg')
