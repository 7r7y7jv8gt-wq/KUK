"""Build an untested FS25 vehicle candidate from the original reference asset."""
from pathlib import Path
import xml.etree.ElementTree as E
from zipfile import ZipFile, ZIP_DEFLATED
from PIL import Image
import json

HERE=Path(__file__).resolve().parent
OUT=HERE.parent/'FS25_TWinch_Test'
OUT.mkdir(exist_ok=True)
def write(root,path):
    E.indent(root); E.ElementTree(root).write(path,encoding='utf-8',xml_declaration=True)

r=E.parse(HERE/'twinch.i3d').getroot()
shapes=r.find('Shapes')
# Rotate from model longitudinal X to GIANTS vehicle forward +Z.
for s in shapes:
    for v in s.find('Vertices'):
        for attr in ['p','n']:
            x,y,z=map(float,v.get(attr).split()); v.set(attr,f'{-z:.6g} {y:.6g} {x:.6g}')

# Add an explicit closed, convex collision hull (never use the detailed visual mesh).
sid=str(max(int(s.get('shapeId')) for s in shapes)+1)
s=E.SubElement(shapes,'IndexedTriangleSet',name='bodyCollision',shapeId=sid)
positions=[(x,y,z) for z in [-1.5,1.38] for y in [.82,2.27] for x in [-.81,.81]]
vs=E.SubElement(s,'Vertices',count='8')
for p in positions:E.SubElement(vs,'v',p=' '.join(map(str,p)))
triangles=[(0,2,3),(0,3,1),(4,5,7),(4,7,6),(0,1,5),(0,5,4),(2,6,7),(2,7,3),(0,4,6),(0,6,2),(1,3,7),(1,7,5)]
ts=E.SubElement(s,'Triangles',count='12')
for t in triangles:E.SubElement(ts,'t',vi=' '.join(map(str,t)))
subs=E.SubElement(s,'Subsets',count='1'); E.SubElement(subs,'Subset',firstVertex='0',numVertices='8',firstIndex='0',numIndices='36')
scene=r.find('Scene'); old=scene[0]; scene.remove(old)
root=E.SubElement(scene,'Shape',name='twinchComponent',nodeId='10000',shapeId=sid,materialIds='2',dynamic='true',compound='true',collisionMask='2105410',nonRenderable='true')
visual=E.SubElement(root,'TransformGroup',name='visual',nodeId='10001')
blade=E.SubElement(root,'TransformGroup',name='bladeLift',nodeId='10002')
for n in list(old):
    (blade if n.get('name','').startswith(('FrontBlade','BladeCuttingEdge','BladeRib','BladeTowEye','WinchHook','ChainLink')) else visual).append(n)
helpers={}
def helper(name,loc,**attrs):
    index=len(root); helpers[name]=f'0>{index}'
    return E.SubElement(root,'TransformGroup',name=name,nodeId=str(11000+index),translation=loc,**attrs)
for name,x,z in [('frontLeft',.88,1.1),('frontRight',-.88,1.1),('rearLeft',.88,-1.12),('rearRight',-.88,-1.12)]:
    h=helper(name,f'{x} 0.43 {z}')
    E.SubElement(h,'TransformGroup',name=name+'Drive',nodeId=str(12000+len(helpers)))
    helpers[name+'Drive']=helpers[name]+'|0'
helper('exitPoint','1.8 0 0')
helper('cameraTarget','0 1.2 0')
cam=helper('outdoorCamera','0 3 -6',rotation='-15 180 0'); cam.tag='Camera'; cam.set('fov','60'); cam.set('nearClip','0.1'); cam.set('farClip','1000')
helper('motorSound','0 1.5 0')
write(r,OUT/'twinch.i3d')

