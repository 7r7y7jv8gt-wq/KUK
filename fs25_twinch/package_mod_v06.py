"""V06: remove front pendant, explicitly control blade hydraulics, detailed steel tracks.

Uses the committed v04 package as baseline. All new artwork is procedural.
"""
from pathlib import Path
import xml.etree.ElementTree as E
import numpy as np
from PIL import Image, ImageDraw, ImageOps
import math,shutil,json,copy,io,struct
from zipfile import ZipFile, ZIP_DEFLATED
HERE=Path(__file__).resolve().parent;OUT=HERE.parent/'FS25_TWinch_v06';OLD=HERE.parent/'FS25_TWinch_v04'
shutil.copytree(OLD,OUT,dirs_exist_ok=True)
r=E.parse(OUT/'twinch.i3d').getroot();root=r.find('Scene')[0];shapes=r.find('Shapes');materials=r.find('Materials');files=r.find('Files');nodes={n.get('name'):n for n in root.iter()};blade=nodes['bladeLift'];visual=nodes['visual']
sid=max(int(s.get('shapeId')) for s in shapes)+1;nid=max(int(n.get('nodeId','0')) for n in root.iter())+1
fmt=lambda p:' '.join(f'{x:.7g}' for x in p)
facesbox=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
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
def group(parent,name,**attrs):
 global nid
 n=E.SubElement(parent,'TransformGroup',name=name,nodeId=str(nid),**attrs);nid+=1;return n

def lathe(name,profile,mat,parent,axis='z',center=(0,0,0),segments=32):
 """Capped revolved solid with smooth radial side normals and hard shoulders."""
 p=[]
 for z,radius in profile:
  for i in range(segments):
   t=i*2*math.pi/segments;q=(radius*math.cos(t),radius*math.sin(t),z)
   if axis=='x':q=(z,radius*math.cos(t),radius*math.sin(t))
   p.append(np.array(q)+center)
 f=[]
 for j in range(len(profile)-1):
  for i in range(segments):a=j*segments+i;b=j*segments+(i+1)%segments;c=b+segments;d=a+segments;f.extend([(a,b,c),(a,c,d)])
 p.extend([np.array(center)+(np.array([profile[0][0],0,0]) if axis=='x' else np.array([0,0,profile[0][0]])),np.array(center)+(np.array([profile[-1][0],0,0]) if axis=='x' else np.array([0,0,profile[-1][0]]))])
 for i in range(segments):j=(i+1)%segments;f.extend([(len(p)-2,j,i),(len(p)-1,(len(profile)-1)*segments+i,(len(profile)-1)*segments+j)])
 mesh(name,p,f,mat,parent)
 # Smooth only faces whose normal has a radial component; keep end caps hard.
 s=shapes[-1];vs=s.find('Vertices');ai=0 if axis=='x' else 2
 for vertex in vs:
  norm=np.array(list(map(float,vertex.get('n').split())))
  if abs(norm[ai])<.7:
   pos=np.array(list(map(float,vertex.get('p').split())))
   if parent is blade:pos+=np.array([0,.7,1.2])
   radial=pos-np.array(center);radial[ai]=0;radial/=np.linalg.norm(radial);vertex.set('n',fmt(radial))

# Remove the object the user marked, including its old roller and hook pieces.
removed=('GreenCastFairlead','FairleadRoller','ForgedHook','HookSafetyGate','RecoveryChain')
for n in list(blade):
 if n.get('name','').startswith(removed):blade.remove(n)
