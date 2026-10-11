from pathlib import Path
import shutil,copy,xml.etree.ElementTree as E,json
from zipfile import ZipFile,ZIP_DEFLATED
HERE=Path(__file__).resolve().parent;OUT=HERE.parent/'FS25_TWinch_v15'
shutil.copytree(HERE.parent/'FS25_TWinch_v14',OUT,dirs_exist_ok=True)
r=E.parse(OUT/'twinch.i3d').getroot();v=E.parse(OUT/'twinch.xml').getroot();d=E.parse(OUT/'modDesc.xml').getroot();root=r.find('Scene')[0]
nid=max(int(n.get('nodeId','0')) for n in root.iter())+1
names={n.get('name'):n for n in root.iter()}
def ids(n):
 global nid
 for c in n.iter():c.set('nodeId',str(nid));nid+=1
rear=E.SubElement(root,'TransformGroup',name='rearWinchAssembly',rotation='0 180 0',translation='0 0 .2',nodeId=str(nid));nid+=1
for n in list(names['visual']):
 if n.get('name')=='WinchDrum' or n.get('name')=='SteelCableOnDrum':
  c=copy.deepcopy(n);ids(c);rear.append(c)
# A close-fitted lower back plate covers the chassis opening behind the rear winch.
plate=E.SubElement(root,'TransformGroup',name='rearWinchMountPlate',translation='0 -.13 0',scale='1 1.2 1',nodeId=str(nid));nid+=1
c=copy.deepcopy(names['RearBumper']);c.set('name','rearWinchBackingPlate');ids(c);plate.append(c)
anchor=E.SubElement(root,'TransformGroup',name='rearWinchAnchor',translation='0 1.2 -1.49',rotation='0 180 0',nodeId=str(nid));nid+=1
# A visible insert uses emission and native visibility switching, independently
# of prefab UV slot indices, so its center lights instead of only its border.
mid=max(int(m.get('materialId')) for m in r.find('Materials'))+1
E.SubElement(r.find('Materials'),'Material',name='FOR9TWhiteWorkEmission',materialId=str(mid),diffuseColor='1 .96 .9 1',emissiveColor='4 3.84 3.6')
for i,a in enumerate(n for n in root.iter() if n.get('name')=='FOR9T_noGlare'):
 transform=next(n for n in a.iter() if n.get('name')=='transform')
 c=copy.deepcopy(next(n for n in a.iter() if n.get('name')=='static'));ids(c);c.set('name',f'for9t_luminousInsert_{i}');c.set('materialIds',','.join([str(mid)]*3));c.set('translation','0 0 .001');c.set('visibility','false');transform.append(c)
 lightType='0' if float(a.get('translation').split()[2])<0 else '1'
 for n in v.findall('lights/staticLights/staticLight')+v.findall('lights/realLights/low/light')+v.findall('lights/realLights/high/light'):
  if n.get('node','').endswith('_'+str(i)):n.set('lightTypes',lightType)
 E.SubElement(v.find('lights/staticLights'),'staticLight',node=c.get('name'),lightTypes=lightType,toggleVisibility='true')
paths={}
def walk(n,path):
 paths[n.get('name')]=path
 for i,c in enumerate(n):walk(c,path+('' if path.endswith('>') else '|')+str(i))
walk(root,'0>')
for name in ['rearWinchAnchor']+[f'for9t_luminousInsert_{i}' for i in range(8)]:E.SubElement(v.find('i3dMappings'),'i3dMapping',id=name,node=paths[name])
E.SubElement(v.find('twinch'),'rearWinch',anchor='rearWinchAnchor')
p=OUT/'scripts/TWinch.lua';s=p.read_text().replace('twinchV14','twinchV15')
s=s.replace('    BladeWinch.load(self)','''    BladeWinch.load(self)
    local rear=self.xmlFile:getValue('vehicle.twinch.rearWinch#anchor',nil,self.components,self.i3dMappings)
    if rear~=nil then BladeWinch.load(self,rear) end''',1)
