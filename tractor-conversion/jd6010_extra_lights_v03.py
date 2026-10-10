"""Wire existing 6010 marker and flash meshes using FS25 light definitions."""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import math
import re
import shutil
import xml.etree.ElementTree as E
import zipfile

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--base', type=Path, default=ROOT / 'output/FS25_JohnDeere6010_Lights_Test_v02')
parser.add_argument('--output', type=Path, default=ROOT / 'output/FS25_JohnDeere6010_Lights_Test_v03')
parser.add_argument('--report', type=Path, default=ROOT / 'reports/lighting_v03_validation.json')
args = parser.parse_args()
BASE = args.base.resolve()
OUT = args.output.resolve()
if not (BASE / 'modDesc.xml').is_file():
    raise SystemExit('Extract the v0.2 ZIP and pass its directory with --base.')
if OUT.exists() or OUT.with_suffix('.zip').exists():
    raise SystemExit('Preserve existing output; do not overwrite edited candidates.')
shutil.copytree(BASE, OUT)
model = E.parse(OUT / 'johndeere6010.i3d')
vehicle = E.parse(OUT / 'johndeere6010.xml')
scene = model.find('Scene')
materials = model.find('Materials')
lights = vehicle.find('lights')

def resolve(path, mappings=None, selected_scene=scene):
    path = (mappings or {}).get(path, path)
    indices = path.replace('>', '|').strip('|').split('|')
    node = selected_scene
    for index in indices:
        node = list(node)[int(index)]
    return node

def parameter(material, name, value):
    node = next((n for n in material.findall('CustomParameter') if n.get('name') == name), None)
    if node is None:
        node = E.SubElement(material, 'CustomParameter', name=name)
    node.set('value', value)

def emission_material(original_id, name, color, flash=False):
    original = next(m for m in materials if m.get('materialId') == original_id)
    material = copy.deepcopy(original)
    material.set('materialId', str(max(int(m.get('materialId')) for m in materials) + 1))
    material.set('name', name)
    material.set('customShaderId', '2')
    material.set('customShaderVariation', 'staticLight_jd6010Flash' if flash else 'staticLight_jd6010Marker')
    parameter(material, 'meshEmission', color)
    parameter(material, 'lightControl', '0')
    if flash:
        parameter(material, 'blinkOffset', '2 3 50 0')
    materials.append(material)
    return material.get('materialId')

# Force emission color for donor meshes whose UV/vertex colors were not authored
# as GIANTS light meshes. Markers are steady; flash meshes always use mVisScale.
shader_path = OUT / 'shaders/vehicleShader.xml'
shader = shader_path.read_text()
shader = shader.replace('</Parameters>',
    '<Parameter name="meshEmission" target="meshEmission" type="float4" group="jd6010Emission" defaultValue="1 1 1 0"/>\n    </Parameters>', 1)
shader = shader.replace('</Variations>', '''
        <Variation name="staticLight_jd6010Marker" groups="base colorMask staticLight vtxColor jd6010Emission">
<![CDATA[
    #define COLOR_MASK
    #define STATIC_LIGHT
    #define JD6010_EMISSION
    #define JD6010_STEADY
]]>
        </Variation>
        <Variation name="staticLight_jd6010Flash" groups="base colorMask staticLight vtxColor jd6010Emission">
<![CDATA[
    #define COLOR_MASK
    #define STATIC_LIGHT
    #define STATIC_MULTI_BLINK
    #define JD6010_EMISSION
    #define JD6010_FLASH
]]>
        </Variation>
    </Variations>''', 1)
needle = '    float3 mEmitColor = In.vs.vertexColor.rgb;'
assert shader.count(needle) == 1
shader = shader.replace(needle, needle + '''
#if defined(JD6010_EMISSION)
    mEmitColor = object.meshEmission.xyz;
#endif''')
needle = '''    if (uv.y < -1.0){
        mEmitColor *= visScale;
    }'''
assert shader.count(needle) == 1
shader = shader.replace(needle, '''#if defined(JD6010_FLASH)
    mEmitColor *= visScale;
#elif !defined(JD6010_STEADY)
    if (uv.y < -1.0){
        mEmitColor *= visScale;
    }
#endif''')
E.fromstring(shader)
shader_path.write_text(shader)

