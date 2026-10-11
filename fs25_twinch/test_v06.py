"""Native camera/control configuration and hydraulic kinematics regressions.

Run with Pillow and lupa installed. Engine behavior still requires FS25 testing.
"""
from pathlib import Path
import xml.etree.ElementTree as E
from zipfile import ZipFile,ZIP_DEFLATED
import unittest,math,json,hashlib
import test_v02 as previous

HERE=Path(__file__).resolve().parent;OUT=HERE.parent/'FS25_TWinch_v06'
previous.OUT=OUT

class V06PackageTests(previous.PackageTests):
    def test_removed_front_attachment(self):
        names=[n.get('name','') for n in self.root.iter()]
        for prefix in ['GreenCastFairlead','FairleadRoller','ForgedHook','HookSafetyGate','RecoveryChain']:
            self.assertFalse(any(name.startswith(prefix) for name in names))
        self.assertIn('RecessedCableOutlet',names)
        self.assertIn(self.resolve('winchAnchor'),list(self.resolve('bladeLift')))

    def test_visible_hydraulic_assemblies(self):
        for sign,side in [(-1,'Right'),(1,'Left')]:
            barrel=self.resolve('hydraulic'+side+'Barrel')
            pin=self.resolve('hydraulic'+side+'BladePin')
            self.assertAlmostEqual(float(barrel.get('translation').split()[0]),sign*.76)
            self.assertAlmostEqual(float(pin.get('translation').split()[0]),sign*.76)
            names=[n.get('name','') for n in barrel.iter()]
            self.assertIn('hydraulic'+side+'PaintedBarrel',names)
            self.assertEqual(names.count(side+'HydraulicHose'),2)
            self.assertIn(side+'BladePivotPin',[n.get('name') for n in pin.iter()])
            self.assertIn('hydraulic'+side+'ChromePiston',[n.get('name') for n in pin.iter()])

    def test_linked_track_details_and_clearance(self):
        for side in ['Left','Right']:
            track=self.resolve('track'+side)
            for link in track:
                names=[n.get('name','') for n in link.iter()]
                for prefix in ['CastTrackShoe','WornTrackGrouser','TrackHingePin','TrackGuideHorn','TrackBolt']:
                    self.assertTrue(any(n.startswith(prefix) for n in names))
            # Detail remains under each animated link, with an uninterrupted loop.
            self.assertEqual(len(track),74)
            for link in track:
                y,z=map(float,link.get('translation').split()[1:]);a=math.radians(float(link.get('rotation').split()[0]))
                for n in link:
                    if n.tag!='Shape':continue
                    for vertex in self.shapes[n.get('shapeId')].find('Vertices'):
                        x,ly,lz=map(float,vertex.get('p').split())
                        self.assertGreater(y+math.cos(a)*ly-math.sin(a)*lz,0)
        for idx in [0,2]:
            wheel=self.resolve('roller_'+str(idx))
            self.assertEqual(sum(n.get('name')=='SprocketTooth' for n in wheel),24)

    def test_normalmap_tangent_generation(self):
        for n in self.root.iter('Shape'):
            if n.get('nonRenderable')=='true':continue
            self.assertEqual(self.shapes[n.get('shapeId')].find('Vertices').get('tangent'),'true')
        for shape in self.shapes.values():
            if shape.find('Vertices').get('tangent')!='true':continue
            for vertex in shape.find('Vertices'):
                norm=list(map(float,vertex.get('n').split()))
                self.assertTrue(all(math.isfinite(x) for x in norm))
                self.assertAlmostEqual(sum(x*x for x in norm),1,places=4)

    def test_native_vehicle_materials(self):
        files={n.get('fileId'):n.get('filename') for n in self.i.find('Files')}
        for m in self.i.find('Materials'):
            self.assertEqual(files[m.get('customShaderId')],'$data/shaders/vehicleShader.xml')
            self.assertEqual(files[m.find('Glossmap').get('fileId')],'$data/shared/default_vmask.dds')
            self.assertEqual({n.get('name') for n in m.findall('Custommap')},{'detailDiffuse','detailNormal','detailSpecular'})
            for n in m.findall('Custommap'):self.assertTrue(files[n.get('fileId')].startswith('$data/shared/detailLibrary/'))

    def test_textures_and_uvs(self):
        import struct
        files=self.r.find('Files') if hasattr(self,'r') else E.parse(OUT/'twinch.i3d').getroot().find('Files')
        self.assertEqual(sum(not f.get('filename').startswith('$data/') for f in files),42)
        for f in files:
            if f.get('filename').startswith('$data/'):continue
            data=(OUT/f.get('filename')).read_bytes()
            self.assertEqual(data[:4],b'DDS ')
            self.assertEqual(struct.unpack_from('<I',data,28)[0],11)
            self.assertEqual(len(data),128+sum(max(1,(1024//2**i+3)//4)**2*16 for i in range(11)))
        for shape in self.shapes.values():
            if shape.get('name')=='BentWornBlade':
                uv={v.get('t0') for v in shape.find('Vertices')}
                self.assertGreaterEqual(len(uv),8)

    def test_current_folding_and_sound_references(self):
        self.assertIsNone(self.v.find('foldable'))
        self.assertIsNone(self.v.find('animations'))
        self.assertIsNone(self.v.find('cylindered'));self.assertIsNotNone(self.v.find('twinch/blade'))
        self.assertEqual(self.paths['wheelBackLeft'],self.paths['rearLeft'])
        self.assertEqual(self.paths['wheelBackRight'],self.paths['rearRight'])

    def test_archive(self):
        with ZipFile(HERE.parent/'FS25_TWinch_v06.zip') as z:
            self.assertIsNone(z.testzip())
            for name in ['modDesc.xml','twinch.xml','twinch.i3d','scripts/TWinch.lua']:self.assertIn(name,z.namelist())
        d=E.parse(OUT/'modDesc.xml').getroot()
        self.assertEqual(d.get('descVersion'),'114');self.assertEqual(d.find('version').text,'0.6.0.0')
        self.assertEqual(d.find('multiplayer').get('supported'),'false')
        typ=d.find('vehicleTypes/type');specs=[n.get('name') for n in typ]
        self.assertNotIn('cylindered',specs);self.assertNotIn('foldable',specs)

    def test_camera_parent_and_positive_zoom(self):
        cam=self.resolve('outdoorCamera');orbit=self.resolve('cameraTarget')
        self.assertEqual(cam.tag,'Camera');self.assertIn(cam,list(orbit))
        self.assertEqual(cam.get('translation'),'0 0 6');self.assertEqual(cam.get('rotation'),'0 0 0')
        cfg=self.v.find('enterable/cameras/camera');self.assertEqual(cfg.get('rotateNode'),'cameraTarget')
        self.assertEqual(cfg.get('translation'),'0 0 6')
        self.assertLess(float(cfg.get('transMin')),6);self.assertGreater(float(cfg.get('transMax')),6)
        self.assertEqual(cfg.get('resetCameraOnVehicleSwitch'),'true')
        theta=math.radians(float(cfg.get('rotation').split()[0]))
        # For a 180-degree yaw, the camera starts behind the body and above its pivot.
        y=1.2-6*math.sin(theta);z=-6*math.cos(theta)
        self.assertGreater(y,2.5);self.assertLess(z,-5)

    def test_left_mouse_full_axis(self):
        d=E.parse(OUT/'modDesc.xml').getroot()
        action=next(n for n in d.find('actions') if n.get('name')=='TWINCH_BLADE_LIFT')
        self.assertEqual(action.get('axisType'),'FULL')
        labels={n.get('name') for n in d.find('l10n')}
        self.assertIn('input_TWINCH_BLADE_LIFT_1',labels);self.assertIn('input_TWINCH_BLADE_LIFT_2',labels)
        ab=next(n for n in d.find('inputBinding') if n.get('action')=='TWINCH_BLADE_LIFT')
        self.assertEqual({n.get('axisComponent') for n in ab},{'+','-'})
        self.assertEqual({n.get('input') for n in ab},{'MOUSE_BUTTON_LEFT AXIS_MOUSE_Y','KEY_pageup','KEY_pagedown'})
        for n in ab:
            self.assertEqual(n.get('inputComponent'),n.get('axisComponent') if 'MOUSE' in n.get('input') else '+')

    def test_blade_rises_and_stays_clear(self):
        blade=self.resolve('bladeLift');pivot=list(map(float,blade.get('translation').split()))
        lo,hi=-28,0
        vertices=[]
        for n in blade.iter('Shape'):
            vertices.extend(tuple(map(float,p.get('p').split())) for p in self.shapes[n.get('shapeId')].find('Vertices'))
        # Only directly baked blade meshes have no local hydraulic transform.
        vertices=[]
        for n in blade:
            if n.tag=='Shape':vertices.extend(tuple(map(float,p.get('p').split())) for p in self.shapes[n.get('shapeId')].find('Vertices'))
        def minheight(angle):
            t=math.radians(angle);return min(pivot[1]+p[1]*math.cos(t)-p[2]*math.sin(t) for p in vertices)
        self.assertGreater(minheight(lo),minheight(hi)+.30)
        for i in range(29):self.assertGreater(minheight(-i),0)
        # Wire fairlead and blade collider remain children of the moving assembly.
        self.assertIn(self.resolve('winchAnchor'),list(blade))
        self.assertIn(self.resolve('bladeCollision'),list(blade))

    def test_hydraulic_coverage_and_endpoint_alignment(self):
        parts=self.v.find('twinch/blade')
        for key,value in parts.attrib.items():self.resolve(value)
        for side in ['Left','Right']:
            base=list(map(float,self.resolve('hydraulic'+side+'BasePin').get('translation').split()))
            pin=list(map(float,self.resolve('hydraulic'+side+'BladePin').get('translation').split()))
            pivot=list(map(float,self.resolve('bladeLift').get('translation').split()))
            for deg in range(29):
                a=math.radians(-deg)
                target=[pivot[0]+pin[0],pivot[1]+math.cos(a)*pin[1]-math.sin(a)*pin[2],pivot[2]+math.sin(a)*pin[1]+math.cos(a)*pin[2]]
                length=math.dist(base,target)
                # Barrels 0.52 m and rods 0.55 m overlap at all supported blade positions.
                self.assertGreater(length,.55);self.assertLess(length,.52+.55)
            self.assertEqual(parts.get(side+'Pin'),'hydraulic'+side+'BladePin')
            self.assertEqual(parts.get(side+'Base'),'hydraulic'+side+'BasePin')

    def test_winching_controller_unchanged(self):
        old=(HERE/'TWinch.lua').read_text();new=(OUT/'scripts/TWinch.lua').read_text()
        for name in ['trackPose','updateTracks','updateWinch','actionConnect','ropeTension']:
            begin=old.index('function TWinch.'+name+'(')
            end=old.find('\nfunction ',begin+1)
            block=old[begin:end if end!=-1 else len(old)].rstrip()
            self.assertIn(block,new)

class V06LuaTests(previous.LuaTests):
    def setUp(self):
        super().setUp()
        self.lua.execute("g_currentModName='FS25_TWinch_v06'")
        self.lua.execute((OUT/'scripts/TWinch.lua').read_text())

    def setup_blade(self):
        self.run_lua('''
          vehicle.spec_twinch.blade={node=30,input=0,angle=0,parts={{node=31,target=33},{node=34,target=32}}}
          nodes[30]={x=0,y=.7,z=1.2};nodes[31]={x=.76,y=.91,z=1.13};nodes[32]={x=.76,y=.91,z=1.13}
          nodes[33]={x=.76,y=1.63,z=1.77};nodes[34]={x=.76,y=1.63,z=1.77}
          directionCalls={}
          local oldRotation=setRotation
          function setRotation(n,x,y,z)
            oldRotation(n,x,y,z)
            if n==30 then
              nodes[33].y=.7+.93*math.cos(x)-.57*math.sin(x)
              nodes[33].z=1.2+.93*math.sin(x)+.57*math.cos(x)
              nodes[34].y=nodes[33].y;nodes[34].z=nodes[33].z
            end
          end
          function localDirectionToWorld(n,x,y,z) return x,y,z end
          function setWorldDirection(n,x,y,z,ux,uy,uz) directionCalls[n]={x,y,z} end
        ''')

    def test_input_tick_blade_and_piston_alignment(self):
        self.setup_blade()
        self.run_lua('''
          TWinch.actionBlade(vehicle,0,1,nil,false,false)
          TWinch.onUpdateTick(vehicle,100)
          assert(math.abs(vehicle.spec_twinch.blade.angle+1.2)<1e-9)
          assert(math.abs(rotations[30][1]-math.rad(-1.2))<1e-9)
          for part,target in pairs({[31]=33,[34]=32}) do
            local dx=nodes[target].x-nodes[part].x
            local dy=nodes[target].y-nodes[part].y
            local dz=nodes[target].z-nodes[part].z
            local len=math.sqrt(dx*dx+dy*dy+dz*dz)
            assert(math.abs(directionCalls[part][2]-dy/len)<1e-9)
            assert(math.abs(directionCalls[part][3]-dz/len)<1e-9)
          end
          TWinch.actionBlade(vehicle,0,-1,nil,false,false);TWinch.onUpdateTick(vehicle,100)
          assert(vehicle.spec_twinch.blade.angle==0)
        ''')

    def test_limits_motor_mouse_delta_and_timeout(self):
        self.setup_blade()
        self.run_lua('''
          for i=1,60 do TWinch.actionBlade(vehicle,0,1,nil,false,false);TWinch.updateBlade(vehicle,100) end
          assert(vehicle.spec_twinch.blade.angle==-28)
          vehicle.engine=false;TWinch.actionBlade(vehicle,0,-1,nil,false,false);TWinch.updateBlade(vehicle,100)
          assert(vehicle.spec_twinch.blade.angle==-28)
          vehicle.engine=true;TWinch.actionBlade(vehicle,0,-1,nil,true,true);TWinch.updateBlade(vehicle,100)
          local angle=vehicle.spec_twinch.blade.angle;TWinch.updateBlade(vehicle,100)
          assert(vehicle.spec_twinch.blade.angle==angle)
          TWinch.actionBlade(vehicle,0,-1,nil,false,false);TWinch.updateBlade(vehicle,100)
          angle=vehicle.spec_twinch.blade.angle;TWinch.updateBlade(vehicle,300)
          assert(vehicle.spec_twinch.blade.angle==angle)
          TWinch.onLeaveVehicle(vehicle);assert(vehicle.spec_twinch.blade.input==0)
        ''')

    def test_registered_event_reaches_blade_controller(self):
        self.setup_blade()
        self.run_lua('''
          InputAction={} -- custom mod names are deliberately absent from the built-in table
          GS_PRIO_HIGH=1;g_inputBinding={setActionEventText=function()end,setActionEventTextPriority=function()end,setActionEventTextVisibility=function()end}
          vehicle.spec_twinch.actionEvents={};registered={}
          function vehicle:clearActionEventsTable(t) end
          function vehicle:addActionEvent(t,action,object,callback,up,down,always,active)
            registered[action]={object=object,callback=callback,always=always};return true,action
          end
          TWinch.onRegisterActionEvents(vehicle,true)
          assert(registered['TWINCH_BLADE_LIFT']~=nil and registered['TWINCH_BLADE_LIFT'].always)
          assert(registered['TWINCH_CONNECT'] and registered['TWINCH_REEL'] and registered['TWINCH_PAYOUT'])
          registered['TWINCH_BLADE_LIFT'].callback(registered['TWINCH_BLADE_LIFT'].object,1,1,nil,false,false)
          TWinch.onUpdateTick(vehicle,100);assert(vehicle.spec_twinch.blade.angle<0)
          registered={};TWinch.onRegisterActionEvents(vehicle,false,false);assert(next(registered)==nil)
          TWinch.onRegisterActionEvents(vehicle,false,true);assert(registered['TWINCH_BLADE_LIFT']~=nil)
        ''')

    def test_blade_schema_node_loading_and_saved_position(self):
        self.setup_blade()
        self.run_lua('''
          vehicle.customEnvironment='FS25_TWinch_v06'
          local ids={node=30,RightBarrel=31,RightBase=32,RightPin=33,RightRod=34,LeftBarrel=31,LeftBase=32,LeftPin=33,LeftRod=34}
          vehicle.xmlFile={getValue=function(self,key,default) return ids[key:match('#(.+)$')] or default end}
          local saved={xmlFile={getValue=function(self,key,default) assert(key=='vehicles.vehicle(0).FS25_TWinch_v06.twinch#bladeAngle');return -17 end},key='vehicles.vehicle(0)'}
          TWinch.loadBlade(vehicle,saved)
          assert(vehicle.spec_twinch.blade.node==30 and #vehicle.spec_twinch.blade.parts==4)
          assert(vehicle.spec_twinch.blade.angle==-17)
          assert(math.abs(rotations[30][1]-math.rad(-17))<1e-9)
          TWinch.loadBlade(vehicle,nil);assert(vehicle.spec_twinch.blade.angle==0)
          local keys={};local schema={register=function(self,typ,key) keys[key]=true end,setXMLSpecializationType=function()end}
          Vehicle={xmlSchema=schema,xmlSchemaSavegame=schema};XMLValueType={NODE_INDEX=1,FLOAT=2}
          TWinch.initSpecialization()
          assert(keys['vehicle.twinch.blade#node'])
          assert(keys['vehicles.vehicle(?).FS25_TWinch_v06.twinch#bladeAngle'])
        ''')

    def test_save_blade_angle(self):
        self.setup_blade()
        self.run_lua('''
          vehicle.spec_twinch.blade.angle=-17
          local values={};local xml={setValue=function(self,key,value) values[key]=value end}
          TWinch.saveToXMLFile(vehicle,xml,'vehicles.vehicle(0).FS25_TWinch_v06.twinch',{})
          assert(values['vehicles.vehicle(0).FS25_TWinch_v06.twinch#bladeAngle']==-17)
        ''')

if __name__=='__main__':
    suite=unittest.TestSuite([
        unittest.defaultTestLoader.loadTestsFromTestCase(V06PackageTests),
        unittest.defaultTestLoader.loadTestsFromTestCase(V06LuaTests)])
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report=json.loads((OUT/'validation.json').read_text())
    report.update(local_tests_run=result.testsRun,local_test_failures=len(result.failures),local_test_errors=len(result.errors),native_engine_input_and_physics='not run')
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    with ZipFile(HERE.parent/'FS25_TWinch_v06.zip','w',ZIP_DEFLATED) as z:
        for f in sorted(OUT.rglob('*')):
            if f.is_file():z.write(f,f.relative_to(OUT))
    raise SystemExit(0 if result.wasSuccessful() else 1)
