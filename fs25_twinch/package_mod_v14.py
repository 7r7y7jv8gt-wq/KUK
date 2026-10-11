"""Package the user's edited FOR9T model with native FS25 DRL/work lighting."""
from pathlib import Path
import shutil,xml.etree.ElementTree as E,json
from zipfile import ZipFile,ZIP_DEFLATED
HERE=Path(__file__).resolve().parent;OUT=HERE.parent/'FS25_TWinch_v14';BASE=HERE.parent/'FS25_TWinch_v13'
shutil.copytree(BASE,OUT,dirs_exist_ok=True)
USER=HERE/'user_for9t'
shutil.copytree(USER,OUT,dirs_exist_ok=True)
r=E.parse(OUT/'twinch.i3d').getroot();original=E.parse(BASE/'twinch.i3d').getroot();v=E.parse(OUT/'twinch.xml').getroot();d=E.parse(OUT/'modDesc.xml').getroot()
def resolve(root,path):
 a,_,b=path.partition('>');n=root.find('Scene')[int(a)]
 for i in b.split('|') if b else []:n=n[int(i)]
 return n
paths={};names={}
def walk(n,path):
 paths[id(n)]=path;names.setdefault(n.get('name'),[]).append(n)
 for i,c in enumerate(n):walk(c,path+('' if path.endswith('>') else '|')+str(i))
for i,n in enumerate(r.find('Scene')):walk(n,str(i)+'>')
# GIANTS Editor renumbered/reordered scene nodes: rebuild all existing mappings.
for m in list(v.find('i3dMappings')):
 old=resolve(original,m.get('node'));candidates=names.get(old.get('name'),[])
 if not candidates:
  if any(m.get('id') in n.attrib.values() for n in v.iter() if n.tag!='i3dMapping'):raise ValueError('Missing referenced node '+m.get('id'))
  v.find('i3dMappings').remove(m);continue
 m.set('node',paths[id(candidates[0])])
lights=v.find('lights');v.remove(lights);lights=E.SubElement(v,'lights');states=E.SubElement(lights,'states')
E.SubElement(states,'state',lightTypes='0');E.SubElement(states,'state',lightTypes='0 1')
drls=E.SubElement(lights,'dayTimeLights');statics=E.SubElement(lights,'staticLights');real=E.SubElement(lights,'realLights');low=E.SubElement(real,'low');high=E.SubElement(real,'high')
assemblies=names.get('FOR9T_noGlare',[]);assert len(assemblies)==8
nid=max(int(n.get('nodeId','0')) for n in r.find('Scene').iter())+1
for i,a in enumerate(assemblies):
 transform=next(n for n in a.iter() if n.get('name')=='transform')
 red=next(n for n in a.iter() if n.get('name')=='DRL_red');red.set('visibility','true')
 for n in a.iter():
  if n.get('name') in ['DRL_orange','DRL_white']:n.set('visibility','false')
 white=next(n for n in a.iter() if n.get('name')=='static')
 for label,node in [('drl',red),('work',white)]:
  key=f'for9t_{label}_{i}';E.SubElement(v.find('i3dMappings'),'i3dMapping',id=key,node=paths[id(node)])
 E.SubElement(drls,'dayTimeLight',node=f'for9t_drl_{i}',intensity='12')
 # Native staticLight sets all shader UV slots equally on this work-only shape.
 lightType='1' if float(a.get('translation').split()[2])<0 else '0'
 E.SubElement(statics,'staticLight',node=f'for9t_work_{i}',lightTypes=lightType,intensity='40')
 beam=E.SubElement(transform,'Light',name=f'for9t_beam_{i}',nodeId=str(nid),translation='0 0 .045',rotation='-12 0 0',type='spot',color='1 .96 .9',range='35',coneAngle='65',dropOff='2',emitDiffuse='true',emitSpecular='true',visibility='false');nid+=1
 path=paths[id(transform)]+'|'+str(len(transform)-1)
 E.SubElement(v.find('i3dMappings'),'i3dMapping',id=f'for9t_beam_{i}',node=path)
 for level in [low,high]:E.SubElement(level,'light',node=f'for9t_beam_{i}',lightTypes=lightType)
# Old beam nodes remain for stable indices, but no longer illuminate.
for n in names.get('worklight0',[])+names.get('worklight1',[])+names.get('worklight2',[])+names.get('worklight3',[]):n.set('visibility','false')
v.set('type','twinchV14');d.find('vehicleTypes/type').set('name','twinchV14');d.find('version').text='0.14.0.0';d.find('title/en').text='T-Winch v14 - Eight FOR9T work lights and red DRLs'
d.find('description/en').text='User-positioned FOR9T lights: eight engine-controlled red DRLs and eight white front/rear work beams using native FS25 lights. V13 blade, winch, tracks and 40-tonne configuration retained.'
for n in v.findall('storeData/name/*'):n.text='T-Winch 30.2 v14'
s=(OUT/'scripts/TWinch.lua').read_text().replace('twinchV13','twinchV14');(OUT/'scripts/TWinch.lua').write_text(s)
index=E.parse(OUT/'machineConfigurations.xml').getroot();index.find('configuration').set('vehicle','FS25_TWinch_v14/twinch.xml')
for tree,name in [(r,'twinch.i3d'),(v,'twinch.xml'),(d,'modDesc.xml'),(index,'machineConfigurations.xml')]:E.indent(tree);E.ElementTree(tree).write(OUT/name,encoding='utf-8',xml_declaration=True)
credits=OUT/'CREDITS.txt'
credits.write_text(credits.read_text()+'\nLizard FOR9T Pack: 5oteruud. Prefab and user-installed geometry supplied by the user.\n')
(OUT/'TESTING.txt').write_text('V14: disable earlier T-Winch versions, install unopened ZIP, buy fresh vehicle.\nEight user-positioned FOR9T lights retained. Red DRLs switch with engine.\nF lighting cycle: front white work lights, then front and rear work lights.\nEight real beams and matching emissive lenses use native Lights.\nV13 blade controls, logging winch and configured 40,000kg total mass retained.\nFS25 visual and functional checks pending.\n')
(OUT/'validation.json').write_text(json.dumps({'version':'0.14.0.0','game_test':'not run','FOR9T_count':8,'DRL':'red, engine-controlled','worklights':'native front/rear lighting states'},indent=2)+'\n')
with ZipFile(HERE.parent/'FS25_TWinch_v14.zip','w',ZIP_DEFLATED) as z:
 for f in sorted(OUT.rglob('*')):
  if f.is_file():z.write(f,f.relative_to(OUT))
print('Built',OUT)
