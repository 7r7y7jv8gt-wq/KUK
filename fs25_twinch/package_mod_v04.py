"""Reproducible reference-inspired front assembly and original weathered textures."""
from pathlib import Path
import xml.etree.ElementTree as E
import numpy as np
from PIL import Image, ImageDraw
import math, shutil, json
from zipfile import ZipFile, ZIP_DEFLATED
HERE=Path(__file__).resolve().parent;OUT=HERE.parent/'FS25_TWinch_v04';OLD=HERE.parent/'FS25_TWinch_v03'
shutil.copytree(OLD,OUT,dirs_exist_ok=True);(OUT/'textures').mkdir(exist_ok=True)
r=E.parse(OUT/'twinch.i3d').getroot();root=r.find('Scene')[0];shapes=r.find('Shapes');materials=r.find('Materials');files=r.find('Files');nodes={n.get('name'):n for n in root.iter()};blade=nodes['bladeLift'];visual=nodes['visual']
sid=max(int(s.get('shapeId')) for s in shapes)+1;nid=max(int(n.get('nodeId','0')) for n in root.iter())+1
fmt=lambda p:' '.join(f'{x:.7g}' for x in p)
def mesh(name,p,faces,mat=2,parent=blade,frontuv=False):
 global sid,nid
 s=E.SubElement(shapes,'IndexedTriangleSet',name=name,shapeId=str(sid));vs=E.SubElement(s,'Vertices',count=str(len(faces)*3),normal='true',uv0='true');ts=E.SubElement(s,'Triangles',count=str(len(faces)))
 for j,f in enumerate(faces):
  a,b,c=np.array([p[i] for i in f]);normal=np.cross(b-a,c-a);normal/=np.linalg.norm(normal)
  for i in f:
   pos=np.array(p[i]);local=pos-np.array([0,.7,1.2]) if parent is blade else pos
   axes=[k for k in range(3) if k!=np.argmax(abs(normal))];uv=pos[axes]*1.4
   if frontuv:uv=[(pos[0]+1.1)/2.2,(pos[1]-.1)/1.2]
   E.SubElement(vs,'v',p=fmt(local),n=fmt(normal),t0=fmt(uv))
  E.SubElement(ts,'t',vi=f'{j*3} {j*3+1} {j*3+2}')
 sub=E.SubElement(s,'Subsets',count='1');E.SubElement(sub,'Subset',firstVertex='0',numVertices=str(len(vs)),firstIndex='0',numIndices=str(len(vs)))
 E.SubElement(parent,'Shape',name=name,nodeId=str(nid),shapeId=str(sid),materialIds=str(mat),castsShadows='true',receiveShadows='true');sid+=1;nid+=1
facesbox=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
def box(name,c,size,mat=2,parent=blade):
 x,y,z=c;dx,dy,dz=np.array(size)/2;p=[(x-dx,y-dy,z-dz),(x+dx,y-dy,z-dz),(x+dx,y+dy,z-dz),(x-dx,y+dy,z-dz),(x-dx,y-dy,z+dz),(x+dx,y-dy,z+dz),(x+dx,y+dy,z+dz),(x-dx,y+dy,z+dz)];mesh(name,p,facesbox,mat,parent)
def tube(name,path,radius,mat=8,parent=blade,closed=False):
 path=np.array(path);p=[];N=len(path);segments=8
 for i,c in enumerate(path):
  t=path[(i+1)%N]-path[(i-1)%N] if closed else path[min(i+1,N-1)]-path[max(0,i-1)];t/=np.linalg.norm(t);ref=np.array([0.,1,0]) if abs(t[1])<.9 else np.array([1.,0,0]);u=np.cross(t,ref);u/=np.linalg.norm(u);v=np.cross(t,u)
  for k in range(segments):p.append(c+radius*(u*math.cos(k*2*math.pi/segments)+v*math.sin(k*2*math.pi/segments)))
 f=[]
 for i in range(N if closed else N-1):
  for k in range(segments):a=i*segments+k;b=i*segments+(k+1)%segments;c=((i+1)%N)*segments+(k+1)%segments;d=((i+1)%N)*segments+k;f.extend([(a,b,c),(a,c,d)])
 mesh(name,p,f,mat,parent)
