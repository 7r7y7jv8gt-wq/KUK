"""Native hydraulic blade mouse controls and correctly parented orbital camera."""
from pathlib import Path
import xml.etree.ElementTree as E
from zipfile import ZipFile, ZIP_DEFLATED
import shutil, math, json

HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'FS25_TWinch_v02'
OUT=HERE.parent/'FS25_TWinch_v03'
OUT.mkdir(exist_ok=True)
def write(r,p):E.indent(r);E.ElementTree(r).write(p,encoding='utf-8',xml_declaration=True)
def fmt(v):return ' '.join(f'{n:.7g}' for n in v)
r=E.parse(OLD/'twinch.i3d').getroot();root=r.find('Scene')[0];shapes=r.find('Shapes')
v=E.parse(OLD/'twinch.xml').getroot();desc=E.parse(OLD/'modDesc.xml').getroot()
nodes={n.get('name'):n for n in root.iter()}
byshape={s.get('shapeId'):s for s in shapes}
node_id=max(int(n.get('nodeId','0')) for n in root.iter())+1
shape_id=max(int(s.get('shapeId')) for s in shapes)+1
def node(parent,tag,name,**attrs):
    global node_id
    n=E.SubElement(parent,tag,name=name,nodeId=str(node_id),**attrs);node_id+=1;return n
def geometry(name,points,faces):
    global shape_id
    sid=str(shape_id);shape_id+=1;s=E.SubElement(shapes,'IndexedTriangleSet',name=name,shapeId=sid)
    vs=E.SubElement(s,'Vertices',count=str(len(faces)*3),normal='true',uv0='true')
    for a,b,c in faces:
        p,q,t=points[a],points[b],points[c];u=[q[i]-p[i] for i in range(3)];w=[t[i]-p[i] for i in range(3)]
        normal=[u[1]*w[2]-u[2]*w[1],u[2]*w[0]-u[0]*w[2],u[0]*w[1]-u[1]*w[0]]
        length=math.sqrt(sum(n*n for n in normal));normal=[n/length for n in normal]
        for i in [a,b,c]:E.SubElement(vs,'v',p=fmt(points[i]),n=fmt(normal),t0='0 0')
    ts=E.SubElement(s,'Triangles',count=str(len(faces)))
    for i in range(len(faces)):E.SubElement(ts,'t',vi=f'{3*i} {3*i+1} {3*i+2}')
    sub=E.SubElement(s,'Subsets',count='1');E.SubElement(sub,'Subset',firstVertex='0',numVertices=str(len(vs)),firstIndex='0',numIndices=str(len(vs)))
    return sid
def cylinder(name,radius,length):
    points=[(radius*math.cos(i*math.pi/8),radius*math.sin(i*math.pi/8),z) for z in [0,length] for i in range(16)]
    points.extend([(0,0,0),(0,0,length)]);faces=[]
    for i in range(16):
        j=(i+1)%16;faces.extend([(i,j,j+16),(i,j+16,i+16),(32,j,i),(33,i+16,j+16)])
    return geometry(name,points,faces)

# The camera must be a child of its orbit pivot. Positive local Z is zoom distance;
# a camera looks along local -Z, toward that pivot. Never use the old negative offset.
cam=nodes['outdoorCamera'];orbit=nodes['cameraTarget']
root.remove(cam);orbit.append(cam)
orbit.set('translation','0 1.2 0');orbit.set('rotation','-18 180 0')
cam.set('translation','0 0 6');cam.set('rotation','0 0 0');cam.set('nearClip','.05');cam.set('fov','60')
camera=v.find('enterable/cameras/camera')
camera.attrib.update(translation='0 0 6',rotation='-18 180 0',rotMinX='-1.15',rotMaxX='.10',transMin='3.5',transMax='18',resetCameraOnVehicleSwitch='true',positionSmoothingParameter='.016',lookAtSmoothingParameter='.022',useWorldXZRotation='true')

