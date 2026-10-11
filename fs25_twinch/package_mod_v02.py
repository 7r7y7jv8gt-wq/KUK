"""Build v02 with corrected FS25 physics, independent moving tracks and a recovery winch.

Run package_mod.py first if the original FS25_TWinch_Test inputs do not exist.
No proprietary game assets are copied into this package.
"""
from pathlib import Path
import xml.etree.ElementTree as E
from zipfile import ZipFile, ZIP_DEFLATED
from PIL import Image
import math, json, shutil, struct, io

HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'FS25_TWinch_Test'
OUT=HERE.parent/'FS25_TWinch_v02'
OUT.mkdir(exist_ok=True)
def write(root,path):
    E.indent(root); E.ElementTree(root).write(path,encoding='utf-8',xml_declaration=True)
def fmt(v):return ' '.join(f'{x:.7g}' for x in v)
r=E.parse(OLD/'twinch.i3d').getroot(); shapes=r.find('Shapes'); root=r.find('Scene')[0]
root.attrib.pop('collisionMask',None)
# Modern vehicle filter values from the FS25 reference tractor already in this repo.
root.set('collisionFilterGroup','0x10004'); root.set('collisionFilterMask','0xfe3ffb83')
root.set('linearDamping','0.05'); root.set('angularDamping','0.15')
body=next(s for s in shapes if s.get('shapeId')==root.get('shapeId'))
body.set('meshUsage','256')
visual=root[0]; blade=root[1]
for node in list(visual):
    if node.get('name','').startswith(('TrackShoe','TrackCleat')):visual.remove(node)

node_id=max(int(n.get('nodeId','0')) for n in r.find('Scene').iter())+1
shape_id=max(int(s.get('shapeId')) for s in shapes)+1
def node(parent,tag,name,**attrs):
    global node_id
    n=E.SubElement(parent,tag,name=name,nodeId=str(node_id),**attrs); node_id+=1;return n
def geometry(name,vertices,triangles,cpu=False):
    global shape_id
    sid=str(shape_id);shape_id+=1
    s=E.SubElement(shapes,'IndexedTriangleSet',name=name,shapeId=sid)
    if cpu:s.set('meshUsage','256')
    vs=E.SubElement(s,'Vertices',count=str(len(triangles)*3),normal='true',uv0='true')
    for a,b,c in triangles:
        p,q,t=vertices[a],vertices[b],vertices[c]
        u=[q[i]-p[i] for i in range(3)];v=[t[i]-p[i] for i in range(3)]
        normal=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
        length=math.sqrt(sum(x*x for x in normal)); normal=tuple(x/length for x in normal)
        for index in [a,b,c]:E.SubElement(vs,'v',p=fmt(vertices[index]),n=fmt(normal),t0='0 0')
    ts=E.SubElement(s,'Triangles',count=str(len(triangles)))
    for i in range(len(triangles)):E.SubElement(ts,'t',vi=f'{3*i} {3*i+1} {3*i+2}')
    sub=E.SubElement(s,'Subsets',count='1');E.SubElement(sub,'Subset',firstVertex='0',numVertices=str(len(vs)),firstIndex='0',numIndices=str(len(vs)))
    return sid
faces=[(0,2,3),(0,3,1),(4,5,7),(4,7,6),(0,1,5),(0,5,4),(2,6,7),(2,7,3),(0,4,6),(0,6,2),(1,3,7),(1,7,5)]
def boxgeometry(name,size,center=(0,0,0),cpu=False):
    sx,sy,sz=size;cx,cy,cz=center
    points=[(cx+x*sx/2,cy+y*sy/2,cz+z*sz/2) for z in [-1,1] for y in [-1,1] for x in [-1,1]]
    return geometry(name,points,faces,cpu)
def box(parent,name,size,loc,material='2',**attrs):
    return node(parent,'Shape',name,shapeId=boxgeometry(name,size),materialIds=material,translation=fmt(loc),castsShadows='true',receiveShadows='true',**attrs)

