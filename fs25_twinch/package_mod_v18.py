"""Set actual peak engine power and store specification to 800 metric hp."""
from pathlib import Path
import shutil,xml.etree.ElementTree as E,json,math
from zipfile import ZipFile,ZIP_DEFLATED
HERE=Path(__file__).resolve().parent;OUT=HERE.parent/'FS25_TWinch_v18'
shutil.copytree(HERE.parent/'FS25_TWinch_v17',OUT,dirs_exist_ok=True)
v=E.parse(OUT/'twinch.xml').getroot();d=E.parse(OUT/'modDesc.xml').getroot();index=E.parse(OUT/'machineConfigurations.xml').getroot()
v.set('type','twinchV18');d.find('vehicleTypes/type').set('name','twinchV18');d.find('version').text='0.18.0.0';d.find('title/en').text='T-Winch v18 - 800 hp and TerraFarm blade'
v.find('storeData/specs/power').text='800'
for n in v.findall('storeData/name/*'):n.text='T-Winch 30.2 v18'
config=v.find('motorized/motorConfigurations/motorConfiguration');config.set('name','800 hp');config.set('hp','800');motor=config.find('motor')
# Peak of retained piecewise-linear torque curve: normRpm .8 * torque .95.
scale=(800*.73549875)/(.8*.95*float(motor.get('maxRpm'))*math.pi/30)
motor.set('torqueScale',f'{scale:.9f}')
index.find('configuration').set('vehicle','FS25_TWinch_v18/twinch.xml')
p=OUT/'scripts/TWinch.lua';p.write_text(p.read_text().replace('twinchV17','twinchV18'))
for tree,name in [(v,'twinch.xml'),(d,'modDesc.xml'),(index,'machineConfigurations.xml')]:E.indent(tree);E.ElementTree(tree).write(OUT/name,encoding='utf-8',xml_declaration=True)
(OUT/'TESTING.txt').write_text((OUT/'TESTING.txt').read_text().replace('V17','V18').replace('v17','v18')+'\nEngine: 800 metric hp peak (588.399kW); shop power 800 hp.\n')
(OUT/'validation.json').write_text(json.dumps({'version':'0.18.0.0','game_test':'not run','peak_hp':800,'peak_kw':588.399,'torque_scale':scale,'TerraFarm':'v17 direct registration retained'},indent=2)+'\n')
with ZipFile(HERE.parent/'FS25_TWinch_v18.zip','w',ZIP_DEFLATED) as z:
 for f in sorted(OUT.rglob('*')):
  if f.is_file():z.write(f,f.relative_to(OUT))
print('800 hp torqueScale',scale)
