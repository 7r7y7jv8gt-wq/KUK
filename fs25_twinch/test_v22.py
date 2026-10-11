from pathlib import Path
import unittest,json
from zipfile import ZipFile,ZIP_DEFLATED
import test_v13 as prior
import test_v14 as lamps
ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'FS25_TWinch_v22';prior.OUT=OUT;prior.old.OUT=OUT;prior.old.previous.OUT=OUT;lamps.OUT=OUT
class WinchTests(prior.LoggingTests):
 def test_registration_uses_vehicle_directory_when_runtime_mod_directory_nil(self):
  self.run_lua("""
    g_currentModDirectory=nil;TWinch.MOD_DIRECTORY=nil;vehicle.baseDirectory='/mods/FS25_TWinch_v22/'
    local called=false
    FS25_0_TerraFarm={g_machineManager={registerConfiguration=function(_,path,key)
      assert(path=='/mods/FS25_TWinch_v22/xml/terraFarmBlade.xml');called=true
    end},MachineUtils={getVehicleModFilename=function()return 'FS25_TWinch_v22/twinch.xml' end}}
    assert(TWinch.registerTerraFarm(vehicle) and called)
    vehicle.baseDirectory=nil;assert(not TWinch.registerTerraFarm(vehicle))
  """)
 def test_external_registration_failure_does_not_abort_vehicle_load(self):
  self.run_lua("""
    TWinch.registerTerraFarm=function()error('external failure')end
    vehicle.xmlFile={getValue=function(_,key,default)return default end,iterate=function()end}
    local bladeLoaded=false;local winchLoaded=false
    TWinch.loadBlade=function()bladeLoaded=true end;BladeWinch.load=function()winchLoaded=true end
    vehicle.spec_twinch=nil;TWinch.onLoad(vehicle,nil)
    assert(vehicle.spec_twinch~=nil and bladeLoaded and winchLoaded)
  """)
 def test_update_during_incomplete_load_is_safe(self):
  self.run_lua("vehicle.spec_twinch=nil;TWinch.onUpdate(vehicle,16);TWinch.onUpdateTick(vehicle,16);TWinch.onDelete(vehicle)")

 def test_direct_registry_before_terrafarm_lookup(self):
  self.run_lua("""
    local entries={}
    FS25_0_TerraFarm={g_machineManager={registerConfiguration=function(_,path,key)entries[key]=path end},MachineUtils={getVehicleModFilename=function(v)return 'RenamedMachine/twinch.xml' end}}
    g_currentModDirectory='/mods/RenamedMachine/'
    assert(TWinch.registerTerraFarm(vehicle))
    assert(entries['RenamedMachine/twinch.xml']=='/mods/RenamedMachine/xml/terraFarmBlade.xml')
    FS25_0_TerraFarm=nil;assert(not TWinch.registerTerraFarm(vehicle))
  """)

 def run_lua(self,text):return prior.old.previous.LuaTests.run_lua(self,text.replace('twinchV13','twinchV22'))
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
 def test_eight_red_drls_and_no_white_or_orange(self):
  drls=[n for n in self.v.findall('lights/dayTimeLights/dayTimeLight') if n.get('node','').startswith('for9t_')]
  self.assertEqual(len(drls),8)
  for n in drls:self.assertEqual(self.resolve(n.get('node')).get('name'),'DRL_red')

 def test_preserves_user_model_geometry_and_positions(self):
  import xml.etree.ElementTree as E
  from zipfile import ZipFile
  with ZipFile(ROOT/'fs25_twinch/user_lighting_v21.zip') as z:
   self.assertEqual(z.read('twinch.i3d.shapes'),(OUT/'twinch.i3d.shapes').read_bytes())
   source=E.fromstring(z.read('twinch.i3d'))
  for name in ['ledbar_main','parkinglights','floodlights']:
   a=next(n for n in source.find('Scene').iter() if n.get('name')==name)
   b=next(n for n in self.r.find('Scene').iter() if n.get('name')==name)
   self.assertEqual(a.get('translation'),b.get('translation'));self.assertEqual(a.get('rotation'),b.get('rotation'))
 def test_whole_bar_flash_is_not_steady_cruise(self):
  names=[n.get('node') for n in self.v.findall('lights/dayTimeLights/dayTimeLight')]
  self.assertNotIn('added_cruiselights',names)
  flash=[n.get('node') for n in self.v.findall('lights/beaconLights/beaconLight/staticLight')]
  self.assertIn('added_cruiselights',flash)
  for name in ['sideCruiseLeft','sideCruiseRight']:
   n=self.resolve(name);self.assertEqual(float(n.get('scale').split()[0]),.1)
   self.assertAlmostEqual(abs(float(n.get('translation').split()[0])),.64)
 def test_added_native_light_controls(self):
  drls=self.v.findall('lights/dayTimeLights/dayTimeLight')
  self.assertIn('added_parkinglights',[n.get('node') for n in drls]);self.assertNotIn('added_cruiselights',[n.get('node') for n in drls]);self.assertIn('sideCruiseLeft',[n.get('node') for n in drls]);self.assertIn('sideCruiseRight',[n.get('node') for n in drls])
  self.assertEqual([n.get('lightTypes') for n in self.v.findall('lights/states/state')],['0','0 1','0 1 2'])
  flash=self.v.findall('lights/beaconLights/beaconLight');self.assertEqual(len(flash),6)
  for n in flash:
   self.assertEqual(self.resolve(n.get('realLight')).get('color'),'1 .5 0')
   self.assertEqual(n.find('staticLight').get('multiBlink'),'true')
  flood=next(n for n in self.v.findall('lights/staticLights/staticLight') if n.get('node')=='added_floodlights')
  self.assertEqual(flood.get('lightTypes'),'0')
  for level in ['low','high']:
   b=next(n for n in self.v.findall('lights/realLights/'+level+'/light') if n.get('node')=='ledbarFloodBeam');self.assertEqual(b.get('lightTypes'),'0')
 def test_existing_work_lenses_remain_eight_distinct_nodes(self):
  nodes=[self.resolve('for9t_work_'+str(i)) for i in range(8)]
  self.assertEqual(len({id(n) for n in nodes}),8)

 def test_speed_is_12_kmh(self):
  motor=self.v.find('motorized/motorConfigurations/motorConfiguration/motor')
  self.assertEqual(motor.get('maxForwardSpeed'),'12')
  self.assertEqual(motor.get('maxBackwardSpeed'),'12')
  self.assertEqual(self.v.find('storeData/specs/maxSpeed').text,'12')

 def test_actual_motor_peak_matches_800_hp(self):
  import math
  config=self.v.find('motorized/motorConfigurations/motorConfiguration');motor=config.find('motor')
  scale=float(motor.get('torqueScale'));rpm=float(motor.get('maxRpm'))
  points=[(float(n.get('normRpm')),float(n.get('torque'))) for n in motor.findall('torque')]
  products=[x*y for x,y in points]
  for (x0,y0),(x1,y1) in zip(points,points[1:]):
   slope=(y1-y0)/(x1-x0);intercept=y0-slope*x0
   if slope<0:
    x=-intercept/(2*slope)
    if x0<=x<=x1:products.append(x*(slope*x+intercept))
  hp=max(products)*rpm*math.pi/30*scale/.73549875
  self.assertAlmostEqual(hp,800,places=5)
  self.assertEqual(config.get('hp'),'800');self.assertEqual(self.v.find('storeData/specs/power').text,'800')

 def test_machine_embedded_at_blade_edge(self):
  import xml.etree.ElementTree as E
  machine=self.v.find('machine');profile=E.parse(OUT/'xml/terraFarmBlade.xml').find('machine')
  self.assertEqual(E.tostring(machine),E.tostring(profile))
  self.assertEqual(machine.get('type'),'leveler')
  edge=self.resolve(machine.find('workArea').get('referenceNode'))
  parent=next(n for n in self.r.find('Scene').iter() if edge in list(n))
  self.assertEqual(parent.get('name'),'bladeLift')
  self.assertEqual(edge.get('translation'),'0 -0.605 0.9375')
  self.assertEqual(E.parse(OUT/'machineConfigurations.xml').find('configuration').get('vehicle'),'FS25_TWinch_v22/twinch.xml')

 def test_complete_installable_zip(self):
  with ZipFile(ROOT/'FS25_TWinch_v22.zip') as z:self.assertIsNone(z.testzip());self.assertIn('modDesc.xml',z.namelist())
 def test_work_lenses_and_beams_match_front_rear_states(self):
  entries=[n for n in self.v.findall('lights/staticLights/staticLight') if n.get('node','').startswith('for9t_')];self.assertEqual(len(entries),16)
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
 with ZipFile(ROOT/'FS25_TWinch_v22.zip','w',ZIP_DEFLATED) as z:
  for f in sorted(OUT.rglob('*')):
   if f.is_file():z.write(f,f.relative_to(OUT))
 raise SystemExit(not result.wasSuccessful())