white_lens = emission_material('26', 'jd6010WhiteDiodeLens', '0.8 0.9 1 0')
white_core = emission_material('74', 'jd6010WhiteDiodeCore', '0.8 0.9 1 0')
red_core = emission_material('74', 'jd6010RedDiodeCore', '1 0.01 0.002 0')
red_lens = emission_material('26', 'jd6010RedDiodeLens', '1 0.01 0.002 0')
amber_flash = emission_material('80', 'jd6010AmberFlash', '1 0.28 0.015 0', flash=True)

mirrors = [f'0>0|7|0|3|0|0|{i}' for i in range(2, 8)]
roof_front = [f'0>0|7|0|3|0|1|{i}' for i in range(12, 17)]
roof_rear = [f'0>0|7|0|3|0|1|{i}' for i in range(17, 24)]
marker_roots = set(mirrors + roof_front + roof_rear)
defaults = lights.find('defaultLights')
for entry in list(defaults):
    if entry.get('shaderNode', entry.get('node')) in marker_roots:
        defaults.remove(entry)

next_id = max(int(n.get('nodeId', '0')) for n in scene.iter()) + 1
added_lights = []
def add_point(parent_path, name, color, distance='2'):
    global next_id
    parent = resolve(parent_path)
    path = parent_path + '|' + str(len(parent))
    E.SubElement(parent, 'Light', name=name, nodeId=str(next_id),
                 type='point', translation='0 0.03 0', color=color,
                 range=distance, clipDistance='70', emitDiffuse='true',
                 emitSpecular='true', castShadowMap='false')
    next_id += 1
    added_lights.append(path)
    return path

for path in mirrors + roof_front:
    resolve(path + '|0').set('materialIds', white_lens)
    resolve(path + '|1').set('materialIds', white_core)
    for child in [0, 1]:
        E.SubElement(defaults, 'defaultLight', node=path + '|' + str(child), lightTypes='0', intensity='1')
    point = add_point(path, 'jd6010WhiteDiodeSpill', '0.08 0.09 0.1')
    for profile in ['low', 'high']:
        E.SubElement(lights.find('realLights/' + profile), 'light', node=point, lightTypes='0')

for path in roof_rear:
    resolve(path + '|0').set('materialIds', red_core)
    resolve(path + '|1').set('materialIds', red_lens)
    # Separate running and brake meshes avoid two controllers sharing one node.
    E.SubElement(defaults, 'defaultLight', node=path + '|0', lightTypes='0', intensity='1')
    E.SubElement(lights.find('brakeLights'), 'brakeLight', node=path + '|1', intensity='3')
    point = add_point(path, 'jd6010RedDiodeSpill', '0.12 0.0012 0.00024')
    for profile in ['low', 'high']:
        E.SubElement(lights.find('realLights/' + profile), 'light', node=point, lightTypes='0')

# Use FS25's inline staticLight/realLight beacon definition rather than loading
# complete donor lamps on top of the lamps already merged into this scene.
# The syntax is established by KUK's FS25 Fendt beaconLightConfigurations.
old_beacons = lights.find('beaconLights')
native_beacons = [copy.deepcopy(b) for b in old_beacons if b.get('filename', '').startswith('$')]
flash_roots = [b.get('node') for b in old_beacons if not b.get('filename', '').startswith('$')]
assert len(flash_roots) == 24 and len(set(flash_roots)) == 24
lights.remove(old_beacons)
configs = E.SubElement(lights, 'beaconLightConfigurations')
configuration = E.SubElement(configs, 'beaconLightConfiguration', name='Blitzbjelke', price='0', isDefault='true')
for beacon in native_beacons:
    configuration.append(beacon)
flash_emitters = []
for index, path in enumerate(flash_roots):
    emitter = resolve(path + '|3')
    assert emitter.tag == 'Shape' and emitter.get('name') == 'TZG_FBK_STATIC'
    emitter.set('materialIds', amber_flash)
    flash_emitters.append(path + '|3')
    point = add_point(path, 'jd6010AmberFlashSpill', '0.35 0.098 0.00525', '3')
    beacon = E.SubElement(configuration, 'beaconLight', realLight=point)
    E.SubElement(beacon, 'staticLight', node=path + '|3', intensity='8',
                 multiBlink='true', multiBlinkParameters='2 3 50 0')

