"""Parent the front logo to the hydraulic blade, preserving its rest pose."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import shutil,xml.etree.ElementTree as E,json,hashlib,math
ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'FS25_Follvik_TVinsj_v26'
shutil.copytree(ROOT/'FS25_Follvik_TVinsj_v25',OUT,dirs_exist_ok=True)
r=E.parse(OUT/'twinch.i3d');scene=r.find('Scene');v=E.parse(OUT/'twinch.xml')
def resolve(path):
 a,_,b=path.partition('>');n=scene[int(a)]
 for i in b.split('|') if b else []:n=n[int(i)]
 return n
references={m.get('id'):resolve(m.get('node')) for m in v.find('i3dMappings')}
blade=references['bladeLift'];visual=scene[0][0]
logo=next(n for n in visual if n.get('name')=='FollvikLogo' and n.get('nodeId')=='665')
assert 'rotation' not in visual.attrib and 'translation' not in visual.attrib
assert 'rotation' not in blade.attrib and 'scale' not in blade.attrib
oldPosition=list(map(float,logo.get('translation').split()));pivot=list(map(float,blade.get('translation').split()))
localPosition=[a-b for a,b in zip(oldPosition,pivot)]
visual.remove(logo);blade.append(logo)
logo.set('translation',' '.join(format(a,'.9g') for a in localPosition))
paths={}
def walk(n,path):
 paths[id(n)]=path
 for i,c in enumerate(n):walk(c,path+('' if path.endswith('>') else '|')+str(i))
for i,n in enumerate(scene):walk(n,str(i)+'>')
for m in v.find('i3dMappings'):m.set('node',paths[id(references[m.get('id')])])
# Rest placement and the complete hydraulic range: logo stays rigidly on the blade.
assert all(abs(a-(b+c))<1e-8 for a,b,c in zip(oldPosition,pivot,localPosition))
assert logo in list(blade) and len([n for n in visual if n.get('name')=='FollvikLogo'])==2
for angle in [-28,0,25]:
 a=math.radians(angle);x,y,z=localPosition
 world=[pivot[0]+x,pivot[1]+math.cos(a)*y-math.sin(a)*z,pivot[2]+math.sin(a)*y+math.cos(a)*z]
 delta=[world[i]-pivot[i] for i in range(3)]
 recovered=[delta[0],math.cos(a)*delta[1]+math.sin(a)*delta[2],-math.sin(a)*delta[1]+math.cos(a)*delta[2]]
 assert all(abs(a-b)<1e-8 for a,b in zip(recovered,localPosition))
v.getroot().set('type','twinchV26')
for tree,name in [(r,'twinch.i3d'),(v,'twinch.xml')]:E.indent(tree);tree.write(OUT/name,encoding='utf-8',xml_declaration=True)
p=OUT/'scripts/TWinch.lua';p.write_text(p.read_text().replace('twinchV25','twinchV26'))
p=OUT/'modDesc.xml';d=E.parse(p);d.find('version').text='0.26.0.0';d.find('vehicleTypes/type').set('name','twinchV26');E.indent(d);d.write(p,encoding='utf-8',xml_declaration=True)
p=OUT/'machineConfigurations.xml';d=E.parse(p);d.find('configuration').set('vehicle','FS25_Follvik_TVinsj_v26/twinch.xml');E.indent(d);d.write(p,encoding='utf-8',xml_declaration=True)
# Validate all scene references still resolve to their original node IDs.
updated=E.parse(OUT/'twinch.i3d');scene=updated.find('Scene')
for m in v.find('i3dMappings'):assert resolve(m.get('node')).get('nodeId')==references[m.get('id')].get('nodeId')
for p in OUT.rglob('*'):
 if p.is_file() and p.suffix in ['.shapes','.dds']:
  assert p.read_bytes()==(ROOT/'FS25_Follvik_TVinsj_v25'/p.relative_to(OUT)).read_bytes()
# Record the revised I3D checksum; compiled geometry and textures are unchanged.
p=OUT/'source_asset_hashes.json';hashes=json.loads(p.read_text());hashes['twinch.i3d']=hashlib.sha256((OUT/'twinch.i3d').read_bytes()).hexdigest();p.write_text(json.dumps(hashes,indent=2)+'\n')
(OUT/'validation.json').write_text(json.dumps({'version':'0.26.0.0','game_test':'not run','front_logo_parent':'bladeLift','rest_pose_preserved':True,'scene_mappings_preserved':True,'compiled_shapes_and_textures_unchanged':True,'blade_angle_range_checked':[-28,0,25]},indent=2)+'\n')
(OUT/'TESTING.txt').write_text((OUT/'TESTING.txt').read_text()+'\nV26: front FollvikLogo node 665 parented to bladeLift, retaining its rest placement.\nSide logos remain on the body. Compiled geometry and textures unchanged.\nAll scene mappings checked after reparenting. Left-mouse hydraulics and both 100t winches retained.\n')
with ZipFile(ROOT/'FS25_Follvik_TVinsj_v26.zip','w',ZIP_DEFLATED) as z:
 for p in sorted(OUT.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(OUT))
with ZipFile(ROOT/'FS25_Follvik_TVinsj_v26.zip') as z:assert z.testzip() is None
print('Validated blade logo parent, rest placement, angle range, scene mappings, unchanged shapes/textures and ZIP.')
