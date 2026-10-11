"""Remove the expanded wheel envelope; add recessed track-frame collision rails."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import shutil,copy,json,hashlib,xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'FS25_Follvik_TVinsj_v30'
shutil.copytree(ROOT/'FS25_Follvik_TVinsj_v29',OUT,dirs_exist_ok=True)
# Use the pre-hover original scene/contact layout, retaining transparent blade-parented logos.
shutil.copyfile(ROOT/'FS25_Follvik_TVinsj_v27/twinch.i3d',OUT/'twinch.i3d')
v=E.parse(OUT/'twinch.xml');stable=E.parse(ROOT/'FS25_Follvik_TVinsj_v27/twinch.xml')
for name in ['wheels','drivable','i3dMappings']:
 old=v.find(name);i=list(v.getroot()).index(old);v.getroot().remove(old);v.getroot().insert(i,copy.deepcopy(stable.find(name)))
old=v.find('motorized/differentialConfigurations');parent=v.find('motorized');i=list(parent).index(old);parent.remove(old);parent.insert(i,copy.deepcopy(stable.find('motorized/differentialConfigurations')))
for p in v.findall('wheels/wheelConfigurations/wheelConfiguration/wheels/wheel/physics'):
 p.set('frictionScale','2.5');p.set('maxLatStiffness','18');p.set('maxLongStiffness','60')
 # Short travel with no initial extension: visible fixed tracks stay at ground height.
 p.set('suspTravel','0.02');p.set('deltaY','0');p.set('mass','.08');p.set('restLoad','9.92')
 p.set('spring','1587.2');p.set('damper','198.4')
v.find('base/components/component').set('centerOfMass','0 .45 -.1')
t=v.find('motorized/motorConfigurations/motorConfiguration/transmission')
for direction in ['Forward','Backward']:t.set('max'+direction+'GearRatio','600')
m=v.find('motorized/motorConfigurations/motorConfiguration/motor');m.set('brakeForce','65');m.set('lowBrakeForceScale','.8')
r=E.parse(OUT/'twinch.i3d');component=r.find('Scene')[0]
component.set('angularDamping','.3');component.set('linearDamping','.08')
# The original compiled bodyCollision is a closed box: x +/- .81,
# y .82..2.27, z -1.5..1.38. Reuse its baked mesh as smaller compound rails.
# Rail bounds: x +/- .2268 around each track, y .20225..47775,
# z -1.1764..1.1564. Recessed above/between ground contacts, not below tread.
nextId=max(int(n.get('nodeId','0')) for n in r.iter())
for side,x in [('Left',1.1),('Right',-1.1)]:
 nextId+=1
 n=E.SubElement(component,'Shape',name='trackFrameCollision'+side,shapeId=component.get('shapeId'),nodeId=str(nextId),materialIds=component.get('materialIds'),translation=f'{x} .04645 .0386',scale='.28 .19 .81',compoundChild='true',collisionFilterGroup=component.get('collisionFilterGroup'),collisionFilterMask=component.get('collisionFilterMask'),nonRenderable='true',castsShadows='false',receiveShadows='false')
 E.SubElement(v.find('i3dMappings'),'i3dMapping',id='trackFrameCollision'+side,node='0>'+str(len(component)-1))
v.getroot().set('type','twinchV30')
for tree,name in [(r,'twinch.i3d'),(v,'twinch.xml')]:E.indent(tree);tree.write(OUT/name,encoding='utf-8',xml_declaration=True)
p=OUT/'modDesc.xml';d=E.parse(p);d.find('version').text='0.30.0.0';d.find('vehicleTypes/type').set('name','twinchV30');E.indent(d);d.write(p,encoding='utf-8',xml_declaration=True)
p=OUT/'machineConfigurations.xml';d=E.parse(p);d.find('configuration').set('vehicle','FS25_Follvik_TVinsj_v30/twinch.xml');E.indent(d);d.write(p,encoding='utf-8',xml_declaration=True)
p=OUT/'scripts/TWinch.lua';p.write_text(p.read_text().replace('twinchV29','twinchV30'))
p=OUT/'source_asset_hashes.json';h=json.loads(p.read_text());h['twinch.i3d']=hashlib.sha256((OUT/'twinch.i3d').read_bytes()).hexdigest();p.write_text(json.dumps(h,indent=2)+'\n')
(OUT/'TESTING.txt').write_text('V30 ground contact and collision revision.\nRestored original four native contact wheels and 2cm travel; removed added middle/end contacts and long suspension.\nOriginal wheel centre .415m and radius .415m retained, deltaY zero.\nTwo closed, recessed track-frame collision rails reuse the existing compiled body box.\nNo collision rail extends below the visible tread baseline. Blade collision stays on its hydraulic pivot.\nImproved V29 low-RPM torque retained; frictionScale 2.5, crawl ratio up to 600, 800hp / 40t / 12km/h.\nMouse hydraulics, logo textures, 100t front/rear winches and TerraFarm retained.\nDisable all older versions. Test a freshly purchased machine on flat ground, then ramps and ditches.\nFS25 physics/clearances need in-game verification; this environment cannot run the game.\n')
(OUT/'validation.json').write_text(json.dumps({'version':'0.30.0.0','game_test':'not run'},indent=2)+'\n')
with ZipFile(ROOT/'FS25_Follvik_TVinsj_v30.zip','w',ZIP_DEFLATED) as z:
 for p in sorted(OUT.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(OUT))
print(OUT)
