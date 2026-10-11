"""Photo-based, approximate T-WINCH forestry assist winch model. Blender 4.3+."""
import bpy
import math
import json
from pathlib import Path
from mathutils import Vector

ROOT = Path('/workspace/twinch')
OUT = ROOT / 'model'
PREVIEW = ROOT / 'previews'
OUT.mkdir(parents=True, exist_ok=True)
PREVIEW.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for block in list(bpy.data.materials):
    bpy.data.materials.remove(block)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0
mesh_objects = []
groups = {}

def lin(x):
    return x / 12.92 if x < .04045 else ((x + .055) / 1.055) ** 2.4

def mat(name, rgb, metallic=0, rough=.45, emission=0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    rgba = tuple(lin(v) for v in rgb) + (1,)
    m.diffuse_color = rgba
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = rgba
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = rough
    if emission:
        bsdf.inputs['Emission Color'].default_value = rgba
        bsdf.inputs['Emission Strength'].default_value = emission
    return m

green = mat('TWINCH_Green_Painted_Steel', (.28,.70,.06), .45, .34)
grey = mat('Graphite_Painted_Steel', (.21,.24,.26), .65, .38)
black = mat('Vent_Interior_Black', (.035,.045,.042), .12, .80)
steel = mat('Machined_Steel', (.60,.64,.67), .90, .27)
trackmat = mat('Track_Steel', (.25,.29,.29), .80, .64)
trackedge = mat('Grouser_Worn_Edges', (.43,.46,.44), .83, .48)
rubber = mat('Hoses_and_Seals', (.045,.05,.049), .0, .72)
red = mat('Safety_Red', (.70,.025,.017), .38, .34)
yellow = mat('Caution_Yellow', (.96,.68,.035), .05, .52)
white = mat('Lettering_White', (.87,.91,.87), .1, .46)
amber = mat('Amber_Beacon_Lens', (1,.38,.015), .15, .25, .65)
led = mat('Worklight_Lenses', (.88,.94,1), .15, .20, .7)
blue = mat('Hydraulic_Fitting_Blue', (.015,.30,.65), .65, .3)

def empty(name, parent=None):
    obj = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(obj)
    obj.empty_display_size = .15
    obj.empty_display_type = 'PLAIN_AXES'
    obj.parent = parent
    return obj

root = empty('TWINCH_Root_METRES')
for name in ['Chassis', 'Left_Track', 'Right_Track', 'Engine_Housing', 'Blade_Pivot', 'Hydraulics', 'Winch_Drum', 'Cable_Guide', 'Lights_and_Decals']:
    groups[name] = empty(name, root)

def finish(obj, name, material, group, bevel=0):
    obj.name = name
    obj.parent = groups[group]
    if material:
        obj.data.materials.append(material)
    if bevel:
        mod = obj.modifiers.new('Small_manufactured_edge_radius', 'BEVEL')
        mod.width = bevel
        mod.segments = 2
        mod.affect = 'EDGES'
    mesh_objects.append(obj)
    return obj

def box(name, loc, dims, material=grey, group='Engine_Housing', bevel=.012):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(obj, name, material, group, bevel)

def mesh(name, verts, faces, material, group, bevel=.008):
    data = bpy.data.meshes.new(name + '_mesh')
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    return finish(obj, name, material, group, bevel)

def prism_x(name, x, thickness, outline_yz, material, group='Engine_Housing', bevel=.009):
    # Keep closed prism faces outward-facing for exact boolean vent cuts.
    signed_area=sum(outline_yz[i][0]*outline_yz[(i+1)%len(outline_yz)][1]
                    -outline_yz[(i+1)%len(outline_yz)][0]*outline_yz[i][1]
                    for i in range(len(outline_yz)))
    if signed_area<0:outline_yz=list(reversed(outline_yz))
    n = len(outline_yz)
    verts = [(x-thickness/2,y,z) for y,z in outline_yz] + [(x+thickness/2,y,z) for y,z in outline_yz]
    faces = [tuple(reversed(range(n))), tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name, verts, faces, material, group, bevel)

def cyl_between(name, start, end, radius, material=steel, group='Hydraulics', vertices=20):
    a,b = Vector(start),Vector(end)
    direction = b-a
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=direction.length, location=(a+b)*.5)
    obj = bpy.context.object
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = direction.to_track_quat('Z','Y')
    return finish(obj,name,material,group,.003)

