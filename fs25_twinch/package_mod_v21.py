"""Wire user-mounted amber lightbar/DRLs and flood high beams with native Lights."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import shutil,xml.etree.ElementTree as E,copy,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=ROOT/'FS25_TWinch_v21';BASE=ROOT/'FS25_TWinch_v20'
shutil.copytree(BASE,OUT,dirs_exist_ok=True)
with ZipFile(HERE/'user_lighting_v21.zip') as z:
 for name in z.namelist():
  if not name.endswith('/') and (name.endswith(('.i3d','.shapes','.dds','.png','.xml')) and name not in ['twinch.xml','modDesc.xml','machineConfigurations.xml']):
   p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(name))
r=E.parse(OUT/'twinch.i3d').getroot();old=E.parse(BASE/'twinch.i3d').getroot();v=E.parse(BASE/'twinch.xml').getroot();d=E.parse(BASE/'modDesc.xml').getroot();root=r.find('Scene')[0]
names={};paths={}
def walk(n,path):
 names.setdefault(n.get('name'),[]).append(n);paths[id(n)]=path
 for i,c in enumerate(n):walk(c,path+('' if path.endswith('>') else '|')+str(i))
walk(root,'0>')
def resolve(root,path):
 a,_,b=path.partition('>');n=root.find('Scene')[int(a)]
 for i in b.split('|') if b else []:n=n[int(i)]
 return n
def named(name,tag=None):return next(n for n in names[name] if tag is None or n.tag==tag)
# Editor reordered nodes: remap original references by node name and node type.
for m in list(v.find('i3dMappings')):
 n=resolve(old,m.get('node'));choices=[c for c in names.get(n.get('name'),[]) if c.tag==n.tag]
 if not choices:
  if any(m.get('id') in e.attrib.values() for e in v.iter() if e.tag!='i3dMapping'):raise ValueError('Missing referenced node '+m.get('id'))
  v.find('i3dMappings').remove(m);continue
 originals=[c for c in old.find('Scene').iter() if c.get('name')==n.get('name') and c.tag==n.tag]
 occurrence=originals.index(n)
 if occurrence>=len(choices):raise ValueError('Missing duplicate mapped node '+m.get('id'))
 m.set('node',paths[id(choices[occurrence])])
lights=v.find('lights');drl=lights.find('dayTimeLights');beacons=E.SubElement(lights,'beaconLights')
E.SubElement(lights.find('states'),'state',lightTypes='0 1 2')
nid=max(int(n.get('nodeId','0')) for n in root.iter())+1
for name in ['parkinglights','cruiselights','floodlights']:
 n=named(name,'Shape');key='added_'+name;E.SubElement(v.find('i3dMappings'),'i3dMapping',id=key,node=paths[id(n)])
 n.set('visibility','true')
 if name!='floodlights':E.SubElement(drl,'dayTimeLight',node=key,intensity='8')
 else:E.SubElement(lights.find('staticLights'),'staticLight',node=key,lightTypes='2',intensity='40')
# All new amber glow meshes use an explicit amber glow shader material.
mid=max(int(m.get('materialId')) for m in r.find('Materials'))+1
amber=copy.deepcopy(r.find("Materials/Material[@materialId='17']"));amber.set('materialId',str(mid));amber.set('name','AmberCruiseDRLFlash');amber.set('diffuseColor','1 .5 0 1')
for n in amber.findall('CustomParameter'):
 if n.get('name')=='colorScale':n.set('value','1 .5 0')
r.find('Materials').append(amber)
for name in ['parkinglights','cruiselights','blitzer1','blitzer2']:named(name,'Shape').set('materialIds',str(mid))
for side,params in [(1,'4 12 65 2'),(2,'5 10 65 0')]:
 shape=named('blitzer'+str(side),'Shape');key=f'flash_mesh_{side}'
 E.SubElement(v.find('i3dMappings'),'i3dMapping',id=key,node=paths[id(shape)])
 for i,n in enumerate(c for c in shape if c.tag=='Light'):
  beamKey=f'flash_beam_{side}_{i}';n.set('color','1 .5 0');n.set('visibility','false')
  E.SubElement(v.find('i3dMappings'),'i3dMapping',id=beamKey,node=paths[id(n)])
  b=E.SubElement(beacons,'beaconLight',realLight=beamKey)
  E.SubElement(b,'staticLight',node=key,intensity='60',multiBlink='true',multiBlinkParameters=params)
# A white spotlight belongs to the flood insert, follows its mounting transform.
flood=named('floodlights','Shape');beam=E.SubElement(flood,'Light',name='ledbarFloodBeam',nodeId=str(nid),type='spot',color='1 .96 .9',translation='0 0 .02',range='45',coneAngle='80',dropOff='2',emitDiffuse='true',emitSpecular='true',visibility='false');nid+=1
beamPath=paths[id(flood)]+'|'+str(len(flood)-1)
E.SubElement(v.find('i3dMappings'),'i3dMapping',id='ledbarFloodBeam',node=beamPath)
for level in ['low','high']:E.SubElement(lights.find('realLights/'+level),'light',node='ledbarFloodBeam',lightTypes='2')
v.set('type','twinchV21');d.find('vehicleTypes/type').set('name','twinchV21');d.find('version').text='0.21.0.0'
for n in v.findall('storeData/name/*'):n.text='Føllvik t vinsj'
d.find('title/en').text='Føllvik t vinsj';d.find('description/en').text='Amber lightbar cruise and flash lights, amber LED-bar DRLs and flood high beams. 800hp, 12km/h, 40 tonnes, front/rear winches and guarded TerraFarm registration retained.'
p=OUT/'scripts/TWinch.lua';p.write_text((BASE/'scripts/TWinch.lua').read_text().replace('twinchV20','twinchV21'))
index=E.parse(BASE/'machineConfigurations.xml').getroot();index.find('configuration').set('vehicle','FS25_TWinch_v21/twinch.xml')
for tree,name in [(r,'twinch.i3d'),(v,'twinch.xml'),(d,'modDesc.xml'),(index,'machineConfigurations.xml')]:E.indent(tree);E.ElementTree(tree).write(OUT/name,encoding='utf-8',xml_declaration=True)
(OUT/'TESTING.txt').write_text('V21: user light placements preserved.\nStart engine: amber lightbar cruise lights and amber LED-bar DRLs.\nNative beacon toggle (default Home): alternating amber multi-flash lightbar.\nF cycle: front worklights, all worklights, then white LED-bar flood high beams.\nDisable previous T-Winch versions; install unopened ZIP.\n800hp, 12km/h, 40 tonnes, winches and guarded TerraFarm registration retained.\nFS25 visual/function test pending.\n')
(OUT/'validation.json').write_text(json.dumps({'version':'0.21.0.0','game_test':'not run','amber':'engine cruise/DRL + native beacon flash','flood':'lighting type 2, third F stage'},indent=2)+'\n')
with ZipFile(ROOT/'FS25_TWinch_v21.zip','w',ZIP_DEFLATED) as z:
 for f in sorted(OUT.rglob('*')):
  if f.is_file():z.write(f,f.relative_to(OUT))
print('Built',OUT)
