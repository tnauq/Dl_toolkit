import struct, itertools, math, json, collections
exec(open('slab.py').read().split('# ------------------------------------------------------------------ verify')[0])
GRID,PLAYER_H,STEP=32,72,18
lo=[-1312,-496,-64]; hi=[2400,3296,446]
NX=int((hi[0]-lo[0])//GRID)+1; NY=int((hi[1]-lo[1])//GRID)+1; NZ=int((hi[2]-lo[2])//GRID)+1
N=NX*NY*NZ
srcs={b['src'] for b in boxes}
brushes=[]
for bi,(f,n,c) in enumerate(BRUSHES):
    if bi in srcs: brushes.append([PLANES[BSIDES[s][0]][:4] for s in range(f,f+n)])
def exact():
    m=bytearray(N)
    for pls in brushes:
        xs=[];ys=[];zs=[]
        for a,b_,c_ in itertools.combinations(pls,3):
            mm=[list(a[:3]),list(b_[:3]),list(c_[:3])]
            det=(mm[0][0]*(mm[1][1]*mm[2][2]-mm[1][2]*mm[2][1])-mm[0][1]*(mm[1][0]*mm[2][2]-mm[1][2]*mm[2][0])+mm[0][2]*(mm[1][0]*mm[2][1]-mm[1][1]*mm[2][0]))
            if abs(det)<1e-6: continue
            rhs=[a[3],b_[3],c_[3]]
            def d3(q): return (q[0][0]*(q[1][1]*q[2][2]-q[1][2]*q[2][1])-q[0][1]*(q[1][0]*q[2][2]-q[1][2]*q[2][0])+q[0][2]*(q[1][0]*q[2][1]-q[1][1]*q[2][0]))
            p=[]
            for i in range(3):
                q=[r[:] for r in mm]
                for r in range(3): q[r][i]=rhs[r]
                p.append(d3(q)/det)
            if all(pl[0]*p[0]+pl[1]*p[1]+pl[2]*p[2]-pl[3]<=0.1 for pl in pls):
                xs.append(p[0]);ys.append(p[1]);zs.append(p[2])
        if not xs: continue
        for iz in range(max(0,int((min(zs)-lo[2])//GRID)),min(NZ-1,int((max(zs)-lo[2])//GRID))+1):
            cz=lo[2]+iz*GRID+GRID/2
            for iy in range(max(0,int((min(ys)-lo[1])//GRID)),min(NY-1,int((max(ys)-lo[1])//GRID))+1):
                cy=lo[1]+iy*GRID+GRID/2
                base=iz*NY*NX+iy*NX
                for ix in range(max(0,int((min(xs)-lo[0])//GRID)),min(NX-1,int((max(xs)-lo[0])//GRID))+1):
                    cx=lo[0]+ix*GRID+GRID/2
                    if all(pl[0]*cx+pl[1]*cy+pl[2]*cz-pl[3]<=0 for pl in pls): m[base+ix]=1
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
                if 0<=nz<NZ:
                    n2=nz*NY*NX+ny*NX+nx
                    if stand[n2] and not seen[n2]: seen[n2]=1;q.append(n2)
    return seen
seeds=[]
for p in [(15,-318,300),(896,2912,40)]:
    c=(int((p[2]-lo[2])//GRID)*NY*NX+int((p[1]-lo[1])//GRID)*NX+int((p[0]-lo[0])//GRID))
    for dz in range(-4,12): seeds.append(c+dz*NY*NX)
me=exact(); re_=flood(standable(me),seeds)
sl=json.load(open('slabbed.json'))['boxes']
plain=[b for b in sl if b['kind']!='ramp-slab']; slabs=[b for b in sl if b['kind']=='ramp-slab']

def mask_mixed():
    m=bytearray(N)
    for b in plain:
        o,e=b['origin'],b['extents']
        for iz in range(max(0,int((o[2]-e[2]/2-lo[2])//GRID)),min(NZ-1,int((o[2]+e[2]/2-lo[2])//GRID))+1):
            for iy in range(max(0,int((o[1]-e[1]/2-lo[1])//GRID)),min(NY-1,int((o[1]+e[1]/2-lo[1])//GRID))+1):
                base=iz*NY*NX+iy*NX
                for ix in range(max(0,int((o[0]-e[0]/2-lo[0])//GRID)),min(NX-1,int((o[0]+e[0]/2-lo[0])//GRID))+1):
                    m[base+ix]=1
    for b in slabs:
        o,e,a=b['origin'],b['extents'],b['angles']
        R=rotm(a[0],a[1],a[2]); h=[e[i]/2 for i in range(3)]
        cs=[]
        for sx in(-1,1):
            for sy in(-1,1):
                for sz in(-1,1):
                    v=mul(R,[sx*h[0],sy*h[1],sz*h[2]]); cs.append([o[i]+v[i] for i in range(3)])
        mn=[min(c[i] for c in cs) for i in range(3)]; mx=[max(c[i] for c in cs) for i in range(3)]
        for iz in range(max(0,int((mn[2]-lo[2])//GRID)),min(NZ-1,int((mx[2]-lo[2])//GRID))+1):
            cz=lo[2]+iz*GRID+GRID/2
            for iy in range(max(0,int((mn[1]-lo[1])//GRID)),min(NY-1,int((mx[1]-lo[1])//GRID))+1):
                cy=lo[1]+iy*GRID+GRID/2
                base=iz*NY*NX+iy*NX
                for ix in range(max(0,int((mn[0]-lo[0])//GRID)),min(NX-1,int((mx[0]-lo[0])//GRID))+1):
                    cx=lo[0]+ix*GRID+GRID/2
                    l=mulT(R,[cx-o[0],cy-o[1],cz-o[2]])
                    if abs(l[0])<=h[0] and abs(l[1])<=h[1] and abs(l[2])<=h[2]: m[base+ix]=1
    return m
mm=mask_mixed(); rm=flood(standable(mm),seeds)
# Compare FOOTPRINTS, not voxels. The slabbed floors sit at slightly
# different heights, so identical ground shows up in different z cells and
# a cell-wise diff reports nonsense. What matters is whether the same
# (x,y) ground is still reachable at ANY height.
def foot(mask):
    f=set()
    for i in range(N):
        if mask[i]:
            iz,rem=divmod(i,NY*NX); iy,ix=divmod(rem,NX); f.add((ix,iy))
    return f
fe, fs = foot(re_), foot(rm)
print(f'reachable FOOTPRINT: exact {len(fe):,} columns   slabbed {len(fs):,}')
print(f'  kept    {len(fe&fs):,} ({100*len(fe&fs)/len(fe):.1f}% of exact)')
print(f'  lost    {len(fe-fs):,}')
print(f'  gained  {len(fs-fe):,}')
lost=[]
for (ix,iy) in (fe-fs): lost.append(iy*NX+ix)
print(f'exact reachable voxels {sum(re_):,}   slabbed {sum(rm):,}')
g=collections.Counter()
for c in lost:
    iy,ix=divmod(c,NX)
    g[(round((lo[0]+ix*GRID)/512)*512, round((lo[1]+iy*GRID)/512)*512)]+=1
print('lost regions (x,y) -> cells:')
for (x,y),n in g.most_common(10): print(f'   ({x:6d},{y:6d})  {n}')
