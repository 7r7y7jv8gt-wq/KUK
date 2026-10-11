import bpy,json,math
from pathlib import Path
from mathutils import Vector
root=Path('/workspace/twinch')
results={}
for ext in ['blend','glb','fbx','obj']:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    file=root/'model'/('TWINCH_forestry_winch.'+ext)
    if ext=='blend':bpy.ops.wm.open_mainfile(filepath=str(file))
    elif ext=='glb':bpy.ops.import_scene.gltf(filepath=str(file))
    elif ext=='fbx':bpy.ops.import_scene.fbx(filepath=str(file))
    else:bpy.ops.wm.obj_import(filepath=str(file),forward_axis='NEGATIVE_Y',up_axis='Z')
    bpy.context.view_layer.update()
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    assert meshes and all(len(o.data.vertices)>0 for o in meshes)
    points=[o.matrix_world@Vector(v) for o in meshes for v in o.bound_box]
    assert all(math.isfinite(x) for p in points for x in p)
    dimensions=[max(p[i] for p in points)-min(p[i] for p in points) for i in range(3)]
    assert all(.1<d<10 for d in dimensions),dimensions
    assert len(meshes)==195,(ext,len(meshes))
    results[ext]={'import_ok':True,'mesh_objects':len(meshes),'dimensions_m':dimensions,'bytes':file.stat().st_size}
(root/'export_validation.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results,indent=2))