s=s.replace('    schema:setXMLSpecializationType("TWinch")','    schema:setXMLSpecializationType("TWinch")\n    schema:register(XMLValueType.NODE_INDEX,"vehicle.twinch.rearWinch#anchor","Rear winch fairlead")',1)
a=s.index('function W.load(vehicle)');b=s.index('function W.deleteMap',a);block=s[a:b]
block=block.replace('function W.load(vehicle)','function W.load(vehicle,anchor)').replace('local s={vehicle=vehicle,','local s={vehicle=vehicle,anchor=anchor or vehicle.spec_twinch.anchor,')
block=block.replace('    vehicle.spec_twinch.logging=s','    vehicle.spec_twinch.loggingWinches=vehicle.spec_twinch.loggingWinches or {}\n    table.insert(vehicle.spec_twinch.loggingWinches,s)\n    if anchor==nil then vehicle.spec_twinch.logging=s end')
block=block.replace('W.selected.vehicle.spec_twinch.anchor','W.selected.anchor').replace('s.vehicle.spec_twinch.anchor','s.anchor')
# Only within the load method, the default anchor expression stays unchanged.
block=block.replace('link(vehicle.spec_twinch.anchor,','link(s.anchor,')
block=block.replace('function W.delete(vehicle)\n    local s=vehicle.spec_twinch.logging;if s==nil then return end','function W.deleteOne(vehicle,s)\n    if s==nil then return end')
block=block.replace('function W.tick(vehicle,dt)\n    local s=vehicle.spec_twinch.logging;if s==nil or #s.targets==0 then return end','function W.tickOne(vehicle,s,dt)\n    if s==nil or #s.targets==0 then return end').replace('distance(vehicle.spec_twinch.anchor,t.ref)','distance(s.anchor,t.ref)').replace('W.pull(s,vehicle.spec_twinch.anchor,','W.pull(s,s.anchor,')
block+='''function W.tick(vehicle,dt)
    for _,s in ipairs(vehicle.spec_twinch.loggingWinches or {vehicle.spec_twinch.logging}) do W.tickOne(vehicle,s,dt) end
end
function W.delete(vehicle)
    for _,s in ipairs(vehicle.spec_twinch.loggingWinches or {vehicle.spec_twinch.logging}) do W.deleteOne(vehicle,s) end
    vehicle.spec_twinch.loggingWinches={}
end
'''
s=s[:a]+block+s[b:];p.write_text(s)
v.set('type','twinchV15');d.find('vehicleTypes/type').set('name','twinchV15');d.find('version').text='0.15.0.0';d.find('description/en').text='Front and close-mounted rear logging winches with independent hooks/cables, rear backing plate, emitting FOR9T center inserts and corrected front-first lighting cycle. Configured total mass 40 tonnes.';d.find('title/en').text='T-Winch v15 - Rear winch and illuminated FOR9T inserts'
for n in v.findall('storeData/name/*'):n.text='T-Winch 30.2 v15'
index=E.parse(OUT/'machineConfigurations.xml').getroot();index.find('configuration').set('vehicle','FS25_TWinch_v15/twinch.xml')
for tree,name in [(r,'twinch.i3d'),(v,'twinch.xml'),(d,'modDesc.xml'),(index,'machineConfigurations.xml')]:E.indent(tree);E.ElementTree(tree).write(OUT/name,encoding='utf-8',xml_declaration=True)
(OUT/'TESTING.txt').write_text('V15: disable older versions, install unopened ZIP, buy fresh machine.\nRear winch sits close against rear body with lower backing plate.\nWalk to front blade or rear winch, R takes nearby hook; R attaches, Z pulls, X pays out.\nF first lights negative-Z bank (front in reported game orientation), then both banks.\nWhite emitting inserts light the worklight centers; red DRLs remain engine-controlled.\n40-tonne mass retained. Geometry fit, beam aim and FS25 operation untested here.\n')
(OUT/'validation.json').write_text(json.dumps({'version':'0.15.0.0','game_test':'not run','winches':2,'rear_mount':'close body, lower backing plate','lights':'emitting center inserts, corrected front-first bank'},indent=2)+'\n')
with ZipFile(HERE.parent/'FS25_TWinch_v15.zip','w',ZIP_DEFLATED) as z:
 for f in sorted(OUT.rglob('*')):
  if f.is_file():z.write(f,f.relative_to(OUT))
print('Built',OUT)
