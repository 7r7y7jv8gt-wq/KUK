"""Excavator-style steel undercarriage with frame clearance and smaller hook."""
from pathlib import Path
import xml.etree.ElementTree as E
import numpy as np
import math,shutil,copy,json
from zipfile import ZipFile,ZIP_DEFLATED
HERE=Path(__file__).resolve().parent;OUT=HERE.parent/'FS25_TWinch_v09'
shutil.copytree(HERE.parent/'FS25_TWinch_v08',OUT,dirs_exist_ok=True)
r=E.parse(OUT/'twinch.i3d').getroot();root=r.find('Scene')[0];shapes=r.find('Shapes');nodes={n.get('name'):n for n in root.iter()};visual=nodes['visual'];blade=nodes['bladeLift']
v=E.parse(OUT/'twinch.xml').getroot();d=E.parse(OUT/'modDesc.xml').getroot()
def resolve(path):
 head,_,tail=path.partition('>');n=r.find('Scene')[int(head)]
 for i in tail.split('|') if tail else []:n=n[int(i)]
 return n
mappings={n.get('id'):resolve(n.get('node')).get('nodeId') for n in v.find('i3dMappings')}
sid=max(int(s.get('shapeId')) for s in shapes)+1;nid=max(int(n.get('nodeId','0')) for n in root.iter())+1
# Reuse only mesh helper definitions; never execute the earlier package builder.
helpers=(HERE/'package_mod_v05.py').read_text();exec(helpers[helpers.index('fmt=lambda'):helpers.index('# Remove the object')])
# Narrower, single-grouser excavator shoes with articulated side chain rails.
prototype=E.Element('TransformGroup')
outline=[(-.185,-.040),(.185,-.040),(.20,-.025),(.20,.025),(.185,.040),(-.185,.040),(-.20,.025),(-.20,-.025)]
p=[(x,y,z) for y in [-.016,.016] for x,z in outline];f=[]
for i in range(1,7):f.extend([(0,i+1,i),(8,8+i,9+i)])
for i in range(8):j=(i+1)%8;f.extend([(i,j,j+8),(i,j+8,i+8)])
mesh('ExcavatorTrackShoe',p,[tuple(reversed(t)) for t in f],3,prototype)
box('SingleTrackGrouser',(0,.023,0),(.394,.014,.014),14,prototype)
for x in [-.13,.13]:
 box('ArticulatedChainRail',(x,-.028,0),(.042,.024,.077),3,prototype)
 lathe('TrackHingePin',[(-.026,.013),(.026,.013)],11,prototype,axis='x',center=(x,-.026,.046),segments=12)
 for z in [-.025,.025]:
  g=group(prototype,'TrackBoltSeat',translation=fmt((x,.016,z)),rotation='-90 0 0')
  lathe('TrackBolt',[(0,.012),(.007,.012)],11,g,segments=6)
for x in [-.042,.042]:box('TrackGuideHorn',(x,-.039,0),(.018,.046,.026),3,prototype)
for sign,side in [(-1,'Right'),(1,'Left')]:
 track=nodes['track'+side];track.set('translation',fmt((sign*1.10,0,0)))
 for i,link in enumerate(track):
  for child in list(link):link.remove(child)
  for part in prototype:
   part=copy.deepcopy(part)
   for child in part.iter():child.set('nodeId',str(nid));nid+=1
   link.append(part)
 for n in v.findall('twinch/track'):
  if n.get('node')=='track'+side:n.set('offsetX',str(sign*1.10))
 for prefix in ['front','rear']:
  n=nodes[prefix+side];xyz=list(map(float,n.get('translation').split()));xyz[0]=sign*1.10;n.set('translation',fmt(xyz))
v.find('base/size').set('width','2.6')
for physics in v.findall('wheels/wheelConfigurations/wheelConfiguration/wheels/wheel/physics'):physics.set('width','.4')
# Delete old external plate guards and stacked full-disk wheels.
for n in list(visual):
 if n.get('name') in ['TrackCarrierBeam','OuterTrackGuard','GuardBoltFrame']:visual.remove(n)
