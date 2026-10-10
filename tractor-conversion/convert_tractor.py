"""Build an FS25 compatibility test candidate without changing the FS22 source."""
from pathlib import Path
from collections import deque
import hashlib
import json
import os
import re
import shutil
import xml.etree.ElementTree as ET
import zipfile
from PIL import Image

ROOT = Path('/workspace/tractor-conversion')
SOURCE = ROOT / 'source/FS22_JohnDeere_6030_edit'
OUTPUT = ROOT / 'output/FS25_JohnDeere_6030_Lights_Test'
CATALOG = next(Path('/workspace/attachments').rglob('FS25_asset_paths.txt'))
SHADER_SOURCE = ROOT / 'source/FS25_vehicleShader_original.xml'
assets = {s.strip().replace('\\', '/').lower(): s.strip().replace('\\', '/')
          for s in CATALOG.read_text(encoding='utf-8-sig').splitlines() if s.strip()}
changes = []
extensions = {'.xml', '.i3d', '.dds', '.png', '.ogg', '.lua', '.shapes', '.gls'}

def local_file(value, context):
    if not value or value.startswith(('$', 'http')) or Path(value).suffix.lower() not in extensions:
        return None
    paths = [context.parent / value, SOURCE / value] if context.suffix == '.i3d' else [SOURCE / value, context.parent / value]
    for p in paths:
        for q in [p, p.with_suffix('.dds')]:
            if q.is_file() and q.resolve().is_relative_to(SOURCE.resolve()):
                return q
    matches = list(SOURCE.rglob(Path(value).name)) + list(SOURCE.rglob(Path(value).with_suffix('.dds').name))
    matches = list(set(matches))
    if len(matches) == 1:
        return matches[0]
    raise FileNotFoundError(f'{context.relative_to(SOURCE)}: {value}')

def dependency_closure():
    queue = deque([SOURCE / 'modDesc.xml', SOURCE / 'JohnDeere6030.xml'])
    files = set()
    while queue:
        p = queue.popleft()
        if p in files:
            continue
        files.add(p)
        if p.suffix in {'.xml', '.i3d'}:
            tree = ET.parse(p)
            for el in tree.iter():
                values = list(el.attrib.values())
                if el.text and el.text.strip():
                    values.append(el.text.strip())
                for value in values:
                    q = local_file(value, p)
                    if q is not None:
                        queue.append(q)
    return files

def available(path):
    return assets.get(path.lower()) or assets.get(str(Path(path).with_suffix('.dds')).lower())

def map_resource(value, context):
    if not value.startswith('$data/'):
        return value
    old = value[6:]
    lower = old.lower()
    if lower.endswith('/vehicleshader.xml') or lower.endswith('/fs17vehicleshader.xml'):
        new = 'fs22support/shaders/vehicleShader.xml'
    elif lower.endswith('/dashboardlightsshader.xml') or lower.endswith('/dashboardsymbolsshader.xml'):
        new = 'fs22support/shaders/vehicleShader.xml'
    elif '/detailarray_' in lower:
        new = 'fs22support/shared/' + Path(old).with_suffix('.dds').name
    elif lower == 'shared/assets/upperlinks/walterscheid03.i3d':
        new = 'shared/assets/upperLinks/walterscheidHO_110_610.xml'
    elif lower == 'shared/assets/upperlinks/johndeereupperlink.i3d':
        new = 'shared/assets/upperLinks/johnDeereUpperlink.xml'
    elif available(old):
        new = available(old)
    elif '/wheels/tires/' in lower and lower.endswith('.i3d'):
        size = context.stem
        new = available(str(Path(old).parent / (size + '.i3d')))
        if new is None and '/trelleborg/' in lower:
            new = available('shared/wheels/tires/trelleborg/TM600/' + size + '.i3d')
        if new is None:
            raise ValueError(f'No matching FS25 tyre size: {context.name}: {value}')
    else:
        same_name = [p for p in assets.values() if Path(p).stem.lower() == Path(old).stem.lower()]
        if len(same_name) == 1:
            new = same_name[0]
        elif lower.endswith(('_normal.dds', '_normal.png')):
            new = 'shared/default_normal.dds'
        elif lower.endswith(('_vmask.dds', '_vmask.png', '_specular.dds', '_specular.png')):
            new = 'shared/default_vmask.dds'
        elif lower.endswith(('_diffuse.dds', '_diffuse.png')):
            replacement = 'Textures/fs25_missing_atlas_transparent.dds'
            changes.append({'file': str(context.relative_to(OUTPUT)), 'from': value, 'to': replacement,
                            'note': 'Unavailable old atlas; corresponding decorative texture is transparent.'})
            return replacement
        else:
            raise ValueError(f'Unresolved FS25 resource: {context.name}: {value}')
    assert available(new), new
    result = '$data/' + assets[new.lower()]
    if result != value:
        changes.append({'file': str(context.relative_to(OUTPUT)), 'from': value, 'to': result})
    return result

