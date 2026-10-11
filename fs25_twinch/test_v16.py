from pathlib import Path
import unittest,json
from zipfile import ZipFile,ZIP_DEFLATED
import test_v13 as prior
import test_v14 as lamps
ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'FS25_TWinch_v16';prior.OUT=OUT;prior.old.OUT=OUT;prior.old.previous.OUT=OUT;lamps.OUT=OUT
class WinchTests(prior.LoggingTests):
 def run_lua(self,text):return prior.old.previous.LuaTests.run_lua(self,text.replace('twinchV13','twinchV16'))
 def test_rear_selects_its_own_hook_and_cleans_up_both(self):
  self.run_lua('''
    local anchor=createTransformGroup('rear');link(1,anchor);setTranslation(anchor,0,1,-10);nodes[anchor].z=-10
    BladeWinch.load(vehicle,anchor)
    local rear=vehicle.spec_twinch.loggingWinches[2]
    assert(#BladeWinch.instances==2 and s.anchor~=rear.anchor and rear.anchor==anchor)
    nodes[5].z=-10;nodes[6].z=-10
    BladeWinch.update(BladeWinch,16);assert(BladeWinch.selected==rear)
    fire('TWINCH_HOOK_V13');assert(rear.carrying and not s.carrying)
    s.hook=createTransformGroup("frontHook");s.hookPivot=createTransformGroup("frontPose");rear.hook=createTransformGroup("rearHook");rear.hookPivot=createTransformGroup("rearPose")
    local first=s.hook;local second=rear.hook
    BladeWinch.delete(vehicle)
    assert(#BladeWinch.instances==0 and not entityExists(first) and not entityExists(second))
  ''')
class LightTests(lamps.LightsTests):
 def test_machine_embedded_at_blade_edge(self):
  import xml.etree.ElementTree as E
  machine=self.v.find('machine');profile=E.parse(OUT/'xml/terraFarmBlade.xml').find('machine')
  self.assertEqual(E.tostring(machine),E.tostring(profile))
  self.assertEqual(machine.get('type'),'leveler')
  edge=self.resolve(machine.find('workArea').get('referenceNode'))
  parent=next(n for n in self.r.find('Scene').iter() if edge in list(n))
  self.assertEqual(parent.get('name'),'bladeLift')
  self.assertEqual(edge.get('translation'),'0 -0.605 0.9375')
  self.assertEqual(E.parse(OUT/'machineConfigurations.xml').find('configuration').get('vehicle'),'FS25_TWinch_v16/twinch.xml')

 def test_complete_installable_zip(self):
  with ZipFile(ROOT/'FS25_TWinch_v16.zip') as z:self.assertIsNone(z.testzip());self.assertIn('modDesc.xml',z.namelist())
 def test_work_lenses_and_beams_match_front_rear_states(self):
  entries=self.v.findall('lights/staticLights/staticLight');self.assertEqual(len(entries),16)
  for i in range(8):
   work=next(n for n in entries if n.get('node')==f'for9t_work_{i}')
   glow=next(n for n in entries if n.get('node')==f'for9t_luminousInsert_{i}')
   self.assertEqual(glow.get('lightTypes'),work.get('lightTypes'));self.assertEqual(glow.get('toggleVisibility'),'true')
   self.assertEqual(work.get('lightTypes'),'0' if i<4 else '1')
   for level in ['low','high']:
    beam=next(n for n in self.v.findall('lights/realLights/'+level+'/light') if n.get('node')==f'for9t_beam_{i}')
    self.assertEqual(beam.get('lightTypes'),work.get('lightTypes'))
 def test_rear_is_close_to_body_and_has_backing(self):
  self.assertEqual(self.resolve('rearWinchAnchor').get('translation'),'0 1.2 -1.49')
  self.assertTrue(any(n.get('name')=='rearWinchBackingPlate' for n in self.r.find('Scene').iter()))
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(c) for c in [WinchTests,LightTests]))
 report=json.loads((OUT/'validation.json').read_text());report.update(local_tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors));(OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
 with ZipFile(ROOT/'FS25_TWinch_v16.zip','w',ZIP_DEFLATED) as z:
  for f in sorted(OUT.rglob('*')):
   if f.is_file():z.write(f,f.relative_to(OUT))
 raise SystemExit(not result.wasSuccessful())
