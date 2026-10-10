"""Apply the user's five lighting edits to the repaired v0.3 candidate."""
from pathlib import Path
import copy
import hashlib
import json
import shutil
import xml.etree.ElementTree as E
import zipfile

ROOT = Path('/workspace/tractor-conversion')
BASE = ROOT/'output/FS25_JohnDeere_6030_Lights_Test'
OUT = ROOT/'output/FS25_JohnDeere_6030_Lights_Test_v04'
if OUT.exists():
    shutil.rmtree(OUT)
shutil.copytree(BASE, OUT)
model = E.parse(OUT/'JohnDeere6030.i3d')
vehicle = E.parse(OUT/'JohnDeere6030.xml')
scene = model.find('Scene')
materials = model.find('Materials')
lights = vehicle.find('lights')
def resolve(path):
    root, tail = path.split('>')
    node = list(scene)[int(root)]
    for part in tail.split('|') if tail else []:
        node = list(node)[int(part)]
    return node
def parameter(material, name, value):
    for p in material.findall('CustomParameter'):
        if p.get('name') == name:
            p.set('value', value)
            return
    E.SubElement(material, 'CustomParameter', name=name, value=value)
def emission_material(original_id, name, color):
    original = next(m for m in materials if m.get('materialId') == original_id)
    new = copy.deepcopy(original)
    new.set('materialId', str(max(int(m.get('materialId')) for m in materials)+1))
    new.set('name', name)
    new.set('customShaderId', '4')
    new.set('customShaderVariation', 'staticLight_customEmission')
    parameter(new, 'meshEmission', color)
    parameter(new, 'lightControl', '0 0 0 0')
    materials.append(new)
    return new.get('materialId')

# Keep the lightbar width and strobe geometry. Thin only the cruise-light mesh.
cruise_path = '0>0|7|0|17|0|2|6'
cruise = resolve(cruise_path)
scale = [float(v) for v in cruise.get('scale', '1 1 1').split()]
cruise.set('scale', f'{scale[0]:.6f} {scale[1]*0.55:.6f} {scale[2]*0.55:.6f}')

# Rear window LEDs: red running lights in the inner mesh, separate brake meshes.
rear_material = emission_material('2752', 'rearWindowDiods_red', '1.4 0.015 0.005 0')
rear_paths = []
for i in range(25,31):
    root_path = f'0>0|7|0|{i}'
    for entry in list(lights.find('defaultLights')):
        if entry.get('shaderNode') == root_path:
            lights.find('defaultLights').remove(entry)
    resolve(root_path+'|0').set('materialIds', rear_material)
    E.SubElement(lights.find('defaultLights'), 'defaultLight', shaderNode=root_path+'|0', lightTypes='0', intensity='1')
    E.SubElement(lights.find('brakeLights'), 'brakeLight', shaderNode=root_path+'|1', intensity='3')
    rear_paths.append(root_path+'|0')

# High beam is light type 3. Keep OZZ position rings on running-light type 0.
ozz_paths = ['0>0|7|0|23', '0>0|7|0|24']
next_id = max(int(n.get('nodeId','0')) for n in scene.iter())+1
for path in ozz_paths:
    for entry in lights.find('defaultLights'):
        if entry.get('shaderNode') == path+'|4':
            entry.set('lightTypes', '3')
            entry.set('intensity', '3')
    parent = resolve(path)
    index = len(parent)
    E.SubElement(parent, 'Light', name='ozzHighBeam', nodeId=str(next_id),
                 translation='0 0 -0.1', rotation='0 0 0', type='spot',
                 color='2.55 2.55 3', range='100', coneAngle='35', dropOff='1',
                 clipDistance='180', emitDiffuse='true', emitSpecular='true')
    next_id += 1
    for profile in ['low','high']:
        E.SubElement(lights.find('realLights/'+profile), 'light', node=path+'|'+str(index), lightTypes='3')

# The five marker lights already exist in the model. Bind all five and increase
# emitted brightness 3x, with a longer 4 m spill. Preserve the amber hue.
markers = ['0>0|7|0|20|3', '0>0|7|0|20|3|0', '0>0|7|0|20|3|1',
           '0>0|7|0|20|4|1', '0>0|7|0|20|4|1|0']
for path in markers:
    node = resolve(path)
    node.set('color', '0.6 0.3 0')
    node.set('range', '4')
    for profile in ['low','high']:
        E.SubElement(lights.find('realLights/'+profile), 'light', node=path, lightTypes='0')
for entry in lights.find('defaultLights'):
    if entry.get('shaderNode') in ['0>0|7|0|20|0', '0>0|7|0|20|1']:
        entry.set('intensity', '3')

# Illuminate the actual Michelin figurine meshes, keeping their stands unlit.
michelin_material = emission_material('2712', 'michelinMen_illuminated', '0.45 0.5 0.6 0')
michelin_paths = ['0>0|7|0|21|0|0', '0>0|7|0|22|0|0']
for path in michelin_paths:
    resolve(path).set('materialIds', michelin_material)
    E.SubElement(lights.find('defaultLights'), 'defaultLight', shaderNode=path, lightTypes='0', intensity='1')