shoe=boxgeometry('sharedTrackShoe',(.54,.045,.083))
cleat=boxgeometry('sharedTrackCleat',(.55,.02,.026),(0,.0325,0))
tracks=[]
for side in [-1,1]:
    # +X is the vehicle's left side in the source convention.
    track=node(root,'TransformGroup','trackLeft' if side==1 else 'trackRight',translation=f'{side*.88} 0 0')
    track.set('offsetX',str(side*.88))  # removed before I3D serialization; used for XML below
    tracks.append(track)
    for i in range(74):
        s=i*(4.68+2*math.pi*.37)/74
        straight,arc=2.34,math.pi*.37
        if s<straight:y,z,a=.785,-1.22+s,0
        elif s<straight+arc:
            a=(s-straight)/.37;y=.415+.37*math.cos(a);z=1.12+.37*math.sin(a)
        elif s<2*straight+arc:y,z,a=.045,1.12-(s-straight-arc),math.pi
        else:a=math.pi+(s-2*straight-arc)/.37;y=.415+.37*math.cos(a);z=-1.22+.37*math.sin(a)
        link=node(track,'TransformGroup',f'link_{i:02d}',translation=fmt((0,y,z)),rotation=fmt((math.degrees(a),0,0)))
        node(link,'Shape','shoe',shapeId=shoe,materialIds='3',castsShadows='true',receiveShadows='true')
        node(link,'Shape','cleat',shapeId=cleat,materialIds='2',castsShadows='true',receiveShadows='true')

# Move each baked wheel mesh into a local rotating assembly, including hubs/bolts.
byid={s.get('shapeId'):s for s in shapes}
roller_groups={};roller_list={-1:[],1:[]}
for n in list(visual):
    name=n.get('name','')
    if not name.startswith(('DriveWheel','WheelHub','HubBolt','RoadWheel','RoadHub')):continue
    shape=byid[n.get('shapeId')];ps=[list(map(float,v.get('p').split())) for v in shape.find('Vertices')]
    center=[(min(p[i] for p in ps)+max(p[i] for p in ps))/2 for i in range(3)]
    side=1 if center[0]>0 else -1
    if name.startswith(('RoadWheel','RoadHub')):
        pivotZ=min([-.9,-.55,-.2,.15,.5,.85],key=lambda z:abs(z-center[2]));pivotY=.3;radius=.17
    else:
        pivotZ=min([-1.22,1.12],key=lambda z:abs(z-center[2]));pivotY=.43;radius=.35
    key=(side,pivotY,pivotZ)
    if key not in roller_groups:
        pivot=(side*.88,pivotY,pivotZ)
        g=node(root,'TransformGroup',f'roller_{len(roller_groups)}',translation=fmt(pivot))
        roller_groups[key]=g;roller_list[side].append((g,radius))
    g=roller_groups[key]
    pivot=(side*.88,pivotY,pivotZ)
    for v,p in zip(shape.find('Vertices'),ps):v.set('p',fmt([p[i]-pivot[i] for i in range(3)]))
    visual.remove(n);g.append(n)

# Blade collisions remain attached to the folding assembly.
blade_shape=boxgeometry('bladeCollision',(.0+2.05,.98,.10),(0,.76,1.83),cpu=True)
node(blade,'Shape','bladeCollision',shapeId=blade_shape,materialIds='2',compoundChild='true',collisionFilterGroup='0x10004',collisionFilterMask='0xfe3ffb83',nonRenderable='true')
# Separate exact fuel fill root with documented FS25 group/mask, matching a modern reference asset.
fuel_shape=boxgeometry('fuelFillPhysics',(.04,.04,.04),cpu=True)
fuel=node(root,'Shape','fuelFillRoot',shapeId=fuel_shape,materialIds='2',translation='.70 1 .3',kinematic='true',compound='true',collisionFilterGroup='0x40000000',collisionFilterMask='0x20000000',nonRenderable='true')
anchor=node(blade,'TransformGroup','winchAnchor',translation='0 1.10 1.96')

# A geometric steel cable, Z=0..1, stretched to the connected vehicle at runtime.
vertices=[]
for z in [0,1]:
    for i in range(8):a=2*math.pi*i/8;vertices.append((.009*math.cos(a),.009*math.sin(a),z))
