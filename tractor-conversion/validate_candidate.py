"""Static resource checks and isolated Lua 5.1 tests; these do not run FS25."""
from pathlib import Path
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path('/workspace/tractor-conversion')
sys.path.insert(0, str(ROOT / 'tools/python-deps'))
from lupa.lua51 import LuaRuntime

SOURCE = ROOT / 'source/FS22_JohnDeere_6030_edit'
OUTPUT = ROOT / 'output/FS25_JohnDeere_6030_Lights_Test'
catalog = next(Path('/workspace/attachments').rglob('FS25_asset_paths.txt'))
assets = {s.strip().replace('\\', '/').lower() for s in catalog.read_text(encoding='utf-8-sig').splitlines()}
errors = []
counts = {'xml_files': 0, 'external_resources': 0, 'local_resources': 0, 'light_node_references': 0}
extensions = {'.xml', '.i3d', '.dds', '.png', '.ogg', '.lua', '.shapes', '.gls'}
for p in OUTPUT.rglob('*'):
    if p.suffix not in {'.xml', '.i3d'}:
        continue
    r = ET.parse(p)
    counts['xml_files'] += 1
    for el in r.iter():
        values = list(el.attrib.values())
        if el.text and el.text.strip():
            values.append(el.text.strip())
        for value in values:
            if value.startswith('$data/'):
                counts['external_resources'] += 1
                if value[6:].lower() not in assets:
                    errors.append(f'{p.name}: unknown FS25 resource {value}')
            elif not value.startswith(('$', 'http')) and Path(value).suffix.lower() in extensions:
                counts['local_resources'] += 1
                if not any(q.is_file() for q in [p.parent/value, OUTPUT/value, (p.parent/value).with_suffix('.dds'), (OUTPUT/value).with_suffix('.dds')]):
                    errors.append(f'{p.name}: missing local resource {value}')

original = ET.parse(SOURCE / 'JohnDeere6030.i3d')
import re
shader_original = (ROOT/'source/FS25_vehicleShader_original.xml').read_text(encoding='utf-8-sig')
shader_fixed = (OUTPUT/'shaders/vehicleShader.xml').read_text()
expected, count = re.subn(
    r'(tex2DSample\(\s*mArray(?:Specular|Normal|Diffuse),\s*standardMaterialSampler,\s*uvs,\s*(?:aIndex|8|15)\s*\))(?=\s*;)',
    r'\1.xyz', shader_original)
assert count == 6
for kind in ['specular', 'normal', 'diffuse']:
    expected = expected.replace(f'../shared/detailArray_{kind}.png', f'$data/fs22support/shared/detailArray_{kind}.dds')
assert shader_fixed == expected, 'Shader changed outside the six casts and texture paths'
for p in OUTPUT.rglob('*.i3d'):
    for f in ET.parse(p).findall('./Files/File'):
        assert f.get('filename') != '$data/fs22support/shaders/vehicleShader.xml', 'Unpatched shader remains'
model = ET.parse(OUTPUT / 'JohnDeere6030.i3d')
def scene_signature(el):
    return el.tag, sorted(el.attrib.items()), [scene_signature(child) for child in el]
assert scene_signature(original.find('Scene')) == scene_signature(model.find('Scene')), 'Scene graph changed'
assert hashlib.sha256((SOURCE/'JohnDeere6030.i3d.shapes').read_bytes()).digest() == hashlib.sha256((OUTPUT/'JohnDeere6030.i3d.shapes').read_bytes()).digest(), 'Model geometry changed'
vehicle = ET.parse(OUTPUT/'JohnDeere6030.xml')
mappings = {el.get('id'): el.get('node') for el in vehicle.findall('./i3dMappings/i3dMapping')}
def resolve(value):
    value = mappings.get(value, value)
    if '>' in value:
        root, tail = value.split('>')
        node = list(model.find('Scene'))[int(root)]
        indices = tail.split('|') if tail else []
    else:
        node = model.find('Scene')
        indices = value.split('|')
    for index in indices:
        node = list(node)[int(index)]
    return node
for el in vehicle.find('lights').iter():
    for key in ['node', 'linkNode']:
        if el.get(key):
            resolve(el.get(key))
            counts['light_node_references'] += 1
for name in ['realLightsL_1200', 'realLightsR_1200']:
    assert resolve(name).tag == 'Light'
for name in ['staticStrobeL', 'staticStrobeR']:
    assert resolve(name).tag == 'Shape'
source_lights = ET.parse(SOURCE/'JohnDeere6030.xml').find('lights')
# Resource filenames may change; the light configuration itself must be identical.
def light_signature(el):
    return el.tag, sorted((k,v) for k,v in el.attrib.items() if k != 'filename'), [light_signature(c) for c in el]
assert light_signature(source_lights) == light_signature(vehicle.find('lights'))
for unit in vehicle.findall('./fillUnit/fillUnitConfigurations/fillUnitConfiguration/fillUnits/fillUnit'):
    if unit.get('fillTypes') == 'DIESEL':
        resolve(unit.find('exactFillRootNode').get('node'))

