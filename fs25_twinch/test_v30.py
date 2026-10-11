from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import unittest,json,math,xml.etree.ElementTree as E,hashlib
import test_v25 as prior
ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'FS25_Follvik_TVinsj_v30'
prior.OUT=OUT;prior.winches.OUT=OUT;prior.winches.baseline.OUT=OUT;prior.hydraulics.OUT=OUT
class WinchTests(prior.WinchTests):
 def run_lua(self,text):self.lua.execute(text.replace('twinchV13','twinchV30'))
 def test_source_assets_preserved_and_package_valid(self):
  for name,digest in json.loads((OUT/'source_asset_hashes.json').read_text()).items():self.assertEqual(hashlib.sha256((OUT/name).read_bytes()).hexdigest(),digest)
  self.assertEqual(E.parse(OUT/'modDesc.xml').find('version').text,'0.30.0.0')
  with ZipFile(ROOT/'FS25_Follvik_TVinsj_v30.zip') as z:self.assertIsNone(z.testzip())
class ContactTests(unittest.TestCase):
 def setUp(self):
  self.v=E.parse(OUT/'twinch.xml');self.r=E.parse(OUT/'twinch.i3d');self.scene=self.r.find('Scene')
  self.mappings={n.get('id'):n.get('node') for n in self.v.find('i3dMappings')}
 def resolve(self,path):
  a,_,b=path.partition('>');n=self.scene[int(a)]
  for i in b.split('|') if b else []:n=n[int(i)]
  return n
 def test_original_ground_envelope_and_mass(self):
  p=self.v.findall('wheels/wheelConfigurations/wheelConfiguration/wheels/wheel/physics');self.assertEqual(len(p),4)
  for n in p:
   y=float(self.resolve(self.mappings[n.get('repr')]).get('translation').split()[1])
   self.assertEqual(float(n.get('radius')),.415);self.assertAlmostEqual(y-float(n.get('radius')),0)
   self.assertEqual(float(n.get('suspTravel')),.02);self.assertEqual(float(n.get('deltaY')),0)
   self.assertEqual(float(n.get('spring')),1587.2);self.assertEqual(float(n.get('damper')),198.4)
  self.assertAlmostEqual(39680+1000*sum(float(n.get('mass')) for n in p),40000)
  self.assertAlmostEqual(sum(float(n.get('restLoad')) for n in p),39.68)
  self.assertFalse(any(n.get('name','').startswith(('Approach','Departure','middleLeft','middleRight')) for n in self.scene.iter()))
  d=self.v.findall('motorized/differentialConfigurations/differentialConfiguration/differentials/differential');self.assertEqual(len(d),3)
  self.assertEqual({int(n.get(k)) for n in d for k in ['wheelIndex1','wheelIndex2'] if n.get(k)}, {1,2,3,4})
 def test_rail_collision_inside_track_envelope_and_uses_closed_box(self):
  old=E.parse(ROOT/'FS25_TWinch_v07/twinch.i3d');sid=old.find('Scene')[0].get('shapeId');shape=old.find("Shapes/IndexedTriangleSet[@shapeId='"+sid+"']")
  self.assertEqual(shape.get('meshUsage'),'256')
  vertices=[list(map(float,n.get('p').split())) for n in shape.find('Vertices')]
  bounds=[(min(p[i] for p in vertices),max(p[i] for p in vertices)) for i in range(3)]
  self.assertEqual(bounds,[(-.81,.81),(.82,2.27),(-1.5,1.38)])
  for side,sign in [('Left',1),('Right',-1)]:
   n=self.resolve(self.mappings['trackFrameCollision'+side]);self.assertEqual(n.get('compoundChild'),'true');self.assertEqual(n.get('shapeId'),self.scene[0].get('shapeId'))
   scale=list(map(float,n.get('scale').split()));translation=list(map(float,n.get('translation').split()))
   transformed=[(a*scale[i]+translation[i],b*scale[i]+translation[i]) for i,(a,b) in enumerate(bounds)]
   self.assertGreater(transformed[1][0],.2);self.assertLess(transformed[1][1],.5)
   self.assertGreater(transformed[2][0],-1.22);self.assertLess(transformed[2][1],1.2)
   self.assertAlmostEqual(sum(transformed[0])/2,sign*1.1)
  blade=next(n for n in self.scene.iter() if n.get('name')=='bladeLift')
  self.assertTrue(any(n.get('name')=='bladeCollision' and n.get('compoundChild')=='true' for n in blade))
  self.assertTrue(any(n.get('nodeId')=='665' for n in blade))
 def test_mappings_and_texture_geometry_preserved(self):
  for path in self.mappings.values():self.resolve(path)
  for p in OUT.rglob('*'):
   if p.suffix in ['.shapes','.dds']:self.assertEqual(p.read_bytes(),(ROOT/'FS25_Follvik_TVinsj_v29'/p.relative_to(OUT)).read_bytes())
  for n in self.r.find('Files'):
   name=n.get('filename')
   if not name.startswith('$'):self.assertTrue((OUT/name).is_file(),name)
  self.assertEqual(self.r.find("Materials/Material[@materialId='3647']").get('alphaBlending'),'true')
 def test_stronger_torque_retained_and_speed_limited(self):
  motor=self.v.find('motorized/motorConfigurations/motorConfiguration/motor')
  previous=E.parse(ROOT/'FS25_Follvik_TVinsj_v29/twinch.xml').find('motorized/motorConfigurations/motorConfiguration/motor')
  self.assertEqual([n.attrib for n in motor],[n.attrib for n in previous])
  self.assertEqual(motor.get('torqueScale'),previous.get('torqueScale'));self.assertEqual(motor.get('minRpm'),'1000')
  self.assertEqual(motor.get('maxForwardSpeed'),'12');self.assertEqual(motor.get('maxBackwardSpeed'),'12')
  self.assertEqual(self.v.getroot().get('type'),'twinchV30')
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(c) for c in [WinchTests,prior.MouseTests,ContactTests]))
 (OUT/'validation.json').write_text(json.dumps({'version':'0.30.0.0','local_tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'game_test':'not run','ground_contacts':4,'suspension_travel_m':.02,'track_collision_rails':2,'mass_kg':40000,'v29_torque_curve_preserved':True},indent=2)+'\n')
 with ZipFile(ROOT/'FS25_Follvik_TVinsj_v30.zip','w',ZIP_DEFLATED) as z:
  for p in sorted(OUT.rglob('*')):
   if p.is_file():z.write(p,p.relative_to(OUT))
 raise SystemExit(not result.wasSuccessful())