def pipe(name, points, radius, material=rubber, group='Hydraulics'):
    curve = bpy.data.curves.new(name+'_curve','CURVE')
    curve.dimensions = '3D'
    curve.resolution_u = 2
    curve.bevel_depth = radius
    curve.bevel_resolution = 2
    spline=curve.splines.new('POLY')
    spline.points.add(len(points)-1)
    for p,co in zip(spline.points,points):p.co=(*co,1)
    obj=bpy.data.objects.new(name,curve)
    bpy.context.collection.objects.link(obj)
    obj.parent=groups[group]
    curve.materials.append(material)
    bpy.context.view_layer.objects.active=obj
    obj.select_set(True)
    bpy.ops.object.convert(target='MESH')
    obj.select_set(False)
    mesh_objects.append(obj)
    return obj

def bolt(name, loc, axis='X', size=.018, group='Engine_Housing'):
    d=Vector((1,0,0) if axis=='X' else (0,-1,0) if axis=='Y' else (0,0,1))
    return cyl_between(name,Vector(loc)-d*.003,Vector(loc)+d*.007,size,steel,group,6)

def torus(name, loc, major, minor, material, group, axis='X'):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=24, minor_segments=8, location=loc)
    obj=bpy.context.object
    if axis=='X':obj.rotation_euler[1]=math.pi/2
    elif axis=='Y':obj.rotation_euler[0]=math.pi/2
    return finish(obj,name,material,group)

font_path='/usr/share/fonts/truetype/open-sans/OpenSans-Bold.ttf'
font=bpy.data.fonts.load(font_path)
def lettering(name, text, loc, size, material=white, side=1, facing='SIDE'):
    data=bpy.data.curves.new(name+'_font','FONT')
    data.body=text
    data.font=font
    data.size=size
    data.extrude=.0006
    data.align_x='CENTER'
    data.align_y='CENTER'
    data.space_character=1.05
    obj=bpy.data.objects.new(name,data)
    bpy.context.collection.objects.link(obj)
    obj.location=loc
    if facing=='SIDE':obj.rotation_euler=(math.pi/2,0, side*math.pi/2)
    else:obj.rotation_euler=(math.pi/2,0,0)
    obj.parent=groups['Lights_and_Decals']
    data.materials.append(material)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active=obj
    bpy.ops.object.convert(target='MESH')
    obj.select_set(False)
    mesh_objects.append(obj)
    return obj

print('Building tracked chassis...',flush=True)
box('Main_frame',(0,.10,.83),(1.73,2.95,.26),grey,'Chassis',.04)
box('Belly_guard',(0,.12,.57),(1.54,2.5,.15),grey,'Chassis',.035)
for y in [-.95,.05,1.05]:
    box('Track_crossmember',(0,y,.67),(2.25,.18,.20),grey,'Chassis')

# Continuous capsule-shaped track paths with individual steel shoes and grousers.
track_radius=.40
track_z=.53
rear_y=1.10
front_y=-1.15
straight=rear_y-front_y
perimeter=2*straight+2*math.pi*track_radius
def track_path(d):
    if d<straight:return front_y+d,track_z+track_radius,1.,0.
    d-=straight
    if d<math.pi*track_radius:
        a=d/track_radius
        return rear_y+track_radius*math.sin(a),track_z+track_radius*math.cos(a),math.cos(a),-math.sin(a)
    d-=math.pi*track_radius
    if d<straight:return rear_y-d,track_z-track_radius,-1.,0.
    a=(d-straight)/track_radius
    return front_y-track_radius*math.sin(a),track_z-track_radius*math.cos(a),-math.cos(a),math.sin(a)