lua = LuaRuntime(unpack_returned_tuples=True)
lua.execute('''
g_currentModName = "FS25_JohnDeere_6030_Lights_Test"
XMLValueType = {STRING=1, FLOAT=2, INT=3}
registeredPaths = {}
local schema = {register=function(self, kind, path) registeredPaths[path] = true end}
Vehicle = {xmlSchema=schema, xmlSchemaSavegame=schema}
SoundManager = {registerSampleXMLPaths=function(s, base, name) registeredPaths[base.."."..name] = true end}
Wheels = {}
WheelsUtil = {getTireType=function(name) return name end}
SpecializationUtil = {hasSpecialization=function() return true end}
Event = {}
function Class() return {} end
function InitEventClass() end
MathUtil = {
 clamp=function(v, lo, hi) return math.min(hi, math.max(lo, v)) end,
 round=function(v, decimals) local scale=10^decimals; return math.floor(v*scale+0.5)/scale end,
 sign=function(v) return v == 0 and 0 or (v > 0 and 1 or -1) end
}
-- Deliberately omit Utils.getNoNil and string.getVectorN: these legacy globals
-- failed in the user's actual FS25 load and must not be mocked into existence.
Utils = {}
AudioGroup = {VEHICLE=1}
g_soundManager = {
 registerModifierType=function() end,
 loadSampleFromXML=function(self, xmlFile) assert(type(xmlFile)=='table'); return {} end,
 deleteSamples=function() end
}
''')
lua.execute((OUTPUT/'scripts/TirePressure.lua').read_text())
lua.execute('''
TirePressure.initSpecialization()
assert(registeredPaths["vehicle.tirePressure#min"])
assert(registeredPaths["vehicle.tirePressure#configurationIndices"])
assert(registeredPaths["vehicle.tirePressure.sounds.air"])
local wheel = {physics={tireType="mud", frictionScale=1.6, suspTravel=0.2}}
local crawler = {physics={tireType="crawler", frictionScale=2.0}}
local values = {
 ["vehicle.tirePressure#min"]=90, ["vehicle.tirePressure#max"]=200,
 ["vehicle.tirePressure#configurationName"]="vehicleType",
 ["vehicle.tirePressure#configurationIndices"]="2"
}
local vehicle = {
 isClient=true, isServer=true, baseDirectory="", components={}, i3dMappings={},
 configurations={vehicleType=2},
 xmlFile={getValue=function(self,key) return values[key] end},
 getWheels=function() return {wheel, crawler} end,
 getNextDirtyFlag=function() return 1 end,
 raiseDirtyFlags=function(self,flag) self.raisedFlag=flag end
}
vehicle["spec_"..g_currentModName..".tirePressure"] = {}
setmetatable(vehicle, {__index=TirePressure})
vehicle:onLoad()
assert(vehicle.spec_tirePressure.isActive)
assert(type(vehicle.spec_tirePressure.actionEvents) == 'table')
vehicle:onLoadFinished()
assert(not vehicle.spec_tirePressure.allWheelsAreCrawlers)
assert(wheel.physics.frictionScale == 1.6)
vehicle:setInflationPressure(90)
assert(math.abs(wheel.physics.frictionScale-3.2)<0.00001)
assert(wheel.physics.isFrictionDirty)
assert(crawler.physics.frictionScale == 2.0)
assert(wheel.physics.suspTravel == 0.2)
vehicle:setInflationPressure(1000)
assert(vehicle:getInflationPressure() == 200)
assert(vehicle.raisedFlag == 1)
vehicle:onPostLoad({key="vehicles.vehicle(0)", xmlFile={getValue=function() return 120 end}})
assert(vehicle:getInflationPressure() == 120)
vehicle.configurations.vehicleType = 1
vehicle:onLoad()
assert(not vehicle.spec_tirePressure.isActive)
assert(vehicle:getCanBeSelected(function() return false end) == false)
vehicle:onDelete()
vehicle.spec_tirePressure = nil
vehicle:onDelete()
assert(TirePressure.valueOrDefault(false, true) == false)
assert(TirePressure.parseConfigurationIndices(nil)[1] == 1)
assert(#TirePressure.parseConfigurationIndices("2 8 9") == 3)
assert(#TirePressure.parseConfigurationIndices("bad") == 0)
''')
with zipfile.ZipFile(OUTPUT.with_suffix('.zip')) as z:
    assert z.testzip() is None
    assert 'modDesc.xml' in z.namelist()
    assert all(not name.startswith('/') and '..' not in Path(name).parts for name in z.namelist())
result = {'static_checks': 'passed' if not errors else 'failed', 'counts': counts,
          'shader_six_float3_assignments': 'passed', 'shader_engine_compilation': 'not_run',
          'lua_5_1_isolated_checks': 'passed', 'light_graph_preserved': True,
          'geometry_unchanged': True, 'zip_crc': 'passed', 'engine_tests': 'not_run', 'errors': errors}
(ROOT/'reports/validation_result.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
if errors:
    sys.exit(1)