# Every old visual mesh gets usable box-projected UV coordinates.
for s in shapes:
 for v in s.find('Vertices'):
  normal=np.array(list(map(float,v.get('n','0 1 0').split())));p=np.array(list(map(float,v.get('p').split())));axes=[i for i in range(3) if i!=np.argmax(abs(normal))];v.set('t0',fmt(p[axes]*1.4))
for n in list(blade):
 if n.tag=='Shape' and n.get('name')!='bladeCollision':blade.remove(n)
for n in list(visual):
 if n.get('name') in ['fairleadFrame','winchDrumHousing']:visual.remove(n)
# Bent, tapered plate; narrow upper edge and broad grounded cutting edge.
profile=[(.14,2.09,1.10),(.27,2.025,1.08),(.79,1.89,1.02),(1.27,1.82,.97)]
p=[]
for y,z,w in profile:p.extend([(-w,y,z),(w,y,z),(-w,y,z-.055),(w,y,z-.055)])
f=[]
for j in range(3):
 a=j*4;b=(j+1)*4;f.extend([(a,a+1,b+1),(a,b+1,b),(a+2,b+3,a+3),(a+2,b+2,b+3),(a,b,a+2),(a+2,b,b+2),(a+1,a+3,b+1),(a+3,b+3,b+1)])
f.extend([(0,2,3),(0,3,1),(12,13,15),(12,15,14)]);mesh('BentWornBlade',p,f,10,frontuv=True)
box('ReplaceableCuttingEdge',(0,.17,2.10),(2.23,.15,.075),11)
for x in np.linspace(-.98,.98,9):box('CuttingEdgeBolt',(x,.205,2.148),(.035,.035,.012),12)
for sign in [-1,1]:
 # Extruded triangular tower with pinned upper end, thick edge gussets.
 x=sign*.68;outline=[(.26,1.96),(1.27,1.76),(1.73,1.67),(1.68,1.39),(.62,1.37)]
 p=[(xx,y,z) for xx in [x-.045,x+.045] for y,z in outline];f=[]
 for i in range(1,4):f.extend([(0,i+1,i),(5,5+i,6+i)])
 for i in range(5):j=(i+1)%5;f.extend([(i,j,j+5),(i,j+5,i+5)])
 mesh('BladeTower',p,f,2)
 box('Reflector',(sign*.81,1.20,1.875),(.25,.045,.018),5)
 tube('TowerWeld',[(x-.047,y,z) for y,z in outline+[outline[0]]],.007,11)
 # Recovery eyes have actual open centers and pinned shackles.
 tube('RecoveryShackle',[(sign*.88+.047*math.cos(t),1.02+.075*math.sin(t),1.944) for t in np.linspace(0,2*math.pi,25)[:-1]],.011,12,closed=True)
 box('ShacklePin',(sign*.88,1.02,1.953),(.10,.014,.018),12)
# Rounded cast fairlead with a genuine opening and visible horizontal rollers.
p=[];N=40
for z in [1.92,2.055]:
 for rx,ry in [(.29,.18),(.195,.075)]:
  p.extend([(rx*math.cos(t),1.49+ry*math.sin(t),z) for t in np.linspace(0,2*math.pi,N,endpoint=False)])