for side,group in [(-1,'Left_Track'),(1,'Right_Track')]:
    x=side*1.16
    box(group+'_frame',(x,0,.49),(.42,2.47,.26),grey,group,.04)
    for y in [-1.12,-.72,-.32,.08,.48,.88,1.10]:
        radius=.30 if abs(y)>1.0 else .245
        cyl_between(group+'_roller',(x-.25,y,.46),(x+.25,y,.46),radius,trackmat,group,28)
        cyl_between(group+'_hub',(x+side*.24,y,.46),(x+side*.27,y,.46),radius*.47,grey,group,20)
        bolt(group+'_hub_bolt',(x+side*.281,y,.46),'X',.04,group)
    cyl_between(group+'_top_roller',(x-.21,.05,.79),(x+.21,.05,.79),.13,grey,group)
    for i in range(52):
        y,z,dy,dz=track_path(i*perimeter/52)
        angle=math.atan2(dz,dy)
        shoe=box(group+f'_shoe_{i:02d}',(x,y,z),(.64,.126,.062),trackmat,group,.008)
        shoe.rotation_euler[0]=angle
        # Grousers follow the outward normal of the closed track loop.
        ny,nz=-dz,dy
        grouser=box(group+f'_grouser_{i:02d}',(x,y+ny*.052,z+nz*.052),(.66,.032,.056),trackedge,group,.005)
        grouser.rotation_euler[0]=angle
        for bx in [-.21,.21]:
            a=Vector((x+bx,y+ny*.037,z+nz*.037))
            b=a+Vector((0,ny*.017,nz*.017))
            cyl_between(group+'_shoe_fastener',a,b,.013,steel,group,6)
    # Outside protection rail, access caps and upper idler hardware.
    box(group+'_side_rail',(x+side*.29,.02,.44),(.055,2.55,.16),grey,group,.016)
    for y in [-1.0,-.5,0,.5,1.0]:bolt(group+'_rail_fastener',(x+side*.323,y,.45),'X',.018,group)

print('Building faceted engine enclosure and vents...',flush=True)
box('Engine_dark_inner_volume',(0,.03,1.88),(1.90,2.34,1.16),black,'Engine_Housing',.08)
box('Lower_engine_sill',(0,.04,1.11),(2.14,2.67,.16),grey,'Engine_Housing',.03)
# Side doors are full thickness closed prisms with chamfered rooflines.
for side in [-1,1]:
    x=side*1.045
    outline=[(-1.23,1.25),(-1.23,2.34),(-.98,2.64),(-.34,2.64),(-.23,2.48),(-.23,1.25)]
    door=prism_x('Green_service_door_'+str(side),x,.045,outline,green)
    rearoutline=[(-.22,1.25),(-.22,2.48),(.15,2.64),(1.04,2.64),(1.23,2.45),(1.23,1.25)]
    panel=prism_x('Graphite_vent_panel_'+str(side),x,.045,rearoutline,grey)
    prism_x('Rear_green_corner_'+str(side),x,.05,[(1.23,1.25),(1.23,2.44),(1.42,2.27),(1.42,1.25)],green)
    # Black recessed vent pockets, with separate steel webs and slotted holes.
    # Slots are real openings cut into the flat part of each side panel.
    for target,y_positions,z_rows,slot_height in [
        (door,[-1.05+i*.087 for i in range(9)],[1.84,2.10],.18),
        (panel,[.06+i*.097 for i in range(10)],[1.73,2.02,2.30],.20)]:
        cutters=[]
        for y in y_positions:
            for z in z_rows:
                cutter=box('Temporary_vent_cut',(x,y,z),(.18,.035,slot_height),None,'Engine_Housing',.012)
                bpy.context.view_layer.objects.active=cutter
                bpy.ops.object.modifier_apply(modifier=cutter.modifiers[0].name)
                cutters.append(cutter)
                mesh_objects.remove(cutter)
        bpy.ops.object.select_all(action='DESELECT')
        for c in cutters:c.select_set(True)
        bpy.context.view_layer.objects.active=cutters[0]
        bpy.ops.object.join()
        cutting=bpy.context.object
        bpy.context.view_layer.objects.active=target
        boolean=target.modifiers.new('Actual_cut_vent_slots','BOOLEAN')
        boolean.operation='DIFFERENCE'
        boolean.solver='EXACT'
        boolean.object=cutting
        bpy.ops.object.modifier_apply(modifier=boolean.name)
        bpy.data.objects.remove(cutting,do_unlink=True)
    for y,z in [(-1.12,1.40),(-1.12,2.38),(-.32,1.40),(-.32,2.42),(.88,1.40),(.94,2.46),(1.32,1.39)]:
        bolt('Service_panel_bolt',(side*1.077,y,z),'X',.014)
    # Door recess, pull handle, warning placard and circular service indicator.
    box('Service_handle_recess',(side*1.077,.45,1.47),(.012,.28,.12),black)
    cyl_between('Service_pull_handle',(side*1.10,.34,1.46),(side*1.10,.56,1.46),.014,steel,'Engine_Housing',12)
    box('Caution_plate',(side*1.075,-.74,2.39),(.012,.40,.17),yellow,'Lights_and_Decals',.003)
    lettering('Warning_heading','WARNING',(side*1.084,-.74,2.425),.039,black,side)
    lettering('Warning_subtext','WINCH / HIGH TENSION',(side*1.084,-.74,2.365),.021,black,side)
    torus('Service_indicator_ring',(side*1.081,-.38,1.80),.074,.011,yellow,'Engine_Housing')
    cyl_between('Service_indicator_face',(side*1.065,-.38,1.80),(side*1.080,-.38,1.80),.060,black,'Engine_Housing')
    # Logo and a small producer-style mark, modeled as geometry rather than
    # claiming exact original decals from the low-resolution photos.
    for i,char in enumerate('TWINCH'):
        lettering('TWINCH_vertical_'+char+str(side),char,(side*1.077,.91,2.38-i*.135),.115,white,side)
    lettering('eco_forest_mark','eco forest',(side*1.079,-.77,1.42),.069,black,side)

