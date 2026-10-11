"""Six driven track contacts, terrain compliance and low-speed climbing setup."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import shutil,copy,json,hashlib,xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'FS25_Follvik_TVinsj_v28'
shutil.copytree(ROOT/'FS25_Follvik_TVinsj_v27',OUT,dirs_exist_ok=True)
v=E.parse(OUT/'twinch.xml');r=E.parse(OUT/'twinch.i3d');component=r.find('Scene')[0]
wheelParent=v.find('wheels/wheelConfigurations/wheelConfiguration/wheels')
# Append support nodes so all original indexed I3D mappings stay valid.
maxId=max(int(n.get('nodeId','0')) for n in r.iter())
rootIndex='0>'
for side,x in [('Left',1.1),('Right',-1.1)]:
 name='middle'+side;maxId+=1
 support=E.SubElement(component,'TransformGroup',name=name,nodeId=str(maxId),translation=f'{x} 0.415 -0.01')
 reprPath=rootIndex+str(len(component)-1)
 maxId+=1;E.SubElement(support,'TransformGroup',name=name+'Drive',nodeId=str(maxId))
 for key,path in [(name,reprPath),(name+'Drive',reprPath+'|0')]:E.SubElement(v.find('i3dMappings'),'i3dMapping',id=key,node=path)
 wheel=copy.deepcopy(wheelParent[0 if side=='Left' else 1]);p=wheel.find('physics')
 p.set('repr',name);p.set('driveNode',name+'Drive');p.set('rotSpeed','0');wheelParent.append(wheel)
for wheel in wheelParent:
 p=wheel.find('physics')
 # 6 x 53 1/3 kg + the original 39680 kg chassis = 40 tonnes.
 p.set('mass',str(.32/6));p.set('restLoad',str(39.68/6))
 p.set('suspTravel','0.18');p.set('spring','900');p.set('damper','120')
 p.set('frictionScale','3.0');p.set('maxLatStiffness','24')
# Each middle contact is driven from its own track-side differential.
diffs=v.find('motorized/differentialConfigurations/differentialConfiguration/differentials')
for n in list(diffs):diffs.remove(n)
for attrs in [dict(wheelIndex1='1',wheelIndex2='3',torqueRatio='.5',maxSpeedRatio='1'),dict(wheelIndex1='2',wheelIndex2='4',torqueRatio='.5',maxSpeedRatio='1'),dict(differentialIndex1='1',wheelIndex2='5',torqueRatio=str(2/3),maxSpeedRatio='1'),dict(differentialIndex1='2',wheelIndex2='6',torqueRatio=str(2/3),maxSpeedRatio='1'),dict(differentialIndex1='3',differentialIndex2='4',torqueRatio='.5',maxSpeedRatio='2')]:E.SubElement(diffs,'differential',**attrs)
# Keep left/right differential slip for steering; same-side contacts stay locked.
idle=v.find('drivable/idleTurning')
E.SubElement(idle,'wheel',node='middleLeft',steeringAngle='90')
E.SubElement(idle,'wheel',node='middleRight',steeringAngle='90')
v.find('base/components/component').set('centerOfMass','0 .4 -.1')
motor=v.find('motorized/motorConfigurations/motorConfiguration/motor')
motor.set('brakeForce','65');motor.set('lowBrakeForceScale','0.8')
transmission=v.find('motorized/motorConfigurations/motorConfiguration/transmission')
for direction in ['Forward','Backward']:
 transmission.set('min'+direction+'GearRatio','28')
 transmission.set('max'+direction+'GearRatio','420')
v.getroot().set('type','twinchV28')
for tree,name in [(r,'twinch.i3d'),(v,'twinch.xml')]:E.indent(tree);tree.write(OUT/name,encoding='utf-8',xml_declaration=True)
p=OUT/'modDesc.xml';d=E.parse(p);d.find('version').text='0.28.0.0';d.find('vehicleTypes/type').set('name','twinchV28');E.indent(d);d.write(p,encoding='utf-8',xml_declaration=True)
p=OUT/'machineConfigurations.xml';d=E.parse(p);d.find('configuration').set('vehicle','FS25_Follvik_TVinsj_v28/twinch.xml');E.indent(d);d.write(p,encoding='utf-8',xml_declaration=True)
p=OUT/'scripts/TWinch.lua';p.write_text(p.read_text().replace('twinchV27','twinchV28'))
(OUT/'TESTING.txt').write_text((OUT/'TESTING.txt').read_text()+'\nV28: six powered track contacts, including middle support on both sides.\nSuspension travel 18cm, frictionScale 3, lower centre of gravity, stronger brakes, wider hydrostatic ratios.\n40t, 800hp and 12km/h retained. Raise the hydraulic blade for ditch crossings; its collision remains active.\nClimbing still depends on slope, terrain and grip; vertical faces are not traversable.\nEngine physics and visible suspension behaviour require FS25 verification.\n')
p=OUT/'source_asset_hashes.json';hashes=json.loads(p.read_text());hashes['twinch.i3d']=hashlib.sha256((OUT/'twinch.i3d').read_bytes()).hexdigest();p.write_text(json.dumps(hashes,indent=2)+'\n')
(OUT/'validation.json').write_text(json.dumps({'version':'0.28.0.0','game_test':'not run'},indent=2)+'\n')
with ZipFile(ROOT/'FS25_Follvik_TVinsj_v28.zip','w',ZIP_DEFLATED) as z:
 for p in sorted(OUT.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(OUT))
print(OUT)