# Reframe the blade's baked mesh geometry around a real chassis hinge.
blade=nodes['bladeLift'];pivot=(0,.70,1.20)
blade.set('translation',fmt(pivot));blade.set('rotation','0 0 0')
shifted=set()
for child in blade:
    if child.get('shapeId'):
        sid=child.get('shapeId')
        if sid not in shifted:
            for vertex in byshape[sid].find('Vertices'):
                p=list(map(float,vertex.get('p').split()));vertex.set('p',fmt([p[i]-pivot[i] for i in range(3)]))
            shifted.add(sid)
    else:
        p=list(map(float,child.get('translation','0 0 0').split()));child.set('translation',fmt([p[i]-pivot[i] for i in range(3)]))

# Remove the original static hydraulic rods before installing two articulated assemblies.
visual=nodes['visual']
for n in list(visual):
    if n.get('name','').startswith(('HydraulicCylinder','HydraulicRod')):visual.remove(n)
barrel_shape=cylinder('hydraulicBarrel',.065,.52)
rod_shape=cylinder('hydraulicChromeRod',.032,.55)
moving_parts=[]
for side,name in [(-1,'Right'),(1,'Left')]:
    a=(side*.53,.91,1.13);b=(side*.53,1.63,1.77)
    base_pin=node(root,'TransformGroup',f'hydraulic{name}BasePin',translation=fmt(a))
    blade_pin=node(blade,'TransformGroup',f'hydraulic{name}BladePin',translation=fmt([b[i]-pivot[i] for i in range(3)]))
    # Initial direction must be right even before the native Cylindered first update.
    dy,dz=b[1]-a[1],b[2]-a[2];angle=math.degrees(math.atan2(-dy,dz))
    barrel=node(root,'TransformGroup',f'hydraulic{name}Barrel',translation=fmt(a),rotation=f'{angle} 0 0')
    node(barrel,'Shape',f'hydraulic{name}BarrelMesh',shapeId=barrel_shape,materialIds='2',castsShadows='true',receiveShadows='true')
    rod=node(blade_pin,'TransformGroup',f'hydraulic{name}Rod',rotation=f'{angle+180} 0 0')
    node(rod,'Shape',f'hydraulic{name}RodMesh',shapeId=rod_shape,materialIds='8',castsShadows='true',receiveShadows='true')
    moving_parts.extend([(barrel,blade_pin),(rod,base_pin)])

# One native moving tool owns the blade and all its collision, chain and winch-anchor nodes.
# Old fold animation must not write to the same transform.
for tag in ['foldable','animations']:
    n=v.find(tag)
    if n is not None:v.remove(n)
cy=E.SubElement(v,'cylindered');tools=E.SubElement(cy,'movingTools')
tool=E.SubElement(tools,'movingTool',node='bladeLift',playSound='true',allowSaving='true')
E.SubElement(tool,'rotation',rotationAxis='1',rotSpeed='12',rotAcceleration='35',rotMin='-28',rotMax='0',startRot='0')
E.SubElement(tool,'controls',axis='TWINCH_BLADE',invertAxis='false',mouseSpeedFactor='1.5')
parts=E.SubElement(cy,'movingParts')
for part,reference in moving_parts:
    E.SubElement(parts,'movingPart',node=part.get('name'),referenceFrame='twinchComponent',referencePoint=reference.get('name'),isActiveDirty='true',scaleZ='false')
    E.SubElement(tool,'dependentPart',node=part.get('name'))

# Regenerate all mapping paths after the camera reparenting and hydraulic additions.
paths={}
def walk(n,path):
    if n.get('name') not in paths:paths[n.get('name')]=path
    for i,c in enumerate(n):walk(c,f'{path}{i}' if path.endswith('>') else f'{path}|{i}')
walk(root,'0>');paths.update(wheelBackLeft=paths['rearLeft'],wheelBackRight=paths['rearRight'])
mapping=v.find('i3dMappings');mapping.clear()
for name,path in paths.items():E.SubElement(mapping,'i3dMapping',id=name,node=path)
used={n.get('shapeId') for n in root.iter('Shape')}
for s in list(shapes):
    if s.get('shapeId') not in used:shapes.remove(s)
