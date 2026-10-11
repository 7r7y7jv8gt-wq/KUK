from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import unittest,json,math,xml.etree.ElementTree as E,hashlib
import test_v25 as prior
ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'FS25_Follvik_TVinsj_v29'
prior.OUT=OUT;prior.winches.OUT=OUT;prior.winches.baseline.OUT=OUT;prior.hydraulics.OUT=OUT
class WinchTests(prior.WinchTests):
 def run_lua(self,text):self.lua.execute(text.replace('twinchV13','twinchV29'))
 def test_source_assets_preserved_and_package_valid(self):
  for name,digest in json.loads((OUT/'source_asset_hashes.json').read_text()).items():self.assertEqual(hashlib.sha256((OUT/name).read_bytes()).hexdigest(),digest)
  self.assertEqual(E.parse(OUT/'modDesc.xml').find('version').text,'0.29.0.0')
  with ZipFile(ROOT/'FS25_Follvik_TVinsj_v29.zip') as z:self.assertIsNone(z.testzip())
class ClimbingTests(unittest.TestCase):
 def setUp(self):self.v=E.parse(OUT/'twinch.xml')
 def test_every_contact_powered_and_mass_preserved(self):
  wheels=self.v.findall('wheels/wheelConfigurations/wheelConfiguration/wheels/wheel');self.assertEqual(len(wheels),10)
  physics=[n.find('physics') for n in wheels]
  self.assertAlmostEqual(39680+sum(float(n.get('mass'))*1000 for n in physics),40000)
  self.assertAlmostEqual(sum(float(n.get('restLoad')) for n in physics),39.68)
  d=self.v.findall('motorized/differentialConfigurations/differentialConfiguration/differentials/differential')
  def leaves(index):
   n=d[index-1];out=[]
   for side in ['1','2']:
    if n.get('wheelIndex'+side):out.append(int(n.get('wheelIndex'+side)))
    else:
     child=int(n.get('differentialIndex'+side));self.assertLess(child,index);out+=leaves(child)
   return out
  self.assertEqual(sorted(leaves(len(d))),list(range(1,11)))
  for n in physics:
   self.assertEqual(float(n.get('frictionScale')),6);self.assertEqual(float(n.get('suspTravel')),.3)
   self.assertLess(float(n.get('restLoad'))*9.80665/float(n.get('spring')),float(n.get('suspTravel')))
 def test_low_rpm_torque_improved_without_exceeding_800_hp(self):
  motor=self.v.find('motorized/motorConfigurations/motorConfiguration/motor')
  old=E.parse(ROOT/'FS25_Follvik_TVinsj_v28/twinch.xml').find('motorized/motorConfigurations/motorConfiguration/motor')
  def torque(motor,x):
   points=[(float(n.get('normRpm')),float(n.get('torque'))) for n in motor]
   if x<=points[0][0]:return points[0][1]
   for (a,b),(c,d) in zip(points,points[1:]):
    if x<=c:return b+(d-b)*(x-a)/(c-a)
   return points[-1][1]
  self.assertGreater(torque(motor,.45)/torque(old,.45),1.5)
  scale=float(motor.get('torqueScale'));rpm=float(motor.get('maxRpm'))
  peak=max(scale*torque(motor,i/10000)*(rpm*i/10000)*2*math.pi/60/.73549875 for i in range(3500,10001))
  self.assertAlmostEqual(peak,800,places=3)
  self.assertEqual(motor.get('minRpm'),'1000');self.assertEqual(motor.get('maxForwardSpeed'),'12')
  self.assertEqual(motor.get('maxBackwardSpeed'),'12')
  t=self.v.find('motorized/motorConfigurations/motorConfiguration/transmission')
  self.assertEqual(t.get('maxForwardGearRatio'),'2000');self.assertEqual(t.get('maxBackwardGearRatio'),'2000')
 def test_new_contacts_ground_level_and_mappings_valid(self):
  r=E.parse(OUT/'twinch.i3d');scene=r.find('Scene')
  def resolve(path):
   a,_,b=path.partition('>');n=scene[int(a)]
   for i in b.split('|') if b else []:n=n[int(i)]
   return n
  mappings={n.get('id'):n.get('node') for n in self.v.find('i3dMappings')}
  for path in mappings.values():resolve(path)
  for p in self.v.findall('wheels/wheelConfigurations/wheelConfiguration/wheels/wheel/physics'):
   y=float(resolve(mappings[p.get('repr')]).get('translation').split()[1]);self.assertAlmostEqual(y-float(p.get('radius')),0)
  for p in OUT.rglob('*'):
   if p.suffix in ['.shapes','.dds']:self.assertEqual(p.read_bytes(),(ROOT/'FS25_Follvik_TVinsj_v28'/p.relative_to(OUT)).read_bytes())
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(c) for c in [WinchTests,prior.MouseTests,ClimbingTests]))
 (OUT/'validation.json').write_text(json.dumps({'version':'0.29.0.0','local_tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'game_test':'not run','powered_contacts':10,'suspension_travel_m':.3,'friction_scale':6,'mass_kg':40000,'hp':800,'speed_kmh':12,'minimum_rpm':1000,'max_crawl_ratio':2000},indent=2)+'\n')
 with ZipFile(ROOT/'FS25_Follvik_TVinsj_v29.zip','w',ZIP_DEFLATED) as z:
  for p in sorted(OUT.rglob('*')):
   if p.is_file():z.write(p,p.relative_to(OUT))
 raise SystemExit(not result.wasSuccessful())
