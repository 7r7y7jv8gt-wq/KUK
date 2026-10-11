from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import unittest,json,xml.etree.ElementTree as E
import test_v24 as winches
import test_v07 as hydraulics
ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'FS25_Follvik_TVinsj_v25'
winches.OUT=OUT;winches.baseline.OUT=OUT;hydraulics.OUT=OUT
class WinchTests(winches.WinchTests):
 def run_lua(self,text):self.lua.execute(text.replace('twinchV13','twinchV25'))
 def test_source_assets_preserved_and_package_valid(self):
  for n,digest in json.loads((OUT/'source_asset_hashes.json').read_text()).items():
   import hashlib
   self.assertEqual(hashlib.sha256((OUT/n).read_bytes()).hexdigest(),digest)
  self.assertEqual(E.parse(OUT/'twinch.xml').getroot().get('type'),'twinchV25')
  self.assertEqual(E.parse(OUT/'modDesc.xml').find('version').text,'0.25.0.0')
  with ZipFile(ROOT/'FS25_Follvik_TVinsj_v25.zip') as z:self.assertIsNone(z.testzip())
class MouseTests(unittest.TestCase):
 def setUp(self):
  hydraulics.previous.LuaTests.setUp(self)
  self.lua.execute("g_currentModName='FS25_Follvik_TVinsj_v25'")
  self.lua.execute((OUT/'scripts/TWinch.lua').read_text())
 setup_blade=hydraulics.V07LuaTests.setup_blade
 def run_lua(self,text):self.lua.execute(text)
 def test_mouse_survives_idle_keyboard_callbacks_both_orders(self):
  self.setup_blade();self.run_lua('''
    local blade=vehicle.spec_twinch.blade
    TWinch.actionBlade(vehicle,'TWINCH_BLADE_MOUSE_V25',1,nil,true,true)
    TWinch.actionBlade(vehicle,'TWINCH_BLADE_RAISE_V13',0,nil,false,false)
    TWinch.actionBlade(vehicle,'TWINCH_BLADE_LOWER_V13',0,nil,false,false)
    TWinch.updateBlade(vehicle,100);assert(math.abs(blade.angle+1.2)<1e-8)
    TWinch.actionBlade(vehicle,'TWINCH_BLADE_RAISE_V13',0,nil,false,false)
    TWinch.actionBlade(vehicle,'TWINCH_BLADE_MOUSE_V25',-1,nil,true,false)
    TWinch.updateBlade(vehicle,100);assert(math.abs(blade.angle)<1e-8)
    assert(rotations[30]~=nil and directionCalls[31]~=nil and directionCalls[34]~=nil)
    local a=blade.angle;TWinch.updateBlade(vehicle,100);assert(blade.angle==a)
  ''')
 def test_keyboard_directions_survive_other_idle_key(self):
  self.setup_blade();self.run_lua('''
    TWinch.actionBlade(vehicle,'TWINCH_BLADE_RAISE_V13',1,nil,false,false)
    TWinch.actionBlade(vehicle,'TWINCH_BLADE_LOWER_V13',0,nil,false,false)
    TWinch.updateBlade(vehicle,100);assert(vehicle.spec_twinch.blade.angle<0)
    TWinch.actionBlade(vehicle,'TWINCH_BLADE_RAISE_V13',0,nil,false,false)
    TWinch.actionBlade(vehicle,'TWINCH_BLADE_LOWER_V13',-1,nil,false,false)
    TWinch.updateBlade(vehicle,100);assert(math.abs(vehicle.spec_twinch.blade.angle)<1e-8)
  ''')
 def test_timeout_leave_vehicle_and_angle_limits(self):
  self.setup_blade();self.run_lua('''
    local b=vehicle.spec_twinch.blade
    for i=1,60 do TWinch.actionBlade(vehicle,'TWINCH_BLADE_MOUSE_V25',1,nil,true,true);TWinch.updateBlade(vehicle,100)end
    assert(b.angle==-28)
    for i=1,60 do TWinch.actionBlade(vehicle,'TWINCH_BLADE_MOUSE_V25',-1,nil,true,true);TWinch.updateBlade(vehicle,100)end
    assert(b.angle==25)
    TWinch.actionBlade(vehicle,'TWINCH_BLADE_MOUSE_V25',1,nil,true,true);TWinch.updateBlade(vehicle,300);assert(b.angle==25)
    TWinch.actionBlade(vehicle,'TWINCH_BLADE_MOUSE_V25',1,nil,true,true);TWinch.onLeaveVehicle(vehicle)
    TWinch.updateBlade(vehicle,100);assert(b.angle==25)
  ''')
 def test_mouse_action_registered_and_left_button_gates_both_directions(self):
  d=E.parse(OUT/'modDesc.xml')
  self.assertEqual(d.find("actions/action[@name='TWINCH_BLADE_MOUSE_V25']").get('axisType'),'FULL')
  entries=d.findall("inputBinding/actionBinding[@action='TWINCH_BLADE_MOUSE_V25']/binding")
  self.assertEqual(len(entries),2)
  self.assertEqual({n.get('input') for n in entries},{'MOUSE_BUTTON_LEFT AXIS_MOUSE_Y'})
  self.assertEqual({(n.get('axisComponent'),n.get('inputComponent')) for n in entries},{('+','-'),('-','+')})
  self.setup_blade();self.run_lua('''
    GS_PRIO_HIGH=1;Logging={warning=function()end}
    g_inputBinding={setActionEventActive=function()end,setActionEventText=function()end,setActionEventTextPriority=function()end,setActionEventTextVisibility=function()end}
    vehicle.clearActionEventsTable=function()end
    callbacks={};function vehicle:addActionEvent(events,name,obj,callback)callbacks[name]=callback;return true,name end
    TWinch.onRegisterActionEvents(vehicle,true,true)
    callbacks.TWINCH_BLADE_MOUSE_V25(vehicle,'TWINCH_BLADE_MOUSE_V25',1,nil,true,true)
    callbacks.TWINCH_BLADE_RAISE_V13(vehicle,'TWINCH_BLADE_RAISE_V13',0,nil,false,false)
    callbacks.TWINCH_BLADE_LOWER_V13(vehicle,'TWINCH_BLADE_LOWER_V13',0,nil,false,false)
    TWinch.updateBlade(vehicle,100);assert(vehicle.spec_twinch.blade.angle<0)
  ''')
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(c) for c in [WinchTests,MouseTests]))
 (OUT/'validation.json').write_text(json.dumps({'version':'0.25.0.0','local_tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'game_test':'not run'},indent=2)+'\n')
 with ZipFile(ROOT/'FS25_Follvik_TVinsj_v25.zip','w',ZIP_DEFLATED) as z:
  for p in sorted(OUT.rglob('*')):
   if p.is_file():z.write(p,p.relative_to(OUT))
 raise SystemExit(not result.wasSuccessful())