vehicle='''<vehicle type="twinchTest">
  <annotation>FS25 prototype: estimated specifications; requires game validation.</annotation>
  <storeData>
    <name><en>T-Winch Reference Test</en><de>T-Winch Referenz Test</de></name>
    <specs><power>58</power><maxSpeed>8</maxSpeed></specs>
    <functions><function>Tracked forestry support vehicle - test prototype</function></functions>
    <image>store_twinch.dds</image><price>85000</price><lifetime>600</lifetime>
    <brand>LIZARD</brand><category>tractorsS</category>
  </storeData>
  <base>
    <typeDesc>$l10n_typeDesc_tractor</typeDesc><filename>twinch.i3d</filename>
    <sounds filename="$data/vehicles/johnDeere/series6M/sounds/series6M.xml"/>
    <size width="2.2" length="3.8" height="2.5"/>
    <components><component centerOfMass="0 0.85 0" solverIterationCount="20" mass="5000"/></components>
    <schemaOverlay name="VEHICLE"/><mapHotspot type="TRACTOR"/>
  </base>
  <wheels>
    <wheelConfigurations><wheelConfiguration name="Prototype tracks" price="0" saveId="DEFAULT"><wheels autoRotateBackSpeed="2">
      <wheel isLeft="true" hasTireTracks="false" hasParticles="false"><physics repr="frontLeft" driveNode="frontLeftDrive" radius="0.37" width="0.42" mass="80" rotSpeed="1" rotMin="-30" rotMax="30" restLoad="1.25" initialCompression="20" suspTravel="0.08" spring="65" damper="50" frictionScale="2"/></wheel>
      <wheel isLeft="false" hasTireTracks="false" hasParticles="false"><physics repr="frontRight" driveNode="frontRightDrive" radius="0.37" width="0.42" mass="80" rotSpeed="1" rotMin="-30" rotMax="30" restLoad="1.25" initialCompression="20" suspTravel="0.08" spring="65" damper="50" frictionScale="2"/></wheel>
      <wheel isLeft="true" hasTireTracks="false" hasParticles="false"><physics repr="rearLeft" driveNode="rearLeftDrive" radius="0.37" width="0.42" mass="80" rotSpeed="0" restLoad="1.25" initialCompression="20" suspTravel="0.08" spring="65" damper="50" frictionScale="2"/></wheel>
      <wheel isLeft="false" hasTireTracks="false" hasParticles="false"><physics repr="rearRight" driveNode="rearRightDrive" radius="0.37" width="0.42" mass="80" rotSpeed="0" restLoad="1.25" initialCompression="20" suspTravel="0.08" spring="65" damper="50" frictionScale="2"/></wheel>
    </wheels></wheelConfiguration></wheelConfigurations>
    <ackermannSteeringConfigurations><ackermannSteering rotSpeed="35" rotMax="30" rotCenterWheel1="3" rotCenterWheel2="4"/></ackermannSteeringConfigurations>
  </wheels>
  <motorized>
    <consumerConfigurations><consumerConfiguration><consumer fillUnitIndex="1" usage="8" fillType="diesel"/></consumerConfiguration></consumerConfigurations>
    <motorConfigurations><motorConfiguration name="58 hp prototype" hp="58" price="0">
      <motor torqueScale="0.24" minRpm="850" maxRpm="2200" maxForwardSpeed="8" maxBackwardSpeed="8" brakeForce="8" lowBrakeForceScale="0.5">
        <torque normRpm="0.45" torque="0.85"/><torque normRpm="0.6" torque="1"/><torque normRpm="0.8" torque="0.95"/><torque normRpm="1" torque="0.7"/>
      </motor>
      <transmission minForwardGearRatio="90" maxForwardGearRatio="300" minBackwardGearRatio="90" maxBackwardGearRatio="300"/>
    </motorConfiguration></motorConfigurations>
    <differentialConfigurations><differentialConfiguration>
      <differentials><differential torqueRatio="0.5" maxSpeedRatio="1.2" wheelIndex1="1" wheelIndex2="2"/>
      <differential torqueRatio="0.5" maxSpeedRatio="1.2" wheelIndex1="3" wheelIndex2="4"/>
      <differential torqueRatio="0.5" maxSpeedRatio="1" differentialIndex1="1" differentialIndex2="2"/></differentials>
    </differentialConfiguration></differentialConfigurations>
  </motorized>
  <fillUnit><fillUnitConfigurations><fillUnitConfiguration><fillUnits>
    <fillUnit capacity="80" fillTypes="diesel" showOnHud="false" showInShop="false"><exactFillRootNode node="0>"/></fillUnit>
  </fillUnits></fillUnitConfiguration></fillUnitConfigurations></fillUnit>
  <enterable isTabbable="true"><exitPoint node="exitPoint"/><enterReferenceNode node="0>"/>
    <cameras><camera node="outdoorCamera" rotateNode="cameraTarget" rotatable="true" limit="true" useWorldXZRotation="true" rotMinX="-1.4" rotMaxX="1" transMin="4" transMax="20"/></cameras>
  </enterable>
  <drivable/>
  <foldable><foldingParts startMoveDirection="1"><foldingPart animationName="bladeLift" speedScale="1"/></foldingParts></foldable>
  <animations><animation name="bladeLift"><part node="bladeLift" startTime="0" endTime="1.5" startTrans="0 0 0" endTrans="0 0.35 0"/></animation></animations>
  <i3dMappings/>
</vehicle>'''
v=E.fromstring(vehicle); mappings=v.find('i3dMappings')
for name,node in {**helpers,'bladeLift':'0>1'}.items():E.SubElement(mappings,'i3dMapping',id=name,node=node)
write(v,OUT/'twinch.xml')