f=[]
for i in range(N):j=(i+1)%N;f.extend([(i,j,j+80),(i,j+80,i+80),(i+40,i+120,j+120),(i+40,j+120,j+40),(i+80,j+80,j+120),(i+80,j+120,i+120),(i,j+40,j),(i,i+40,j+40)])
mesh('GreenCastFairlead',p,f,1)
for y in [1.435,1.545]:tube('FairleadRoller',[(-.175,y,1.99),(.175,y,1.99)],.018,12)
nodes['winchAnchor'].set('translation','0 .79 .87')
# Forged hook and a short alternating oval-link chain.
tube('ForgedHook',[(.055*math.cos(t),1.34+.09*math.sin(t),2.085) for t in np.linspace(-.4,4.8,24)],.016,6)
tube('HookSafetyGate',[(.05,1.305,2.085),(.006,1.245,2.085)],.005,12)
for j in range(9):
 path=[]
 for t in np.linspace(0,2*math.pi,24,endpoint=False):
  a=.026*math.cos(t);y=1.23-j*.061+.045*math.sin(t);path.append((a if j%2==0 else 0,y,2.08+(a if j%2 else 0)))
 tube('RecoveryChain',path,.0065,12,closed=True)
# Front engine/winch bay masks the blank flat housing face with reinforced gray steel.
box('FrontBay',(0,1.75,1.29),(1.10,1.08,.19),2,visual)
box('RecessedFrontGrille',(0,1.85,1.399),(.84,.66,.024),4,visual)
for y in np.linspace(1.55,2.14,11):box('FrontGrilleSlat',(0,y,1.419),(.86,.015,.025),2,visual)
for x in [-.50,.50]:
 box('BayUpright',(x,1.77,1.435),(.052,1.03,.045),2,visual)
 for y in [1.32,1.68,2.18]:box('BayFastener',(x,y,1.467),(.025,.025,.016),12,visual)
