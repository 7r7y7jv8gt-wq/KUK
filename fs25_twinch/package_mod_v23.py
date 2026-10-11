"""Native progressive scratches/dirt and worn-silver crawler finish."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import xml.etree.ElementTree as E,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=ROOT/'FS25_Follvik_TVinsj_v23'
OUT.mkdir(exist_ok=True)
with ZipFile(HERE/'user_wear_v23.zip') as z:
 for name in z.namelist():
  if not name.endswith('/'):
   p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(name))
v=E.parse(OUT/'twinch.xml').getroot();d=E.parse(OUT/'modDesc.xml').getroot();r=E.parse(OUT/'twinch.i3d').getroot()
# The uploaded model was edited again: rebuild stale XML scene references.
oldScene=E.parse(ROOT/'FS25_TWinch_v22/twinch.i3d').getroot()
paths={};names={}
def walk(n,path):
 paths[id(n)]=path;names.setdefault((n.tag,n.get('name')),[]).append(n)
 for i,c in enumerate(n):walk(c,path+('' if path.endswith('>') else '|')+str(i))
for i,n in enumerate(r.find('Scene')):walk(n,str(i)+'>')
missing=set()
for m in list(v.find('i3dMappings')):
 a,_,b=m.get('node').partition('>');old=oldScene.find('Scene')[int(a)]
 for i in b.split('|') if b else []:old=old[int(i)]
 choices=names.get((old.tag,old.get('name')),[])
 originals=[n for n in oldScene.find('Scene').iter() if n.tag==old.tag and n.get('name')==old.get('name')]
 idx=originals.index(old)
 if idx>=len(choices):missing.add(m.get('id'));v.find('i3dMappings').remove(m)
 else:m.set('node',paths[id(choices[idx])])
# Removed bars must not leave invalid lighting nodes; keep remaining lights.
lights=v.find('lights')
for parent in lights.iter():
 for child in list(parent):
  if any(value in missing for value in child.attrib.values()):parent.remove(child)
for group in lights.findall('beaconLights'):
 for beacon in list(group):
  if len(beacon)==0:group.remove(beacon)
for n in v.iter():
 if n not in list(lights.iter()) and n.tag!='i3dMapping' and any(value in missing for value in n.attrib.values()):raise ValueError('Missing non-light vehicle reference '+str(n.attrib))
for tag in ['wearable','washable']:
 n=v.find(tag)
 if n is not None:v.remove(n)
E.SubElement(v,'wearable',wearDuration='1200',workMultiplier='2',fieldMultiplier='1',showOnHud='true')
E.SubElement(v,'washable',dirtDuration='60',washDuration='1',rainWashDuration='30',workMultiplier='2',fieldMultiplier='1.5',wetMultiplier='3')
# Every native vehicle material participates in native scratch/dirt/wetness.
vehicleShaders={n.get('fileId') for n in r.find('Files') if n.get('filename')=='$data/shaders/vehicleShader.xml'}
for m in r.find('Materials'):
 if m.get('customShaderId') in vehicleShaders and m.find("CustomParameter[@name='scratches_dirt_snow_wetness']") is None:
  E.SubElement(m,'CustomParameter',name='scratches_dirt_snow_wetness',value='0 0 0 0')
c=E.parse(OUT/'crawlers/volvo/ec380DLCrawler.i3d').getroot()
for m in c.find('Materials'):
 if m.get('customShaderVariation')=='motionPath_vmaskUV2':
  m.set('diffuseColor','1 1 1 1')
  if m.find("CustomParameter[@name='scratches_dirt_snow_wetness']") is None:E.SubElement(m,'CustomParameter',name='scratches_dirt_snow_wetness',value='0 0 0 0')
  if m.find("CustomParameter[@name='smoothnessScale']") is None:E.SubElement(m,'CustomParameter',name='smoothnessScale',value='.3')
for n in c.find('Files'):
 if n.get('fileId')=='6':n.set('filename','$data/shared/detailLibrary/metallic/clear_diffuse.png')
 if n.get('fileId')=='4':n.set('filename','$data/shared/detailLibrary/metallic/rough_specular.png')
v.set('type','twinchV23');d.find('vehicleTypes/type').set('name','twinchV23');d.find('version').text='0.23.0.0'
for n in v.findall('storeData/name/*'):n.text='Føllvik t vinsj'
d.find('title/en').text='Føllvik t vinsj';d.find('description/en').text='Gradual native paint scratches and full-body dirt, with dark crawler steel becoming silver as wear accumulates. User model and lights retained; 800hp, 12km/h, 40 tonnes, winches and TerraFarm.'
p=OUT/'scripts/TWinch.lua';s=p.read_text().replace('twinchV22','twinchV23')
s=s.replace('    TWinch.updateTracks(self)','    TWinch.updateTrackWear(self,dt)\n    TWinch.updateTracks(self)',1)
# Extend pre-validation registration without duplicating inherited native specs.
s=s.replace("    local vehicleType=manager.types[volvoCrawlerVehicleType]", """    local vehicleType=manager.types[volvoCrawlerVehicleType]
    if vehicleType~=nil then
        for _,entry in ipairs({{'wearable',Wearable},{'washable',Washable}}) do
            if entry[2]~=nil and not SpecializationUtil.hasSpecialization(entry[2],vehicleType.specializations) then manager:addSpecialization(volvoCrawlerVehicleType,entry[1]) end
        end
    end""")
s+='\n'+(HERE/'TrackWear.lua').read_text();p.write_text(s)
index=E.parse(OUT/'machineConfigurations.xml').getroot();index.find('configuration').set('vehicle','FS25_Follvik_TVinsj_v23/twinch.xml')
for tree,name in [(v,'twinch.xml'),(d,'modDesc.xml'),(r,'twinch.i3d'),(c,'crawlers/volvo/ec380DLCrawler.i3d'),(index,'machineConfigurations.xml')]:E.indent(tree);E.ElementTree(tree).write(OUT/name,encoding='utf-8',xml_declaration=True)
(OUT/'TESTING.txt').write_text('V23: native progressive wear and dirt.\nDark crawler paint gradually fades to silver as native wear rises; both LODs supported.\nBody vehicle materials use native scratch/dirt shader channels.\nWear duration configured 1200min; actual rate depends on use and game multipliers.\nDirt duration 60min with working/field/wet multipliers. Wash removes dirt; repaint resets wear.\nExisting worn vehicles retain native wear. Fresh machine begins clean/unworn.\nUse ASCII ZIP filename as supplied; disable older versions.\nUser geometry, lighting, 800hp, 12km/h, 40 tonnes, winches and TerraFarm retained.\nFS25 shader appearance and progression need in-game verification.\n')
(OUT/'validation.json').write_text(json.dumps({'version':'0.23.0.0','game_test':'not run','wear_duration_config_minutes':1200,'dirt_duration_config_minutes':60,'track_finish':'native wear drives dark-to-silver tint','state':'native save/wash/repaint'},indent=2)+'\n')
with ZipFile(ROOT/'FS25_Follvik_TVinsj_v23.zip','w',ZIP_DEFLATED) as z:
 for f in sorted(OUT.rglob('*')):
  if f.is_file():z.write(f,f.relative_to(OUT))
print('Built',OUT)
