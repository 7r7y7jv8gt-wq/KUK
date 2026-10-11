import bpy, math, os, xml.etree.ElementTree as ET
from mathutils import Vector

OUT = os.path.dirname(os.path.abspath(__file__))
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
materials = {}
for name, color in [('Green',(0.08,0.65,0.025,1)),('Steel',(0.12,0.15,0.17,1)),('Track',(0.025,0.032,0.036,1)),('Vent',(0.012,0.018,0.016,1)),('Red',(0.75,0.025,0.015,1)),('Orange',(1,0.3,0.01,1)),('Blue',(0.025,0.12,0.6,1)),('Silver',(0.45,0.48,0.5,1)),('Yellow',(1,0.8,0.03,1))]:
    m=bpy.data.materials.new(name); m.diffuse_color=color; m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=color
    bs.inputs['Roughness'].default_value=0.55
    materials[name]=m

def finish(o,name,mat):
    o.name=name; o.data.materials.append(materials[mat]); return o
def box(name,loc,scale,mat,bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=bpy.context.object; o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        mod=o.modifiers.new('Panel bevel','BEVEL'); mod.width=bevel; mod.segments=1
        bpy.context.view_layer.objects.active=o; bpy.ops.object.modifier_apply(modifier=mod.name)
    return finish(o,name,mat)
def cylinder(name,loc,radius,depth,mat,axis='Z'):
    bpy.ops.mesh.primitive_cylinder_add(vertices=20,radius=radius,depth=depth,location=loc)
    o=bpy.context.object
    if axis=='Y': o.rotation_euler[0]=math.pi/2
    if axis=='X': o.rotation_euler[1]=math.pi/2
    return finish(o,name,mat)
def rod(name,a,b,radius,mat):
    a,b=Vector(a),Vector(b); o=cylinder(name,(a+b)/2,radius,(b-a).length,mat)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler(); return o
def ring(name,loc,mat,rotation=(0,0,0),major=.06,minor=.012):
    bpy.ops.mesh.primitive_torus_add(major_segments=12,minor_segments=6,location=loc,major_radius=major,minor_radius=minor,rotation=rotation)
    return finish(bpy.context.object,name,mat)

# Approximate envelope: 3.9 m long, 2.1 m wide, 2.3 m tall. Blender Z up.
box('Chassis',(0,0,.78),(2.85,1.55,.3),'Steel',.06)
box('EngineHousing',(-.15,0,1.61),(2.72,1.7,1.35),'Green',.16)
box('Roof',(-.15,0,2.3),(2.4,1.5,.06),'Steel',.025)
for side in [-1,1]:
    y=side*.88
    box('TrackFrame',(-.05,y,.43),(2.56,.42,.34),'Steel',.1)
    for x in [-1.22,1.12]:
        cylinder('DriveWheel',(x,y,.43),.35,.43,'Track','Y')
        cylinder('WheelHub',(x,y+side*.23,.43),.24,.025,'Steel','Y')
        for k in range(10):
            a=k*2*math.pi/10
            cylinder('HubBolt',(x+.19*math.cos(a),y+side*.25,.43+.19*math.sin(a)),.015,.02,'Silver','Y')
    for x in [-.9,-.55,-.2,.15,.5,.85]:
        cylinder('RoadWheel',(x,y,.3),.17,.42,'Track','Y')
        cylinder('RoadHub',(x,y+side*.23,.3),.08,.015,'Steel','Y')
    # Individual steel track shoes follow the rounded belt.
    path=[]
    for i in range(25): path.append((-1.22+2.34*i/25,.8,0))
    for i in range(12):
        a=math.pi/2-math.pi*i/12; path.append((1.12+.37*math.cos(a),.43+.37*math.sin(a),a-math.pi/2))
    for i in range(25): path.append((1.12-2.34*i/25,.06,0))
    for i in range(12):
        a=-math.pi/2-math.pi*i/12; path.append((-1.22+.37*math.cos(a),.43+.37*math.sin(a),a-math.pi/2))
    for i,(x,z,angle) in enumerate(path):
        o=box('TrackShoe_%s_%02d'%(side,i),(x,y,z),(.094,.53,.045),'Track'); o.rotation_euler[1]=-angle
        o=box('TrackCleat',(x,y,z+.024),(.025,.54,.021),'Steel'); o.rotation_euler[1]=-angle
    box('CenterAccessPanel',(-.15,side*.856,1.67),(.49,.026,1.19),'Steel')
    for xcenter in [-.94,.65]:
        box('VentRecess',(xcenter,side*.865,1.7),(.85,.025,.78),'Vent')
        for j in range(18): box('VentVertical',(xcenter-.41+j*.048,side*.884,1.7),(.016,.018,.8),'Green')
        for z in [1.42,1.65,1.9]: box('VentCrossbar',(xcenter,side*.89,z),(.85,.02,.015),'Green')
    for x in [-1.25,-.35,.45,1.05]: box('DoorHinge',(x,side*.88,1.04),(.09,.04,.025),'Silver')
    box('WarningLabel',(.98,side*.89,1.15),(.1,.008,.15),'Yellow')
    # Raised lettering retained as geometry in the exports.
    bpy.ops.object.text_add(location=(-.16,side*.895,2.16))
    txt=bpy.context.object; txt.name='TWINCH_marking'; txt.data.body='T\nW\nI\nN\nC\nH'; txt.data.size=.115; txt.data.space_line=.85
    txt.rotation_euler=(math.pi/2,0,0 if side==-1 else math.pi)
    txt.data.extrude=.001; txt.data.materials.append(materials['Silver'])
    bpy.context.view_layer.objects.active=txt; bpy.ops.object.convert(target='MESH')

box('RearGrille',(-1.522,0,1.73),(.035,1.08,.96),'Vent')
for y in [i*.07 for i in range(-7,8)]: box('RearGrilleBar',(-1.55,y,1.73),(.025,.018,.9),'Steel')
box('RearBumper',(-1.6,0,.97),(.2,1.68,.16),'Green',.03)
cylinder('FireExtinguisher',(-1.58,-.66,1.55),.065,.38,'Red')
rod('ExtinguisherHandle',(-1.58,-.66,1.76),(-1.58,-.66,1.83),.015,'Silver')
for x in [-1.15,.8]:
    for y in [-.65,.65]: cylinder('RoofLiftPoint',(x,y,2.36),.04,.12,'Silver')
cylinder('Exhaust',(-.8,.35,2.43),.045,.2,'Steel')
box('BladeMount',(1.38,0,.7),(.4,1.15,.24),'Steel',.04)
blade=box('FrontBlade',(1.83,0,.76),(.16,2.07,1.21),'Steel',.045); blade.rotation_euler[1]=-.14
box('BladeCuttingEdge',(1.92,0,.17),(.25,2.16,.07),'Silver')
for side in [-1,1]:
    box('BladeRib',(1.7,side*.71,.85),(.22,.1,.95),'Steel',.025)
    rod('HydraulicCylinder',(1.13,side*.53,.91),(1.61,side*.53,1.44),.065,'Steel')
    rod('HydraulicRod',(1.61,side*.53,1.44),(1.77,side*.53,1.63),.032,'Silver')
    ring('BladeTowEye',(1.97,side*.87,1.22),'Silver',(math.pi/2,0,0))
ring('WinchHook',(2.02,0,1.03),'Orange',(math.pi/2,0,0),.065,.017)
for i in range(14): ring('ChainLink',(2.04,.04*math.sin(i*.45),.94-i*.043),'Blue',(math.pi/2 if i%2 else 0,0,0),.028,.008)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'twinch.blend'))
bpy.ops.wm.obj_export(filepath=os.path.join(OUT,'twinch.obj'),export_materials=True,forward_axis='NEGATIVE_Z',up_axis='Y')