desc=E.fromstring('''<modDesc descVersion="92">
  <author>Reference model project</author><version>0.1.0.0</version>
  <title><en>T-Winch Vehicle Test</en></title>
  <description><en>Untested FS25 driving prototype. Simplified wheel physics, static tracks and decorative chain. Not a functional winch. See TESTING.txt.</en></description>
  <iconFilename>icon_twinch.dds</iconFilename><multiplayer supported="false"/>
  <vehicleTypes><type name="twinchTest" parent="baseDrivable" className="Vehicle" filename="$dataS/scripts/vehicles/Vehicle.lua"><specialization name="foldable"/></type></vehicleTypes>
  <storeItems><storeItem xmlFilename="twinch.xml"/></storeItems>
</modDesc>''')
write(desc,OUT/'modDesc.xml')
im=Image.open(HERE/'preview.png').convert('RGBA')
for name,size in [('icon_twinch.dds',(256,256)),('store_twinch.dds',(512,512))]:
    thumb=Image.new('RGBA',size,(65,65,65,255)); src=im.copy(); src.thumbnail(size); thumb.paste(src,((size[0]-src.width)//2,(size[1]-src.height)//2)); thumb.save(OUT/name)
(OUT/'TESTING.txt').write_text('''FS25 T-Winch v0.1 - UNTESTED VEHICLE CANDIDATE

Put FS25_TWinch_Test.zip in Documents/My Games/FarmingSimulator2025/mods.
Do not unpack it. Enable T-Winch Vehicle Test in a NEW test savegame.
Find LIZARD T-Winch Reference Test under small tractors.
Try purchase, entering with E/Tab, motor start, forward/reverse, steering,
braking, camera movement and fold/unfold (default X) to move the blade.
Save/reload and check that the vehicle remains stable.

This package has not been opened in GIANTS Editor or run in FS25.
XML checks do not prove game compatibility. If unavailable in the store,
or it fails purchase/physics, send log.txt from the FS25 user directory.
Do not use an established savegame for the first test.

Known limitations: no functioning winch or rope, no moving track belts,
wheel steering rather than skid steering, estimated dimensions and power,
simple materials, no headlights, no working hydraulic linkage, no AI worker,
no multiplayer support. Blade movement is visual only; it does not grade
terrain or manipulate piles. The collision hull covers the body only.
The XML-based I3D importer and baseDrivable defaults need game verification.
modDesc version 92 follows the existing FS25 test package in this repository;
newer game patches may require adjustments.
''',encoding='utf-8')

# Verify every local file reference and mapped scene path, and triangle indices.
def resolve(path):
    top,sep,tail=path.partition('>'); n=scene[int(top)]
    if tail:
        for index in tail.split('|'): n=n[int(index)]
    return n
mapping={n.get('id'):n.get('node') for n in mappings}
for name,path in mapping.items():assert resolve(path).get('name')==name
for n in v.iter():
    for key in ['node','repr','driveNode','rotateNode','linkNode']:
        if key in n.attrib: resolve(mapping.get(n.get(key),n.get(key)))
for node in list(root.iter('Shape')):
    assert node.get('shapeId') in {s.get('shapeId') for s in shapes}
for s in shapes:
    vs=s.find('Vertices'); ts=s.find('Triangles'); assert len(vs)==int(vs.get('count')); assert len(ts)==int(ts.get('count'))
    for t in ts: assert all(0<=int(i)<len(vs) for i in t.get('vi').split())
for tree in [v,desc]:
    for tag in ['filename','image','iconFilename']:
        for n in tree.iter(tag):
            if n.text and not n.text.startswith('$'):assert (OUT/n.text).is_file(),n.text
for f in OUT.glob('*.xml'):E.parse(f)
report={'xml_and_scene_reference_checks':'passed','scene_meshes':len(shapes),'mapped_nodes':len(mapping),'giants_editor':'not run','fs25_purchase_drive_save_reload':'not run','release_status':'untested prototype'}
(OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
with ZipFile(HERE.parent/'FS25_TWinch_Test.zip','w',ZIP_DEFLATED) as z:
    for f in sorted(OUT.iterdir()):z.write(f,f.name)
print(json.dumps(report,indent=2))
