"""Is a plate a genuine upper storey, or stranded geometry?

Three outcomes, and they want different treatment:
  reachable on top AND underneath -> a real two-level space, leave it
  reachable underneath only       -> a roof; fine, nobody stands on it
  reachable on top only, or neither -> stranded
"""
import json, collections, math
GRID, HERO, STEP = 64, 120, 40
p = json.load(open('dust2_half.json'))
B = p['boxes']
lo = lambda b,i: b['origin'][i]-b['extents'][i]/2
hi = lambda b,i: b['origin'][i]+b['extents'][i]/2
mn = [min(lo(b,i) for b in B) for i in range(3)]
mx = [max(hi(b,i) for b in B) for i in range(3)]
NX=int((mx[0]-mn[0])//GRID)+2; NY=int((mx[1]-mn[1])//GRID)+2; NZ=int((mx[2]-mn[2])//GRID)+3
N=NX*NY*NZ
def rotm(pi,ya,ro=0.0):
    pi,ya,ro=math.radians(pi),math.radians(ya),math.radians(ro)
    cp,sp,cy,sy,cr,sr=math.cos(pi),math.sin(pi),math.cos(ya),math.sin(ya),math.cos(ro),math.sin(ro)
    return [[cp*cy,sr*sp*cy-cr*sy,cr*sp*cy+sr*sy],[cp*sy,sr*sp*sy+cr*cy,cr*sp*sy-sr*cy],[-sp,sr*cp,cr*cp]]
mask=bytearray(N)
for b in B:
    o,e,a=b['origin'],b['extents'],b['angles']
    if abs(a[0])>0.01:
        R=rotm(*a); h=[e[i]/2 for i in range(3)]; cs=[]
        for sx in(-1,1):
            for sy in(-1,1):
                for sz in(-1,1):
                    v=[sum(R[i][k]*[sx*h[0],sy*h[1],sz*h[2]][k] for k in range(3)) for i in range(3)]
                    cs.append([o[i]+v[i] for i in range(3)])
        bl=[min(c[i] for c in cs) for i in range(3)]; bh=[max(c[i] for c in cs) for i in range(3)]
        for iz in range(max(0,int((bl[2]-mn[2])//GRID)),min(NZ-1,int((bh[2]-mn[2])//GRID))+1):
            cz=mn[2]+iz*GRID+GRID/2
            for iy in range(max(0,int((bl[1]-mn[1])//GRID)),min(NY-1,int((bh[1]-mn[1])//GRID))+1):
                cy=mn[1]+iy*GRID+GRID/2
                base=iz*NY*NX+iy*NX
                for ix in range(max(0,int((bl[0]-mn[0])//GRID)),min(NX-1,int((bh[0]-mn[0])//GRID))+1):
                    cx=mn[0]+ix*GRID+GRID/2
                    l=[sum(R[k][i]*[cx-o[0],cy-o[1],cz-o[2]][k] for k in range(3)) for i in range(3)]
                    if abs(l[0])<=h[0] and abs(l[1])<=h[1] and abs(l[2])<=h[2]: mask[base+ix]=1
    else:
        for iz in range(max(0,int((lo(b,2)-mn[2])//GRID)),min(NZ-1,int((hi(b,2)-mn[2])//GRID))+1):
            for iy in range(max(0,int((lo(b,1)-mn[1])//GRID)),min(NY-1,int((hi(b,1)-mn[1])//GRID))+1):
                base=iz*NY*NX+iy*NX
                for ix in range(max(0,int((lo(b,0)-mn[0])//GRID)),min(NX-1,int((hi(b,0)-mn[0])//GRID))+1):
                    mask[base+ix]=1
need=max(1,HERO//GRID)
stand=bytearray(N)
for iz in range(1,NZ):
    for iy in range(NY):
        base=iz*NY*NX+iy*NX; below=(iz-1)*NY*NX+iy*NX
        for ix in range(NX):
            if mask[base+ix] or not mask[below+ix]: continue
            ok=True
            for k in range(1,need+1):
                if iz+k>=NZ or mask[(iz+k)*NY*NX+iy*NX+ix]: ok=False;break
            if ok: stand[base+ix]=1
seeds=[]
for en in p['entities']:
    o=en['origin']
    c=int((o[2]-mn[2])//GRID)*NY*NX+int((o[1]-mn[1])//GRID)*NX+int((o[0]-mn[0])//GRID)
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
print(f'reachable cells {sum(reach):,}')

def report(name):
    b=[x for x in B if x['name']==name][0]
    ix0=max(0,int((lo(b,0)-mn[0])//GRID)); ix1=min(NX-1,int((hi(b,0)-mn[0])//GRID))
    iy0=max(0,int((lo(b,1)-mn[1])//GRID)); iy1=min(NY-1,int((hi(b,1)-mn[1])//GRID))
    ztop=int((hi(b,2)-mn[2])//GRID); zbot=int((lo(b,2)-mn[2])//GRID)
    on=under=0; cells=0
    for iy in range(iy0,iy1+1):
        for ix in range(ix0,ix1+1):
            cells+=1
            for dz in (0,1,2):
                if ztop+dz<NZ and reach[(ztop+dz)*NY*NX+iy*NX+ix]: on+=1; break
            for z in range(0,max(0,zbot)):
                if reach[z*NY*NX+iy*NX+ix]: under+=1; break
    print(f'{name}: {cells} columns  reachable ON TOP {100*on/cells:.0f}%  '
          f'reachable UNDERNEATH {100*under/cells:.0f}%')
    return on/cells, under/cells

for n in ['axis_199','axis_42','axis_475','axis_473','axis_355','axis_470','axis_546','axis_62','axis_63','axis_763','axis_764','axis_769']:
    try: report(n)
    except Exception as e: print(n,'?',e)