# These decorative models don't have reliable light vertex colors. A narrowly
# scoped shader variation supplies their color and still uses lightControl for
# switching. All other shader variations and existing strobe code are retained.
shader_path = OUT/'shaders/vehicleShader.xml'
shader = shader_path.read_text()
shader = shader.replace('</Parameters>', '    <Parameter name="meshEmission" target="meshEmission" type="float4" group="customEmission" defaultValue="1 1 1 0"/>\n    </Parameters>', 1)
shader = shader.replace('</Variations>', '''<Variation name="staticLight_customEmission" groups="base colorMask staticLight vtxColor customEmission">
<![CDATA[
    #define COLOR_MASK
    #define STATIC_LIGHT
    #define CUSTOM_MESH_EMISSION
]]>
        </Variation>
    </Variations>''', 1)
needle = '    float3 mEmitColor = In.vs.vertexColor.rgb;'
assert shader.count(needle) == 1
shader = shader.replace(needle, needle+'\n#if defined(CUSTOM_MESH_EMISSION)\n    mEmitColor = object.meshEmission.xyz;\n#endif')
E.fromstring(shader)
shader_path.write_text(shader)
model.write(OUT/'JohnDeere6030.i3d', encoding='utf-8', xml_declaration=True)
vehicle.write(OUT/'JohnDeere6030.xml', encoding='utf-8', xml_declaration=True)
desc = E.parse(OUT/'modDesc.xml')
desc.find('version').text = '0.4.0.0'
desc.write(OUT/'modDesc.xml', encoding='utf-8', xml_declaration=True)
(OUT/'LIGHTING_CHANGES.txt').write_text('''v0.4 — requested lighting edits
Cruise-light illuminated mesh cross-section reduced to 55%; full bar width and strobes retained.
Six LEDs beside rear window wired as red running lights, with separate brake-light meshes.
OZZ main beams changed from work-light type 2 to high-beam type 3; position rings remain type 0.
Two OZZ spot beams added, active on high beam in both graphics light profiles.
Five front marker lamps: 3x emitted brightness, 4 m spill, 3x lens emission.
Both Michelin figurines glow cool white with running lights; their stands remain unlit.
Actual brightness/appearance and the new shader variation require an FS25 test.
''')
readme = OUT/'FS25_TEST_README.txt'
readme.write_text(readme.read_text().replace('v0.3', 'v0.4').replace(
    'No geometry or scene node ordering was changed.',
    'Original binary geometry and existing node indices are retained. See LIGHTING_CHANGES.txt for the v0.4 lighting edits.'))

# Focused validation of the requested behaviors, including resolving every
# static shaderNode (which older checks did not include) and real light node.
mapping = {n.get('id'):n.get('node') for n in vehicle.findall('./i3dMappings/i3dMapping')}
references = 0
for element in lights.iter():
    for key in ['node','shaderNode','linkNode']:
        if element.get(key):
            resolve(mapping.get(element.get(key), element.get(key)))
            references += 1
assert len(rear_paths)==6 and len(markers)==5 and len(michelin_paths)==2
for path in ozz_paths:
    matches=[e for e in lights.find('defaultLights') if e.get('shaderNode')==path+'|4']
    assert len(matches)==1 and matches[0].get('lightTypes')=='3'
    for profile in ['low','high']:
        assert any(e.get('node')==path+'|6' and e.get('lightTypes')=='3' for e in lights.find('realLights/'+profile))
assert hashlib.sha256((OUT/'JohnDeere6030.i3d.shapes').read_bytes()).digest()==hashlib.sha256((BASE/'JohnDeere6030.i3d.shapes').read_bytes()).digest()
original_ids={n.get('nodeId') for n in E.parse(BASE/'JohnDeere6030.i3d').find('Scene').iter() if n.get('nodeId')}
current_ids=[n.get('nodeId') for n in scene.iter() if n.get('nodeId')]
assert len(current_ids)==len(set(current_ids))
assert original_ids.issubset(current_ids)
for path in ['staticStrobeL','staticStrobeR','realLightsL_1200','realLightsR_1200']:
    assert resolve(mapping[path]).get('name')==path
for p in OUT.rglob('*'):
    if p.suffix in ['.xml','.i3d']:
        E.parse(p)
archive = OUT.with_suffix('.zip')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(OUT.rglob('*')):
        if p.is_file():z.write(p,p.relative_to(OUT).as_posix())
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
report={'version':'0.4.0.0','light_references_resolved':references,'rear_leds':6,
        'front_markers':5,'michelin_figures':2,'ozz_high_beams':2,
        'geometry_binary_unchanged':True,'existing_node_ids_preserved':True,
        'zip_crc':'passed','game_tests':'not_run',
        'sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}
(ROOT/'reports/lighting_v04_validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
