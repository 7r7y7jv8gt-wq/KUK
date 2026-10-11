"""Restrict steady amber cruise to side inserts; whole bar flashes; LED work light."""
from pathlib import Path
import copy,shutil,xml.etree.ElementTree as E,json
from zipfile import ZipFile,ZIP_DEFLATED
HERE=Path(__file__).resolve().parent;OUT=HERE.parent/'FS25_TWinch_v22'
shutil.copytree(HERE.parent/'FS25_TWinch_v21',OUT,dirs_exist_ok=True)
r=E.parse(OUT/'twinch.i3d').getroot();v=E.parse(OUT/'twinch.xml').getroot();d=E.parse(OUT/'modDesc.xml').getroot();root=r.find('Scene')[0]
parents={c:p for p in root.iter() for c in p};cruise=next(n for n in root.iter() if n.get('name')=='cruiselights');bar=parents[cruise];cruise.set('name','wholeBarFlash')
day=v.find('lights/dayTimeLights')
for n in list(day):
 if n.get('node')=='added_cruiselights':day.remove(n)
# Original full-width emitting mesh is now beacon-only. Compact clones at
# either end provide independent steady cruise inserts, without whole-bar glow.
nid=max(int(n.get('nodeId','0')) for n in root.iter())+1
for sign,side in [(-1,'Left'),(1,'Right')]:
 n=copy.deepcopy(cruise);n.set('name','sideCruise'+side);n.set('nodeId',str(nid));nid+=1
 n.set('scale','.10 .917888 1');n.set('translation',f'{sign*.64} .0298212 -.00939866');bar.append(n)
 E.SubElement(day,'dayTimeLight',node=n.get('name'),intensity='1.5')
beacons=v.find('lights/beaconLights')
E.SubElement(beacons[0],'staticLight',node='added_cruiselights',intensity='12',multiBlink='true',multiBlinkParameters='4 12 65 2')
for b in beacons:
 for s in b.findall('staticLight'):s.set('intensity','12')
# LED white flood insert now responds to the first front work-light state.
for n in v.findall('lights/staticLights/staticLight')+v.findall('lights/realLights/low/light')+v.findall('lights/realLights/high/light'):
 if n.get('node') in ['added_floodlights','ledbarFloodBeam']:n.set('lightTypes','0')
paths={}
def walk(n,p):
 paths[n.get('name')]=p
 for i,c in enumerate(n):walk(c,p+('' if p.endswith('>') else '|')+str(i))
walk(root,'0>')
for name in ['sideCruiseLeft','sideCruiseRight']:E.SubElement(v.find('i3dMappings'),'i3dMapping',id=name,node=paths[name])
v.set('type','twinchV22');d.find('vehicleTypes/type').set('name','twinchV22');d.find('version').text='0.22.0.0'
d.find('description/en').text='Steady amber lightbar cruise only at its ends; entire bar flashes with beacon toggle. LED bar white light activates with front work lights. Føllvik t vinsj, 800hp, 12km/h, 40 tonnes, winches and TerraFarm retained.'
p=OUT/'scripts/TWinch.lua';p.write_text(p.read_text().replace('twinchV21','twinchV22'))
index=E.parse(OUT/'machineConfigurations.xml').getroot();index.find('configuration').set('vehicle','FS25_TWinch_v22/twinch.xml')
for tree,name in [(r,'twinch.i3d'),(v,'twinch.xml'),(d,'modDesc.xml'),(index,'machineConfigurations.xml')]:E.indent(tree);E.ElementTree(tree).write(OUT/name,encoding='utf-8',xml_declaration=True)
(OUT/'TESTING.txt').write_text('V22: only two compact end inserts show steady amber cruise.\nWhole bar flashes using native beacon toggle (default Home); lower glow intensity.\nLED bar white light activates with front work lights (first F stage).\nAmber LED DRL remains engine-controlled. Other lights and vehicle systems retained.\nDisable earlier versions, install unopened ZIP. FS25 visual test pending.\n')
(OUT/'validation.json').write_text(json.dumps({'version':'0.22.0.0','game_test':'not run','cruise':'two end inserts only','beacons':'whole bar flash','LED':'front work light stage'},indent=2)+'\n')
with ZipFile(HERE.parent/'FS25_TWinch_v22.zip','w',ZIP_DEFLATED) as z:
 for f in sorted(OUT.rglob('*')):
  if f.is_file():z.write(f,f.relative_to(OUT))