# Retain a discreet cable outlet inside the blade; no dangling cosmetic chain.
nodes['winchAnchor'].set('translation','0 .48 .65')
box('RecessedCableOutlet',(0,1.18,1.849),(.13,.065,.02),4)
# Put the hydraulic cylinder pairs outside the front bay, on real clevis mounts.
for sign,side in [(-1,'Right'),(1,'Left')]:
 base=nodes[f'hydraulic{side}BasePin'];barrel=nodes[f'hydraulic{side}Barrel'];pin=nodes[f'hydraulic{side}BladePin'];rod=nodes[f'hydraulic{side}Rod']
 base.set('translation',fmt((sign*.76,.91,1.13)));barrel.set('translation',base.get('translation'));pin.set('translation',fmt((sign*.76,.93,.57)))
 for n in list(barrel):barrel.remove(n)
 for n in list(rod):rod.remove(n)
 lathe(f'hydraulic{side}PaintedBarrel',[(0,.064),(.04,.074),(.445,.074),(.47,.083),(.515,.083),(.525,.052)],1,barrel)
 lathe(f'hydraulic{side}Gland',[(.475,.086),(.515,.086),(.525,.045)],2,barrel)
 lathe(f'hydraulic{side}ChromePiston',[(0,.036),(.55,.036)],12,rod)
 lathe(f'hydraulic{side}RodEye',[(-.050,.056),(.050,.056)],2,rod,axis='x')
 # Both mounting ears and pins stay in the same frames as the corresponding endpoints.
 for x in [-.065,.065]:box(f'{side}BaseClevis',(x,0,.016),(.027,.14,.14),2,base);box(f'{side}BladeClevis',(x,0,-.018),(.027,.15,.14),2,pin)
 lathe(f'{side}BasePivotPin',[(-.09,.031),(.09,.031)],12,base,axis='x')
 lathe(f'{side}BladePivotPin',[(-.09,.032),(.09,.032)],12,pin,axis='x')
 for x in [-.092,.092]:lathe(f'{side}PivotCap',[(x-.005,.043),(x+.005,.043)],11,pin,axis='x',segments=6)
 box(f'{side}ChassisCylinderBracket',(sign*.76,.84,1.12),(.17,.20,.21),2,visual)
 # Two hydraulic supply lines, fittings and retaining clamps on each moving barrel.
 for offset in [-.028,.028]:
  tube(f'{side}HydraulicHose',[(offset,-.082,.42),(offset,-.11,.37),(offset,-.12,.15),(offset,-.15,-.03),(offset,-.09,-.12),(offset,-.01,-.10)],.012,13,barrel)
  lathe(f'{side}HoseFitting',[(.408,.018),(.452,.018)],12,barrel,center=(offset,-.079,0),segments=6)
 for z in [.14,.34]:box(f'{side}HoseClamp',(0,-.113,z),(.10,.018,.025),2,barrel)
 # Hinged blade arms carry the lower plate back to the chassis hinge.
 tube(f'{side}BladeLiftArm',[(sign*.76,.70,1.22),(sign*.76,.65,1.51),(sign*.76,.53,1.87)],.075,2)
box('BladeHingeCrossmember',(0,.70,1.20),(1.68,.12,.13),2)

# Shared track-shoe prototype. Link frames continue using the tested 74-link loop.
prototype=E.Element('TransformGroup')
# A beveled, cast steel plate, rounded corners, two bolt pairs, full-width worn grouser.
outline=[(-.26,-.041),(.26,-.041),(.276,-.025),(.276,.025),(.26,.041),(-.26,.041),(-.276,.025),(-.276,-.025)]
p=[(x,y,z) for y in [-.018,.017] for x,z in outline];f=[]
for i in range(1,7):f.extend([(0,i+1,i),(8,8+i,9+i)])
for i in range(8):j=(i+1)%8;f.extend([(i,j,j+8),(i,j+8,i+8)])
mesh('CastTrackShoe',p,[tuple(reversed(t)) for t in f],3,prototype)
# Low sloped edges avoid the square-block appearance of the old belts.
p=[(x,y,z) for x in [-.272,.272] for y,z in [(.017,-.015),(.032,-.009),(.032,.009),(.017,.015)]]
mesh('WornTrackGrouser',p,facesbox,14,prototype)
for x in [-.157,.157]:
 box('ChainRail',(x,-.028,0),(.067,.025,.077),3,prototype)
 for z in [.047325]:lathe('TrackHingePin',[(-.018,.012),(.018,.012)],11,prototype,axis='x',center=(x,-.024,z),segments=12)
 for z in [-.025,.025]:lathe('ShoeBolt',[(.018,.014),(.025,.014)],11,prototype,axis='z',segments=6)
# Actual bolt geometry should face outward (+Y); transform the local axial bolt pair.
for n in list(prototype):
 if n.get('name')=='ShoeBolt':prototype.remove(n)
for x in [-.155,.155]:
 for z in [-.024,.024]:
  g=group(prototype,'TrackBoltSeat',translation=fmt((x,.018,z)),rotation='-90 0 0');lathe('TrackBolt',[(0,.012),(.008,.012)],11,g,segments=6)
