"""Repair the uploaded Engelsen registry and register the v15 moving blade edge."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import xml.etree.ElementTree as E
import json,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
source=Path(sys.argv[1]) if len(sys.argv)>1 else HERE/'user_engelsen_v15.zip'
out=ROOT/'FS25_0_TerraFarmMachines_Engelsen_Anlegg_TWinch_v15.zip'
with ZipFile(source) as z:files={n:z.read(n) for n in z.namelist() if not n.endswith('/')}
key='xml/machineConfigurations.xml';text=files[key].decode('utf-8-sig')
# Retain the last closing tag; earlier closing tags incorrectly terminate root.
last=text.rfind('</configurations>');fixed=text[:last].replace('</configurations>','')+text[last:]
r=E.fromstring(fixed);original=len(r.findall('configuration'))
for n in list(r):
 if n.get('vehicle')=='FS25_TWinch_v15/twinch.xml':r.remove(n)
E.SubElement(r,'configuration',vehicle='FS25_TWinch_v15/twinch.xml',file='xml/TWinch/terraFarmBlade.xml')
def xml_bytes(root):E.indent(root);return E.tostring(root,encoding='utf-8',xml_declaration=True)
files[key]=xml_bytes(r)
# Identical profile to the vehicle's own registry avoids conflicting definitions.
files['xml/TWinch/terraFarmBlade.xml']=(ROOT/'FS25_TWinch_v15/xml/terraFarmBlade.xml').read_bytes()
d=E.fromstring(files['modDesc.xml']);d.find('version').text='1.0.0.15';d.find('title/en').text='TerraFarm - Engelsen Anlegg + T-Winch v15';files['modDesc.xml']=xml_bytes(d)
files['TWINCH_INSTALL.txt']=('Replace the previous Engelsen addon with this unopened ZIP; do not enable both.\nKeep FS25_0_TerraFarm installed separately and enable it in the save.\nUse FS25_TWinch_v15.zip with its original filename, unopened; disable earlier T-Winch versions.\nEnable the machine in TerraFarm, start engine, choose terrain mode and lower blade to ground.\nThe work area is the 2.23m moving lower blade edge, not the rear winch or chassis.\nThe repaired registry preserves the original Engelsen entries and adds v15.\nConfiguring an addon does not install the TerraFarm core. Actual FS25 operation untested.\n').encode()
files['TWINCH_VALIDATION.json']=json.dumps({'original_registry_entries':original,'vehicle':'FS25_TWinch_v15/twinch.xml','reference_node':'terraFarmBladeEdge','width_m':2.23,'game_test':'not run'},indent=2).encode()
with ZipFile(out,'w',ZIP_DEFLATED) as z:
 for name,data in sorted(files.items()):z.writestr(name,data)
print(out)
