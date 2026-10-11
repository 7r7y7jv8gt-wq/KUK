from pathlib import Path
import shutil,xml.etree.ElementTree as E,json
from zipfile import ZipFile,ZIP_DEFLATED
HERE=Path(__file__).resolve().parent;OUT=HERE.parent/'FS25_TWinch_v17'
shutil.copytree(HERE.parent/'FS25_TWinch_v16',OUT,dirs_exist_ok=True)
p=OUT/'scripts/TWinch.lua';s=p.read_text().replace('twinchV16','twinchV17').replace('function TWinch.onLoad(self, savegame)','function TWinch.onLoad(self, savegame)\n    TWinch.registerTerraFarm(self)')
s+='\n'+(HERE/'TerraFarmRegistration.lua').read_text();p.write_text(s)
v=E.parse(OUT/'twinch.xml').getroot();d=E.parse(OUT/'modDesc.xml').getroot();index=E.parse(OUT/'machineConfigurations.xml').getroot()
v.set('type','twinchV17');d.find('vehicleTypes/type').set('name','twinchV17');d.find('version').text='0.17.0.0';d.find('title/en').text='T-Winch v17 - TerraFarm registration recovery'
for n in v.findall('storeData/name/*'):n.text='T-Winch 30.2 v17'
index.find('configuration').set('vehicle','FS25_TWinch_v17/twinch.xml')
for tree,name in [(v,'twinch.xml'),(d,'modDesc.xml'),(index,'machineConfigurations.xml')]:E.indent(tree);E.ElementTree(tree).write(OUT/name,encoding='utf-8',xml_declaration=True)
(OUT/'TESTING.txt').write_text('V17: enable TerraFarm core and only this T-Winch version. Buy fresh v17.\nDirectly registers the actual vehicle filename before TerraFarm resolves its machine profile.\nCheck log for T-Winch: registered TerraFarm blade profile.\nIf manager unavailable, log reports it; send latest log if TerraFarm is still missing.\nAll blade/winch/light/mass settings retained. FS25 runtime test pending.\n')
(OUT/'validation.json').write_text(json.dumps({'version':'0.17.0.0','game_test':'not run','change':'direct profile registration during vehicle load using actual registry key'},indent=2)+'\n')
with ZipFile(HERE.parent/'FS25_TWinch_v17.zip','w',ZIP_DEFLATED) as z:
 for f in sorted(OUT.rglob('*')):
  if f.is_file():z.write(f,f.relative_to(OUT))
