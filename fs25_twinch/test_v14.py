from pathlib import Path
import unittest,xml.etree.ElementTree as E,hashlib
from zipfile import ZipFile,ZIP_DEFLATED
import json
ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'FS25_TWinch_v14'
class LightsTests(unittest.TestCase):
 def setUp(self):
  self.r=E.parse(OUT/'twinch.i3d').getroot();self.v=E.parse(OUT/'twinch.xml').getroot();self.maps={n.get('id'):n.get('node') for n in self.v.find('i3dMappings')}
 def resolve(self,name):
  a,_,b=self.maps.get(name,name).partition('>');n=self.r.find('Scene')[int(a)]
  for i in b.split('|') if b else []:n=n[int(i)]
  return n
 def test_preserves_user_model_geometry_and_positions(self):
  user=ROOT/'fs25_twinch/user_for9t'
  self.assertEqual(hashlib.sha256((user/'twinch.i3d.shapes').read_bytes()).digest(),hashlib.sha256((OUT/'twinch.i3d.shapes').read_bytes()).digest())
  def locations(root):return [(n.get('translation'),n.get('rotation')) for n in root.find('Scene').iter() if n.get('name')=='FOR9T_noGlare']
  self.assertEqual(locations(self.r),locations(E.parse(user/'twinch.i3d').getroot()));self.assertEqual(len(locations(self.r)),8)
 def test_eight_red_drls_and_no_white_or_orange(self):
  lights=self.v.findall('lights/dayTimeLights/dayTimeLight');self.assertEqual(len(lights),8)
  for n in lights:
   node=self.resolve(n.get('node'));self.assertEqual(node.get('name'),'DRL_red');self.assertEqual(node.get('visibility'),'true')
  for n in self.r.find('Scene').iter():
   if n.get('name') in ['DRL_white','DRL_orange']:self.assertEqual(n.get('visibility'),'false')
 def test_work_lenses_and_beams_match_front_rear_states(self):
  self.assertEqual([n.get('lightTypes') for n in self.v.findall('lights/states/state')],['0','0 1'])
  lenses=self.v.findall('lights/staticLights/staticLight');self.assertEqual(len(lenses),8)
  for n in lenses:self.assertEqual(self.resolve(n.get('node')).get('name'),'static')
  for level in ['low','high']:
   beams=self.v.findall('lights/realLights/'+level+'/light');self.assertEqual(len(beams),8)
   self.assertEqual([n.get('lightTypes') for n in beams],[n.get('lightTypes') for n in lenses])
   for n in beams:self.assertEqual(self.resolve(n.get('node')).tag,'Light')
 def test_assets_mappings_and_retained_mass_controls(self):
  for path in self.maps:self.resolve(path)
  for n in self.r.find('Files'):
   f=n.get('filename')
   if not f.startswith('$'):self.assertTrue((OUT/f).is_file(),f)
  self.assertEqual(self.v.find('base/components/component').get('mass'),'39680')
  self.assertIsNotNone(self.v.find('twinch/blade'))
  script=(OUT/'scripts/TWinch.lua').read_text();self.assertIn('TWINCH_BLADE_RAISE_V13',script);self.assertIn('function W.drawWinch',script)
 def test_complete_installable_zip(self):
  with ZipFile(ROOT/'FS25_TWinch_v14.zip') as z:
   self.assertIsNone(z.testzip())
   for f in ['modDesc.xml','twinch.xml','twinch.i3d.shapes','scripts/TWinch.lua','prefabs/FS25_LizardFOR9T_prefab/FOR9T_emissive.dds']:self.assertIn(f,z.namelist())
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(LightsTests))
 report=json.loads((OUT/'validation.json').read_text());report.update(local_tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors));(OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
 with ZipFile(ROOT/'FS25_TWinch_v14.zip','w',ZIP_DEFLATED) as z:
  for f in sorted(OUT.rglob('*')):
   if f.is_file():z.write(f,f.relative_to(OUT))
 raise SystemExit(not result.wasSuccessful())