# Convert the retained static-light node attribute names to the current FS25
# syntax demonstrated by the native FS25 defaultLight definitions.
for n in lights.iter():
    if n.get('shaderNode'):
        n.set('node', n.attrib.pop('shaderNode'))
model.write(OUT / 'johndeere6010.i3d', encoding='utf-8', xml_declaration=True)
vehicle.write(OUT / 'johndeere6010.xml', encoding='utf-8', xml_declaration=True)
four = E.parse(OUT / 'johndeere60104cyl.xml')
for n in four.find('lights').iter():
    if n.get('shaderNode'):
        n.set('node', n.attrib.pop('shaderNode'))
old = four.find('./lights/beaconLights')
if old is not None:
    groups = E.SubElement(four.find('lights'), 'beaconLightConfigurations')
    group = E.SubElement(groups, 'beaconLightConfiguration', name='Standard', price='0', isDefault='true')
    for b in old:
        group.append(copy.deepcopy(b))
    four.find('lights').remove(old)
four.write(OUT / 'johndeere60104cyl.xml', encoding='utf-8', xml_declaration=True)
desc = E.parse(OUT / 'modDesc.xml')
desc.find('version').text = '0.3.0.0'
desc.write(OUT / 'modDesc.xml', encoding='utf-8', xml_declaration=True)

# Revalidate all light nodes and file references, including newly coded lamps.
node_references = 0
local_references = 0
xml_files = 0
for stem in ['johndeere6010', 'johndeere60104cyl']:
    v = E.parse(OUT / (stem + '.xml'))
    s = E.parse(OUT / (stem + '.i3d')).find('Scene')
    mappings = {n.get('id'): n.get('node') for n in v.findall('./i3dMappings/i3dMapping')}
    for n in v.find('lights').iter():
        for key in ['node', 'linkNode', 'realLight']:
            if n.get(key):
                resolve(n.get(key), mappings, s)
                node_references += 1
        assert not n.get('shaderNode')
for path in mirrors + roof_front:
    assert all(any(n.get('node') == path + '|' + str(i) and n.get('lightTypes') == '0'
                   for n in lights.findall('./defaultLights/defaultLight')) for i in [0, 1])
for path in roof_rear:
    assert any(n.get('node') == path + '|0' for n in defaults)
    assert any(n.get('node') == path + '|1' for n in lights.findall('./brakeLights/brakeLight'))
for path in flash_emitters:
    assert resolve(path).get('materialIds') == amber_flash
    assert any(n.get('node') == path for n in configuration.findall('./beaconLight/staticLight'))
ids = [n.get('nodeId') for n in scene.iter() if n.get('nodeId')]
assert len(ids) == len(set(ids))
old_scene = E.parse(BASE / 'johndeere6010.i3d').find('Scene')
def validate_existing_nodes(before, after):
    # Existing child order, geometry, transforms and node IDs must be retained.
    assert len(after) >= len(before)
    for key, value in before.attrib.items():
        if key != 'materialIds':
            assert after.get(key) == value, (before.get('name'), key)
    for i, child in enumerate(before):
        validate_existing_nodes(child, list(after)[i])
validate_existing_nodes(old_scene, scene)
for p in OUT.rglob('*.shapes'):
    assert hashlib.sha256(p.read_bytes()).digest() == hashlib.sha256((BASE / p.relative_to(OUT)).read_bytes()).digest()
