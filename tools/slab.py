"""Wedges -> pitched slabs, then the same reachability check.

The AABB pass lost 99.4% of the reachable space because bounding-boxing a
wedge fills the volume above its sloped face. A pitched slab instead lays a
thin plate ON that face and leaves the space above it open, which is what a
ramp actually is.

Sign convention is not assumed. For each ramp the slab is built both ways
and the one whose top-face centre lands on the brush's real sloped plane is
kept, so a wrong pitch sign cannot silently survive.
"""
import struct, itertools, math, json, collections

GRID, PLAYER_H, STEP = 32, 72, 18
RAMP_DEG, WALL_DEG = 10.0, 60.0
THICK = 32.0

d = open('de_dust2_txt.bsp','rb').read()
def lump(i):
    off,ln,lv,fc = struct.unpack_from('<iiii', d, 8+i*16); return d[off:off+ln]
PLANES=[struct.unpack_from('<4fi',lump(1),i*20) for i in range(len(lump(1))//20)]
BRUSHES=[struct.unpack_from('<iii',lump(18),i*12) for i in range(len(lump(18))//12)]
BSIDES=[struct.unpack_from('<hhhh',lump(19),i*8) for i in range(len(lump(19))//8)]

boxes = json.load(open('simplified.json'))['boxes']
by_src = {b['src']: b for b in boxes}

def rotm(pitch, yaw, roll=0.0):
    p,y,r = math.radians(pitch), math.radians(yaw), math.radians(roll)
    cp,sp,cy,sy,cr,sr = math.cos(p),math.sin(p),math.cos(y),math.sin(y),math.cos(r),math.sin(r)
    return [[cp*cy, sr*sp*cy-cr*sy, cr*sp*cy+sr*sy],
            [cp*sy, sr*sp*sy+cr*cy, cr*sp*sy-sr*cy],
            [-sp,   sr*cp,          cr*cp]]

def mul(R,v): return [sum(R[i][k]*v[k] for k in range(3)) for i in range(3)]
def mulT(R,v): return [sum(R[k][i]*v[k] for k in range(3)) for i in range(3)]

slabs, plain, failed = [], [], 0
for bi,(first,num,cont) in enumerate(BRUSHES):
    if bi not in by_src: continue
    b = by_src[bi]
    if b['kind'] != 'ramp':
        plain.append(b); continue

    pls  = [PLANES[BSIDES[s][0]][:4] for s in range(first,first+num)]
    real = [PLANES[BSIDES[s][0]][:4] for s in range(first,first+num) if not BSIDES[s][3]]
    # the walkable face: points up, tilted between RAMP_DEG and WALL_DEG
    cands = []
    for pl in real:
        nz = pl[2]
        if nz <= 1e-4: continue
        tilt = math.degrees(math.acos(min(1, abs(nz))))
        if RAMP_DEG <= tilt <= WALL_DEG: cands.append((tilt, pl))
    if not cands:
        plain.append(b); continue
    tilt, pl = min(cands, key=lambda t: t[0])

    o, e = b['origin'], b['extents']
    hx, hy = pl[0], pl[1]
    hl = math.hypot(hx, hy)
    if hl < 1e-6:
        plain.append(b); continue
    hx, hy = hx/hl, hy/hl
    yaw = math.degrees(math.atan2(hy, hx))

    run   = abs(e[0]*hx) + abs(e[1]*hy)
    width = abs(e[0]*hy) + abs(e[1]*hx)
    length = math.hypot(run, e[2])

    cx, cy = o[0], o[1]
    cz = (pl[3] - pl[0]*cx - pl[1]*cy) / pl[2]     # the plane's z at centre

    best = None
    for sign in (1.0, -1.0):
        pitch = sign * tilt
        R = rotm(pitch, yaw)
        # centre the slab THICK/2 below the face along its normal
        org = [cx - pl[0]*THICK/2, cy - pl[1]*THICK/2, cz - pl[2]*THICK/2]
        top = [org[i] + mul(R, [0,0,THICK/2])[i] for i in range(3)]
        err = abs(top[2] - cz)
        if best is None or err < best[0]:
            best = (err, pitch, org, R)

    err, pitch, org, R = best
    if err > 8.0:
        failed += 1; plain.append(b); continue

    slabs.append({'src': bi, 'kind': 'ramp-slab',
                  'origin': [round(x,1) for x in org],
                  'extents': [round(length,1), round(width,1), THICK],
                  'angles': [round(pitch,2), round(yaw,2), 0.0]})

print(f'ramps converted to pitched slabs: {len(slabs)}')
print(f'kept as boxes:                    {len(plain)}')
print(f'ramp conversions rejected (top face missed the plane): {failed}')

# ------------------------------------------------------------------ verify
lo=[-1312,-496,-64]; hi=[2400,3296,446]
NX=int((hi[0]-lo[0])//GRID)+1; NY=int((hi[1]-lo[1])//GRID)+1; NZ=int((hi[2]-lo[2])//GRID)+1
N=NX*NY*NZ

def mask_mixed():
    m=bytearray(N)
    for b in plain:
        o,e=b['origin'],b['extents']
        r=[range(max(0,int((o[i]-e[i]/2-lo[i])//GRID)),
                 min([NX,NY,NZ][i]-1,int((o[i]+e[i]/2-lo[i])//GRID))+1) for i in range(3)]
        for iz in r[2]:
            for iy in r[1]:
                base=iz*NY*NX+iy*NX
                for ix in r[0]: m[base+ix]=1
    for b in slabs:
        o,e,a=b['origin'],b['extents'],b['angles']
        R=rotm(a[0],a[1],a[2]); h=[e[i]/2 for i in range(3)]
        cs=[]
        for sx in(-1,1):
            for sy in(-1,1):
                for sz in(-1,1):
                    v=mul(R,[sx*h[0],sy*h[1],sz*h[2]])
                    cs.append([o[i]+v[i] for i in range(3)])
        mn=[min(c[i] for c in cs) for i in range(3)]
        mx=[max(c[i] for c in cs) for i in range(3)]
        for iz in range(max(0,int((mn[2]-lo[2])//GRID)), min(NZ-1,int((mx[2]-lo[2])//GRID))+1):
            cz=lo[2]+iz*GRID+GRID/2
            for iy in range(max(0,int((mn[1]-lo[1])//GRID)), min(NY-1,int((mx[1]-lo[1])//GRID))+1):
                cy=lo[1]+iy*GRID+GRID/2
                base=iz*NY*NX+iy*NX
                for ix in range(max(0,int((mn[0]-lo[0])//GRID)), min(NX-1,int((mx[0]-lo[0])//GRID))+1):
                    cx=lo[0]+ix*GRID+GRID/2
                    l=mulT(R,[cx-o[0],cy-o[1],cz-o[2]])
                    if abs(l[0])<=h[0] and abs(l[1])<=h[1] and abs(l[2])<=h[2]:
                        m[base+ix]=1
    return m

def standable(mask):
    need=max(1,PLAYER_H//GRID); out=bytearray(N)
    for iz in range(1,NZ):
        for iy in range(NY):
            base=iz*NY*NX+iy*NX; below=(iz-1)*NY*NX+iy*NX
            for ix in range(NX):
                if mask[base+ix] or not mask[below+ix]: continue
                ok=True
                for k in range(1,need):
                    if iz+k>=NZ or mask[(iz+k)*NY*NX+iy*NX+ix]: ok=False;break
                if ok: out[base+ix]=1
    return out

def flood(stand,seeds):
    seen=bytearray(N); q=collections.deque()
    for s in seeds:
        if 0<=s<N and stand[s]: seen[s]=1;q.append(s)
    steps=max(1,STEP//GRID)+1
    while q:
        c=q.popleft(); iz,rem=divmod(c,NY*NX); iy,ix=divmod(rem,NX)
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx,ny=ix+dx,iy+dy
            if not(0<=nx<NX and 0<=ny<NY): continue
            for dz in range(-steps,steps+1):
                nz=iz+dz
                if not(0<=nz<NZ): continue
                n=nz*NY*NX+ny*NX+nx
                if stand[n] and not seen[n]: seen[n]=1;q.append(n)
    return seen

seeds=[]
for p in [(15,-318,300),(896,2912,40)]:
    c=(int((p[2]-lo[2])//GRID)*NY*NX+int((p[1]-lo[1])//GRID)*NX+int((p[0]-lo[0])//GRID))
    for dz in range(-4,12): seeds.append(c+dz*NY*NX)

print('\nbuilding mixed mask (boxes + pitched slabs)...')
mm=mask_mixed()
sm=standable(mm)
rm=flood(sm,seeds)
print(f'solid    {sum(mm):,}   (exact brushes were 44,636; pure AABB was 81,774)')
print(f'standable {sum(sm):,}  (exact 22,312; pure AABB 18,027)')
print(f'REACHABLE {sum(rm):,}  (exact 16,698; pure AABB 2,768)')
print(f'recovered {100*sum(rm)/16698:.1f}% of the exact reachable space')

json.dump({'boxes': plain + slabs}, open('slabbed.json','w'))
print(f'\nwrote slabbed.json: {len(plain)+len(slabs)} solids')
