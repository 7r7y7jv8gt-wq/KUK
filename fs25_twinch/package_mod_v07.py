"""Extend v06 blade lowering by 25 degrees, with cylinder overlap and blade contact."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import xml.etree.ElementTree as E
import shutil,copy,json
HERE=Path(__file__).resolve().parent;OLD=HERE.parent/'FS25_TWinch_v06';OUT=HERE.parent/'FS25_TWinch_v07'
shutil.copytree(OLD,OUT,dirs_exist_ok=True)
script=(OLD/'scripts/TWinch.lua').read_text().replace('math.min(0,savegame.xmlFile:getValue','math.min(25,savegame.xmlFile:getValue').replace('math.min(0,blade.angle-blade.input','math.min(25,blade.angle-blade.input').replace('T-Winch v06:','T-Winch v07:')
(OUT/'scripts/TWinch.lua').write_text(script)
r=E.parse(OUT/'twinch.i3d').getroot();shapes=r.find('Shapes');root=r.find('Scene')[0];nodes={n.get('name'):n for n in root.iter()};byid={s.get('shapeId'):s for s in shapes}
for side in ['Right','Left']:
 rod=byid[nodes['hydraulic'+side+'ChromePiston'].get('shapeId')]
 for vertex in rod.find('Vertices'):
  p=list(map(float,vertex.get('p').split()))
  if abs(p[2]-.55)<1e-5:p[2]=.65;vertex.set('p',' '.join(f'{n:.7g}' for n in p))
# Replace the obsolete rectangular collider with the bent plate's closed shell.
# Extend its bottom edge to include the replaceable cutting edge.
old=byid[nodes['bladeCollision'].get('shapeId')];source=byid[nodes['BentWornBlade'].get('shapeId')];collision=copy.deepcopy(source)
collision.attrib.update(name='bladeContactCollision',shapeId=old.get('shapeId'),meshUsage='256')
vs=collision.find('Vertices');vs.attrib.clear();vs.set('count',str(len(vs)))
for vertex in vs:
 p=list(map(float,vertex.get('p').split()))
 if abs(p[1]+.56)<1e-5:
  p[0]=1.115 if p[0]>0 else -1.115;p[1]=-.605;p[2]+=.0475
 vertex.attrib.clear();vertex.set('p',' '.join(f'{n:.7g}' for n in p))
shapes.remove(old);shapes.append(collision)
v=E.parse(OUT/'twinch.xml').getroot();desc=E.parse(OUT/'modDesc.xml').getroot()
v.set('type','twinchV07');desc.find('vehicleTypes/type').set('name','twinchV07');desc.find('version').text='0.7.0.0';desc.find('title/en').text='T-Winch v07 - Extended Blade Lowering'
for n in v.findall('storeData/name/*'):n.text='T-Winch 30.2 v07'
v.find('annotation').text='v07: blade -28..+25 degrees, 34cm additional cutting-edge lowering, extended piston rods and matching ground-contact collider. Engine validation pending.'
desc.find('description/en').text='V07 extends blade lowering by 25 degrees (about 34cm at the cutting edge). Engine on: left mouse vertical or Page Up/Page Down. Extended chrome rods and blade collision follow the new movement range.'
for tree,name in [(r,'twinch.i3d'),(v,'twinch.xml'),(desc,'modDesc.xml')]:E.indent(tree);E.ElementTree(tree).write(OUT/name,encoding='utf-8',xml_declaration=True)
(OUT/'TESTING.txt').write_text('''T-Winch v07: extended blade range
Disable earlier versions; install unopened FS25_TWinch_v07.zip and purchase a
new v07 in a test save. Start the engine. Page Up raises, Page Down lowers;
hold left mouse and drag vertically for proportional blade control.
Range: -28 degrees raised through +25 degrees lowered. Cutting edge reaches
about 34cm lower than v06. Chrome rods lengthened to .65m for safe overlap.
The blade now has a collision shell matching its bent plate/cutting edge.
On flat ground contact may stop lowering or lift the front of the machine;
maximum visual travel can be checked over a dip or a slope. This does not
implement terrain deformation. Check ground contact and stability in FS25.
Native vehicle materials, independent track animation and vehicle recovery
winch controls are carried forward from v06. Actual engine testing pending.
''')
(OUT/'validation.json').write_text(json.dumps({'version':'0.7.0.0','blade_angle_degrees':[-28,25],'additional_edge_lowering_metres':.340,'chrome_rod_length_metres':.65,'collision':'closed bent plate shell extended to cutting edge','game_test':'not run'},indent=2)+'\n')
with ZipFile(HERE.parent/'FS25_TWinch_v07.zip','w',ZIP_DEFLATED) as z:
 for f in sorted(OUT.rglob('*')):
  if f.is_file():z.write(f,f.relative_to(OUT))
print('Built',OUT)