# Sloped roof planes and shoulders rather than a rectangular box.
roofverts=[(-1.06,-1.2,2.33),(1.06,-1.2,2.33),(-.71,-.98,2.70),(.71,-.98,2.70),
           (-.71,1.02,2.70),(.71,1.02,2.70),(-1.06,1.42,2.27),(1.06,1.42,2.27)]
mesh('Faceted_roof',roofverts,[(0,1,3,2),(2,3,5,4),(4,5,7,6),(0,2,4,6),(1,7,5,3)],grey,'Engine_Housing',.015)
for side in [-1,1]:
    verts=[(side*.66,-1.2,2.34),(side*1.067,-1.2,2.34),(side*1.067,-.96,2.64),(side*.66,-.96,2.70),
           (side*.66,1.01,2.70),(side*1.067,1.04,2.64)]
    mesh('Green_roof_shoulder',verts,[(0,1,2,3),(3,2,5,4)],green,'Engine_Housing',.006)
box('Front_nose_grille',(0,-1.25,1.99),(1.26,.072,1.04),grey,'Engine_Housing',.04)
box('Nose_grille_backing',(0,-1.294,2.02),(1.12,.01,.82),black,'Engine_Housing',.01)
for i in range(12):
    slat=box('Nose_grille_vertical_web',(-.515+i*.093,-1.307,2.02),(.023,.021,.76),grey,'Engine_Housing',.005)
    slat.rotation_euler[1]=-.11
for z in [1.80,2.08,2.33]:box('Nose_grille_horizontal_web',(0,-1.318,z),(1.15,.025,.03),grey,'Engine_Housing',.004)
box('Rear_access_panel',(0,1.43,1.88),(1.88,.058,1.17),green,'Engine_Housing',.025)
for i in range(14):box('Rear_vent_slot',(-.66+i*.10,1.462,2.03),(.038,.009,.47),black,'Engine_Housing',.008)
lettering('Rear_TWINCH','T-WINCH',(0,1.465,1.62),.18,white,facing='FRONT').rotation_euler[2]=math.pi