triangles=[]
for i in range(8):j=(i+1)%8;triangles.extend([(i,j,8+j),(i,8+j,8+i)])
cable_id=geometry('winchSteelCable',vertices,triangles)
cable=node(root,'Shape','winchCable',shapeId=cable_id,materialIds='7',visibility='false',castsShadows='true',receiveShadows='true')

# Additional reference details: winch drum, fairlead, roof rails and work-light housings.
box(visual,'winchDrumHousing',(.7,.36,.4),(0,1.15,1.48),'2')
box(visual,'fairleadFrame',(.3,.17,.07),(0,1.1,1.83),'8')
for x in [-.68,.68]:
    box(visual,'roofRail',(.035,.065,2.15),(x,2.36,-.15),'2')
    for z in [-1.02,.72]:box(visual,'roofRailFoot',(.055,.07,.09),(x,2.33,z),'2')
lights=[]
for x in [-.62,.62]:
    for z,angle in [(1.13,0),(-1.4,180)]:
        number=len(lights);loc=(x,2.20,z)
        box(visual,f'worklightHousing{number}',(.20,.10,.07),loc,'2')
        lens=(x,2.20,z+.04 if angle==0 else z-.04)
        box(visual,f'worklightLens{number}',(.16,.066,.008),lens,'8')
        lights.append(node(root,'Light',f'worklight{number}',translation=fmt(lens),rotation=f'-12 {angle} 0',type='spot',color='1 .95 .82',range='22',intensity='5',coneAngle='65',dropOff='3',castShadowMap='false'))

# Wheel mass is tonnes in FS25; body component mass is kilograms.
v=E.parse(OLD/'twinch.xml').getroot();v.find('annotation').text='v02 repair candidate for FS25 1.24: requires in-game validation.'
v.set('type','twinchV02')
v.find('storeData/name/en').text='T-Winch 30.2 v02'
v.find('storeData/name/de').text='T-Winch 30.2 v02'
v.find('storeData/functions/function').text='Tracked support machine with vehicle recovery winch'
v.find('base/components/component').set('centerOfMass','0 .65 -.1')
v.find('base/components/component').set('solverIterationCount','30')
for i,w in enumerate(v.findall('wheels/wheelConfigurations/wheelConfiguration/wheels/wheel')):
    p=w.find('physics')
    for k in ['initialCompression','rotMin','rotMax']:p.attrib.pop(k,None)
    p.attrib.update(mass='0.08',radius='0.415',width='0.5',deltaY='0',suspTravel='0.02',spring='200',damper='25',restLoad='1.25',forcePointRatio='.5',tireType='crawler',frictionScale='1.5',maxLatStiffness='12',showSteeringAngle='false',supportsWheelSink='false',transRatio='1',rotSpeed='1' if i<2 else '-1')
    reprnode=next(n for n in root if n.get('name')==p.get('repr'));reprnode.set('translation',reprnode.get('translation').replace('0.43','0.415'))
ack=v.find('wheels/ackermannSteeringConfigurations/ackermannSteering')
ack.attrib.clear();ack.attrib.update(rotSpeed='35',rotMax='40',rotCenter='0 0',rotCenterWheels='1 2 3 4')
motor=v.find('motorized/motorConfigurations/motorConfiguration/motor');motor.set('brakeForce','20')
transmission=v.find('motorized/motorConfigurations/motorConfiguration/transmission');transmission.set('minForwardGearRatio','60');transmission.set('minBackwardGearRatio','60')
diffs=v.find('motorized/differentialConfigurations/differentialConfiguration/differentials')
for d in list(diffs):diffs.remove(d)
# Each belt has a front/rear wheel pair; the central differential allows differing belt speeds.
E.SubElement(diffs,'differential',torqueRatio='.5',maxSpeedRatio='1',wheelIndex1='1',wheelIndex2='3')
E.SubElement(diffs,'differential',torqueRatio='.5',maxSpeedRatio='1',wheelIndex1='2',wheelIndex2='4')
E.SubElement(diffs,'differential',torqueRatio='.5',maxSpeedRatio='2',differentialIndex1='1',differentialIndex2='2')
v.find('fillUnit/fillUnitConfigurations/fillUnitConfiguration/fillUnits/fillUnit/exactFillRootNode').set('node','fuelFillRoot')
drive=v.find('drivable')
idle=E.SubElement(drive,'idleTurning',allowed='true',lockDirection='false',updateSteeringWheel='false',maxSpeed='2',steeringFactor='50')
for name,angle in [('frontLeft',128.66),('frontRight',51.34),('rearLeft',-128.16),('rearRight',-51.84)]:E.SubElement(idle,'wheel',node=name,steeringAngle=str(angle))
fold=v.find('foldable');old=fold.find('foldingParts');fold.remove(old)
configs=E.SubElement(fold,'foldingConfigurations');config=E.SubElement(configs,'foldingConfiguration');config.append(old)

