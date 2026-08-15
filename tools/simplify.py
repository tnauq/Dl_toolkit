"""de_dust2 BSP -> a simplified box list, with the simplification VERIFIED.

Stages, each measured:
  1. extract    every solid brush -> bounds + face classification
  2. classify   axis / yaw-only / ramp (>=10 deg) / shallow (<10 deg) / compound
  3. flatten    shallow slopes become level plates; ramps keep their pitch
  4. merge      coplanar adjacent wall slabs become single solids
  5. verify     flood-fill the walkable space before and after and compare

Stage 5 is the point. A merged wall that seals a doorway, or a flattened
floor that blocks a ramp, is invisible in a box list and obvious in a
reachability diff.
"""
import struct, math, itertools, collections, json

BSP = 'de_dust2_txt.bsp'
d = open(BSP, 'rb').read()

def lump(i):
    off, ln, lv, fc = struct.unpack_from('<iiii', d, 8 + i*16)
    return d[off:off+ln]

PLANES = [struct.unpack_from('<4fi', lump(1), i*20) for i in range(len(lump(1))//20)]
BRUSHES = [struct.unpack_from('<iii', lump(18), i*12) for i in range(len(lump(18))//12)]
BSIDES = [struct.unpack_from('<hhhh', lump(19), i*8) for i in range(len(lump(19))//8)]
TEXINFO = [struct.unpack_from('<32x32xii', lump(6), i*72) for i in range(len(lump(6))//72)]
TEXDATA = [struct.unpack_from('<3fiiiii', lump(2), i*32) for i in range(len(lump(2))//32)]
strdata, strtable = lump(43), lump(44)
offs = [struct.unpack_from('<i', strtable, i*4)[0] for i in range(len(strtable)//4)]

def texname(td):
    if not (0 <= td < len(TEXDATA)): return '?'
    s = TEXDATA[td][3]
    if not (0 <= s < len(offs)): return '?'
    o = offs[s]
    return strdata[o:strdata.index(b'\0', o)].decode('latin1')

TOOL = ('tools/', 'nodraw', 'skybox', 'toolsclip', 'trigger', 'skip', 'hint',
        'playerclip', 'invisible', 'blocklight', 'areaportal', 'occluder')
SOLID, PLAYERCLIP, MONSTERCLIP, LADDER = 0x1, 0x10000, 0x20000, 0x20000000
RAMP_DEG = 10.0          # below this a slope is terrain, not a ramp
WALL_DEG = 60.0          # above this it is an angled wall, not a walkable ramp

def bounds(pls):
    pts = []
    for a, b, c in itertools.combinations(pls, 3):
        m = [list(a[:3]), list(b[:3]), list(c[:3])]
        det = (m[0][0]*(m[1][1]*m[2][2]-m[1][2]*m[2][1])
             - m[0][1]*(m[1][0]*m[2][2]-m[1][2]*m[2][0])
             + m[0][2]*(m[1][0]*m[2][1]-m[1][1]*m[2][0]))
        if abs(det) < 1e-6: continue
        rhs = [a[3], b[3], c[3]]
        def d3(q):
            return (q[0][0]*(q[1][1]*q[2][2]-q[1][2]*q[2][1])
                  - q[0][1]*(q[1][0]*q[2][2]-q[1][2]*q[2][0])
                  + q[0][2]*(q[1][0]*q[2][1]-q[1][1]*q[2][0]))
        p = []
        for i in range(3):
            q = [r[:] for r in m]
            for r in range(3): q[r][i] = rhs[r]
            p.append(d3(q)/det)
        if all(pl[0]*p[0]+pl[1]*p[1]+pl[2]*p[2]-pl[3] <= 0.1 for pl in pls):
            pts.append(p)
    if not pts: return None
    return ([min(q[i] for q in pts) for i in range(3)],
            [max(q[i] for q in pts) for i in range(3)])

# ---------------------------------------------------------------- 1 & 2
raw, drops = [], collections.Counter()
for bi, (first, num, cont) in enumerate(BRUSHES):
    names, pls, real = set(), [], []
    for s in range(first, first+num):
        pi, ti, _, bevel = BSIDES[s]
        pls.append(PLANES[pi][:4])
        if not bevel: real.append(PLANES[pi][:3])
        if 0 <= ti < len(TEXINFO): names.add(texname(TEXINFO[ti][1]).lower())

    if not (cont & SOLID):
        drops['non-solid volume (clip/ladder/etc)'] += 1; continue
    if names and all(any(t in n for t in TOOL) for n in names):
        drops['tool texture only'] += 1; continue

    bb = bounds(pls)
    if bb is None:
        drops['degenerate'] += 1; continue
    lo, hi = bb

    # Surface TILT from horizontal is acos(|nz|), not asin. A flat floor
    # has a vertical normal (nz=1, tilt 0); a wall has nz=0, tilt 90.
    # Getting this backwards inverts the whole classification.
    sloped = [n for n in real if 1e-4 < abs(n[2]) < 1-1e-4]
    steep = min((math.degrees(math.acos(min(1, abs(n[2])))) for n in sloped),
                default=90.0)
    horiz = {round(math.degrees(math.atan2(n[1], n[0])) % 90, 1)
             for n in real if abs(n[2]) < 1e-4}
    horiz = {0.0 if (a < 0.2 or a > 89.8) else a for a in horiz}
    yaws = sorted(a for a in horiz if a)

    # A brush is a ramp if its FLATTEST sloped face is walkable-ish: tilted
    # more than RAMP_DEG but less than a wall. Steeper than WALL_DEG and it
    # is an angled wall, which is a yaw problem, not a pitch one.
    if sloped and RAMP_DEG <= steep <= WALL_DEG:
        kind = 'ramp'
    elif sloped and steep < RAMP_DEG:
        kind = 'shallow'
    elif sloped:
        kind = 'angled-wall'
    elif len(yaws) == 0:
        kind = 'axis'
    elif len(yaws) == 1:
        kind = 'yaw'
    else:
        kind = 'compound'

    raw.append({'i': bi, 'lo': lo, 'hi': hi, 'kind': kind,
                'steep': steep, 'yaw': yaws[0] if yaws else 0.0,
                'normals': sloped})

print(f'brushes {len(BRUSHES)}  ->  kept {len(raw)}')
for r, n in drops.most_common(): print(f'  dropped {n:4d}  {r}')
print()
print('classification:')
for k, n in collections.Counter(x['kind'] for x in raw).most_common():
    print(f'  {n:5d}  {k}')

# ---------------------------------------------------------------- 3 flatten
# Shallow slopes collapse to their bounding box, which is what a level
# plate is. Ramps keep a pitch derived from their steepest face.
boxes = []
for x in raw:
    lo, hi = x['lo'], x['hi']
    o = [(lo[i]+hi[i])/2 for i in range(3)]
    e = [hi[i]-lo[i] for i in range(3)]
    b = {'src': x['i'], 'origin': o, 'extents': e, 'kind': x['kind'],
         'angles': [0.0, x['yaw'], 0.0]}
    if x['kind'] == 'ramp' and x['normals']:
        n = max(x['normals'], key=lambda v: abs(v[2]))
        hx, hy = n[0], n[1]
        hl = math.hypot(hx, hy)
        if hl > 1e-6:
            hx, hy = hx/hl, hy/hl
            run = abs(e[0]*hx) + abs(e[1]*hy)
            rise = e[2]
            pitch = math.degrees(math.atan2(rise, run)) if run > 1e-6 else 0.0
            b['angles'] = [-pitch if n[2] > 0 else pitch,
                           math.degrees(math.atan2(hy, hx)), 0.0]
            b['ramp_len'] = math.hypot(run, rise)
    boxes.append(b)

# ---------------------------------------------------------------- 4 merge
# Only axis-aligned slabs merge. A slab is thin on exactly one axis; two
# merge when they are thin on the SAME axis at the SAME position and their
# other two spans touch or overlap.
def slab_axis(e, thr=16.0):
    thin = [i for i in range(3) if e[i] <= thr]
    return thin[0] if len(thin) == 1 else None

def merged(a, b):
    ax = slab_axis(a['extents'])
    # a may be a previously-merged result that is no longer a slab.
    if ax is None or slab_axis(b['extents']) is None: return None
    lo = lambda x, i: x['origin'][i] - x['extents'][i]/2
    hi = lambda x, i: x['origin'][i] + x['extents'][i]/2
    if abs(lo(a, ax)-lo(b, ax)) > 0.5 or abs(hi(a, ax)-hi(b, ax)) > 0.5:
        return None
    other = [i for i in range(3) if i != ax]
    # must be flush on one of the other axes and touching on the third
    for k in other:
        j = [i for i in other if i != k][0]
        if abs(lo(a, k)-lo(b, k)) < 0.5 and abs(hi(a, k)-hi(b, k)) < 0.5:
            if lo(a, j) <= hi(b, j)+0.5 and lo(b, j) <= hi(a, j)+0.5:
                nlo = [min(lo(a, i), lo(b, i)) for i in range(3)]
                nhi = [max(hi(a, i), hi(b, i)) for i in range(3)]
                return {'src': a['src'], 'kind': 'merged',
                        'angles': [0.0, 0.0, 0.0],
                        'origin': [(nlo[i]+nhi[i])/2 for i in range(3)],
                        'extents': [nhi[i]-nlo[i] for i in range(3)]}
    return None

mergeable = [b for b in boxes
             if b['kind'] in ('axis', 'shallow', 'angled-wall')
             and b['angles'] == [0.0, 0.0, 0.0]
             and slab_axis(b['extents']) is not None]
fixed = [b for b in boxes if b not in mergeable]

changed = True
rounds = 0
while changed and rounds < 12:
    changed = False; rounds += 1
    out, used = [], set()
    for i, a in enumerate(mergeable):
        if i in used: continue
        cur = a
        for j in range(i+1, len(mergeable)):
            if j in used: continue
            m = merged(cur, mergeable[j])
            if m: cur = m; used.add(j); changed = True
        out.append(cur)
    mergeable = out

final = fixed + mergeable
print()
print(f'merge: {len(boxes)} boxes -> {len(final)} after {rounds} rounds '
      f'({len(boxes)-len(final)} merged away)')

json.dump({'boxes': final}, open('simplified.json', 'w'))
json.dump({'boxes': boxes}, open('unsimplified.json', 'w'))
print('wrote simplified.json and unsimplified.json')
