from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import unittest,xml.etree.ElementTree as E,json,hashlib
import test_v13 as baseline
ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'FS25_Follvik_TVinsj_v24'
baseline.OUT=OUT
class WinchTests(unittest.TestCase):
 setUp=baseline.LoggingTests.setUp
 def run_lua(self,text):self.lua.execute(text.replace('twinchV13','twinchV24'))
 def test_both_hooks_attach_and_pull_100_tonne_vehicle(self):
  self.run_lua('''
    nodes[1].mass=40;nodes[2].mass=100
    nodes[30]={x=0,y=0,z=10,parent=2,body=0,group=64}
    function g_currentMission:getNodeObject(n) if n==30 then return target end end
    local rear=createTransformGroup('rear');nodes[rear].z=-1
    BladeWinch.load(vehicle,rear)
    for _,w in ipairs(vehicle.spec_twinch.loggingWinches) do
        BladeWinch.selected=w;BladeWinch.hit=nil
        BladeWinch.raycastCallback(BladeWinch,30,0,0,10,2)
        assert(BladeWinch.hit.node==2 and BladeWinch.hit.vehicle==target)
        BladeWinch.attach(w,BladeWinch.hit);assert(#w.targets==1)
        w.length=1;forces={}
        BladeWinch.tickOne(vehicle,w,16)
        assert(#forces==2 and target.raised)
        assert(math.abs(math.sqrt(forces[1].x^2+forces[1].y^2+forces[1].z^2)-980.665)<1e-6)
        assert(math.abs(forces[1].z+forces[2].z)<1e-8)
        BladeWinch.clear(w);assert(#w.targets==0)
    end
  ''')
 def test_multicomponent_vehicle_mass_limit(self):
  self.run_lua('''
    nodes[2].mass=60;nodes[31]={x=0,y=0,z=11,mass=40,body=1}
    target.components={{node=2},{node=31}}
    assert(BladeWinch.targetMass({vehicle=target,node=2})==100)
    BladeWinch.attach(s,{vehicle=target,node=2,shape=2,x=0,y=0,z=10,static=false});assert(#s.targets==1)
    BladeWinch.attach(s,{vehicle=target,node=31,shape=31,x=0,y=0,z=11,static=false});assert(#s.targets==1)
    BladeWinch.clear(s);nodes[31].mass=40.1
    BladeWinch.attach(s,{vehicle=target,node=2,shape=2,x=0,y=0,z=10,static=false});assert(#s.targets==0)
    nodes[2].mass=60;target.components={{node=2}};nodes[32]={x=0,y=0,z=12,mass=41}
    BladeWinch.attach(s,{vehicle=target,node=2,shape=2,x=0,y=0,z=10,static=false})
    BladeWinch.attach(s,{node=32,shape=32,x=0,y=0,z=12,static=false});assert(#s.targets==1)
  ''')
 def test_vehicle_lookup_fallback_own_components_and_static_scenery(self):
  self.run_lua('''
    nodes[30]={x=0,y=0,z=10,parent=2,body=0,group=64}
    BladeWinch.selected=s;BladeWinch.hit=nil
    BladeWinch.raycastCallback(BladeWinch,30,0,0,10,2);assert(BladeWinch.hit.vehicle==target)
    nodes[33]={x=0,y=0,z=0,body=1,mass=1};vehicle.components[2]={node=33}
    nodes[34]={x=0,y=0,z=0,parent=33,body=0,group=64}
    BladeWinch.hit=nil;BladeWinch.raycastCallback(BladeWinch,34,0,0,0,1);assert(BladeWinch.hit==nil)
    nodes[35]={x=0,y=0,z=1,body=0,group=32}
    BladeWinch.raycastCallback(BladeWinch,35,0,0,1,1);assert(BladeWinch.hit==nil)
  ''')
 def test_deleted_vehicle_releases_hook(self):
  self.run_lua('''
    BladeWinch.attach(s,{vehicle=target,node=2,shape=2,x=0,y=0,z=10,static=false})
    local ref=s.targets[1].ref;target.isDeleted=true
    BladeWinch.tickOne(vehicle,s,16);assert(#s.targets==0 and not entityExists(ref))
  ''')
 def test_force_curve_slack_damping_and_full_rating_before_stall(self):
  self.run_lua('''
    assert(TWinch.winchTension(10,10,100,40,100)==0)
    assert(TWinch.winchTension(10,9.2,0,40,100)==980.665)
    assert(TWinch.winchTension(10,9.9,-10,40,100)==0)
    assert(math.abs(TWinch.winchTension(10,9.9,0,40,100)-125)<1e-8)
    assert(TWinch.winchTension(10,9.9,1,40,100)>125)
    vehicle.spec_twinch.target=target;nodes[2].mass=100
    vehicle.spec_twinch.length=1;TWinch.updateWinch(vehicle,16)
    assert(vehicle.spec_twinch.tension==980.665 and #forces==2)
  ''')
 def test_source_assets_preserved_and_package_valid(self):
  for n,digest in json.loads((OUT/'source_asset_hashes.json').read_text()).items():
   self.assertEqual(hashlib.sha256((OUT/n).read_bytes()).hexdigest(),digest)
  self.assertEqual(E.parse(OUT/'twinch.xml').getroot().get('type'),'twinchV24')
  self.assertEqual(E.parse(OUT/'modDesc.xml').find('version').text,'0.24.0.0')
  self.assertEqual(E.parse(OUT/'machineConfigurations.xml').find('configuration').get('vehicle'),'FS25_Follvik_TVinsj_v24/twinch.xml')
  with ZipFile(ROOT/'FS25_Follvik_TVinsj_v24.zip') as z:self.assertIsNone(z.testzip())
# Existing meaningful controls, static tree anchors, cleanup and hydraulic regressions.
for name in ['test_registered_walkup_take_attach_dynamic_pull_release','test_fixed_tree_anchor_only_moves_chassis','test_engine_gate_payout_timeout_gui_and_vehicle','test_prompt_uses_player_root_when_hand_helper_is_far_away','test_cleanup_releases_runtime_meshes']:
 setattr(WinchTests,name,getattr(baseline.LoggingTests,name))
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(WinchTests))
 (OUT/'validation.json').write_text(json.dumps({'version':'0.24.0.0','local_tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'game_test':'not run','per_winch_capacity_tonnes':100,'per_winch_force_kN':980.665},indent=2)+'\n')
 with ZipFile(ROOT/'FS25_Follvik_TVinsj_v24.zip','w',ZIP_DEFLATED) as z:
  for f in sorted(OUT.rglob('*')):
   if f.is_file():z.write(f,f.relative_to(OUT))
 raise SystemExit(not result.wasSuccessful())