print('Building winch, blade, hydraulic cylinders and safety hardware...',flush=True)
# Broad segmented blade with a forward-leaning upper surface and thick edge.
verts=[(-1.53,-2.20,.16),(1.53,-2.20,.16),(-1.53,-1.93,.96),(1.53,-1.93,.96),
       (-1.53,-2.09,.17),(1.53,-2.09,.17),(-1.53,-1.82,.96),(1.53,-1.82,.96)]
mesh('Front_ground_anchor_blade',verts,[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)],grey,'Blade_Pivot',.027)
box('Replaceable_blade_cutting_edge',(0,-2.21,.18),(3.08,.09,.14),trackedge,'Blade_Pivot',.008)
for x in [-1.35,-.90,-.45,0,.45,.90,1.35]:bolt('Cutting_edge_bolt',(x,-2.26,.19),'Y',.02,'Blade_Pivot')
for side in [-1,1]:
    prism_x('Blade_end_plate',side*1.49,.11,[(-2.22,.16),(-2.30,.43),(-2.04,1.24),(-1.43,1.03),(-1.52,.58)],grey,'Blade_Pivot',.02)
    box('Blade_red_reflector',(side*1.55,-1.76,1.03),(.015,.42,.055),red,'Blade_Pivot',.005)
    cyl_between('Blade_pivot_pin',(side*.81-.10,-1.16,.89),(side*.81+.10,-1.16,.89),.095,steel,'Chassis')
    box('Blade_support_arm',(side*.82,-1.54,.76),(.16,.80,.22),grey,'Blade_Pivot',.02)
    a=Vector((side*.94,-1.06,1.27));b=Vector((side*1.16,-1.92,.72));d=b-a
    cyl_between('Green_hydraulic_barrel',a,a+d*.61,.078,green,'Hydraulics',24)
    cyl_between('Hydraulic_seal',a+d*.59,a+d*.65,.090,grey,'Hydraulics')
    cyl_between('Chromed_hydraulic_rod',a+d*.62,b,.037,steel,'Hydraulics',24)
    for endpoint in [a,b]:
        cyl_between('Hydraulic_mount_pin',endpoint-Vector((.07,0,0)),endpoint+Vector((.07,0,0)),.042,steel,'Hydraulics')
    pipe('Hydraulic_pressure_hose',[(side*.98,-.87,1.34),(side*1.0,-1.2,1.16),(side*1.12,-1.53,.96),(side*1.16,-1.75,.79)],.018)
    cyl_between('Blue_hydraulic_coupling',(side*.95,-1.1,1.22),(side*.99,-1.1,1.22),.035,blue,'Hydraulics',12)

# Visible internal drum, lead-in roller and substantial front cable guide.
cyl_between('Winch_main_drum',(-.43,-.90,1.39),(.43,-.90,1.39),.285,grey,'Winch_Drum',40)
for x in [-.44,.44]:cyl_between('Winch_drum_flange',(x-.025,-.90,1.39),(x+.025,-.90,1.39),.335,steel,'Winch_Drum',40)
for i in range(26):torus('Wound_steel_rope_turn',(-.36+i*.028,-.90,1.39),.297,.0105,trackedge,'Winch_Drum')
prism_x('Front_winch_guard_L',-.52,.095,[(-1.79,.98),(-1.79,1.63),(-1.52,1.69),(-1.27,1.27)],grey,'Cable_Guide',.022)
prism_x('Front_winch_guard_R',.52,.095,[(-1.79,.98),(-1.79,1.63),(-1.52,1.69),(-1.27,1.27)],grey,'Cable_Guide',.022)
box('Cable_fairlead_green_mount',(0,-1.86,1.30),(.61,.30,.28),green,'Cable_Guide',.03)
cyl_between('Cable_horizontal_roller',(-.20,-2.035,1.30),(.20,-2.035,1.30),.066,steel,'Cable_Guide',24)
for x in [-.22,.22]:cyl_between('Cable_vertical_roller',(x,-2.05,1.17),(x,-2.05,1.45),.044,steel,'Cable_Guide')
pipe('Winch_short_rope',[(0,-1.02,1.62),(0,-1.60,1.41),(0,-2.12,1.30),(0,-2.25,1.13)],.012,trackedge,'Cable_Guide')
hookpoints=[]
for i in range(18):
    a=math.radians(30+285*i/17)
    hookpoints.append((.02,-2.27+.06*math.sin(a),1.00+.13*math.cos(a)))