lightxml=E.SubElement(v,'lights');states=E.SubElement(lightxml,'states')
E.SubElement(states,'state',lightTypes='0');E.SubElement(states,'state',lightTypes='0 1')
real=E.SubElement(lightxml,'realLights');low=E.SubElement(real,'low');high=E.SubElement(real,'high')
for i,light in enumerate(lights):
    typ='0' if i%2==0 else '1'
    E.SubElement(low,'light',node=light.get('name'),lightTypes=typ)
    E.SubElement(high,'light',node=light.get('name'),lightTypes=typ)

# Generate stable node paths after all reparenting. No reliance on stale v01 indices.
paths={}
def walk(n,path):
    if n.get('name') not in paths:paths[n.get('name')]=path
    for i,c in enumerate(n):walk(c,f'{path}{i}' if path.endswith('>') else f'{path}|{i}')
walk(root,'0>')
paths.update(wheelBackLeft=paths['rearLeft'],wheelBackRight=paths['rearRight']) # stock series6M sound references
mappings=v.find('i3dMappings');mappings.clear()
for name,path in paths.items():E.SubElement(mappings,'i3dMapping',id=name,node=path)
twinch=E.SubElement(v,'twinch',anchor='winchAnchor',cable='winchCable')
for track in tracks:
    offset=float(track.attrib.pop('offsetX'));side=1 if offset>0 else -1
    xt=E.SubElement(twinch,'track',node=track.get('name'),offsetX=str(offset))
    for n,radius in roller_list[side]:E.SubElement(xt,'roller',node=n.get('name'),radius=str(radius))

# Prune disconnected meshes (old baked track links) to reduce archive size.
used={n.get('shapeId') for n in root.iter('Shape')}
for s in list(shapes):
    if s.get('shapeId') not in used:shapes.remove(s)
write(r,OUT/'twinch.i3d');write(v,OUT/'twinch.xml')
desc=E.parse(OLD/'modDesc.xml').getroot();desc.set('descVersion','114')
desc.find('version').text='0.2.0.0';desc.find('title/en').text='T-Winch v02 - Physics and Winch Test'
desc.find('description/en').text='v02: repaired physics setup, moving belt links and wheels, work lights and single-player vehicle recovery winch. Ctrl+B attach/release, Ctrl+R reel toggle, Ctrl+N payout toggle. Requires game testing.'
typ=desc.find('vehicleTypes/type');typ.set('name','twinchV02');E.SubElement(typ,'specialization',name='twinch')
specializations=E.SubElement(desc,'specializations');E.SubElement(specializations,'specialization',name='twinch',className='TWinch',filename='scripts/TWinch.lua')
actions=E.SubElement(desc,'actions');bindings=E.SubElement(desc,'inputBinding');l10n=E.SubElement(desc,'l10n')
for action,key,label in [('TWINCH_CONNECT','KEY_b','T-Winch: attach / release vehicle'),('TWINCH_REEL','KEY_r','T-Winch: reel in on / off'),('TWINCH_PAYOUT','KEY_n','T-Winch: pay out on / off')]:
    E.SubElement(actions,'action',name=action,axisType='HALF')
    ab=E.SubElement(bindings,'actionBinding',action=action);E.SubElement(ab,'binding',device='KB_MOUSE_DEFAULT',input=f'KEY_lctrl {key}')
    tx=E.SubElement(l10n,'text',name='input_'+action);E.SubElement(tx,'en').text=label
write(desc,OUT/'modDesc.xml')
(OUT/'scripts').mkdir(exist_ok=True);shutil.copyfile(HERE/'TWinch.lua',OUT/'scripts/TWinch.lua')