for idx in range(16):
 roller=nodes['roller_'+str(idx)];sign=-1 if idx in [0,1,4,5,6,7,8,9] else 1
 xyz=list(map(float,roller.get('translation').split()));xyz[0]=sign*1.10
 if idx>=4:xyz[1]=.255
 roller.set('translation',fmt(xyz))
 for child in list(roller):roller.remove(child)
 if idx<4:
  # Twin shoulders leave a channel for central guide horns; recessed hubs.
  for x in [-.12,.12]:lathe('RecessedEndWheel',[(-.036,.265),(-.026,.34),(.026,.34),(.036,.265)],3,roller,axis='x',center=(x,0,0),segments=48)
  lathe('EndWheelHub',[(-.15,.115),(-.13,.16),(.13,.16),(.15,.115)],2,roller,axis='x',segments=32)
  if idx in [0,2]:
   for j in range(24):
    a=2*math.pi*j/24
    for x in [-.13,.13]:
     g=group(roller,'SprocketTooth',translation=fmt((x,.343*math.cos(a),.343*math.sin(a))),rotation=fmt((math.degrees(a),0,0)))
     box('SprocketToothSteel',(0,0,0),(.052,.024,.031),11,g)
  for j in range(8):
   a=2*math.pi*j/8;g=group(roller,'HubBoltSeat',translation=fmt((sign*.154,.125*math.cos(a),.125*math.sin(a))),rotation=f'0 {sign*90} 0')
   lathe('HubBolt',[(0,.014),(.012,.014)],11,g,segments=6)
 else:
  for x in [-.11,.11]:lathe('RoadWheelRim',[(-.031,.165),(-.025,.19),(.025,.19),(.031,.165)],3,roller,axis='x',center=(x,0,0))
  lathe('RoadWheelAxle',[(-.16,.054),(.16,.054)],2,roller,axis='x')
# Box-section crawler carriages, return rollers and idler tensioning mechanism.
for sign,side in [(-1,'Right'),(1,'Left')]:
 carriage=group(visual,'ExcavatorCarriage'+side)
 box('CrawlerCarrierBeam',(sign*1.10,.49,-.04),(.26,.14,2.05),2,carriage)
 box('OuterCarrierPlate',(sign*1.26,.465,-.04),(.028,.17,1.98),2,carriage)
 for z in [-.65,.25]:
  g=group(root,'returnRoller'+side+str(z),translation=fmt((sign*1.10,.67,z)))
  box('ReturnRollerMount',(sign*1.10,.59,z),(.11,.12,.09),2,carriage)
  for x in [-.10,.10]:lathe('UpperReturnRoller',[(-.025,.074),(.025,.074)],3,g,axis='x',center=(x,0,0))
  config=next(n for n in v.findall('twinch/track') if n.get('node')=='track'+side)
  key=g.get('name');mappings[key]=g.get('nodeId');E.SubElement(config,'roller',node=key,radius='.074')
 box('IdlerSlideRail',(sign*1.10,.50,.79),(.19,.15,.54),2,carriage)
 lathe('GreaseTensionCylinder',[(.42,.048),(.79,.048)],2,carriage,center=(sign*1.10,.51,0))
 lathe('IdlerTensionRod',[(.75,.027),(1.04,.027)],12,carriage,center=(sign*1.10,.51,0))
# Visible hydrostatic crawler drivetrain, protected underneath the central chassis.
drive=group(visual,'HydrostaticDrivetrain')
box('UndersideGearbox',(0,.49,-.47),(.56,.29,.64),2,drive)
box('GearboxSump',(0,.305,-.47),(.48,.075,.56),3,drive)
box('BellySkidPlate',(0,.25,-.35),(1.04,.045,1.66),10,drive)
for z in [-.87,.61]:box('UndercarriageCrossmember',(0,.51,z),(1.77,.12,.17),2,drive)
for sign,side in [(-1,'Right'),(1,'Left')]:
 box('DriveMount'+side,(sign*.72,.47,-1.05),(.16,.27,.30),2,drive)
 lathe('FinalDriveHousing'+side,[(-.10,.14),(-.08,.20),(.08,.20),(.10,.14)],2,drive,axis='x',center=(sign*.86,.415,-1.22))
 lathe('HydraulicTravelMotor'+side,[(-.12,.10),(.12,.10)],3,drive,axis='x',center=(sign*.64,.415,-1.22))
 lathe('DriveOutputShaft'+side,[(-.16,.06),(.16,.06)],11,drive,axis='x',center=(sign*.94,.415,-1.22))
 for offset in [-.04,.04]:tube('TravelHydraulicLine'+side,[(sign*.22,.53,-.49+offset),(sign*.40,.55,-.72+offset),(sign*.46,.49,-1.05+offset),(sign*.58,.46,-1.16+offset)],.012,13,drive)
 for z in [-.97,.22]:
  g=group(drive,'SkidBoltSeat',translation=fmt((sign*.45,.222,z)),rotation='90 0 0');lathe('SkidPlateBolt',[(0,.016),(.010,.016)],11,g,segments=6)