pipe('Orange_recovery_hook',hookpoints,.026,red,'Cable_Guide')
box('Hook_latch',(.02,-2.285,1.07),(.036,.033,.12),steel,'Cable_Guide',.005)

# Fire extinguisher, brackets, tow points and boom/exhaust details.
cyl_between('Fire_extinguisher',(.87,-1.93,.87),(1.26,-1.93,.87),.085,red,'Blade_Pivot',28)
for x in [.92,1.20]:torus('Extinguisher_strap',(x,-1.93,.87),.087,.009,black,'Blade_Pivot')
cyl_between('Extinguisher_valve',(1.25,-1.93,.87),(1.34,-1.93,.87),.025,steel,'Blade_Pivot')
pipe('Extinguisher_hose',[(1.31,-1.92,.87),(1.38,-1.87,.81),(1.25,-1.81,.78)],.010,rubber,'Blade_Pivot')
for x in [-.34,.34]:torus('Blade_tie_down_ring',(x,-1.92,1.05),.07,.019,steel,'Blade_Pivot',axis='Y')
pipe('Raised_exhaust_pipe',[(0,.12,2.58),(0,.12,2.86),(0,.24,3.04),(0,.42,3.12),(0,.56,3.12)],.09,steel,'Engine_Housing')
cyl_between('Exhaust_rain_cap',(-.10,.56,3.12),(.10,.56,3.12),.025,grey,'Engine_Housing')
cyl_between('Green_antenna_mast',(-.42,.61,2.62),(-.42,.61,3.24),.017,green,'Engine_Housing',12)
cyl_between('Mast_mount',(-.42,.61,2.62),(-.42,.61,2.73),.052,grey,'Engine_Housing')
for x in [-.81,.81]:
    box('Worklight_bracket',(x,-.91,2.67),(.11,.13,.06),grey,'Lights_and_Decals')
    box('LED_worklight_housing',(x,-.94,2.75),(.36,.10,.12),grey,'Lights_and_Decals',.015)
    for i in range(6):box('LED_worklight_lens',(x-.145+i*.058,-.997,2.75),(.043,.012,.082),led,'Lights_and_Decals',.006)
    cyl_between('Beacon_dark_base',(x,-.56,2.67),(x,-.56,2.71),.055,black,'Lights_and_Decals')
    cyl_between('Amber_warning_beacon',(x,-.56,2.71),(x,-.56,2.79),.044,amber,'Lights_and_Decals')
for x in [-.68,.68]:box('Rear_red_lamp',(x,1.476,1.34),(.15,.022,.07),red,'Lights_and_Decals',.009)

print('Applying manufactured edges and exporting model...',flush=True)
bpy.ops.object.select_all(action='DESELECT')
for obj in mesh_objects:
    if obj.type!='MESH':continue
    bpy.context.view_layer.objects.active=obj
    obj.select_set(True)
    for modifier in list(obj.modifiers):
        if modifier.type=='BEVEL':
            bpy.ops.object.modifier_apply(modifier=modifier.name)
    obj.select_set(False)
    # Auto smooth by angle is exporter-independent when normals are calculated.
    for poly in obj.data.polygons:poly.use_smooth=False

# Keep all visible geometry in place while setting a usable blade pivot.
pivot=groups['Blade_Pivot']
offset=Vector((0,-1.16,.89))
pivot.location=offset
for obj in pivot.children:obj.location-=offset

# Merge repetitive rigid track parts to make one export mesh per track assembly.
for group_name in ['Left_Track','Right_Track']:
    candidates=[o for o in mesh_objects if o.parent==groups[group_name] and o.type=='MESH']
    bpy.ops.object.select_all(action='DESELECT')
    for obj in candidates:obj.select_set(True)
    bpy.context.view_layer.objects.active=candidates[0]
    bpy.ops.object.join()
    joined=bpy.context.object
    joined.name=group_name+'_complete_assembly'
    mesh_objects=[o for o in mesh_objects if o not in candidates]+[joined]

