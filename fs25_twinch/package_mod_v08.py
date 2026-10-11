"""Blade-mounted on-foot logging winch, preserving the v07 blade/track setup."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import shutil, xml.etree.ElementTree as E, copy, json
HERE=Path(__file__).resolve().parent; OUT=HERE.parent/'FS25_TWinch_v08'
shutil.copytree(HERE.parent/'FS25_TWinch_v07',OUT,dirs_exist_ok=True)
source=Path('/tmp/tajfun-inspect')
asset=OUT/'winch';asset.mkdir(exist_ok=True)
for name in ['chainMaterialHolder.i3d','chainMaterialHolder.i3d.shapes','shaders/winchChainShader.xml','textures/chain_diffuse.dds','textures/chain_normal.dds','textures/chain_vmask.dds','textures/tajfunEGV80_decal_normal.dds','textures/tajfunEGV80_decal_vmask.dds','sounds/chainAttach.ogg','sounds/chainDetach.ogg','sounds/transmissionOld.ogg']:
    target=asset/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source/name,target)
scene=E.parse(asset/'chainMaterialHolder.i3d').getroot()
scene.remove(scene.find('UserAttributes')) # Private holder, no global tension-belt registration.
E.indent(scene);E.ElementTree(scene).write(asset/'chainMaterialHolder.i3d',encoding='utf-8',xml_declaration=True)
script=(OUT/'scripts/TWinch.lua').read_text().replace('TWinch.loadBlade(self,savegame)','TWinch.loadBlade(self,savegame)\n    BladeWinch.load(self)').replace('TWinch.updateWinch(self,dt) end','TWinch.updateWinch(self,dt); BladeWinch.tick(self,dt) end').replace('function TWinch.onDelete(self)\n    TWinch.disconnect(self)','function TWinch.onDelete(self)\n    BladeWinch.delete(self)\n    TWinch.disconnect(self)')
script=script.replace('schema:setXMLSpecializationType()','for _,name in ipairs({\"winching\",\"chainAttach\",\"chainDetach\"}) do SoundManager.registerSampleXMLPaths(schema,\"vehicle.twinch.logging.sounds\",name) end\n    schema:setXMLSpecializationType()')
script+='\n'+(HERE/'BladeWinch.lua').read_text()
(OUT/'scripts/TWinch.lua').write_text(script)
v=E.parse(OUT/'twinch.xml').getroot();d=E.parse(OUT/'modDesc.xml').getroot()
v.set('type','twinchV08');d.find('vehicleTypes/type').set('name','twinchV08');d.find('version').text='0.8.0.0'
d.find('title/en').text='T-Winch v08 - Walk-up Blade Winch'
for n in v.findall('storeData/name/*'):n.text='T-Winch 30.2 v08'
v.find('annotation').text='v08: single-player blade winch; R take / attach hook, Z reel, Shift+Z fast, X payout, Shift+R release. Actual engine validation pending.'
d.find('description/en').text='Walk up to the blade and press R to take the hook. Look at a tree, log or movable object and press R to attach. Hold Z to winch, Shift+Z fast, X to pay out. Shift+R releases all. Up to eight logs / eight tonnes, 60m cable; a standing tree acts as a fixed recovery anchor. Blade and tracks retained from v07.'
for name,key,text in [('TWINCH_HOOK','KEY_r','Take / attach winch hook'),('TWINCH_LOG_REEL','KEY_z','Winch: hold to reel'),('TWINCH_LOG_FAST','KEY_lshift KEY_z','Winch: hold to reel fast'),('TWINCH_LOG_OUT','KEY_x','Winch: hold to pay out'),('TWINCH_LOG_CLEAR','KEY_lshift KEY_r','Winch: release all / return hook')]:
    E.SubElement(d.find('actions'),'action',name=name,axisType='HALF')
    binding=E.SubElement(d.find('inputBinding'),'actionBinding',action=name)
    E.SubElement(binding,'binding',device='KB_MOUSE_DEFAULT',input=key)
    E.SubElement(E.SubElement(d.find('l10n'),'text',name='input_'+name),'en').text=text
logging=E.SubElement(v.find('twinch'),'logging');sounds=E.SubElement(logging,'sounds')
original=E.parse(source/'tajfunEGV80AHK.xml').getroot().find('logsWinch/sounds')
for n in original:
    n=copy.deepcopy(n);n.set('file','winch/'+n.get('file'))
    for parent in n.iter():
        for modifier in list(parent.findall('modifier')):parent.remove(modifier)
    sounds.append(n)
# TerraFarm's documented external configuration discovery adds its own machine
# specialization only when TerraFarm is installed. Native Leveler requires the
# existing inherited FillUnit; material unit is separate from fuel (index 1).
E.SubElement(d.find('vehicleTypes/type'),'specialization',name='leveler')
i=E.parse(OUT/'twinch.i3d').getroot();component=i.find('Scene')[0]
blade=next(n for n in component.iter() if n.get('name')=='bladeLift')
node_id=str(max(int(n.get('nodeId','0')) for n in i.find('Scene').iter())+1)
E.SubElement(blade,'TransformGroup',name='terraFarmBladeEdge',nodeId=node_id,translation='0 -0.605 0.9375')
def node_path(root,target,prefix):
    if root is target:return prefix
    for idx,child in enumerate(root):
        result=node_path(child,target,prefix+('' if prefix.endswith('>') else '|')+str(idx))
        if result:return result
edge=blade[-1]
E.SubElement(v.find('i3dMappings'),'i3dMapping',id='terraFarmBladeEdge',node=node_path(component,edge,'0>'))
E.indent(i);E.ElementTree(i).write(OUT/'twinch.i3d',encoding='utf-8',xml_declaration=True)
units=v.find('fillUnit/fillUnitConfigurations/fillUnitConfiguration/fillUnits')
unit=E.SubElement(units,'fillUnit',capacity='2500',fillTypeCategories='bulk',showOnHud='false',showInShop='false',updateMass='false')
E.SubElement(unit,'exactFillRootNode',node='terraFarmBladeEdge')
leveler=E.SubElement(v,'leveler',fillUnitIndex='2')
E.SubElement(leveler,'levelerNode',node='terraFarmBladeEdge',width='2.23',fillUnitIndex='2',alignToWorldY='true')
config=E.Element('configurations')
E.SubElement(config,'configuration',vehicle='FS25_TWinch_v08/twinch.xml',file='xml/terraFarmBlade.xml')
machine_file=E.Element('vehicle');machine=E.SubElement(machine_file,'machine',type='leveler',fillUnitIndex='2',requirePoweredOn='true')
E.SubElement(machine,'input',modes='FLATTEN SMOOTH LOWER PAINT')
E.SubElement(machine,'workArea',referenceNode='terraFarmBladeEdge',width='2.23',density='0.3',raycastDistance='0.15')
E.SubElement(E.SubElement(machine,'updateCollisionNodes'),'updateNode',node='bladeCollision')
(OUT/'xml').mkdir(exist_ok=True)
for tree,name in [(config,'machineConfigurations.xml'),(machine_file,'xml/terraFarmBlade.xml')]:
    E.indent(tree);E.ElementTree(tree).write(OUT/name,encoding='utf-8',xml_declaration=True)

for tree,name in [(v,'twinch.xml'),(d,'modDesc.xml')]:
    E.indent(tree);E.ElementTree(tree).write(OUT/name,encoding='utf-8',xml_declaration=True)
(OUT/'CREDITS.txt').write_text('Original T-Winch integration code: this project.\nHook mesh, chain DDS textures, winchChainShader.xml and chain/winch sounds: 50keda, supplied FS25_TajfunEGV80AHK v1.0.0.0.\nTajfun physical winch body and vehicle XML/scripts are not distributed in this package.\n')
(OUT/'TESTING.txt').write_text('''T-Winch v08 - single-player blade logging / anchor winch
Disable older T-Winch packages and purchase the v08 in a test save.
Start the engine, leave the vehicle and walk within 2.5m of the blade.
R takes the hook. Walk to a tree/log/object, aim at it (within 4m), press R.
Hold Z to reel, Shift+Z for fast reeling; hold X to pay out. Shift+R returns
hook / disconnects everything. Remote controls work within 60m of the blade.
A standing tree pulls the machine toward the fixed anchor; a dynamic log or
object is pulled toward the machine. Rope force has an equal chassis reaction.
R beside the blade after attachment takes an additional chain (up to eight
objects, eight tonnes total). Extra objects must be within 15m of the first.
Fixed tree anchors are used alone. Invalid/deleted targets disconnect safely.
Hook and wrapped chain assets come from the supplied 50keda Tajfun mod;
no physical Tajfun winch is included. Parked interaction is updated globally,
separately from vehicle selection. On-foot actions use the player input context.
The old Ctrl+B vehicle recovery mode is exclusive with the logging mode.
Reeling requires a running engine. Attachments are temporary, not saved.
No multiplayer support. Install FS25_0_TerraFarm separately for terrain deformation. The external
machine configuration provides FLATTEN, SMOOTH, LOWER and PAINT on the 2.23m
cutting edge. Enable the machine in TerraFarm, choose a mode, then lower the
blade. Work nodes follow the hydraulic blade. TerraFarm handles land access
and terrain costs. Keep the ZIP filename FS25_TWinch_v08.zip for discovery.
The force model is bounded,
not a port of Tajfun's PTO / implement joints or every attachment feature.
Packaged Lua and asset checks run locally; actual FS25 play testing is pending.
''')
(OUT/'validation.json').write_text(json.dumps({'version':'0.8.0.0','game_test':'not run','max_rope_metres':60,'max_log_tonnes':8,'max_objects':8},indent=2)+'\n')
with ZipFile(HERE.parent/'FS25_TWinch_v08.zip','w',ZIP_DEFLATED) as z:
    for f in sorted(OUT.rglob('*')):
        if f.is_file():z.write(f,f.relative_to(OUT))
print('Built',OUT)
