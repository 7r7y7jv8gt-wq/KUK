"""Protect operating hook scale and register the blade with supplied TerraFarm pack."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import xml.etree.ElementTree as E
import shutil,json,sys
HERE=Path(__file__).resolve().parent;OUT=HERE.parent/'FS25_TWinch_v10'
shutil.copytree(HERE.parent/'FS25_TWinch_v09',OUT,dirs_exist_ok=True)
script=(OUT/'scripts/TWinch.lua').read_text().split('-- Single-player blade-mounted logging winch.')[0]+(HERE/'BladeWinch_v10.lua').read_text()
(OUT/'scripts/TWinch.lua').write_text(script)
v=E.parse(OUT/'twinch.xml').getroot();d=E.parse(OUT/'modDesc.xml').getroot()
v.set('type','twinchV10');d.find('vehicleTypes/type').set('name','twinchV10');d.find('version').text='0.10.0.0';d.find('title/en').text='T-Winch v10 - Hook Scale and Engelsen TerraFarm'
for n in v.findall('storeData/name/*'):n.text='T-Winch 30.2 v10'
d.find('description/en').text='Protected small winch hooks with independent pose pivots. Engelsen Anlegg TerraFarm dozer profile adapted to the moving blade edge, 2.23m width. V09 crawler drivetrain and controls retained.'
index=E.parse(OUT/'machineConfigurations.xml').getroot();index.find('configuration').set('vehicle','FS25_TWinch_v10/twinch.xml')
# Adapt uploaded dozer profile; raw offsets reference a different model's
# origin and would displace our precisely mapped cutting-edge work area.
profile=E.parse(OUT/'xml/terraFarmBlade.xml').getroot()
profile.find('machine/input').set('modes','FLATTEN SMOOTH LOWER PAINT')
for tree,name in [(v,'twinch.xml'),(d,'modDesc.xml'),(index,'machineConfigurations.xml'),(profile,'xml/terraFarmBlade.xml')]:
 E.indent(tree);E.ElementTree(tree).write(OUT/name,encoding='utf-8',xml_declaration=True)
source=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/workspace/attachments/d1102834-c1b2-4baa-936f-b75e58444e4a/FS25_0_TerraFarmMachines_Engelsen_Anlegg.zip')
# Filename must retain the original mod name in the user's mods directory.
addon=HERE.parent/'FS25_0_TerraFarmMachines_Engelsen_Anlegg.zip'
with ZipFile(source) as old,ZipFile(addon,'w',ZIP_DEFLATED) as z:
 registry_text=old.read('xml/machineConfigurations.xml').decode('utf-8-sig')
 # Uploaded registry closes the document before its Engelsen entries.
 registry_text=registry_text.replace('</configurations>','',registry_text.count('</configurations>')-1)
 registry=E.fromstring(registry_text)
 registry.text=None
 for entry in registry:entry.tail=None
 E.SubElement(registry,'configuration',vehicle='FS25_TWinch_v10/twinch.xml',file='xml/twinch/Blade.xml')
 desc=E.fromstring(old.read('modDesc.xml'));desc.find('version').text='1.0.0.1'
 for info in old.infolist():
  if info.filename=='xml/machineConfigurations.xml':data=E.tostring(registry,encoding='utf-8',xml_declaration=True)
  elif info.filename=='modDesc.xml':data=E.tostring(desc,encoding='utf-8',xml_declaration=True)
  else:data=old.read(info.filename)
  z.writestr(info.filename,data)
 z.writestr('xml/twinch/Blade.xml',E.tostring(profile,encoding='utf-8',xml_declaration=True))
 z.writestr('TWINCH_ADDITION.txt','Original machine configurations by scfmod / uploaded Engelsen Anlegg pack.\nOnly additions: T-Winch v10 registry entry and adapted blade profile; version 1.0.0.1.\nInstall FS25_0_TerraFarm and FS25_TWinch_v10 separately. Replace the old Engelsen pack.\n')
(OUT/'TESTING.txt').write_text((OUT/'TESTING.txt').read_text().replace('v09','v10')+'\nV10: hook mesh scale .014 is isolated under a pose transform. Carrying,\naiming, docking and extra chains retain the small size. Engelsen pack now\nregisters T-Winch v10. Replace its old ZIP with the companion download.\nFS25 TerraFarm itself remains a separate required mod for terrain work.\n')
(OUT/'CREDITS.txt').write_text((OUT/'CREDITS.txt').read_text()+'Engelsen TerraFarm profile based on uploaded scfmod machine pack; original configurations retained in companion ZIP.\n')
(OUT/'validation.json').write_text(json.dumps({'version':'0.10.0.0','game_test':'not run','hook_mesh_scale':.014,'hook_pose':'independent parent transform','terrafarm':'Engelsen pack registry + moving blade profile'},indent=2)+'\n')
with ZipFile(HERE.parent/'FS25_TWinch_v10.zip','w',ZIP_DEFLATED) as z:
 for f in sorted(OUT.rglob('*')):
  if f.is_file():z.write(f,f.relative_to(OUT))
print('Built T-Winch v10 and patched Engelsen addon')
