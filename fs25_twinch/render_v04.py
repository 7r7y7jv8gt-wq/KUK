import bpy,xml.etree.ElementTree as E,math
from pathlib import Path
from mathutils import Euler
HERE=Path(__file__).resolve().parent;OUT=HERE.parent/'FS25_TWinch_v04'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
r=E.parse(OUT/'twinch.i3d').getroot();files={f.get('fileId'):OUT/f.get('filename') for f in r.find('Files')};mats={}
for m in r.find('Materials'):
 mat=bpy.data.materials.new(m.get('name'));mat.use_nodes=True;ns=mat.node_tree.nodes;links=mat.node_tree.links;p=ns.get('Principled BSDF')
 for tag,channel in [('Texture','Base Color'),('Normalmap','Normal')]:
  f=m.find(tag)
  if f is None:continue
  tex=ns.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(files[f.get('fileId')]))
  if tag=='Normalmap':tex.image.colorspace_settings.name='Non-Color';normal=ns.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.3;links.new(tex.outputs['Color'],normal.inputs['Color']);links.new(normal.outputs['Normal'],p.inputs['Normal'])
  else:links.new(tex.outputs['Color'],p.inputs[channel])
 p.inputs['Roughness'].default_value=.55;p.inputs['Metallic'].default_value=.65 if int(m.get('materialId')) in [8,10,11,12] else .12;mats[m.get('materialId')]=mat
meshes={}
for s in r.find('Shapes'):
 vs=list(s.find('Vertices'));p=[tuple(map(float,v.get('p').split())) for v in vs];faces=[tuple(map(int,t.get('vi').split())) for t in s.find('Triangles')];me=bpy.data.meshes.new(s.get('name'));me.from_pydata(p,[],faces);uv=me.uv_layers.new()
 for poly in me.polygons:
  for li in poly.loop_indices:uv.data[li].uv=tuple(map(float,vs[me.loops[li].vertex_index].get('t0','0 0').split()))
 meshes[s.get('shapeId')]=me
def walk(n,parent=None):
 if n.tag not in ['Shape','TransformGroup','Camera']:return
 me=meshes.get(n.get('shapeId'));ob=bpy.data.objects.new(n.get('name'),me.copy() if me else None);bpy.context.collection.objects.link(ob);ob.parent=parent;ob.location=tuple(map(float,n.get('translation','0 0 0').split()));ob.rotation_euler=Euler(tuple(math.radians(x) for x in map(float,n.get('rotation','0 0 0').split())),'XYZ');ob.scale=tuple(map(float,n.get('scale','1 1 1').split()))
 if me:
  ob.data.materials.append(mats[n.get('materialIds').split()[0]]);ob.hide_render=n.get('nonRenderable')=='true' or n.get('visibility')=='false'
 for c in n:walk(c,ob)
walk(r.find('Scene')[0]);bpy.context.scene.render.engine='CYCLES';bpy.context.scene.cycles.samples=24;bpy.context.scene.cycles.use_denoising=False
# I3D has Y up: rotate assembly into Blender's Z-up world.
root=bpy.data.objects['twinchComponent'];root.rotation_euler.x=math.pi/2
bpy.ops.mesh.primitive_plane_add(size=200);floor=bpy.context.object;floor.location.z=-.02;mat=bpy.data.materials.new('Floor');mat.diffuse_color=(.11,.12,.13,1);floor.data.materials.append(mat)
world=bpy.context.scene.world;world.color=(.3,.3,.3)
from mathutils import Vector
for loc,power,size in [((3,-4,7),1800,5),((-4,-1,5),1300,4),((0,5,6),1800,4)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(4,-6,3.6));cam=bpy.context.object;cam.rotation_euler=(Vector((0,-.3,1.2))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=48;bpy.context.scene.camera=cam
s=bpy.context.scene;s.render.resolution_x=1300;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.render.filepath=str(HERE/'preview_v04.png');s.view_settings.view_transform='AgX';bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'twinch_v04.blend'));bpy.ops.render.render(write_still=True)
