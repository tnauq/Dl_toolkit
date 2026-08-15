"""Close the dead void under raised floors, and ONLY where it is dead.

A global raise of the base plate would bury 1,602 cells of legitimate
z=0 ground under a plateau. So the fill is masked twice:

  1. only cells that have a raised floor above the base at all
  2. minus cells where reachable space exists between the two, because
     that is a genuine lower route, not dead air

Works in the ORIGINAL CS units on unsimplified.json, then the result is
carried through the existing pipeline. Reachability comes from the plan
as it stands, so two-level spaces already proven reachable are protected.
"""
import json, collections, math

G = 64
BASE_TOP, RAISED = 0.0, 128.0
X0, X1, Y0, Y1 = -1312, 2400, -496, 3296
NXc, NYc = (X1-X0)//G, (Y1-Y0)//G

un = json.load(open('unsimplified.json'))['boxes']
lo = lambda b,i: b['origin'][i]-b['extents'][i]/2
hi = lambda b,i: b['origin'][i]+b['extents'][i]/2

# --- 1. where is there a raised floor over the base? ---
has_base = [[False]*NYc for _ in range(NXc)]
has_up   = [[False]*NYc for _ in range(NXc)]
for b in un:
    if abs(b['angles'][0]) > 0.01: continue
    t = hi(b,2)
    base = abs(t-BASE_TOP) < 1
    up   = t > BASE_TOP + 32 and t <= RAISED + 32
    if not (base or up): continue
    i0=max(0,int((lo(b,0)-X0)//G)); i1=min(NXc-1,int((hi(b,0)-X0)//G))
    j0=max(0,int((lo(b,1)-Y0)//G)); j1=min(NYc-1,int((hi(b,1)-Y0)//G))
    for i in range(i0,i1+1):
        for j in range(j0,j1+1):
            if base: has_base[i][j] = True
            else: has_up[i][j] = True

# --- 2. is there reachable space in the gap? ---
# Reachability is computed on the CURRENT plan (Deadlock scale), so the
# two-level spaces already measured as real are protected automatically.
S = 1.667
plan = json.load(open('dust2_half.json'))
PB = plan['boxes']
GD, HERO = 64, 120
mn = [min(lo(b,i) for b in PB) for i in range(3)]
mx = [max(hi(b,i) for b in PB) for i in range(3)]
NX=int((mx[0]-mn[0])//GD)+2; NY=int((mx[1]-mn[1])//GD)+2; NZ=int((mx[2]-mn[2])//GD)+3
N=NX*NY*NZ
def rotm(pi,ya,ro=0.0):
    pi,ya,ro=math.radians(pi),math.radians(ya),math.radians(ro)
    cp,sp,cy,sy,cr,sr=math.cos(pi),math.sin(pi),math.cos(ya),math.sin(ya),math.cos(ro),math.sin(ro)
    return [[cp*cy,sr*sp*cy-cr*sy,cr*sp*cy+sr*sy],[cp*sy,sr*sp*sy+cr*cy,cr*sp*sy-sr*cy],[-sp,sr*cp,cr*cp]]
mask=bytearray(N)
for b in PB:
    o,e,a=b['origin'],b['extents'],b['angles']
    if abs(a[0])>0.01:
        R=rotm(*a); h=[e[i]/2 for i in range(3)]; cs=[]
        for sx in(-1,1):
            for sy in(-1,1):
                for sz in(-1,1):
                    v=[sum(R[i][k]*[sx*h[0],sy*h[1],sz*h[2]][k] for k in range(3)) for i in range(3)]
                    cs.append([o[i]+v[i] for i in range(3)])
        bl=[min(c[i] for c in cs) for i in range(3)]; bh=[max(c[i] for c in cs) for i in range(3)]
        for iz in range(max(0,int((bl[2]-mn[2])//GD)),min(NZ-1,int((bh[2]-mn[2])//GD))+1):
            cz=mn[2]+iz*GD+GD/2
            for iy in range(max(0,int((bl[1]-mn[1])//GD)),min(NY-1,int((bh[1]-mn[1])//GD))+1):
                cy=mn[1]+iy*GD+GD/2
                base_=iz*NY*NX+iy*NX
                for ix in range(max(0,int((bl[0]-mn[0])//GD)),min(NX-1,int((bh[0]-mn[0])//GD))+1):
                    cx=mn[0]+ix*GD+GD/2
                    l=[sum(R[k][i]*[cx-o[0],cy-o[1],cz-o[2]][k] for k in range(3)) for i in range(3)]
                    if abs(l[0])<=h[0] and abs(l[1])<=h[1] and abs(l[2])<=h[2]: mask[base_+ix]=1
    else:
        for iz in range(max(0,int((lo(b,2)-mn[2])//GD)),min(NZ-1,int((hi(b,2)-mn[2])//GD))+1):
            for iy in range(max(0,int((lo(b,1)-mn[1])//GD)),min(NY-1,int((hi(b,1)-mn[1])//GD))+1):
                base_=iz*NY*NX+iy*NX
                for ix in range(max(0,int((lo(b,0)-mn[0])//GD)),min(NX-1,int((hi(b,0)-mn[0])//GD))+1):
                    mask[base_+ix]=1
need=max(1,HERO//GD); stand=bytearray(N)
for iz in range(1,NZ):
    for iy in range(NY):
        base_=iz*NY*NX+iy*NX; below=(iz-1)*NY*NX+iy*NX
        for ix in range(NX):
            if mask[base_+ix] or not mask[below+ix]: continue
            ok=True
            for k in range(1,need+1):
                if iz+k>=NZ or mask[(iz+k)*NY*NX+iy*NX+ix]: ok=False;break
            if ok: stand[base_+ix]=1
seeds=[]
for en in plan['entities']:
    o=en['origin']
    c=int((o[2]-mn[2])//GD)*NY*NX+int((o[1]-mn[1])//GD)*NX+int((o[0]-mn[0])//GD)
    for dz in range(-2,6):
        if 0<=c+dz*NY*NX<N: seeds.append(c+dz*NY*NX)
reach=bytearray(N); q=collections.deque()
for s in seeds:
    if stand[s] and not reach[s]: reach[s]=1;q.append(s)
while q:
    c0=q.popleft(); iz,rem=divmod(c0,NY*NX); iy,ix=divmod(rem,NX)
    for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
        nx,ny=ix+dx,iy+dy
        if not(0<=nx<NX and 0<=ny<NY): continue
        for dz in range(-3,2):
            nz=iz+dz
            if 0<=nz<NZ:
                n2=nz*NY*NX+ny*NX+nx
                if stand[n2] and not reach[n2]: reach[n2]=1;q.append(n2)

def gap_is_live(i,j):
    """Any reachable standing space between base and raised floor here?"""
    cx = (X0 + i*G + G/2)*S; cy = (Y0 + j*G + G/2)*S
    ix = int((cx-mn[0])//GD); iy = int((cy-mn[1])//GD)
    if not (0<=ix<NX and 0<=iy<NY): return True
    z0 = int((BASE_TOP*S-mn[2])//GD); z1 = int((RAISED*S-mn[2])//GD)
    for z in range(max(0,z0), min(NZ-1,z1)+1):
        if reach[z*NY*NX+iy*NX+ix]: return True
    return False

# First pass: mark live cells. Then DILATE by one cell before filling.
# gap_is_live samples only the centre column, so a cell that is half open
# route reads as dead; filling it eats the edge of a real corridor. The
# first run lost 465 reachable cells exactly that way.
livemask = [[False]*NYc for _ in range(NXc)]
gapmask  = [[False]*NYc for _ in range(NXc)]
for i in range(NXc):
    for j in range(NYc):
        if not (has_base[i][j] and has_up[i][j]): continue
        gapmask[i][j] = True
        if gap_is_live(i,j): livemask[i][j] = True

dil = [[livemask[i][j] for j in range(NYc)] for i in range(NXc)]
for i in range(NXc):
    for j in range(NYc):
        if not livemask[i][j]: continue
        for di in (-1,0,1):
            for dj in (-1,0,1):
                a,b_ = i+di, j+dj
                if 0<=a<NXc and 0<=b_<NYc: dil[a][b_] = True

fill, live, nogap = 0, 0, 0
cells=[]
for i in range(NXc):
    for j in range(NYc):
        if not gapmask[i][j]: nogap += 1; continue
        if dil[i][j]: live += 1; continue
        fill += 1; cells.append((i,j))
print(f'cells with a gap under a raised floor : {fill+live}')
print(f'  LIVE  (reachable route beneath, left alone): {live}')
print(f'  DEAD  (to fill)                            : {fill}')

# merge the fill cells into runs so we add tens of boxes, not thousands
used=set(); boxes=[]
cellset=set(cells)
for (i,j) in sorted(cellset):
    if (i,j) in used: continue
    w=0
    while (i+w,j) in cellset and (i+w,j) not in used: w+=1
    h=1
    while all((i+k,j+h) in cellset and (i+k,j+h) not in used for k in range(w)): h+=1
    for k in range(w):
        for l in range(h): used.add((i+k,j+l))
    x0=X0+i*G; y0=Y0+j*G
    boxes.append({'name':f'gapfill_{i}_{j}',
                  'origin':[round((x0+w*G/2)*S,1), round((y0+h*G/2)*S,1),
                            round(((BASE_TOP+RAISED)/2)*S,1)],
                  'extents':[round(w*G*S,1), round(h*G*S,1), round(RAISED*S,1)],
                  'angles':[0.0,0.0,0.0],
                  'material':'materials/dev/reflectivity_30.vmat'})
print(f'  merged into {len(boxes)} fill boxes')
plan['boxes'] = PB + boxes
json.dump(plan, open('dust2_half.json','w'), indent=1)
print(f'plan now {len(plan["boxes"])} boxes')