tube('WinchDrum',[(-.35,1.20,1.51),(.35,1.20,1.51)],.13,2,visual)
for x in np.linspace(-.29,.29,38):tube('SteelCableOnDrum',[(x,1.20+.134*math.sin(t),1.51+.134*math.cos(t)) for t in np.linspace(0,2*math.pi,24,endpoint=False)],.005,12,visual,True)
# Texture sets: original deterministic paint, scratches, steel wear and soil.
colors={1:(45,153,24),2:(61,68,71),3:(47,46,42),4:(18,23,24),5:(173,29,23),6:(222,102,19),7:(38,53,63),8:(136,144,145),9:(217,181,27),10:(87,95,98),11:(119,119,113),12:(154,161,162)}
for i in [10,11,12]:E.SubElement(materials,'Material',name={10:'WornBladeSteel',11:'CuttingSteel',12:'MachinedSteel'}[i],materialId=str(i))
rng=np.random.default_rng(302);size=1024
for mid,color in colors.items():
 noise=rng.normal(0,1,(size,size));coarse=np.array(Image.fromarray(rng.integers(0,255,(32,32),dtype=np.uint8)).resize((size,size),Image.Resampling.BICUBIC))/255
 rgb=np.clip(np.array(color)[None,None,:]*(.89+.16*coarse[:,:,None])+noise[:,:,None]*2,0,255)
 scratches=Image.new('L',(size,size));d=ImageDraw.Draw(scratches)
 for _ in range(240 if mid in [3,10,11] else 55):
  x,y=rng.integers(0,size,2);d.line((int(x),int(y),int(x+rng.integers(8,100)),int(y+rng.integers(-5,6))),fill=int(rng.integers(50,180)),width=1)
 mask=np.array(scratches)/255;rgb=rgb*(1-mask[:,:,None]*.4)+np.array([146,143,128])*mask[:,:,None]*.4
 if mid==10:
  # DDS/UV origin is lower left: grime concentrated at lower blade height.
  band=np.linspace(0,1,size)[:,None];dirt=np.clip((band-.58)*1.6+coarse*.19,0,.72);rgb=rgb*(1-dirt[:,:,None])+np.array([78,61,40])*dirt[:,:,None]
 if mid==3:rgb=rgb*(.78+.22*coarse[:,:,None])
 height=coarse*.025+noise*.001;gy,gx=np.gradient(height);normal=np.stack((-gx*6,-gy*6,np.ones_like(gx)),axis=2);normal/=np.linalg.norm(normal,axis=2)[:,:,None]
 gloss=np.empty_like(rgb);gloss[:]=[95 if mid in [1,5,6] else 58,100,200 if mid in [8,11,12] else 25];gloss[:,:,0]+=coarse*20
 if mid==12:gloss[:,:,0]=190
 for kind,array in [('diffuse',rgb),('normal',(normal*.5+.5)*255),('gloss',gloss)]:
  name=f'textures/m{mid}_{kind}.dds';im=Image.fromarray(np.uint8(np.clip(array,0,255))).convert('RGBA');im.save(OUT/name,pixel_format='DXT5')
  # Pillow writes one level; append every mip and repair DDS mip flags/count.
  data=bytearray((OUT/name).read_bytes());level=im
  while level.width>1:level=level.resize((max(1,level.width//2),max(1,level.height//2)),Image.Resampling.LANCZOS);import io;b=io.BytesIO();level.save(b,format='DDS',pixel_format='DXT5');data.extend(b.getvalue()[128:])
  import struct
  flags=struct.unpack_from('<I',data,8)[0]|0x20000;struct.pack_into('<I',data,8,flags);struct.pack_into('<I',data,28,11);struct.pack_into('<I',data,108,0x401008);(OUT/name).write_bytes(data)
  fid=str(len(files)+1);E.SubElement(files,'File',fileId=fid,filename=name)
  mat=next(m for m in materials if m.get('materialId')==str(mid));E.SubElement(mat,{'diffuse':'Texture','normal':'Normalmap','gloss':'Glossmap'}[kind],fileId=fid)
 for key,val in [('diffuseColor','1 1 1 1'),('specularColor','.35 .4 .15')]:mat.set(key,val)
used={n.get('shapeId') for n in root.iter('Shape')}
for s in list(shapes):
 if s.get('shapeId') not in used:shapes.remove(s)
v=E.parse(OUT/'twinch.xml').getroot();desc=E.parse(OUT/'modDesc.xml').getroot();v.set('type','twinchV04');desc.find('vehicleTypes/type').set('name','twinchV04');desc.find('version').text='0.4.0.0';desc.find('title/en').text='T-Winch v04 - Detailed Front and Weathered Steel'
for n in v.findall('storeData/name/*'):n.text='T-Winch 30.2 v04'
v.find('annotation').text='v04 reference-inspired front assembly and textured materials. Game validation pending.'
mapping=v.find('i3dMappings');mapping.clear();seen=set()
def walk(n,path):
 name=n.get('name')
 if name and name not in seen:E.SubElement(mapping,'i3dMapping',id=name,node=path);seen.add(name)
 for i,c in enumerate(n):walk(c,f'{path}{i}' if path.endswith('>') else f'{path}|{i}')
walk(root,'0>')
for alias,target in [('wheelBackLeft','rearLeft'),('wheelBackRight','rearRight')]:E.SubElement(mapping,'i3dMapping',id=alias,node=next(n.get('node') for n in mapping if n.get('id')==target))
for tree,name in [(r,'twinch.i3d'),(v,'twinch.xml'),(desc,'modDesc.xml')]:E.indent(tree);E.ElementTree(tree).write(OUT/name,encoding='utf-8',xml_declaration=True)
(OUT/'TESTING.txt').write_text((OLD/'TESTING.txt').read_text().replace('v03','v04')+'\nV04: new tapered blade, gusset towers, fairlead, chain, front grille, cable drum, weathered diffuse/normal/gloss textures. Inspect both raised/lowered positions. Reference-inspired approximation, not a manufacturer CAD model.\n')
(OUT/'validation.json').write_text(json.dumps({'version':'0.4.0.0','game_test':'not run','textures':'original procedural diffuse, normal and gloss; 1024px full mip chains'},indent=2))
with ZipFile(HERE.parent/'FS25_TWinch_v04.zip','w',ZIP_DEFLATED) as z:
 for f in sorted(OUT.rglob('*')):
  if f.is_file():z.write(f,f.relative_to(OUT))
print('Built',OUT)
