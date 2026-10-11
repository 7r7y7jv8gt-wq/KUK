"""Aggressive off-road tune with powered approach/departure track contacts."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import shutil,copy,json,hashlib,xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'FS25_Follvik_TVinsj_v29'
shutil.copytree(ROOT/'FS25_Follvik_TVinsj_v28',OUT,dirs_exist_ok=True)
v=E.parse(OUT/'twinch.xml');r=E.parse(OUT/'twinch.i3d');component=r.find('Scene')[0]
wheelParent=v.find('wheels/wheelConfigurations/wheelConfiguration/wheels')
maxId=max(int(n.get('nodeId','0')) for n in r.iter())
# Small terrain-contact rollers under each curved track end; no extra visible tyres.
for end,z in [('Approach',1.4),('Departure',-1.42)]:
 for side,x in [('Left',1.1),('Right',-1.1)]:
  name=end+side;maxId+=1
  n=E.SubElement(component,'TransformGroup',name=name,nodeId=str(maxId),translation=f'{x} 0.45 {z}')
  path='0>'+str(len(component)-1);maxId+=1
  E.SubElement(n,'TransformGroup',name=name+'Drive',nodeId=str(maxId))
  for key,ref in [(name,path),(name+'Drive',path+'|0')]:E.SubElement(v.find('i3dMappings'),'i3dMapping',id=key,node=ref)
  wheel=copy.deepcopy(wheelParent[0 if side=='Left' else 1]);p=wheel.find('physics')
  p.set('repr',name);p.set('driveNode',name+'Drive');p.set('radius','.45');p.set('rotSpeed','0')
  wheelParent.append(wheel)
  E.SubElement(v.find('drivable/idleTurning'),'wheel',node=name,steeringAngle='90')
for wheel in wheelParent:
 p=wheel.find('physics');p.set('mass','.032');p.set('restLoad','3.968')
 p.set('width','.5');p.set('suspTravel','.3');p.set('spring','650');p.set('damper','100')
 p.set('frictionScale','6');p.set('maxLatStiffness','48')
# Balanced torque to every physical contact; lock contacts along each track.
diffs=v.find('motorized/differentialConfigurations/differentialConfiguration/differentials')
for n in list(diffs):diffs.remove(n)
def add(a,b,ratio,speed='1'):
 attrs={'torqueRatio':str(ratio),'maxSpeedRatio':speed}
 attrs[a[0]+'Index1']=str(a[1]);attrs[b[0]+'Index2']=str(b[1])
 E.SubElement(diffs,'differential',**attrs);return ('differential',len(diffs))
roots=[]
for leaves in [[1,3,5,7,9],[2,4,6,8,10]]:
 branch=('wheel',leaves[0])
 for count,index in enumerate(leaves[1:],start=1):branch=add(branch,('wheel',index),count/(count+1))
 roots.append(branch)
add(roots[0],roots[1],.5,'2')
v.find('base/components/component').set('centerOfMass','0 .28 -.1')
motor=v.find('motorized/motorConfigurations/motorConfiguration/motor')
motor.set('minRpm','1000')
for point in list(motor):motor.remove(point)
for rpm,torque in [(.35,1.5),(.45,1.35),(.6,1.15),(.8,.95),(1,.7)]:E.SubElement(motor,'torque',normRpm=str(rpm),torque=str(torque))
motor.set('brakeForce','100');motor.set('lowBrakeForceScale','1')
t=v.find('motorized/motorConfigurations/motorConfiguration/transmission')
for direction in ['Forward','Backward']:t.set('max'+direction+'GearRatio','2000')
v.getroot().set('type','twinchV29')
for tree,name in [(r,'twinch.i3d'),(v,'twinch.xml')]:E.indent(tree);tree.write(OUT/name,encoding='utf-8',xml_declaration=True)
p=OUT/'modDesc.xml';d=E.parse(p);d.find('version').text='0.29.0.0';d.find('vehicleTypes/type').set('name','twinchV29');E.indent(d);d.write(p,encoding='utf-8',xml_declaration=True)
p=OUT/'machineConfigurations.xml';d=E.parse(p);d.find('configuration').set('vehicle','FS25_Follvik_TVinsj_v29/twinch.xml');E.indent(d);d.write(p,encoding='utf-8',xml_declaration=True)
p=OUT/'scripts/TWinch.lua';p.write_text(p.read_text().replace('twinchV28','twinchV29'))
p=OUT/'source_asset_hashes.json';h=json.loads(p.read_text());h['twinch.i3d']=hashlib.sha256((OUT/'twinch.i3d').read_bytes()).hexdigest();p.write_text(json.dumps(h,indent=2)+'\n')
(OUT/'TESTING.txt').write_text((OUT/'TESTING.txt').read_text()+'\nV29 aggressive off-road tune: ten driven contact points including front/rear curved track ends.\nFrictionScale 6 (double V28), 30cm suspension travel, centre of gravity 28cm, crawl ratio up to 2000; stronger low-RPM torque curve and 1000RPM minimum.\nTotal 40t, 800hp, governed 12km/h retained. Stronger service/low-speed brakes.\nRaise blade for crossing ditches. The physical blade and chassis collisions remain active.\nNo scripted pushing, teleporting or airborne drive force. Steep-slope performance still requires FS25 testing.\n')
(OUT/'validation.json').write_text(json.dumps({'version':'0.29.0.0','game_test':'not run'},indent=2)+'\n')
with ZipFile(ROOT/'FS25_Follvik_TVinsj_v29.zip','w',ZIP_DEFLATED) as z:
 for p in sorted(OUT.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(OUT))
print(OUT)