v.set('type','twinchV03')
v.find('annotation').text='v03: native mouse hydraulic blade and orbital camera correction; game test pending.'
for n in v.findall('storeData/name/*'):n.text='T-Winch 30.2 v03'
typ=desc.find('vehicleTypes/type');typ.set('name','twinchV03')
for s in list(typ):
    if s.get('name')=='foldable':typ.remove(s)
E.SubElement(typ,'specialization',name='cylindered')
desc.find('version').text='0.3.0.0';desc.find('title/en').text='T-Winch v03 - Mouse Hydraulics and Camera'
desc.find('description/en').text='v03: orbit camera repair and articulated hydraulic blade. Hold left mouse button and drag up/down to raise/lower blade. Vehicle recovery winch controls retained. Game validation pending.'
E.SubElement(desc.find('actions'),'action',name='TWINCH_BLADE',axisType='FULL')
ab=E.SubElement(desc.find('inputBinding'),'actionBinding',action='TWINCH_BLADE')
for component in ['+','-']:
    E.SubElement(ab,'binding',device='KB_MOUSE_DEFAULT',input='MOUSE_BUTTON_LEFT AXIS_MOUSE_Y',axisComponent=component,inputComponent=component)
tx=E.SubElement(desc.find('l10n'),'text',name='input_TWINCH_BLADE');E.SubElement(tx,'en').text='T-Winch hydraulic blade: raise / lower'

write(r,OUT/'twinch.i3d');write(v,OUT/'twinch.xml');write(desc,OUT/'modDesc.xml')
for name in ['icon_twinch.dds','store_twinch.dds']:shutil.copyfile(OLD/name,OUT/name)
(OUT/'scripts').mkdir(exist_ok=True);shutil.copyfile(OLD/'scripts/TWinch.lua',OUT/'scripts/TWinch.lua')
(OUT/'TESTING.txt').write_text('''T-Winch v03 - Camera and native hydraulic blade

Disable v01/v02. Put FS25_TWinch_v03.zip unopened in the mods directory and
purchase a NEW v03 machine in a test savegame. Existing vehicle physics and
camera states are not migrated.

CAMERA: Start view is behind the machine, centred at 1.2 m height with 6 m
distance. Normal mouse camera movement and wheel zoom remain available.
Switch out/in and check that the start view is restored. Zoom is 3.5-18 m.

BLADE: Start the motor. HOLD LEFT MOUSE BUTTON and drag UP to raise the blade,
DOWN to lower. Release to hold its position. The blade pivots at the chassis
hinge over 28 degrees. Both hydraulic barrels aim at the blade pins; chrome
rods aim back toward the chassis pins. The blade collision and winch anchor
move with it. Native Cylindered saves the blade position with the vehicle.
X is no longer the blade control. This does not implement terrain leveling.

If your existing custom mouse settings cause camera movement while dragging
the blade, bind the vehicle camera axes to RIGHT MOUSE BUTTON + mouse axes in
the game controls. The mod does not overwrite global camera bindings. You
can invert the blade axis or rebind it under T-Winch hydraulic blade controls.

WINCH: Ctrl+B attaches/releases the nearest eligible same-farm vehicle within
25 m. Ctrl+R toggles reeling in (engine required); Ctrl+N toggles paying out.
Other v02 limitations remain: single player, vehicle recovery only, no log
winching, no saved cable connection and approximate crawler wheel contacts.

v03 has local XML/geometry/kinematics checks but has not run in GIANTS Engine.
Please send a fresh game log.txt and describe camera and blade behavior.
''',encoding='utf-8')
report={'version':'0.3.0.0','camera':'nested orbit, positive 6 m local Z','blade':'native Cylindered rotation, -28..0 degrees','input':'left mouse button + mouse Y, full axis','hydraulics':'two fixed-length barrels and chrome rods with native endpoint alignment','game_test':'not run','source':'v02, preserving winch and track behavior'}
(OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
with ZipFile(HERE.parent/'FS25_TWinch_v03.zip','w',ZIP_DEFLATED) as z:
    for f in sorted(OUT.rglob('*')):
        if f.is_file():z.write(f,f.relative_to(OUT))
print(json.dumps(report,indent=2))
