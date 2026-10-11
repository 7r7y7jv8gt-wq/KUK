"""Regression checks; GIANTS Engine is not simulated by these tests.

Requires Pillow and lupa. Run: PYTHONPATH=/tmp/twinch-test-deps python test_v02.py
"""
from pathlib import Path
import xml.etree.ElementTree as E
import unittest, math, struct, json
from zipfile import ZipFile, ZIP_DEFLATED
from PIL import Image
from lupa import LuaRuntime

HERE=Path(__file__).resolve().parent
OUT=HERE.parent/'FS25_TWinch_v02'

class PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v=E.parse(OUT/'twinch.xml').getroot();cls.i=E.parse(OUT/'twinch.i3d').getroot()
        cls.root=cls.i.find('Scene')[0]
        cls.shapes={s.get('shapeId'):s for s in cls.i.find('Shapes')}
        cls.paths={n.get('id'):n.get('node') for n in cls.v.find('i3dMappings')}

    def resolve(self,path):
        path=self.paths.get(path,path);head,_,tail=path.partition('>');n=self.i.find('Scene')[int(head)]
        for part in tail.split('|') if tail else []:n=n[int(part)]
        return n

    def test_vehicle_collision_flags(self):
        self.assertEqual(self.root.get('dynamic'),'true')
        self.assertTrue(int(self.root.get('collisionFilterGroup'),0)&(1<<16))
        self.assertTrue(int(self.root.get('collisionFilterMask'),0)&(1<<16))
        self.assertNotIn('collisionMask',self.root.attrib)
        self.assertEqual(self.shapes[self.root.get('shapeId')].get('meshUsage'),'256')

    def test_fill_and_blade_collision(self):
        n=self.resolve('fuelFillRoot');self.assertTrue(int(n.get('collisionFilterGroup'),0)&(1<<30))
        for n in self.root.iter('Shape'):
            if n.get('name') in ['bladeCollision','fuelFillRoot']:
                self.assertEqual(self.shapes[n.get('shapeId')].get('meshUsage'),'256')

    def test_correct_wheel_mass_and_support(self):
        wheels=self.v.findall('wheels/wheelConfigurations/wheelConfiguration/wheels/wheel')
        self.assertEqual(len(wheels),4)
        for w in wheels:
            p=w.find('physics');self.assertAlmostEqual(float(p.get('mass')),.08)
            y=float(self.resolve(p.get('repr')).get('translation').split()[1])
            self.assertAlmostEqual(y-float(p.get('radius')),0)
            self.assertEqual(float(p.get('deltaY')),0)
            self.assertEqual(p.get('tireType'),'crawler')
        self.assertEqual(float(self.v.find('base/components/component').get('mass')),5000)

    def test_current_folding_and_sound_references(self):
        self.assertIsNone(self.v.find('foldable/foldingParts'))
        self.assertIsNotNone(self.v.find('foldable/foldingConfigurations/foldingConfiguration/foldingParts'))
        self.assertEqual(self.paths['wheelBackLeft'],self.paths['rearLeft'])
        self.assertEqual(self.paths['wheelBackRight'],self.paths['rearRight'])

    def test_all_indices_and_node_references(self):
        nodeids=[n.get('nodeId') for n in self.i.find('Scene').iter() if n.get('nodeId')]
        self.assertEqual(len(nodeids),len(set(nodeids)))
        for shape in self.shapes.values():
            vs=shape.find('Vertices');ts=shape.find('Triangles')
            self.assertEqual(len(vs),int(vs.get('count')));self.assertEqual(len(ts),int(ts.get('count')))
            for vertex in vs:self.assertTrue(all(math.isfinite(float(x)) for x in vertex.get('p').split()))
            for tri in ts:self.assertTrue(all(0<=int(i)<len(vs) for i in tri.get('vi').split()))
        for n in self.root.iter('Shape'):self.assertIn(n.get('shapeId'),self.shapes)
        for n in self.v.iter():
            for key in ['node','repr','driveNode','rotateNode','anchor','cable']:
                if n.get(key) is not None:self.resolve(n.get(key))
        for path in self.paths.values():self.resolve(path)

    def test_independent_tracks_and_rollers(self):
        tracks=self.v.findall('twinch/track');self.assertEqual(len(tracks),2)
        for track in tracks:
            self.assertEqual(len(self.resolve(track.get('node'))),74)
            self.assertEqual(len(track.findall('roller')),8)
        self.assertTrue(self.v.find('drivable/idleTurning').get('allowed')=='true')

    def test_compressed_mipmaps(self):
        for name in ['icon_twinch.dds','store_twinch.dds']:
            data=(OUT/name).read_bytes();self.assertEqual(data[84:88],b'DXT5')
            w,h=struct.unpack_from('<2I',data,12)[::-1]
            self.assertEqual(struct.unpack_from('<I',data,28)[0],int(math.log2(w))+1)
            expected=128
            while True:
                expected+=max(1,(w+3)//4)*max(1,(h+3)//4)*16
                if w==h==1:break
                w=max(1,w//2);h=max(1,h//2)
            self.assertEqual(len(data),expected)
            Image.open(OUT/name).load()

    def test_archive(self):
        with ZipFile(HERE.parent/'FS25_TWinch_v02.zip') as z:
            self.assertIsNone(z.testzip())
            self.assertIn('modDesc.xml',z.namelist());self.assertIn('scripts/TWinch.lua',z.namelist())
        d=E.parse(OUT/'modDesc.xml').getroot()
        self.assertEqual(d.get('descVersion'),'114')
        self.assertEqual(d.find('multiplayer').get('supported'),'false')

class LuaTests(unittest.TestCase):
    def setUp(self):
        self.lua=LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute((HERE/'TWinch.lua').read_text())
        self.lua.execute('''
            RigidBodyType={DYNAMIC=1}; FSBaseMission={INGAME_NOTIFICATION_INFO=1}
            forces={}; translations={}; rotations={}; visibility={}
            nodes={ [1]={x=0,y=0,z=0,mass=5},[2]={x=0,y=0,z=10,mass=6},[3]={x=0,y=1,z=0} }
            function entityExists(n) return nodes[n]~=nil end
            function getWorldTranslation(n) local p=nodes[n];return p.x,p.y,p.z end
            function getCenterOfMass(n) return 0,0,0 end
            function localToWorld(n,x,y,z) local p=nodes[n];return p.x+x,p.y+y,p.z+z end
            function worldDirectionToLocal(n,x,y,z) return x,y,z end
            function getLinearVelocity(n) local p=nodes[n];return p.vx or 0,p.vy or 0,p.vz or 0 end
            function getMass(n) return nodes[n].mass end
            function getRigidBodyType(n) return 1 end
            function setVisibility(n,v) visibility[n]=v end
            function addForce(n,x,y,z,px,py,pz,localPosition)
                assert(localPosition);table.insert(forces,{node=n,x=x,y=y,z=z})
            end
            function setTranslation(n,x,y,z) translations[n]={x,y,z} end
            function setRotation(n,x,y,z) rotations[n]={x,y,z} end
            function getChildAt(n,i) return 1000+n*100+i end
            target={components={{node=2}},isAddedToPhysics=true,isDeleted=false}
            function target:raiseActive() self.raised=true end
            function target:getOwnerFarmId() return 1 end
            function target:getRootVehicle() return self end
            vehicle={components={{node=1}},isServer=true,isClient=true,isAddedToPhysics=true,engine=true,
                spec_twinch={anchor=3,cable=4,target=target,length=9,reel=false,payout=false,tension=0}}
            function vehicle:getIsMotorStarted() return self.engine end
            function vehicle:raiseActive() self.raised=true end
            function vehicle:getOwnerFarmId() return 1 end
            function vehicle:getRootVehicle() return self end
            g_currentMission={vehicleSystem={vehicles={vehicle,target}}}
        ''')

    def run_lua(self,text):self.lua.execute(text)

    def test_track_loop_and_tangent_continuity(self):
        pose=self.lua.globals().TWinch.trackPose;length=4.68+2*math.pi*.37
        for s in [0,2.34,2.34+math.pi*.37,4.68+math.pi*.37,length]:
            y,z,a=pose(s);yy,zz,_=pose(s+length)
            self.assertAlmostEqual(y,yy);self.assertAlmostEqual(z,zz)
            y0,z0,_=pose(s-1e-6);y1,z1,_=pose(s+1e-6)
            self.assertLess(math.hypot(y1-y0,z1-z0),3e-6)
            self.assertAlmostEqual((y1-y0)/2e-6,-math.sin(a),places=4)
            self.assertAlmostEqual((z1-z0)/2e-6,math.cos(a),places=4)
        self.assertGreaterEqual(.415-.37-.0425,0)

    def test_belts_stop_reverse_and_independent_turn(self):
        self.run_lua('''
            local s=vehicle.spec_twinch
            s.tracks={{node=10,offsetX=.88,phase=0,count=74,rollers={{node=11,radius=.35,angle=0}}},
                      {node=20,offsetX=-.88,phase=0,count=74,rollers={{node=21,radius=.35,angle=0}}}}
            TWinch.updateTracks(vehicle);TWinch.updateTracks(vehicle)
            assert(s.tracks[1].phase==0 and s.tracks[2].phase==0)
            nodes[1].z=.5;TWinch.updateTracks(vehicle)
            assert(math.abs(s.tracks[1].phase-.5)<1e-9)
            assert(math.abs(rotations[11][1]-.5/.35)<1e-9)
            nodes[1].z=0;TWinch.updateTracks(vehicle)
            assert(s.tracks[1].phase<1e-9)
            -- Stub an incremental yaw displacement of opposite sign at each side.
            function localToWorld(n,x,y,z) return x,y,nodes[n].z+x*.1 end
            TWinch.updateTracks(vehicle)
            assert(math.abs(s.tracks[1].phase-.088)<1e-9)
            assert(s.tracks[2].phase>6)
        ''')

    def test_rope_is_tension_only_and_force_limited(self):
        tension=self.lua.globals().TWinch.ropeTension
        self.assertEqual(tension(9,10,50,25),0)
        self.assertEqual(tension(10,10,50,25),0)
        self.assertEqual(tension(30,5,100,15),15)
        self.assertEqual(tension(10,9,-10,25),0)
        self.assertEqual(tension(10,9,0,25),8)

    def test_balanced_pull_without_teleport(self):
        self.run_lua('''
            TWinch.updateWinch(vehicle,16)
            assert(#forces==2 and vehicle.spec_twinch.tension>0)
            assert(forces[1].node==2 and forces[2].node==1)
            assert(math.abs(forces[1].x+forces[2].x)<1e-10)
            assert(math.abs(forces[1].y+forces[2].y)<1e-10)
            assert(math.abs(forces[1].z+forces[2].z)<1e-10)
            assert(forces[1].z<0 and forces[2].z>0)
            assert(vehicle.spec_twinch.tension<=15)
            assert(nodes[1].z==0 and nodes[2].z==10)
        ''')

    def test_reeling_motor_gate_stall_and_payout(self):
        self.run_lua('''
            local s=vehicle.spec_twinch;s.length=10;s.reel=true
            vehicle.engine=false;TWinch.updateWinch(vehicle,100);assert(s.length==10)
            vehicle.engine=true;TWinch.updateWinch(vehicle,100);assert(math.abs(s.length-9.94)<1e-9)
            s.length=7;TWinch.updateWinch(vehicle,100);assert(s.length==7)
            s.payout=true;TWinch.updateWinch(vehicle,100);assert(math.abs(s.length-7.08)<1e-9)
            s.length=40;TWinch.updateWinch(vehicle,100);assert(s.length==40)
        ''')

    def test_deleted_target_overrange_and_leaving(self):
        self.run_lua('''
            vehicle.spec_twinch.reel=true;vehicle.spec_twinch.payout=true
            TWinch.onLeaveVehicle(vehicle)
            assert(not vehicle.spec_twinch.reel and not vehicle.spec_twinch.payout)
            nodes[2].z=50;TWinch.updateWinch(vehicle,16)
            assert(vehicle.spec_twinch.target==nil and visibility[4]==false)
            vehicle.spec_twinch.target=target;target.isDeleted=true
            TWinch.updateWinch(vehicle,16);assert(vehicle.spec_twinch.target==nil)
        ''')

    def test_attachment_selection_and_release(self):
        self.run_lua('''
            local s=vehicle.spec_twinch;s.target=nil
            TWinch.actionConnect(vehicle);assert(s.target==target)
            TWinch.actionReel(vehicle);assert(s.reel)
            TWinch.actionPayout(vehicle);assert(s.payout and not s.reel)
            TWinch.actionConnect(vehicle);assert(s.target==nil)
            function target:getOwnerFarmId() return 2 end
            TWinch.actionConnect(vehicle);assert(s.target==nil)
            function target:getOwnerFarmId() return 1 end
            vehicle.isServer=false;TWinch.actionConnect(vehicle);assert(s.target==nil)
        ''')

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromModule(__import__(__name__))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report=json.loads((OUT/'validation.json').read_text())
    report.update(local_tests_run=result.testsRun,local_test_failures=len(result.failures),local_test_errors=len(result.errors),lua_tests='mocked engine API; not game validation')
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    # Keep the distributed evidence in sync with the checks just executed.
    with ZipFile(HERE.parent/'FS25_TWinch_v02.zip','w',ZIP_DEFLATED) as z:
        for f in sorted(OUT.rglob('*')):
            if f.is_file():z.write(f,f.relative_to(OUT))
    raise SystemExit(0 if result.wasSuccessful() else 1)