# Two narrow guide horns leave room for the road-wheel faces.
for x in [-.043,.043]:
 p=[(x-.012,-.022,-.027),(x+.012,-.022,-.027),(x+.012,-.022,.027),(x-.012,-.022,.027),(x-.008,-.071,-.009),(x+.008,-.071,-.009),(x+.008,-.071,.009),(x-.008,-.071,.009)]
 mesh('TrackGuideHorn',p,facesbox,3,prototype)
for track in [nodes['trackLeft'],nodes['trackRight']]:
 for i,link in enumerate(track):
  link.clear();link.attrib.update(name=f'{track.get("name")}Link{i:02d}',nodeId=str(nid));nid+=1
  # Preserve the starting loop pose using the same arc-length function as Lua.
  length=4.68+2*math.pi*.37;s=i*length/74;arc=math.pi*.37
  if s<2.34:y,z,a=.785,-1.22+s,0
  elif s<2.34+arc:a=(s-2.34)/.37;y,z=.415+.37*math.cos(a),1.12+.37*math.sin(a)
  elif s<4.68+arc:y,z,a=.045,1.12-(s-2.34-arc),math.pi
  else:a=math.pi+(s-4.68-arc)/.37;y,z=.415+.37*math.cos(a),-1.22+.37*math.sin(a)
  link.set('translation',fmt((0,y,z)));link.set('rotation',fmt((math.degrees(a),0,0)))
  for source in prototype:
   part=copy.deepcopy(source)
   for child in part.iter():child.set('nodeId',str(nid));nid+=1
   # Keep link details under the animated frame; mesh data is shared.
   for child in part.iter('Shape'):child.set('name',f'{child.get("name")}_{i:02d}')
   link.append(part)
# Outer undercarriage guards show layered steel construction instead of bare disks.
for n in list(visual):
 if n.get('name','').startswith('TrackFrame'):visual.remove(n)
for sign in [-1,1]:
 box('TrackCarrierBeam',(sign*.88,.43,-.04),(.34,.24,2.02),2,visual)
 box('OuterTrackGuard',(sign*1.09,.39,-.04),(.055,.19,2.04),2,visual)
 for z in [-.84,-.42,0,.42,.84]:
  g=group(visual,'GuardBoltFrame',translation=fmt((sign*1.128,.39,z)),rotation=f'0 {sign*90} 0');lathe('GuardBolt',[(0,.019),(.012,.019)],11,g,segments=6)
# Toothed rear sprockets and reinforced front idlers rotate with existing wheel frames.
for idx in range(4):
 roller=nodes[f'roller_{idx}'];sign=-1 if idx<2 else 1
 position=list(map(float,roller.get('translation').split()));position[1]=.415;roller.set('translation',fmt(position))
 if idx in [0,2]:
  for n in list(roller):
   if n.get('name','').startswith('DriveWheel'):roller.remove(n)
 lathe('SprocketRim',[(-.205,.285),(-.185,.313),(.185,.313),(.205,.285)],3,roller,axis='x',segments=48)
 if idx in [0,2]:
  for j in range(24):
   t=2*math.pi*j/24;g=group(roller,'SprocketTooth',translation=fmt((0,.327*math.cos(t),.327*math.sin(t))),rotation=fmt((math.degrees(t),0,0)));box('SprocketToothSteel',(0,0,0),(.32,.043,.038),11,g)
 lathe('OuterWheelBoss',sorted([(sign*.195,.16),(sign*.22,.16)]),2,roller,axis='x',segments=32)
for idx in range(4,16):
 roller=nodes[f'roller_{idx}'];sign=-1 if idx<10 else 1
 lathe('RoadWheelRim',[(-.15,.155),(-.12,.177),(.12,.177),(.15,.155)],3,roller,axis='x')

# Neutral, restrained finishes. New maps replace the prior cloudy/speckled paint.
for mid,name in [(13,'HydraulicRubber'),(14,'WornGrouserSteel')]:E.SubElement(materials,'Material',name=name,materialId=str(mid))
colors={1:(36,121,23),2:(62,68,70),3:(53,52,47),4:(19,22,22),5:(171,28,24),6:(207,91,23),7:(38,49,54),8:(121,129,131),9:(195,158,32),10:(79,86,88),11:(109,111,106),12:(155,164,168),13:(21,23,24),14:(112,112,105)}
size=1024;rng=np.random.default_rng(305)
for mat in materials:
 for child in list(mat):mat.remove(child)
