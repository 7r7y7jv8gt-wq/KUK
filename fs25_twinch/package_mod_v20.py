from pathlib import Path
import shutil,xml.etree.ElementTree as E,json
from zipfile import ZipFile,ZIP_DEFLATED
HERE=Path(__file__).resolve().parent;OUT=HERE.parent/'FS25_TWinch_v20'
shutil.copytree(HERE.parent/'FS25_TWinch_v19',OUT,dirs_exist_ok=True)
p=OUT/'scripts/TWinch.lua';s=p.read_text().replace('twinchV19','twinchV20')
s=s.replace('TWinch.MOD_NAME = g_currentModName','TWinch.MOD_NAME = g_currentModName\nTWinch.MOD_DIRECTORY = g_currentModDirectory')
s=s.replace('    TWinch.registerTerraFarm(self)\n','')
s=s.replace('    self.spec_twinch = spec','''    self.spec_twinch = spec
    local ok,err=pcall(TWinch.registerTerraFarm,self)
    if not ok and Logging~=nil then Logging.warning('T-Winch: TerraFarm registration failed; continuing vehicle load: %s',tostring(err)) end''',1)
s=s.replace('    local directory=g_currentModDirectory','''    local directory=vehicle.baseDirectory or TWinch.MOD_DIRECTORY or g_currentModDirectory
    if directory==nil or directory=='' then
        if Logging~=nil then Logging.warning('T-Winch: TerraFarm profile base directory unavailable') end
        return false
    end''')
for name,args in [('onUpdate','self, dt'),('onUpdateTick','self, dt'),('onDelete','self'),('onRegisterActionEvents','self, isActiveForInput, isActiveForInputIgnoreSelection')]:
 s=s.replace(f'function TWinch.{name}({args})',f'function TWinch.{name}({args})\n    if self.spec_twinch==nil then return end')
p.write_text(s)
v=E.parse(OUT/'twinch.xml').getroot();d=E.parse(OUT/'modDesc.xml').getroot();index=E.parse(OUT/'machineConfigurations.xml').getroot()
v.set('type','twinchV20');d.find('vehicleTypes/type').set('name','twinchV20');d.find('version').text='0.20.0.0';d.find('title/en').text='T-Winch v20 - Purchase loading fix'
for n in v.findall('storeData/name/*'):n.text='T-Winch 30.2 v20'
index.find('configuration').set('vehicle','FS25_TWinch_v20/twinch.xml')
for tree,name in [(v,'twinch.xml'),(d,'modDesc.xml'),(index,'machineConfigurations.xml')]:E.indent(tree);E.ElementTree(tree).write(OUT/name,encoding='utf-8',xml_declaration=True)
(OUT/'TESTING.txt').write_text('V20: fixes purchase crash caused by runtime g_currentModDirectory=nil.\nUses vehicle.baseDirectory/captured mod directory; registration failures cannot abort load.\nDisable earlier T-Winch versions, restart FS25 and install unopened v20 ZIP.\n800hp, 12km/h, 40 tonnes, winches, lights and TerraFarm profile retained.\nGame purchase confirmation still requires FS25 testing.\n')
(OUT/'validation.json').write_text(json.dumps({'version':'0.20.0.0','game_test':'not run','fix':'stable profile base path and non-fatal TerraFarm registration'},indent=2)+'\n')
with ZipFile(HERE.parent/'FS25_TWinch_v20.zip','w',ZIP_DEFLATED) as z:
 for f in sorted(OUT.rglob('*')):
  if f.is_file():z.write(f,f.relative_to(OUT))
