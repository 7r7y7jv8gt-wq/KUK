from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import unittest,json,math,xml.etree.ElementTree as E,hashlib
import test_v25 as prior
ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'FS25_Follvik_TVinsj_v28'
prior.OUT=OUT;prior.winches.OUT=OUT;prior.winches.baseline.OUT=OUT;prior.hydraulics.OUT=OUT
class WinchTests(prior.WinchTests):
 def run_lua(self,text):self.lua.execute(text.replace('twinchV13','twinchV28'))
 def test_source_assets_preserved_and_package_valid(self):
  for name,digest in json.loads((OUT/'source_asset_hashes.json').read_text()).items():self.assertEqual(hashlib.sha256((OUT/name).read_bytes()).hexdigest(),digest)
  self.assertEqual(E.parse(OUT/'modDesc.xml').find('version').text,'0.28.0.0')
  with ZipFile(ROOT/'FS25_Follvik_TVinsj_v28.zip') as z:self.assertIsNone(z.testzip())
class TerrainTests(unittest.TestCase):
 def setUp(self):
  self.v=E.parse(OUT/'twinch.xml');self.scene=E.parse(OUT/'twinch.i3d').find('Scene')
 def resolve(self,path):
  a,_,b=path.partition('>');n=self.scene[int(a)]
  for i in b.split('|') if b else []:n=n[int(i)]
  return n
 def test_contact_mass_load_and_drivetrain_connectivity(self):
  wheels=self.v.findall('wheels/wheelConfigurations/wheelConfiguration/wheels/wheel');self.assertEqual(len(wheels),6)
  physics=[n.find('physics') for n in wheels]
  self.assertAlmostEqual(39680+1000*sum(float(p.get('mass')) for p in physics),40000)
  self.assertAlmostEqual(sum(float(p.get('restLoad')) for p in physics),39.68)
  diff=self.v.findall('motorized/differentialConfigurations/differentialConfiguration/differentials/differential')
  def leaves(i):
   node=diff[i-1];result=[]
   for side in ['1','2']:
    if node.get('wheelIndex'+side):result.append(int(node.get('wheelIndex'+side)))
    else:
     child=int(node.get('differentialIndex'+side));self.assertLess(child,i);result+=leaves(child)
   return result
  self.assertEqual(sorted(leaves(5)),[1,2,3,4,5,6])
  for p in physics:
   self.assertEqual(float(p.get('suspTravel')),.18);self.assertEqual(float(p.get('frictionScale')),3)
   self.assertLess(float(p.get('restLoad'))*9.80665/float(p.get('spring')),float(p.get('suspTravel')))
 def test_original_mappings_assets_and_new_contacts(self):
  old=E.parse(ROOT/'FS25_Follvik_TVinsj_v27/twinch.xml');oldScene=E.parse(ROOT/'FS25_Follvik_TVinsj_v27/twinch.i3d').find('Scene')
  new={m.get('id'):m.get('node') for m in self.v.find('i3dMappings')}
  for m in old.find('i3dMappings'):self.assertEqual(new[m.get('id')],m.get('node'))
  for m in self.v.find('i3dMappings'):self.resolve(m.get('node'))
  for side,sign in [('Left',1),('Right',-1)]:
   n=self.resolve(new['middle'+side]);x,y,z=map(float,n.get('translation').split());self.assertEqual(x,sign*1.1);self.assertEqual(y,.415)
  for p in OUT.rglob('*'):
   if p.suffix in ['.shapes','.dds']:self.assertEqual(p.read_bytes(),(ROOT/'FS25_Follvik_TVinsj_v27'/p.relative_to(OUT)).read_bytes())
 def test_power_speed_gearing_stability_and_logo(self):
  motor=self.v.find('motorized/motorConfigurations/motorConfiguration/motor');scale=float(motor.get('torqueScale'));maxrpm=float(motor.get('maxRpm'))
  hp=max(scale*float(n.get('torque'))*(maxrpm*float(n.get('normRpm')))*2*math.pi/60/.73549875 for n in motor)
  self.assertAlmostEqual(hp,800,places=3);self.assertEqual(motor.get('maxForwardSpeed'),'12');self.assertEqual(motor.get('maxBackwardSpeed'),'12')
  self.assertEqual(self.v.find('base/components/component').get('centerOfMass'),'0 .4 -.1')
  trans=self.v.find('motorized/motorConfigurations/motorConfiguration/transmission')
  self.assertEqual(trans.get('maxForwardGearRatio'),'420');self.assertEqual(trans.get('minForwardGearRatio'),'28')
  # High range reaches the requested governed speed; low range gives crawl torque.
  radius=.415;speed=maxrpm*2*math.pi/60*radius/28*3.6
  self.assertGreater(speed,12)
  self.assertEqual(self.v.getroot().get('type'),'twinchV28')
  blade=next(n for n in self.scene.iter() if n.get('name')=='bladeLift')
  self.assertTrue(any(n.get('nodeId')=='665' for n in blade))
  r=E.parse(OUT/'twinch.i3d');self.assertEqual(r.find("Materials/Material[@materialId='3647']").get('alphaBlending'),'true')
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(c) for c in [WinchTests,prior.MouseTests,TerrainTests]))
 (OUT/'validation.json').write_text(json.dumps({'version':'0.28.0.0','local_tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'game_test':'not run','powered_contacts':6,'suspension_travel_m':.18,'friction_scale':3,'mass_kg':40000,'hp':800,'speed_kmh':12},indent=2)+'\n')
 with ZipFile(ROOT/'FS25_Follvik_TVinsj_v28.zip','w',ZIP_DEFLATED) as z:
  for p in sorted(OUT.rglob('*')):
   if p.is_file():z.write(p,p.relative_to(OUT))
 raise SystemExit(not result.wasSuccessful())
