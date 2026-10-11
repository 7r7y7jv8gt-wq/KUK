import unittest,xml.etree.ElementTree as E
from zipfile import ZipFile
from pathlib import Path
import test_v15 as prior
ROOT=Path(__file__).resolve().parent.parent
class AddonTests(unittest.TestCase):
 def test_registry_xml_and_original_assets(self):
  with ZipFile(ROOT/'FS25_0_TerraFarmMachines_Engelsen_Anlegg_TWinch_v15.zip') as z,ZipFile(ROOT/'fs25_twinch/user_engelsen_v15.zip') as src:
   self.assertIsNone(z.testzip())
   for n in z.namelist():
    if n.endswith('.xml'):E.fromstring(z.read(n))
   for n in src.namelist():
    if not n.endswith('/') and n not in ['modDesc.xml','xml/machineConfigurations.xml']:self.assertEqual(z.read(n),src.read(n))
   entries=E.fromstring(z.read('xml/machineConfigurations.xml')).findall('configuration')
   self.assertEqual(len([n for n in entries if n.get('vehicle')=='FS25_TWinch_v15/twinch.xml']),1)
   self.assertEqual(z.read('xml/TWinch/terraFarmBlade.xml'),(ROOT/'FS25_TWinch_v15/xml/terraFarmBlade.xml').read_bytes())
 def test_work_reference_is_on_lower_blade(self):
  v=E.parse(ROOT/'FS25_TWinch_v15/twinch.xml');r=E.parse(ROOT/'FS25_TWinch_v15/twinch.i3d')
  path=v.find("i3dMappings/i3dMapping[@id='terraFarmBladeEdge']").get('node');a,_,b=path.partition('>');n=r.find('Scene')[int(a)];parent=None
  for i in b.split('|'):parent=n;n=n[int(i)]
  self.assertEqual(parent.get('name'),'bladeLift');self.assertEqual(n.get('translation'),'0 -0.605 0.9375')
if __name__=='__main__':
 suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(AddonTests),prior.WinchTests('test_terrafarm_actual_work_area_follows_lowered_blade')])
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 raise SystemExit(not result.wasSuccessful())