# GIANTS XML scene with embedded indexed triangle geometry; no binary shapes dependency.
root=ET.Element('i3D',name='TWinch reference model',version='1.6')
ET.SubElement(root,'Asset',{'xmlns':''})
ET.SubElement(root,'Files')
ms=ET.SubElement(root,'Materials')
matids={}
for i,(name,m) in enumerate(materials.items(),1):
    matids[name]=str(i)
    ET.SubElement(ms,'Material',name=name,materialId=str(i),diffuseColor=' '.join(str(v) for v in m.diffuse_color),specularColor='0.2 0.2 0.2',cosPower='30')
shapes=ET.SubElement(root,'Shapes'); scene=ET.SubElement(root,'Scene')
group=ET.SubElement(scene,'TransformGroup',name='twinch',nodeId='1')
def cv(v): return (v.x,v.z,-v.y)
fmt=lambda vs:' '.join('%.6g'%v for v in vs)
count=0
for sid,o in enumerate([o for o in bpy.data.objects if o.type=='MESH'],1):
    mesh=o.data; mesh.calc_loop_triangles(); verts=[]; normals=[]
    # Split triangle corners to preserve crisp hard-surface normals.
    for tri in mesh.loop_triangles:
        for vi in tri.vertices:
            verts.append(cv(o.matrix_world @ mesh.vertices[vi].co))
            normals.append(cv((o.matrix_world.to_3x3().inverted().transposed() @ tri.normal).normalized()))
    if not verts: continue
    shape=ET.SubElement(shapes,'IndexedTriangleSet',name=o.name,shapeId=str(sid))
    vn=ET.SubElement(shape,'Vertices',count=str(len(verts)),normal='true',uv0='true')
    for p,n in zip(verts,normals): ET.SubElement(vn,'v',p=fmt(p),n=fmt(n),t0='0 0')
    ts=ET.SubElement(shape,'Triangles',count=str(len(verts)//3))
    for i in range(0,len(verts),3): ET.SubElement(ts,'t',vi=f'{i} {i+1} {i+2}')
    subs=ET.SubElement(shape,'Subsets',count='1')
    ET.SubElement(subs,'Subset',firstVertex='0',numVertices=str(len(verts)),firstIndex='0',numIndices=str(len(verts)))
    ET.SubElement(group,'Shape',name=o.name,shapeId=str(sid),nodeId=str(sid+1),materialIds=matids[o.data.materials[0].name],castsShadows='true',receiveShadows='true')
    count+=len(verts)//3
ET.indent(root)
ET.ElementTree(root).write(os.path.join(OUT,'twinch.i3d'),encoding='utf-8',xml_declaration=True)
print('EXPORTED',count,'triangles')

# Produce a preview using Blender's software-compatible workbench renderer.
bpy.ops.object.camera_add(location=(5,-6,4))
cam=bpy.context.object; cam.rotation_euler=(Vector((0,0,1.15))-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.type='ORTHO'; cam.data.ortho_scale=5.3
scene=bpy.context.scene; scene.camera=cam; scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.light='STUDIO'; scene.display.shading.color_type='MATERIAL'; scene.display.shading.show_shadows=True; scene.display.shading.show_cavity=True
scene.display.shading.background_type='WORLD'; scene.world.color=(.22,.22,.22)
scene.render.resolution_x=1200; scene.render.resolution_y=850; scene.render.resolution_percentage=100
scene.render.filepath=os.path.join(OUT,'preview.png'); bpy.ops.render.render(write_still=True)