# Generate tangents for the new normal-mapped meshes; discard unused old shapes.
used={n.get('shapeId') for n in root.iter('Shape')}
for shape in list(shapes):
 if shape.get('shapeId') not in used:shapes.remove(shape)
 elif shape.find('Vertices').get('normal')=='true':shape.find('Vertices').set('tangent','true')
# Repair all mappings after edits, including wheel physics, camera and hydraulics.
paths={}
def walk(n,path):
 paths[n.get('nodeId')]=path
 for i,c in enumerate(n):walk(c,path+('' if path.endswith('>') else '|')+str(i))
walk(root,'0>')
# Root is indexed as 0; root children start at 0>n rather than 0>|n.
paths[root.get('nodeId')]='0'
for n in list(v.find('i3dMappings')):v.find('i3dMappings').remove(n)
for key,nodeid in mappings.items():
 if nodeid in paths:E.SubElement(v.find('i3dMappings'),'i3dMapping',id=key,node=paths[nodeid])
 else:
  assert not any(key==value for n in v.iter() if n.tag!='i3dMapping' for value in n.attrib.values()), 'Removed referenced node '+key
script=(OUT/'scripts/TWinch.lua').read_text().replace('setScale(s.hook,.14,.14,.14)','setScale(s.hook,.014,.014,.014)')
(OUT/'scripts/TWinch.lua').write_text(script)
d.find('description/en').text='V09: one-tenth-size winch hooks, excavator-style single-grouser steel tracks with paired wheels and return rollers, 55mm frame clearance and visible underside hydrostatic drivetrain. On-foot winch, hydraulic blade and TerraFarm compatibility retained.'
v.set('type','twinchV09');d.find('vehicleTypes/type').set('name','twinchV09');d.find('version').text='0.9.0.0';d.find('title/en').text='T-Winch v09 - Excavator Undercarriage'
for n in v.findall('storeData/name/*'):n.text='T-Winch 30.2 v09'
v.find('annotation').text='Excavator single-grouser tracks, wider track centers for frame clearance, twin-wheel running gear and underside hydrostatic drive. Hook scale reduced tenfold.'
config=E.parse(OUT/'machineConfigurations.xml').getroot();config.find('configuration').set('vehicle','FS25_TWinch_v09/twinch.xml')
for tree,name in [(r,'twinch.i3d'),(v,'twinch.xml'),(d,'modDesc.xml'),(config,'machineConfigurations.xml')]:E.indent(tree);E.ElementTree(tree).write(OUT/name,encoding='utf-8',xml_declaration=True)
text=(OUT/'TESTING.txt').read_text().replace('v08','v09')
(OUT/'TESTING.txt').write_text(text+'\nV09: hook scale .014 (one tenth of .14). Excavator-style 400mm shoes,\ntrack centers +/-1.10m, twin running wheels, return rollers, tensioner,\ncentral gearbox, travel motors, final drive housings, shafts, lines and skid.\nUnderside drivetrain is visible geometry; existing hydrostatic wheel physics\nremain the driving system. Check clearance and ground behavior in FS25.\n')
# Refresh shop thumbnails from the exported preview, preserving DXT5/mipmaps.
preview=HERE/'preview_v09.png'
if preview.exists():
 from PIL import Image,ImageOps
 import io,struct
 for name in ['icon_twinch.dds','store_twinch.dds']:
  dimensions=Image.open(OUT/name).size
  level=ImageOps.fit(Image.open(preview).convert('RGBA'),dimensions,method=Image.Resampling.LANCZOS)
  stream=io.BytesIO();level.save(stream,format='DDS',pixel_format='DXT5');data=bytearray(stream.getvalue());count=1
  while level.width>1 or level.height>1:
   level=level.resize((max(1,level.width//2),max(1,level.height//2)),Image.Resampling.LANCZOS)
   stream=io.BytesIO();level.save(stream,format='DDS',pixel_format='DXT5');data.extend(stream.getvalue()[128:]);count+=1
  struct.pack_into('<I',data,8,struct.unpack_from('<I',data,8)[0]|0x20000)
  struct.pack_into('<I',data,28,count)
  struct.pack_into('<I',data,108,0x401008)
  (OUT/name).write_bytes(data)
(OUT/'validation.json').write_text(json.dumps({'version':'0.9.0.0','game_test':'not run','track_centers_metres':[-1.10,1.10],'shoe_width_metres':.40,'hook_scale':.014,'drivetrain':'visible hydrostatic components; existing vehicle driving physics'},indent=2)+'\n')
with ZipFile(HERE.parent/'FS25_TWinch_v09.zip','w',ZIP_DEFLATED) as z:
 for f in sorted(OUT.rglob('*')):
  if f.is_file():z.write(f,f.relative_to(OUT))
print('Built',OUT)