def update_i3d(tree):
    shader_files = {el.get('fileId'): el.get('filename') for el in tree.findall('./Files/File')}
    for material in tree.findall('./Materials/Material'):
        shader = shader_files.get(material.get('customShaderId'), '')
        if 'dashboardLightsShader' in shader or 'dashboardSymbolsShader' in shader:
            material.set('customShaderVariation', 'staticLight')
            parameters = {el.get('name'): el for el in material.findall('CustomParameter')}
            if 'colorMat0' not in parameters:
                color = parameters.get('baseColor')
                ET.SubElement(material, 'CustomParameter', name='colorMat0', value=color.get('value') if color is not None else '1 1 1 0')
            if 'lightControl' not in parameters:
                ET.SubElement(material, 'CustomParameter', name='lightControl', value='0 0 0 0')
        # FS25's compatibility shader retains the old UV material slot layout.
        for parameter in material.findall('CustomParameter'):
            if 'Position' in parameter.get('name', ''):
                parameter.set('name', parameter.get('name').replace('Position', 'Pos'))

def update_lua(path):
    s = path.read_text()
    # FS25 no longer provides these legacy utility functions. Keep parsing and
    # nil defaults local to this specialization instead of assuming globals.
    helpers = '''
function TirePressure.valueOrDefault(value, defaultValue)
    if value == nil then
        return defaultValue
    end
    return value
end

function TirePressure.parseConfigurationIndices(value)
    if value == nil then
        return {1}
    end
    local indices = {}
    for entry in string.gmatch(value, "%S+") do
        local index = tonumber(entry)
        if index ~= nil then
            table.insert(indices, index)
        end
    end
    return indices
end

'''
    s = s.replace('function TirePressure.initSpecialization()', helpers + 'function TirePressure.initSpecialization()', 1)
    s = s.replace('Utils.getNoNil', 'TirePressure.valueOrDefault')
    s = s.replace('string.getVectorN', 'TirePressure.parseConfigurationIndices')
    schema = '''    local schema = Vehicle.xmlSchema
    schema:register(XMLValueType.STRING, "vehicle.tirePressure#configurationName", "Configuration enabling tire pressure")
    schema:register(XMLValueType.STRING, "vehicle.tirePressure#configurationIndices", "Enabled configuration indices")
    schema:register(XMLValueType.FLOAT, "vehicle.tirePressure#min", "Minimum tire pressure", TirePressure.PRESSURE_MIN)
    schema:register(XMLValueType.FLOAT, "vehicle.tirePressure#max", "Maximum tire pressure", TirePressure.PRESSURE_MAX)
    schema:register(XMLValueType.INT, "vehicle.tirePressure#maxSpeed", "Maximum adjustment speed", 0)
    SoundManager.registerSampleXMLPaths(schema, "vehicle.tirePressure.sounds", "air")
'''
    s = s.replace('function TirePressure.initSpecialization()\n', 'function TirePressure.initSpecialization()\n' + schema)
    s = re.sub(r'getXML(?:String|Float|Int)\(self.xmlFile.handle, ("[^"]+")\)', r'self.xmlFile:getValue(\1)', s)
    s = s.replace('g_soundManager:loadSampleFromXML(self.xmlFile.handle,', 'g_soundManager:loadSampleFromXML(self.xmlFile,')
    s = s.replace('    spec.isActive = true -- default enabled.',
                  '    spec.actionEvents = spec.actionEvents or {}\n    spec.isActive = true -- default enabled.')
    s = s.replace('if wheel.tireType ~= tireTypeCrawler then', 'if wheel.physics ~= nil and wheel.physics.tireType ~= tireTypeCrawler then')
    s = s.replace('    SpecializationUtil.registerEventListener(vehicleType, "onPostLoad", TirePressure)',
                  '    SpecializationUtil.registerEventListener(vehicleType, "onPostLoad", TirePressure)\n    SpecializationUtil.registerEventListener(vehicleType, "onLoadFinished", TirePressure)')
    start = s.index('function TirePressure:updateInflationPressure()')
    end = s.index('\nfunction TirePressure:updateInflation(', start)
    s = s[:start] + '''function TirePressure:onLoadFinished()
    local spec = self.spec_tirePressure
    spec.allWheelsAreCrawlers = true
    local crawler = WheelsUtil.getTireType("crawler")
    for _, wheel in ipairs(self:getWheels()) do
        if wheel.physics ~= nil and wheel.physics.tireType ~= crawler then
            spec.allWheelsAreCrawlers = false
        end
    end
    self:updateInflationPressure()
end

function TirePressure:updateInflationPressure()
    local spec = self.spec_tirePressure
    local crawler = WheelsUtil.getTireType("crawler")
    for _, wheel in ipairs(self:getWheels()) do
        local physics = wheel.physics
        if physics ~= nil and physics.tireType ~= crawler then
            physics.tpOriginalFrictionScale = physics.tpOriginalFrictionScale or physics.frictionScale
            -- FS25 stores physics on Wheel.physics. Do not change suspension travel:
            -- the old deformation formula operates on obsolete flat wheel fields.
            local ratio = TirePressure.PRESSURE_NORMAL / spec.inflationPressure
            physics.frictionScale = math.max(0.01, physics.tpOriginalFrictionScale * ratio)
            physics.isFrictionDirty = true
        end
    end
end
''' + s[end:]
    # Preserve the base vehicle's selection behavior.
    s = s.replace('function TirePressure:getCanBeSelected(superFunc)\n    return true',
                  'function TirePressure:getCanBeSelected(superFunc)\n    return superFunc(self)')
    s = s.replace('if self.isClient then\n        g_soundManager:deleteSamples(spec.samples)',
                  'if self.isClient and spec ~= nil and spec.samples ~= nil then\n        g_soundManager:deleteSamples(spec.samples)')
    path.write_text(s)