# BC3-compressed DDS images with a complete mip chain.
def dds_mips(image,path):
    payloads=[];size=image.width;level=image
    while True:
        encoded=io.BytesIO();level.resize((max(4,level.width),max(4,level.height))).save(encoded,format='DDS',pixel_format='DXT5')
        data=encoded.getvalue();payloads.append(data[128:])
        if level.width==1 and level.height==1:break
        level=level.resize((max(1,level.width//2),max(1,level.height//2)),Image.Resampling.LANCZOS)
    encoded=io.BytesIO();image.save(encoded,format='DDS',pixel_format='DXT5');header=bytearray(encoded.getvalue()[:128])
    struct.pack_into('<I',header,8,struct.unpack_from('<I',header,8)[0]|0x20000)
    struct.pack_into('<I',header,20,len(payloads[0]));struct.pack_into('<I',header,28,len(payloads))
    struct.pack_into('<I',header,108,0x401008)
    path.write_bytes(bytes(header)+b''.join(payloads))
for name in ['icon_twinch.dds','store_twinch.dds']:dds_mips(Image.open(OLD/name).convert('RGBA'),OUT/name)

(OUT/'TESTING.txt').write_text('''T-Winch v02 - FS25 1.24 repair candidate

Remove/disable the old FS25_TWinch_Test mod and old test vehicle. Install ONLY
FS25_TWinch_v02.zip (unopened) in the FS25 mods folder. Buy a NEW v02 vehicle
in a test save; old save entries do not migrate physics or wheel configuration.

1. Inspect log.txt for twinchComponent wheel-shape errors, missing collision
   flags and Lua errors. Confirm it rests on the ground after purchase.
2. Start motor, drive forwards/backwards, brake and steer. With no throttle,
   steer left/right to test native low-speed pivot mode. Belts and rollers
   follow physical travel on each side, including opposite motion in turns.
3. F toggles lights using the game's existing light controls. X raises/lowers
   the blade through the game's fold control. Blade is not a terrain leveler.
4. Park another vehicle from your farm 3-20 m in front of the blade.
   Ctrl+B connects to the nearest eligible vehicle within 25 m, or releases.
   Ctrl+R toggles reeling in (motor must run); press again to stop.
   Ctrl+N toggles paying out; press again to stop. The cable holds under load.
   Park with the brakes holding and test on flat ground first.
5. Release cable before save/reload. Connections intentionally are not saved.
   Exiting stops reeling/pay-out; the attached line still holds until released.

Changes based on the supplied log: 80 t wheel masses corrected to 0.08 t;
modern vehicle collision filters; CPU collision mesh retention; stock sound
node aliases; modern foldingConfigurations; BC3 icons with mipmaps.

Added: 74 separately animated track links per side, rotating wheel assemblies,
low-speed native pivot setup, four worklights, visible steel cable and bounded
spring/damper recovery winch with equal/opposite reaction forces.

Limitations: SINGLE PLAYER ONLY; no log/tree towing, manual ground anchor or
multiplayer network events. Vehicle winch is automatic nearest-target, not a
walk-out hook system. Steering uses hidden wheel contacts plus native idle
turning; this is not a validated industrial differential-drive simulation.
Model details/dimensions remain approximations. XML geometry remains embedded
and will show a non-binary geometry warning; GIANTS Editor can save native
binary geometry. CPU mesh retention is not a claim of console compatibility.

Local checks are not FS25 physics tests. This v02 has NOT been run in the game.
Send a fresh log.txt plus the behavior of the above checks after testing.
''',encoding='utf-8')
report={'version':'0.2.0.0','target_game':'FS25 1.24.0.0','game_modDesc_version':114,'game_test':'not run','changes_based_on':'user supplied v01 game log','geometry_meshes':len(shapes),'wheel_mass_tonnes':0.08,'single_player_only':True}
(OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
with ZipFile(HERE.parent/'FS25_TWinch_v02.zip','w',ZIP_DEFLATED) as z:
    for f in sorted(OUT.rglob('*')):
        if f.is_file():z.write(f,f.relative_to(OUT))
print(json.dumps(report,indent=2))