extensions = {'.xml', '.i3d', '.dds', '.png', '.ogg', '.gls', '.shapes', '.lua'}
for p in OUT.rglob('*'):
    if p.suffix not in {'.xml', '.i3d'}:
        continue
    xml_files += 1
    tree = E.parse(p)
    for n in tree.iter():
        values = list(n.attrib.values()) + ([n.text.strip()] if n.text and n.text.strip() else [])
        for value in values:
            if not value.startswith(('http', '$')) and Path(value).suffix.lower() in extensions:
                q = p.parent / value if p.suffix == '.i3d' else OUT / value
                assert q.resolve().is_relative_to(OUT) and q.is_file(), (p.name, value)
                local_references += 1
    if p.suffix == '.i3d':
        files = {n.get('fileId'): n.get('filename') for n in tree.findall('./Files/File')}
        for mat in tree.findall('./Materials/Material'):
            shader_file = files.get(mat.get('customShaderId'), '')
            variation = mat.get('customShaderVariation')
            if variation and shader_file and not shader_file.startswith('$'):
                definitions = E.parse(p.parent / shader_file)
                assert variation in {n.get('name') for n in definitions.findall('./Variations/Variation')}, (p.name, variation)

# Check the inherited multiblink formula produces two distinct pulses followed
# by a dark pause per period using the XML's actual configured parameters.
x, y, frequency, _ = map(float, configuration.find('./beaconLight/staticLight').get('multiBlinkParameters').split())
period = (2*x + 2*y) * math.pi / frequency
samples = []
for i in range(2000):
    time = i * period / 2000
    value = math.sin(time * frequency) - max(math.fmod(time * frequency, (2*x + 2*y)*math.pi) - (2*x - 1)*math.pi, 0) + 0.2
    samples.append(max(0, min(1, value)) > 0.5)
pulses = sum(samples[i] and not samples[i-1] for i in range(1, len(samples)))
assert pulses == 2 and not samples[-1]
report = {'version': '0.3.0.0', 'mirror_diodes': 6, 'front_roof_diodes': 5,
          'rear_roof_diodes': 7, 'bar_flash_modules': 20,
          'separate_mirror_rear_flash_modules': 4, 'inline_flash_beacons': 24,
          'new_point_lights': len(added_lights), 'resolved_light_references': node_references,
          'local_file_references': local_references, 'xml_files': xml_files,
          'double_flash_pulses_per_period': pulses, 'flash_period_seconds': period,
          'existing_node_order_and_transforms_preserved': True,
          'geometry_binary_unchanged': True,
          'game_tests': 'not_run', 'shader_compilation': 'not_run',
          'external_game_resources': 'validation_outstanding'}
readme = OUT / 'FS25_TEST_README.txt'
readme.write_text('''John Deere 6010 FS25 lights test v0.3
Both tractors are included. The requested edited lights are on the six-cylinder.
HOME/beacon toggle: 20 existing lightbar flash modules, two mirror flash modules
and two rear flash modules use FS25 inline beacon registrations with double flash.
The existing in-model emitting surfaces are used; donor lamps are not cloned on
top of the existing geometry. Each flash module has an amber light spill.
Normal lights: six white mirror diodes and five white front roof diodes emit from
the lens and inner surfaces. Seven rear roof diodes use red running-light cores
and separate brighter red brake lenses. All marker groups have gentle light spill
in both graphics light profiles. Lamp housings stay unlit.
The current FS25 node attribute and beaconLightConfigurations structure are used.
Original node order, transforms and binary geometry are preserved.
Install ZIP without extracting; disable older 6010 copies. Enable in a test save.
Buy the six-cylinder tractor; check normal lights, high beams, work lights, brakes,
turn signals, hazards and HOME beacons. Check the same in low/high graphics profiles.
Shader compilation, game loading, sound templates and native FS25 asset paths need
testing in your installed game. Send a fresh FS25 log.txt if anything fails.
This cloud machine has no FS25/Editor; these checks are static and mathematical.
The v0.2 legacy texture fallback and unused donor BKT variant limitations remain.
''')
(OUT / 'conversion_validation.json').write_text(json.dumps(report, indent=2))
archive = OUT.with_suffix('.zip')
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for p in sorted(OUT.rglob('*')):
        if p.is_file():
            info = zipfile.ZipInfo(p.relative_to(OUT).as_posix(), date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, p.read_bytes())
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
report['zip_crc'] = 'passed'
report['sha256'] = hashlib.sha256(archive.read_bytes()).hexdigest()
args.report.parent.mkdir(parents=True, exist_ok=True)
args.report.write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
