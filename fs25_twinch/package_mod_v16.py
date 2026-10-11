"""Embed the TerraFarm blade machine definition directly in the vehicle package."""
from pathlib import Path
import shutil,copy,json,xml.etree.ElementTree as E
from zipfile import ZipFile,ZIP_DEFLATED
HERE=Path(__file__).resolve().parent;OUT=HERE.parent/'FS25_TWinch_v16'
shutil.copytree(HERE.parent/'FS25_TWinch_v15',OUT,dirs_exist_ok=True)
v=E.parse(OUT/'twinch.xml').getroot();d=E.parse(OUT/'modDesc.xml').getroot()
profile=E.parse(OUT/'xml/terraFarmBlade.xml').getroot()
machine=profile.find('machine');machine.find('workArea').set('offset','0 0 0')
# TerraFarm can read the actual vehicle definition as well as the included registry.
old=v.find('machine')
if old is not None:v.remove(old)
v.append(copy.deepcopy(machine))
v.set('type','twinchV16');d.find('vehicleTypes/type').set('name','twinchV16');d.find('version').text='0.16.0.0';d.find('title/en').text='T-Winch v16 - TerraFarm blade built in'
d.find('description/en').text='TerraFarm machine definition embedded directly in the vehicle XML, with work area on the moving bottom blade edge. TerraFarm core required; separate Engelsen addon not needed. Rear/front winches, FOR9T lights and 40-tonne configuration retained.'
for n in v.findall('storeData/name/*'):n.text='T-Winch 30.2 v16'
index=E.parse(OUT/'machineConfigurations.xml').getroot();index.find('configuration').set('vehicle','FS25_TWinch_v16/twinch.xml')
p=OUT/'scripts/TWinch.lua';p.write_text(p.read_text().replace('twinchV15','twinchV16'))
for tree,name in [(v,'twinch.xml'),(d,'modDesc.xml'),(profile,'xml/terraFarmBlade.xml'),(index,'machineConfigurations.xml')]:E.indent(tree);E.ElementTree(tree).write(OUT/name,encoding='utf-8',xml_declaration=True)
(OUT/'TESTING.txt').write_text('V16: TerraFarm profile built directly into vehicle XML and included registry.\nNo separate Engelsen addon required for this machine. TerraFarm core must be installed/enabled.\nDisable older T-Winch versions, install unopened ZIP, buy fresh vehicle.\nEnable machine in TerraFarm, start engine, choose mode and lower blade into ground.\nWork area is 2.23m along bottom edge, parented to hydraulic blade.\nFront/rear winches, FOR9T lights and 40-tonne mass retained.\nFS25 runtime testing pending.\n')
(OUT/'validation.json').write_text(json.dumps({'version':'0.16.0.0','game_test':'not run','TerraFarm':'embedded vehicle machine + matching internal profile/registry','separate_machine_addon_required':False,'TerraFarm_core_required':True},indent=2)+'\n')
with ZipFile(HERE.parent/'FS25_TWinch_v16.zip','w',ZIP_DEFLATED) as z:
 for f in sorted(OUT.rglob('*')):
  if f.is_file():z.write(f,f.relative_to(OUT))
print('Built',OUT)