bpy.context.view_layer.update()
verts=[]
triangles=0
for obj in mesh_objects:
    obj.data.calc_loop_triangles()
    triangles+=len(obj.data.loop_triangles)
    verts.extend(obj.matrix_world@Vector(v) for v in obj.bound_box)
low=Vector(tuple(min(v[i] for v in verts) for i in range(3)))
high=Vector(tuple(max(v[i] for v in verts) for i in range(3)))
report={'asset':'Photo-based T-WINCH-style tracked forestry winch','units':'metres',
        'reference':'Last three supplied photographs; first rounded machine is a different enclosure',
        'dimensions_approx_m':list(high-low),'mesh_objects':len(mesh_objects),
        'triangles':triangles,'materials':len(bpy.data.materials),
        'measurements':'Estimated from photos; not manufacturer dimensions',
        'game_status':'3D asset only; no FS25 vehicle configuration or game test',
        'groups':list(groups),'coordinate_convention':'Z up; front is -Y'}
(ROOT/'model_report.json').write_text(json.dumps(report,indent=2))
for obj in bpy.context.scene.objects:obj.select_set(False)
for obj in [root]+list(groups.values())+mesh_objects:obj.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=str(OUT/'TWINCH_forestry_winch.glb'),export_format='GLB',use_selection=True,export_yup=True)
bpy.ops.export_scene.fbx(filepath=str(OUT/'TWINCH_forestry_winch.fbx'),use_selection=True,
                         object_types={'EMPTY','MESH'},apply_unit_scale=True,
                         bake_anim=False,axis_forward='-Z',axis_up='Y',path_mode='AUTO')
bpy.ops.wm.obj_export(filepath=str(OUT/'TWINCH_forestry_winch.obj'),export_selected_objects=True,
                      forward_axis='NEGATIVE_Y',up_axis='Z',export_materials=True)

# Save the editable asset without studio props/cameras, then render a separate
# presentation scene so the model exports remain clean.
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'TWINCH_forestry_winch.blend'))
scene.render.engine='CYCLES'
scene.cycles.samples=32
scene.cycles.use_denoising=False
scene.render.resolution_x=1400
scene.render.resolution_y=1100
scene.render.resolution_percentage=100
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.16,.19,.23,1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.6
scene.view_settings.view_transform='AgX'
ground=mat('Studio_ground',(.37,.40,.42),0,.82)
bpy.ops.mesh.primitive_plane_add(size=200, location=(0,0,.066))
bpy.context.object.data.materials.append(ground)
bpy.context.object.name='PREVIEW_ONLY_ground'
def area(name,loc,power,size,color):
    data=bpy.data.lights.new(name,'AREA')
    data.energy=power
    data.shape='DISK'
    data.size=size
    data.color=color
    obj=bpy.data.objects.new(name,data)
    scene.collection.objects.link(obj)
    obj.location=loc
    obj.rotation_euler=(Vector((0,0,1.2))-obj.location).to_track_quat('-Z','Y').to_euler()
area('Key_softbox',(4,-5,7),1700,5,(1,.93,.84))
area('Fill_softbox',(-4,-1,5),1100,4,(.78,.89,1))
area('Rim_softbox',(0,5,7),2200,4,(1,1,1))
data=bpy.data.cameras.new('Presentation_camera')
camera=bpy.data.objects.new('Presentation_camera',data)
scene.collection.objects.link(camera)
scene.camera=camera
data.type='ORTHO'
data.ortho_scale=5.7
def render(name,position,target=(0,-.18,1.55)):
    camera.location=position
    camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(PREVIEW/name)
    bpy.ops.render.render(write_still=True)
render('TWINCH_front_three_quarter.png',(6,-8,5.1))
render('TWINCH_rear_three_quarter.png',(-6,7,4.7))
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'TWINCH_presentation.blend'))
print('COMPLETE',json.dumps(report),flush=True)