files.clear()
def save_dds(im,path):
 im=im.convert('RGBA');b=io.BytesIO();im.save(b,format='DDS',pixel_format='DXT5');data=bytearray(b.getvalue());level=im;mips=1
 while level.width>1 or level.height>1:
  level=level.resize((max(1,level.width//2),max(1,level.height//2)),Image.Resampling.LANCZOS);b=io.BytesIO();level.save(b,format='DDS',pixel_format='DXT5');data.extend(b.getvalue()[128:]);mips+=1
 struct.pack_into('<I',data,8,struct.unpack_from('<I',data,8)[0]|0x20000);struct.pack_into('<I',data,28,mips);struct.pack_into('<I',data,108,0x401008);path.write_bytes(data)
for mid,color in colors.items():
 coarse=np.array(Image.fromarray(rng.integers(0,255,(24,24),dtype=np.uint8)).resize((size,size),Image.Resampling.BICUBIC))/255
 fine=rng.normal(0,.65,(size,size));paint=mid in [1,5,6,9];variation=.016 if paint else .055
 rgb=np.array(color)[None,None,:]*(1+(coarse[:,:,None]-.5)*variation)+fine[:,:,None]*(.35 if paint else 1.0)
 scratch=Image.new('L',(size,size));d=ImageDraw.Draw(scratch)
 for _ in range(140 if paint else (1100 if mid==10 else (1900 if mid in [3,11,14] else 350))):
  x,y=rng.integers(0,size,2)
  if mid==10:
   y=min(size-1,int(rng.beta(6,2)*size))
   length=int(rng.integers(12,125));dy=int(rng.integers(-28,29));strength=int(rng.integers(30,120))
  else:length=int(rng.integers(5,65));dy=int(rng.integers(-3,4));strength=int(rng.integers(65,215))
  d.line((int(x),int(y),int(x)+length,int(y)+dy),fill=strength,width=1)
 wear=np.array(scratch)/255;rgb=rgb*(1-wear[:,:,None])+(np.array([109,111,104]) if paint else np.array([137,136,127]))*wear[:,:,None]
 if mid in [3,10,11]:
  if mid==10:
   v=np.linspace(1,0,size)[:,None];soil=np.clip((.38-v)*2.7+coarse*.12,0,.6)
  else:soil=np.clip((coarse-.4)*.7,0,.20)
  rgb=rgb*(1-soil[:,:,None])+np.array([65,53,36])*soil[:,:,None]
 if mid==14:rgb+=np.sin(np.arange(size)[None,:]*.7)[:,:,None]*1.2
 # Subtle normal variation avoids sparkling pits on painted panels.
 height=coarse*.002+fine*.00006-wear*.0018;gy,gx=np.gradient(height);normal=np.stack((-gx*3,-gy*3,np.ones_like(gx)),axis=2);normal/=np.linalg.norm(normal,axis=2)[:,:,None]
 gloss=np.empty_like(rgb);g=75 if paint else (210 if mid==12 else (95 if mid in [3,10,11,14] else 52));gloss[:]=[g,65,210 if mid in [3,10,11,12,14] else 20];gloss[:,:,0]+=(coarse-.5)*8
 for kind,array in [('diffuse',rgb),('normal',(normal*.5+.5)*255),('gloss',gloss)]:
  name=f'textures/m{mid}_{kind}.dds';save_dds(Image.fromarray(np.uint8(np.clip(array,0,255))),OUT/name);fid=str(len(files)+1);E.SubElement(files,'File',fileId=fid,filename=name);mat=next(m for m in materials if m.get('materialId')==str(mid));E.SubElement(mat,{'diffuse':'Texture','normal':'Normalmap','gloss':'Glossmap'}[kind],fileId=fid)
 mat.set('diffuseColor','1 1 1 1');mat.set('specularColor',fmt((g/255,.25,.75 if mid in [11,12,14] else .08)));mat.set('cosPower','24')
# Use FS25's stock vehicle material pipeline. Its Glossmap is a vehicle mask,
# not the RGB smoothness/specular/metalness preview map generated above.
stock={}
def stockfile(path):
 if path not in stock:
  stock[path]=str(len(files)+1);E.SubElement(files,'File',fileId=stock[path],filename=path)
 return stock[path]
shader=stockfile('$data/shaders/vehicleShader.xml');vmask=stockfile('$data/shared/default_vmask.dds')
for mat in materials:
 mid=int(mat.get('materialId'));mat.set('customShaderId',shader)
 mat.attrib.pop('specularColor',None);mat.attrib.pop('cosPower',None)
 mat.find('Glossmap').set('fileId',vmask)
 if mid in [1,2,5,6,9]:
  detail=['calibrated/calibratedPaint_diffuse.png','calibrated/calibratedPaint_normal.png','calibrated/calibratedPaint_specular.png'];smooth=.55;coat=.15
 elif mid in [4,13]:
  detail=['nonMetallic/rubber/rubberBlack_diffuse.png','nonMetallic/rubber/rubber_normal.png','nonMetallic/rubber/rubber_specular.png'];smooth=.25;coat=0
 elif mid==12:
  detail=['metallic/clear_diffuse.png','flat_normal.png','metallic/clear_specular.png'];smooth=.88;coat=0
 elif mid in [8,11,14]:
  detail=['metallic/silverScratched_diffuse.png','flat_normal.png','metallic/silverScratched_specular.png'];smooth=.55;coat=0
 else:
  detail=['metallic/clear_diffuse.png','calibrated/castIron_normal.png','metallic/rough_specular.png'];smooth=.32;coat=0
 for name,path in zip(['detailDiffuse','detailNormal','detailSpecular'],detail):E.SubElement(mat,'Custommap',name=name,fileId=stockfile('$data/shared/detailLibrary/'+path))
 for name,value in [('colorScale','1 1 1'),('smoothnessScale',str(smooth)),('clearCoatIntensity',str(coat)),('clearCoatSmoothness','.5')]:E.SubElement(mat,'CustomParameter',name=name,value=value)
# Worn blade gets an explicit clamp-safe, non-repeating face UV layout.
for shape in shapes:
 if shape.get('name')=='BentWornBlade':
  for v in shape.find('Vertices'):
   x,y,z=map(float,v.get('p').split());v.set('t0',fmt((min(.995,max(.005,(x+1.10)/2.20)),min(.995,max(.005,(y+.7-.10)/1.20)))))
# GIANTS exporter requests runtime tangent generation for normal-mapped meshes.
rendered={n.get('shapeId') for n in root.iter('Shape') if n.get('nonRenderable')!='true'}
for shape in shapes:
 if shape.get('shapeId') not in rendered:continue
 vertices=shape.find('Vertices');vertices.set('tangent','true');triangles=shape.find('Triangles')
 # Legacy text meshes include collapsed triangles and zero normals. Remove
 # collapsed faces; repair only missing/zero normals without flattening smooth parts.
 for triangle in list(triangles):
  indices=list(map(int,triangle.get('vi').split()));p=[np.array(list(map(float,vertices[i].get('p').split()))) for i in indices];normal=np.cross(p[1]-p[0],p[2]-p[0]);length=np.linalg.norm(normal)
  if length<1e-10:triangles.remove(triangle);continue
  for i in indices:
   old=np.array(list(map(float,vertices[i].get('n','0 0 0').split())))
   if np.linalg.norm(old)<.5:vertices[i].set('n',fmt(normal/length))
 for vertex in vertices:
  if np.linalg.norm(list(map(float,vertex.get('n','0 0 0').split())))<.5:vertex.set('n','0 1 0')
 triangles.set('count',str(len(triangles)))
 shape.find('Subsets/Subset').set('numIndices',str(len(triangles)*3))
used={n.get('shapeId') for n in root.iter('Shape')}
for s in list(shapes):
 if s.get('shapeId') not in used:shapes.remove(s)
v=E.parse(OUT/'twinch.xml').getroot();desc=E.parse(OUT/'modDesc.xml').getroot();v.set('type','twinchV06');desc.find('vehicleTypes/type').set('name','twinchV06');desc.find('version').text='0.6.0.0';desc.find('title/en').text='T-Winch v06 - Blade Hydraulics and Steel Tracks';desc.find('description/en').text='V06: clean front without hanging fairlead/chain, exposed native hydraulic cylinders with mounts and hoses, linked steel track shoes and sprockets, restrained weathered materials. Engine testing pending.'
for n in v.findall('storeData/name/*'):n.text='T-Winch 30.2 v06'
v.find('annotation').text='v06 visible native blade hydraulics and detailed steel crawler tracks. Game test pending.'
# Explicit controller owns the blade and all four cylinder endpoints.
# baseDrivable already inherits Cylindered (confirmed by the supplied game log).
# Remove its duplicate declaration and movingTools XML; our handler owns movement.
cylindered=v.find('cylindered')
if cylindered is not None:v.remove(cylindered)
for spec in list(desc.find('vehicleTypes/type')):
 if spec.get('name')=='cylindered':desc.find('vehicleTypes/type').remove(spec)
E.SubElement(v.find('twinch'),'blade',node='bladeLift',RightBarrel='hydraulicRightBarrel',RightPin='hydraulicRightBladePin',RightRod='hydraulicRightRod',RightBase='hydraulicRightBasePin',LeftBarrel='hydraulicLeftBarrel',LeftPin='hydraulicLeftBladePin',LeftRod='hydraulicLeftRod',LeftBase='hydraulicLeftBasePin')
ab=next(a for a in desc.find('inputBinding') if a.get('action')=='TWINCH_BLADE')
for key,component in [('KEY_pageup','+'),('KEY_pagedown','-')]:E.SubElement(ab,'binding',device='KB_MOUSE_DEFAULT',input=key,axisComponent=component,inputComponent='+')
# New action name avoids inheriting stale custom-axis bindings from older releases.
for action in desc.find('actions'):
 if action.get('name')=='TWINCH_BLADE':action.set('name','TWINCH_BLADE_LIFT')
ab.set('action','TWINCH_BLADE_LIFT')
for text in desc.find('l10n'):
 if text.get('name')=='input_TWINCH_BLADE':text.set('name','input_TWINCH_BLADE_LIFT');text.find('en').text='Hydraulic blade (mouse / Page Up / Page Down)'
for suffix,label in [('1','Raise hydraulic blade'),('2','Lower hydraulic blade')]:
 text=E.SubElement(desc.find('l10n'),'text',name='input_TWINCH_BLADE_LIFT_'+suffix);E.SubElement(text,'en').text=label
script=(OLD/'scripts/TWinch.lua').read_text()
script=script.replace('schema:setXMLSpecializationType()',"""
    for _,key in ipairs({'node','RightBarrel','RightPin','RightRod','RightBase','LeftBarrel','LeftPin','LeftRod','LeftBase'}) do
        schema:register(XMLValueType.NODE_INDEX,'vehicle.twinch.blade#'..key,'Hydraulic blade endpoint')
    end
    Vehicle.xmlSchemaSavegame:register(XMLValueType.FLOAT,'vehicles.vehicle(?).'..TWinch.MOD_NAME..'.twinch#bladeAngle','Blade angle in degrees',0)
    schema:setXMLSpecializationType()
""")
script=script.replace('if spec.cable ~= nil then setVisibility(spec.cable, false) end','if spec.cable ~= nil then setVisibility(spec.cable, false) end\n    TWinch.loadBlade(self,savegame)',1)
script=script.replace('if self.isServer and self.isAddedToPhysics then TWinch.updateWinch(self,dt) end','if self.isServer and self.isAddedToPhysics then TWinch.updateBlade(self,dt); TWinch.updateWinch(self,dt) end')
script=script.replace('    for _,action in ipairs({',"""
    if spec.blade ~= nil then
        local _,id=self:addActionEvent(spec.actionEvents,InputAction.TWINCH_BLADE,self,TWinch.actionBlade,true,false,true,true)
        if id ~= nil then
            g_inputBinding:setActionEventText(id,'Hydraulic blade: left mouse + vertical / Page Up / Page Down')
            g_inputBinding:setActionEventTextPriority(id,GS_PRIO_HIGH)
        end
    end
    for _,action in ipairs({
""")
script=script.replace('function TWinch.onLeaveVehicle(self)','function TWinch.onLeaveVehicle(self)\n    if self.spec_twinch.blade ~= nil then self.spec_twinch.blade.input=0 end')
script=script.replace('InputAction.TWINCH_BLADE','InputAction.TWINCH_BLADE_LIFT')
script=script.replace('function TWinch.onRegisterActionEvents(self, isActiveForInput)','function TWinch.onRegisterActionEvents(self, isActiveForInput, isActiveForInputIgnoreSelection)')
script=script.replace('if not isActiveForInput then return end','if not (isActiveForInput or isActiveForInputIgnoreSelection) then return end')
# Custom mod actions are named actions, not guaranteed built-in enum entries.
for action in ['TWINCH_BLADE_LIFT','TWINCH_CONNECT','TWINCH_REEL','TWINCH_PAYOUT']:
 script=script.replace('InputAction.'+action,repr(action))
script=script.replace('g_inputBinding:setActionEventTextPriority(id,GS_PRIO_HIGH)',"g_inputBinding:setActionEventTextPriority(id,GS_PRIO_HIGH)\n            g_inputBinding:setActionEventTextVisibility(id,true)")
script=script.replace('g_inputBinding:setActionEventTextPriority(id,GS_PRIO_HIGH)\n            g_inputBinding:setActionEventTextVisibility(id,true)\n        end',"g_inputBinding:setActionEventTextPriority(id,GS_PRIO_HIGH)\n            g_inputBinding:setActionEventTextVisibility(id,true)\n        else\n            Logging.warning('T-Winch: could not register an input action; check input bindings')\n        end")
script+='\n'+(HERE/'BladeControl.lua').read_text()
script='\n'.join(line.rstrip() for line in script.splitlines())+'\n'
(OUT/'scripts/TWinch.lua').write_text(script)
desc.find('description/en').text='V06: explicit hydraulic blade input with left mouse and Page Up/Down fallback, aligned cylinders, scratched weathered steel textures. Game validation pending.'
v.find('annotation').text='v06 explicit blade input/controller and original weathered textures. Game test pending.'
mapping=v.find('i3dMappings');mapping.clear();seen=set()
def walk(n,path):
 name=n.get('name')
 if name and name not in seen:E.SubElement(mapping,'i3dMapping',id=name,node=path);seen.add(name)
 for i,c in enumerate(n):walk(c,f'{path}{i}' if path.endswith('>') else f'{path}|{i}')
walk(root,'0>')
for alias,target in [('wheelBackLeft','rearLeft'),('wheelBackRight','rearRight')]:E.SubElement(mapping,'i3dMapping',id=alias,node=next(n.get('node') for n in mapping if n.get('id')==target))
for tree,name in [(r,'twinch.i3d'),(v,'twinch.xml'),(desc,'modDesc.xml')]:E.indent(tree);E.ElementTree(tree).write(OUT/name,encoding='utf-8',xml_declaration=True)
preview=HERE/'preview_v06.png'
if preview.exists():
 for name in ['icon_twinch.dds','store_twinch.dds']:
  save_dds(ImageOps.pad(Image.open(preview).convert('RGB'),(512,512),method=Image.Resampling.LANCZOS,color=(24,27,28)),OUT/name)
(OUT/'TESTING.txt').write_text('''T-Winch v06
Disable older T-Winch versions; place FS25_TWinch_v06.zip unopened in mods.
Purchase a NEW v06 in a test save. Engine on: hold left mouse and drag vertically
for blade raise/lower. Inspect both green cylinders, chrome rods, clevis pins
and hoses throughout the motion. Explicit TWinch controller moves/persists the blade. Page Up raises; Page Down lowers.
No protruding green fairlead or dangling chain remains. Cable outlet is recessed.
Track shoes have pins, guide horns, bolts and worn grousers. Both tracks and
sprockets animate from chassis movement. Check straight travel, reverse, pivot
turning and slopes. Physics uses approximate crawler wheel contacts.
Ctrl+B attaches/releases a same-farm vehicle within 25m, Ctrl+R reels in,
Ctrl+N pays out. Single-player vehicle recovery only, not log winching.
Check paint/steel at daytime and under shop lights; materials use FS25 vehicleShader and stock detail-library paint/metal/rubber finishes. Model remains a reference-
inspired approximation. FS25/GIANTS Editor validation has not run here.
''')
(OUT/'validation.json').write_text(json.dumps({'version':'0.6.0.0','game_test':'not run','v05_log_findings':['duplicate cylindered specialization inherited from baseDrivable','missing FULL-axis input labels input_TWINCH_BLADE_1 and _2'],'removed':'front green fairlead, rollers, hook and pendant chain','hydraulics':'explicit blade controller with endpoint-aligned barrels and rods, exposed at x +/-0.76m, clevises, pins, supply hoses','tracks':'74 detailed shared-mesh steel links per side, pins, guides, bolts, grousers, sprockets and guards','textures':'14 original 1024px texture sets; native FS25 vehicleShader with stock vmask and detail-library finishes; preview gloss maps are not fed to vehicleShader'},indent=2)+'\n')
with ZipFile(HERE.parent/'FS25_TWinch_v06.zip','w',ZIP_DEFLATED) as z:
 for f in sorted(OUT.rglob('*')):
  if f.is_file():z.write(f,f.relative_to(OUT))
print('Built',OUT)