def main():
    files = dependency_closure()
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    for p in files:
        q = OUTPUT / p.relative_to(SOURCE)
        q.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, q)
    Image.new('RGBA', (16, 16), (0, 0, 0, 0)).save(OUTPUT / 'Textures/fs25_missing_atlas_transparent.dds')
    shader = SHADER_SOURCE.read_text(encoding='utf-8-sig')
    # GISL's texture-array sample returns float4. The six consumers reported
    # by the actual game compiler are float3; select RGB explicitly.
    shader, swizzles = re.subn(
        r'(tex2DSample\(\s*mArray(?:Specular|Normal|Diffuse),\s*standardMaterialSampler,\s*uvs,\s*(?:aIndex|8|15)\s*\))(?=\s*;)',
        r'\1.xyz', shader)
    assert swizzles == 6, f'Unexpected shader revision: {swizzles} matching assignments'
    for kind in ['specular', 'normal', 'diffuse']:
        shader = shader.replace(f'../shared/detailArray_{kind}.png',
                                f'$data/fs22support/shared/detailArray_{kind}.dds')
    ET.fromstring(shader)
    local_shader = OUTPUT / 'shaders/vehicleShader.xml'
    local_shader.parent.mkdir(parents=True, exist_ok=True)
    # Write text directly to retain shader CDATA and preprocessing exactly.
    local_shader.write_text(shader, encoding='utf-8')
    for p in sorted(OUTPUT.rglob('*')):
        if p.suffix not in {'.xml', '.i3d'}:
            continue
        if p == local_shader:
            continue
        tree = ET.parse(p)
        if p.suffix == '.i3d':
            update_i3d(tree)
        for el in tree.iter():
            for key, value in list(el.attrib.items()):
                if value.startswith('$data/'):
                    mapped = map_resource(value, p)
                    if p.suffix == '.i3d' and mapped == '$data/fs22support/shaders/vehicleShader.xml':
                        mapped = Path(os.path.relpath(local_shader, p.parent)).as_posix()
                    el.set(key, mapped)
                elif 'fs22/vehicle.xsd' in value:
                    el.set(key, value.replace('fs22/vehicle.xsd', 'fs25/vehicle.xsd'))
        if p.name == 'JohnDeere6030.xml':
            tree.find('./storeData/image').text = 'Textures/store_series6x30.dds'
            # The supplied game log confirms the old sound template names no
            # longer exist. Use the installed FS25 John Deere 6M sound set.
            tree.find('./base/sounds').set('filename', '$data/vehicles/johnDeere/series6M/sounds/series6M.xml')
            for unit in tree.findall('./fillUnit/fillUnitConfigurations/fillUnitConfiguration/fillUnits/fillUnit'):
                if unit.get('fillTypes') == 'DIESEL' and unit.find('exactFillRootNode') is None:
                    ET.SubElement(unit, 'exactFillRootNode', node='0>0')
        if p.name == 'modDesc.xml':
            tree.getroot().set('descVersion', '92')
            tree.find('version').text = '0.3.0.0'
            tree.find('iconFilename').text = 'Textures/icon_series6x30.dds'
            for title in tree.findall('./title/*'):
                title.text = 'John Deere 6030 Lights — FS25 Test'
        tree.write(p, encoding='utf-8', xml_declaration=True)
    update_lua(OUTPUT / 'scripts/TirePressure.lua')
    (OUTPUT / 'FS25_TEST_README.txt').write_text('''John Deere 6030 Lights — FS25 compatibility test, v0.3

Fixes the v0.1 loading-script failure and the six float4-to-float3 assignments
reported by the game shader compiler. The corrected shader is included in this
mod; the installed game files are not edited.

NOT VERIFIED IN GIANTS EDITOR OR FARMING SIMULATOR 25.
Put the ZIP, without extracting it, in Documents/My Games/FarmingSimulator2025/mods.
Enable the mod in a test save and buy the tractor. Test headlights, front/rear work
lights, turn indicators, brake lights and HOME-key beacons/light-bar strobes.
Try the light/cab configurations in the shop. Test driving, steering and attachments.
If it fails or lights/materials look wrong, send FarmingSimulator2025/log.txt.

Uses a repaired copy of FS25's FS22 compatibility shader to preserve the original UV material
slots and static light controls. No geometry or scene node ordering was changed.
Unavailable old normal/mask textures use FS25 neutral shared resources. Missing
decorative diffuse atlases are transparent: some decals/detail are absent.
Tyres use FS25 models with matching brand/product and size where available;
two missing Trelleborg TM100 sizes use TM600. Tyre fit still needs game validation.
Legacy dashboard shaders use compatibility static-light materials; dashboard
illumination needs checking. Top arms use FS25 XML assets. Diesel tanks have an
exact fill root at the chassis origin; the refill position needs checking.
TirePressure has been adapted to XMLFile and FS25 Wheel.physics; pressure changes
friction, while the obsolete suspension/deformation adjustment is removed.
Legacy nil/default and vector parsers have been replaced with local helpers;
cleanup tolerates a vehicle that failed to load. The sound set uses FS25 John Deere
6M sounds instead of the missing legacy hydraulic/attachment/horn templates.
InteractiveControl definitions are retained, but require a compatible FS25 IC mod.
Collision conversion, suspension, sound templates, attachments, fuel refilling,
materials, dashboards, physics and multiplayer require engine validation.

Original credits: Udruzenje Nezavisnih Modera, ANO Modding; TirePressure: Wopster.
Original source is retained separately and unchanged.
''', encoding='utf-8')
    report = {'status': 'static_checks_only_engine_validation_pending', 'source_sha256': hashlib.sha256((ROOT / 'source/FS22_JohnDeere_6030_edit.zip').read_bytes()).hexdigest(),
              'included_source_files': len(files), 'resource_changes': changes}
    (ROOT / 'reports/conversion_manifest.json').write_text(json.dumps(report, indent=2))
    archive = OUTPUT.with_suffix('.zip')
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in sorted(OUTPUT.rglob('*')):
            if p.is_file():
                z.write(p, p.relative_to(OUTPUT).as_posix())
    print(json.dumps({'archive': str(archive), 'bytes': archive.stat().st_size, 'included_source_files': len(files), 'resource_changes': len(changes)}))

if __name__ == '__main__':
    main()
