"""Repair walk-up winch input lifecycle and expose hydraulic blade assemblies."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import shutil,xml.etree.ElementTree as E,json
HERE=Path(__file__).resolve().parent;OUT=HERE.parent/'FS25_TWinch_v12'
shutil.copytree(HERE.parent/'FS25_TWinch_v11',OUT,dirs_exist_ok=True)
old=(OUT/'scripts/TWinch.lua').read_text()
prefix=old.split('-- Single-player blade-mounted logging winch.')[0]
native=old[old.index('-- Add native crawler support exactly once'):].replace('twinchV11','twinchV12')
prefix=prefix.replace('    TWinch.updateTracks(self)\n    local spec=self.spec_twinch','    BladeWinch.update(BladeWinch,dt)\n    TWinch.updateTracks(self)\n    local spec=self.spec_twinch',1)
# Keep hydraulics functional if automatic engine stop has shut down the motor.
prefix=prefix.replace('function TWinch.actionBlade(self,actionName,value,callbackState,isAnalog,isMouse)', 'function TWinch.actionBlade(self,actionName,value,callbackState,isAnalog,isMouse)\n    if value~=0 and self.startMotor~=nil and not self:getIsMotorStarted() then self:startMotor() end')
script=prefix+(HERE/'BladeWinch_v12.lua').read_text()+'\n'+native
# Distinct new bindings avoid stale custom action entries from previous builds.
for name in ['TWINCH_HOOK','TWINCH_LOG_REEL','TWINCH_LOG_FAST','TWINCH_LOG_OUT','TWINCH_LOG_CLEAR']:
 script=script.replace("'"+name+"'","'"+name+"_V12'")
(OUT/'scripts/TWinch.lua').write_text(script)
v=E.parse(OUT/'twinch.xml').getroot();d=E.parse(OUT/'modDesc.xml').getroot();r=E.parse(OUT/'twinch.i3d').getroot()
for n in r.find('Scene').iter():
 name=n.get('name','')
 if 'hydraulic' in name or 'Hydraulic' in name or 'Clevis' in name or 'PivotPin' in name:n.set('visibility','true')
# 39,680 kg component + four 80 kg support wheels = 40,000 kg.
v.find('base/components/component').set('mass','39680')
r.find('Scene')[0].set('mass','39680')
for physics in v.findall('wheels/wheelConfigurations/wheelConfiguration/wheels/wheel/physics'):
 physics.set('restLoad','9.92');physics.set('spring','1587.2');physics.set('damper','198.4')
v.set('type','twinchV12');d.find('vehicleTypes/type').set('name','twinchV12');d.find('version').text='0.12.0.0';d.find('title/en').text='T-Winch v12 - Walk-up Winch and Blade Hydraulics'
for n in v.findall('storeData/name/*'):n.text='T-Winch 30.2 v12'
d.find('description/en').text='Player-root proximity, fresh on-foot bindings and player-context registration recovery for the R winch prompt. Both hydraulic blade cylinders, chrome rods, pins and hoses explicitly visible; blade input can start the engine. Volvo shoes retained; a full Volvo drivetrain needs its main model.'
for n in d.find('actions'):
 if n.get('name') in ['TWINCH_HOOK','TWINCH_LOG_REEL','TWINCH_LOG_FAST','TWINCH_LOG_OUT','TWINCH_LOG_CLEAR']:n.set('name',n.get('name')+'_V12')
for n in d.find('inputBinding'):
 if n.get('action') in ['TWINCH_HOOK','TWINCH_LOG_REEL','TWINCH_LOG_FAST','TWINCH_LOG_OUT','TWINCH_LOG_CLEAR']:n.set('action',n.get('action')+'_V12')
for n in d.find('l10n'):
 if n.get('name') in ['input_TWINCH_HOOK','input_TWINCH_LOG_REEL','input_TWINCH_LOG_FAST','input_TWINCH_LOG_OUT','input_TWINCH_LOG_CLEAR']:n.set('name',n.get('name')+'_V12')
index=E.parse(OUT/'machineConfigurations.xml').getroot();index.find('configuration').set('vehicle','FS25_TWinch_v12/twinch.xml')
for tree,name in [(v,'twinch.xml'),(d,'modDesc.xml'),(r,'twinch.i3d'),(index,'machineConfigurations.xml')]:E.indent(tree);E.ElementTree(tree).write(OUT/name,encoding='utf-8',xml_declaration=True)
(OUT/'TESTING.txt').write_text('''V12: walk-up winch and hydraulic blade
Disable earlier T-Winch mods. Install unopened v12 ZIP; purchase a fresh v12.
Walk within 3m horizontally of the blade: R should show Take winch hook.
Press R, look at tree/log within 4m, press R. Hold Z to pull, X to pay out,
Shift+R release. Reeling can start the engine; wait for normal engine start.
Both blade cylinders/rods/pins/hoses are explicitly visible. In the vehicle:
Page Up raises, Page Down lowers; left mouse + vertical drag controls blade.
Blade input can start the engine, and waits for normal engine start.
Fresh V12 on-foot action names avoid old input entries. Events are deferred
until the player context is active, retried on failures and refreshed when
player inputs are rebuilt. Player-root proximity avoids tool-hand offsets.
Native Volvo shoes are unchanged. Uploaded crawler assets do not contain
Volvo drivetrain geometry: that transfer still requires the main Volvo model.
Local checks are not FS25 tests. Supply latest log if R remains missing.
''')
(OUT/'validation.json').write_text(json.dumps({'version':'0.12.0.0','game_test':'not run','proximity':'player root/camera, 3m horizontal','input':'player context refresh + atomic retry + fresh V12 names','hydraulics':'two exposed cylinders, rods, clevises, pins and hoses; explicit controller','volvo_drivetrain':'not supplied in crawler files','component_mass_kg':39680,'support_wheel_mass_kg':320,'total_mass_kg':40000},indent=2)+'\n')
with ZipFile(HERE.parent/'FS25_TWinch_v12.zip','w',ZIP_DEFLATED) as z:
 for f in sorted(OUT.rglob('*')):
  if f.is_file():z.write(f,f.relative_to(OUT))
print('Built',OUT)
