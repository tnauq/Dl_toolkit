"""Extract solid brushes from a Source BSP and report exactly what gets
filtered out, so the removals can be checked rather than trusted.

Lump indices matter and are easy to get wrong: 17 is LEAFBRUSHES,
18 is BRUSHES, 19 is BRUSHSIDES. An off-by-one there produces lump
lengths that do not divide cleanly, which is the tell.
"""
import struct, collections, json, sys, itertools

BSP = 'de_dust2_txt.bsp'
d = open(BSP, 'rb').read()

def lump(i):
    off, ln, lv, fc = struct.unpack_from('<iiii', d, 8 + i*16)
    return d[off:off+ln]

# ---- lumps ----
planes_b = lump(1)
texdata_b = lump(2)
texinfo_b = lump(6)
brushes_b = lump(18)
bsides_b = lump(19)
strdata = lump(43)
strtable = lump(44)

PLANES = [struct.unpack_from('<4fi', planes_b, i*20) for i in range(len(planes_b)//20)]
BRUSHES = [struct.unpack_from('<iii', brushes_b, i*12) for i in range(len(brushes_b)//12)]
BSIDES = [struct.unpack_from('<hhhh', bsides_b, i*8) for i in range(len(bsides_b)//8)]
TEXINFO = [struct.unpack_from('<32x32xii', texinfo_b, i*72) for i in range(len(texinfo_b)//72)]
TEXDATA = [struct.unpack_from('<3fiiiii', texdata_b, i*32) for i in range(len(texdata_b)//32)]

offsets = [struct.unpack_from('<i', strtable, i*4)[0] for i in range(len(strtable)//4)]
def texname(td_index):
    if td_index < 0 or td_index >= len(TEXDATA): return '?'
    sid = TEXDATA[td_index][3]
    if sid < 0 or sid >= len(offsets): return '?'
    o = offsets[sid]
    end = strdata.index(b'\0', o)
    return strdata[o:end].decode('latin1')

# ---- content flags we care about ----
CONTENTS_SOLID       = 0x1
CONTENTS_WINDOW      = 0x2
CONTENTS_GRATE       = 0x8
CONTENTS_PLAYERCLIP  = 0x10000
CONTENTS_MONSTERCLIP = 0x20000
CONTENTS_LADDER      = 0x20000000
CONTENTS_DETAIL      = 0x8000000

# Tool textures never become geometry.
TOOL = ('tools/', 'toolsnodraw', 'toolsclip', 'toolsskybox', 'toolstrigger',
        'toolsskip', 'toolshint', 'toolsplayerclip', 'toolsinvisible',
        'toolsblocklight', 'toolsareaportal', 'toolsoccluder')

def brush_bounds(first, num):
    """Bounds of the convex region defined by the brush's halfspaces.

    Computed by intersecting every triple of planes and keeping points
    that satisfy all of them. Exact for a convex brush and needs no
    assumption that it is axis-aligned.
    """
    pls = []
    for s in range(first, first+num):
        pi = BSIDES[s][0]
        n = PLANES[pi]
        pls.append((n[0], n[1], n[2], n[3]))
    pts = []
    for a, b, c in itertools.combinations(pls, 3):
        m = [[a[0], a[1], a[2]], [b[0], b[1], b[2]], [c[0], c[1], c[2]]]
        det = (m[0][0]*(m[1][1]*m[2][2]-m[1][2]*m[2][1])
             - m[0][1]*(m[1][0]*m[2][2]-m[1][2]*m[2][0])
             + m[0][2]*(m[1][0]*m[2][1]-m[1][1]*m[2][0]))
        if abs(det) < 1e-6: continue
        rhs = [a[3], b[3], c[3]]
        def col(mat, i, v):
            q = [r[:] for r in mat]
            for r in range(3): q[r][i] = v[r]
            return q
        def d3(q):
            return (q[0][0]*(q[1][1]*q[2][2]-q[1][2]*q[2][1])
                  - q[0][1]*(q[1][0]*q[2][2]-q[1][2]*q[2][0])
                  + q[0][2]*(q[1][0]*q[2][1]-q[1][1]*q[2][0]))
        p = [d3(col(m, i, rhs))/det for i in range(3)]
        if all(pl[0]*p[0] + pl[1]*p[1] + pl[2]*p[2] - pl[3] <= 0.1 for pl in pls):
            pts.append(p)
    if not pts: return None
    lo = [min(q[i] for q in pts) for i in range(3)]
    hi = [max(q[i] for q in pts) for i in range(3)]
    return lo, hi

kept, dropped = [], collections.Counter()
dropped_detail = collections.defaultdict(list)

for bi, (first, num, contents) in enumerate(BRUSHES):
    names = set()
    axial = True
    for s in range(first, first+num):
        pi, ti = BSIDES[s][0], BSIDES[s][1]
        if 0 <= ti < len(TEXINFO):
            names.add(texname(TEXINFO[ti][1]).lower())
        n = PLANES[pi][:3]
        nz = sum(1 for c in n if abs(c) > 1e-4)
        if nz != 1 or not any(abs(abs(c)-1) < 1e-4 for c in n):
            axial = False

    tooly = all(any(t in nm for t in TOOL) for nm in names) if names else False

    reason = None
    if not (contents & CONTENTS_SOLID):
        if contents & CONTENTS_PLAYERCLIP: reason = 'playerclip (invisible collision)'
        elif contents & CONTENTS_MONSTERCLIP: reason = 'monsterclip'
        elif contents & CONTENTS_LADDER: reason = 'ladder volume'
        elif contents & CONTENTS_GRATE: reason = 'grate'
        elif contents & CONTENTS_WINDOW: reason = 'window/glass'
        else: reason = f'non-solid contents 0x{contents:x}'
    elif tooly:
        reason = 'tool texture only (nodraw/skybox/clip)'

    bb = brush_bounds(first, num)
    if bb is None:
        reason = reason or 'degenerate, no bounded volume'

    if reason:
        dropped[reason] += 1
        if bb:
            lo, hi = bb
            size = [hi[i]-lo[i] for i in range(3)]
            dropped_detail[reason].append((bi, [round(x) for x in lo], [round(s) for s in size]))
        continue

    lo, hi = bb
    size = [hi[i]-lo[i] for i in range(3)]
    kept.append({
        'i': bi,
        'origin': [round((lo[k]+hi[k])/2, 1) for k in range(3)],
        'extents': [round(s, 1) for s in size],
        'axial': axial,
        'vol': size[0]*size[1]*size[2],
        'tex': sorted(names)[:2],
    })

print(f'brushes total      {len(BRUSHES)}')
print(f'kept as geometry   {len(kept)}')
print(f'dropped            {sum(dropped.values())}')
print()
print('--- dropped, by reason ---')
for r, n in dropped.most_common():
    print(f'{n:5d}  {r}')
    for bi, lo, size in dropped_detail[r][:3]:
        print(f'         e.g. brush {bi} at {lo} size {size}')
print()
ax = sum(1 for k in kept if k['axial'])
print(f'of the kept: {ax} axis-aligned ({100*ax/max(len(kept),1):.0f}%), '
      f'{len(kept)-ax} angled')
vols = sorted(k['vol'] for k in kept)
print(f'volume: smallest {vols[0]:.0f}, median {vols[len(vols)//2]:.0f}, largest {vols[-1]:.0f}')
json.dump(kept, open('brushes.json','w'))
print('wrote brushes.json')
