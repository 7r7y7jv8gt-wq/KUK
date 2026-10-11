"""Packaged Lua event/state/force regressions and TerraFarm configuration checks."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import xml.etree.ElementTree as E
import unittest,json
import test_v07 as old
HERE=Path(__file__).resolve().parent;OUT=HERE.parent/'FS25_TWinch_v08'
old.OUT=OUT;old.previous.OUT=OUT
class PackageTests(old.V07PackageTests):
    def test_archive(self):
        with ZipFile(HERE.parent/'FS25_TWinch_v08.zip') as z:
            self.assertIsNone(z.testzip())
            self.assertIn('winch/chainMaterialHolder.i3d.shapes',z.namelist())
            self.assertNotIn('tajfunEGV80AHK.i3d',z.namelist())
            self.assertIn('machineConfigurations.xml',z.namelist())
        self.assertEqual(E.parse(OUT/'modDesc.xml').find('version').text,'0.8.0.0')
    def test_terrafarm_discovery_and_material_unit(self):
        config=E.parse(OUT/'machineConfigurations.xml').find('configuration')
        self.assertEqual(config.get('vehicle'),'FS25_TWinch_v08/twinch.xml')
        machine=E.parse(OUT/config.get('file')).find('machine')
        self.assertEqual(machine.get('type'),'leveler')
        self.assertEqual(machine.find('input').get('modes'),'FLATTEN SMOOTH LOWER PAINT')
        edge=self.resolve(machine.find('workArea').get('referenceNode'))
        self.assertIn(edge,list(self.resolve('bladeLift')))
        self.assertEqual(edge.get('translation'),'0 -0.605 0.9375')
        self.assertEqual(machine.find('workArea').get('width'),'2.23')
        units=self.v.findall('fillUnit/fillUnitConfigurations/fillUnitConfiguration/fillUnits/fillUnit')
        self.assertEqual(units[0].get('fillTypes'),'diesel')
        self.assertEqual(units[1].get('fillTypeCategories'),'bulk')
        self.assertEqual(self.v.find('leveler/levelerNode').get('fillUnitIndex'),'2')
        self.assertEqual(machine.get('fillUnitIndex'),'2')
        specs=[n.get('name') for n in E.parse(OUT/'modDesc.xml').find('vehicleTypes/type')]
        self.assertEqual(specs.count('leveler'),1)
        self.assertNotIn('fillUnit',specs) # inherited; duplicate stock specializations break loading
    def test_private_asset_references(self):
        asset=E.parse(OUT/'winch/chainMaterialHolder.i3d').getroot()
        self.assertIsNone(asset.find('UserAttributes'))
        for f in asset.find('Files'):
            if not f.get('filename').startswith('$data/'):self.assertTrue((OUT/'winch'/f.get('filename')).is_file())
        self.assertEqual([n.get('name') for n in asset.find('Scene')[0]],['material','dummyMaterial','hook'])
        for n in self.v.find('twinch/logging/sounds'):
            self.assertTrue((OUT/n.get('file')).is_file())
            self.assertEqual(len(list(n.iter('modifier'))),0)
class RegressionTests(old.V07LuaTests):
    def setUp(self):
        super().setUp()
        self.run_lua('SoundManager={registerSampleXMLPaths=function()end}')
class LoggingTests(unittest.TestCase):
    run_lua=old.previous.LuaTests.run_lua
    # Avoid running inherited cases twice.
    def setUp(self):
        old.previous.LuaTests.setUp(self)
        self.lua.execute("g_currentModName='FS25_TWinch_v08'")
        self.lua.execute((OUT/'scripts/TWinch.lua').read_text())
        self.run_lua('''
        CollisionFlag={TREE=16,DYNAMIC_OBJECT=32,VEHICLE=64};RigidBodyType.STATIC=0
        GS_PRIO_HIGH=1;PlayerInputComponent={INPUT_CONTEXT_NAME='PLAYER'}
        function bitAND(x,y) return x & y end
        function getParent(n) return nodes[n] and nodes[n].parent or 0 end
        function getCollisionFilterGroup(n) return nodes[n].group or 32 end
        function getRigidBodyType(n) return nodes[n].body or 1 end
        function localDirectionToWorld(n,x,y,z) return x,y,z end
        function getWorldTranslation(n)
            local p=nodes[n]
            if p.relative and p.parent and p.parent~=0 then
                local x,y,z=getWorldTranslation(p.parent);return x+p.x,y+p.y,z+p.z
            end
            return p.x,p.y,p.z
        end
        function setWorldTranslation(n,x,y,z)
            local p=nodes[n]
            if p.parent and p.parent~=0 then local a,b,c=getWorldTranslation(p.parent);p.relative=true;p.x=x-a;p.y=y-b;p.z=z-c
            else p.x=x;p.y=y;p.z=z end
        end
        function setWorldDirection(n,x,y,z,ux,uy,uz) assert(x==x and y==y and z==z) end
        function setScale(n,x,y,z) end
        function link(parent,n) nodes[n].parent=parent end
        function delete(n) nodes[n]=nil end
        nextNode=100
        function createTransformGroup(name) nextNode=nextNode+1;nodes[nextNode]={x=0,y=0,z=0,mass=0};return nextNode end
        function clone(n) return createTransformGroup('clone') end
        function getTerrainHeightAtWorldPos(n,x,y,z) return 0 end
        notifications={};function g_currentMission:addIngameNotification(_,text) table.insert(notifications,text) end
        nodes[4]={x=0,y=0,z=0};nodes[5]={x=0,y=1,z=1};nodes[6]={x=0,y=1.6,z=1}
        playerInVehicle=false;menu=false
        g_gui={getIsGuiVisible=function()return menu end}
        g_localPlayer={getIsInVehicle=function()return playerInVehicle end,
          getHandsKinematicNode=function()return 5 end,getCurrentCameraNode=function()return 6 end}
        g_currentMission.terrainRootNode=999
        events={};active={};eventText={};context=nil
        g_inputBinding={beginActionEventsModification=function(_,c)context=c end,
          endActionEventsModification=function()context=nil end,
          registerActionEvent=function(_,name,object,callback,up,down,always)
            assert(context=='PLAYER');events[name]={object=object,callback=callback,always=always};return true,name end,
          setActionEventText=function(_,id,text)eventText[id]=text end,
          setActionEventTextPriority=function()end,setActionEventTextVisibility=function()end,
          setActionEventActive=function(_,id,value)active[id]=value end,
          removeActionEvent=function(_,id)events[id]=nil end}
        function fire(name,value) events[name].callback(events[name].object,name,value or 1) end
        g_i3DManager={loadSharedI3DFile=function()return 0,9 end,releaseSharedI3DFile=function()end}
        Utils={getFilename=function(name,dir)return name end};Logging={warning=function()end}
        g_soundManager=nil
        vehicle.spec_twinch.target=nil
        BladeWinch.load(vehicle);s=vehicle.spec_twinch.logging
        rayHits={}
        function raycastAll(x,y,z,dx,dy,dz,length,callback,self,mask)
            for _,h in ipairs(rayHits) do self[callback](self,h.node,h.x,h.y,h.z,h.d) end
        end
        BladeWinch.update(BladeWinch,16)
        ''')
    def test_registered_walkup_take_attach_dynamic_pull_release(self):
        self.run_lua('''
        assert(events.TWINCH_HOOK and not events.TWINCH_HOOK.always)
        assert(events.TWINCH_LOG_REEL.always and active.TWINCH_HOOK)
        fire('TWINCH_HOOK');assert(s.carrying)
        nodes[2].mass=6;nodes[5].z=8;nodes[6].z=8
        rayHits={{node=2,x=0,y=0,z=10,d=2}}
        BladeWinch.update(BladeWinch,16);fire('TWINCH_HOOK')
        assert(not s.carrying and #s.targets==1 and s.targets[1].node==2)
        local initial=s.length
        fire('TWINCH_LOG_REEL');BladeWinch.tick(vehicle,100)
        assert(s.length<initial and #forces==2)
        assert(forces[1].node==1 and forces[2].node==2)
        assert(math.abs(forces[1].z+forces[2].z)<1e-10)
        assert(forces[1].z>0 and forces[2].z<0)
        assert(nodes[1].z==0 and nodes[2].z==10)
        BladeWinch.update(BladeWinch,16)
        assert(visibility[s.segments[1]])
        local ref=s.targets[1].ref
        fire('TWINCH_LOG_CLEAR');assert(#s.targets==0 and not s.carrying and not entityExists(ref))
        assert(not visibility[s.segments[1]])
        ''')
    def test_fixed_tree_anchor_only_moves_chassis(self):
        self.run_lua('''
        fire('TWINCH_HOOK')
        nodes[20]={x=0,y=0,z=15,body=0,group=16,mass=0}
        rayHits={{node=20,x=0,y=1,z=15,d=2}}
        fire('TWINCH_HOOK');assert(s.targets[1].static)
        fire('TWINCH_LOG_FAST');BladeWinch.tick(vehicle,100)
        assert(#forces==1 and forces[1].node==1 and forces[1].z>0)
        assert(nodes[20].z==15)
        local n=#s.targets
        BladeWinch.attach(s,{node=2,shape=2,x=0,y=0,z=10,static=false})
        assert(#s.targets==n)
        ''')
    def test_engine_gate_payout_timeout_gui_and_vehicle(self):
        self.run_lua('''
        fire('TWINCH_HOOK');rayHits={{node=2,x=0,y=0,z=10,d=2}};fire('TWINCH_HOOK')
        local length=s.length
        vehicle.engine=false;fire('TWINCH_LOG_REEL');BladeWinch.tick(vehicle,100);assert(s.length==length)
        fire('TWINCH_LOG_OUT');BladeWinch.tick(vehicle,100);assert(s.length>length)
        BladeWinch.update(BladeWinch,300);assert(s.reel==0 and s.payout==0)
        menu=true;BladeWinch.update(BladeWinch,16);assert(not active.TWINCH_HOOK)
        fire('TWINCH_LOG_CLEAR');assert(#s.targets==1)
        menu=false;playerInVehicle=true;BladeWinch.update(BladeWinch,16);assert(not active.TWINCH_HOOK)
        fire('TWINCH_LOG_CLEAR');assert(#s.targets==1)
        ''')
    def test_self_static_scenery_and_mass_rejected(self):
        self.run_lua('''
        nodes[22]={x=0,y=0,z=2,parent=1,body=1}
        nodes[23]={x=0,y=0,z=3,body=0,group=0}
        rayHits={{node=22,x=0,y=0,z=2,d=1},{node=23,x=0,y=0,z=3,d=2}}
        fire('TWINCH_HOOK');fire('TWINCH_HOOK');assert(s.carrying and #s.targets==0)
        nodes[2].mass=9;rayHits={{node=2,x=0,y=0,z=10,d=2}}
        fire('TWINCH_HOOK');assert(s.carrying and #s.targets==0)
        ''')
    def test_additional_log_reaction_and_deleted_target_cleanup(self):
        self.run_lua('''
        nodes[2].mass=3
        nodes[24]={x=0,y=0,z=13,mass=2}
        fire('TWINCH_HOOK');rayHits={{node=2,x=0,y=0,z=10,d=2}};fire('TWINCH_HOOK')
        fire('TWINCH_HOOK');assert(s.carrying)
        rayHits={{node=24,x=0,y=0,z=13,d=2}};fire('TWINCH_HOOK');assert(#s.targets==2)
        nodes[24].z=14;BladeWinch.tick(vehicle,100)
        assert(#forces==2 and forces[1].node==2 and forces[2].node==24)
        assert(math.abs(forces[1].z+forces[2].z)<1e-10)
        local a,b=s.targets[1].ref,s.targets[2].ref
        nodes[24]=nil;BladeWinch.tick(vehicle,100)
        assert(#s.targets==0 and not entityExists(a) and not entityExists(b))
        ''')
    def test_far_player_no_prompt_and_hook_limit(self):
        self.run_lua('''
        nodes[5].z=30;BladeWinch.update(BladeWinch,16);assert(not active.TWINCH_HOOK)
        nodes[5].z=1;BladeWinch.update(BladeWinch,16);fire('TWINCH_HOOK')
        nodes[5].z=65;BladeWinch.update(BladeWinch,16);assert(not s.carrying)
        ''')
    def test_cleanup_releases_runtime_meshes(self):
        self.run_lua('''
        local segment=s.segments[1]
        TWinch.onDelete(vehicle)
        assert(#BladeWinch.instances==0 and not entityExists(segment))
        BladeWinch.deleteMap(BladeWinch);assert(next(events)==nil)
        ''')
    def test_loaded_hook_and_chain_geometry_are_cleaned(self):
        self.run_lua('''
        BladeWinch.delete(vehicle)
        nodes[50]={x=0,y=0,z=0};nodes[51]={x=0,y=0,z=0,parent=50}
        nodes[52]={x=0,y=0,z=0,parent=50};nodes[53]={x=0,y=0,z=0,parent=50}
        g_i3DManager.loadSharedI3DFile=function()return 50,10 end
        I3DUtil={indexToObject=function(root,path)return ({['0|0']=51,['0|1']=52,['0|2']=53})[path] end}
        function getMaterial(n,index) assert(n==51);return 7 end
        g_tensionBeltManager={getBeltData=function()return {dummyMaterial={uvScale=1}} end}
        chainFinalized=false;chainPoints=0
        TensionBeltGeometryConstructor={new=function()
            return {setWidth=function()end,setMaxEdgeLength=function()end,setMaterial=function(_,m)assert(m==7)end,
            setUVscale=function()end,setFixedPoints=function()end,setGeometryBias=function()end,setLinkNode=function()end,
            addIntersectionPoint=function()chainPoints=chainPoints+1 end,
            finalize=function()chainFinalized=true;return createTransformGroup('wrappedChain')end}
        end}
        BladeWinch.load(vehicle);s=vehicle.spec_twinch.logging
        BladeWinch.update(BladeWinch,16)
        assert(s.hook==53 and nodes[53].parent==3)
        assert(not visibility[51] and not visibility[52])
        fire('TWINCH_HOOK');rayHits={{node=2,x=0,y=0,z=10,d=2}};fire('TWINCH_HOOK')
        assert(chainFinalized and chainPoints==64 and s.targets[1].chain~=nil)
        local chain=s.targets[1].chain
        BladeWinch.clear(s);assert(not entityExists(chain))
        BladeWinch.delete(vehicle);assert(not entityExists(53) and not entityExists(50))
        ''')
    def test_terrafarm_actual_work_area_follows_lowered_blade(self):
        reference=Path('/tmp/twinch-terrafarm/scripts/MachineWorkArea.lua')
        if not reference.exists():self.skipTest('Optional upstream TerraFarm checkout unavailable')
        self.run_lua('''
        function Class(c)return {__index=c} end
        MathUtil={round=function(x)return math.floor(x+.5)end}
        MachineUtils={getHasOutputs=function()return false end}
        function setTranslation(n,x,y,z) nodes[n].x=x;nodes[n].y=y;nodes[n].z=z;nodes[n].relative=true end
        function localToWorld(n,x,y,z)
            local p=nodes[n];local angle=rotations[n] and rotations[n][1] or 0
            local ly,lz=math.cos(angle)*y-math.sin(angle)*z,math.sin(angle)*y+math.cos(angle)*z
            x=x+p.x;y=ly+p.y;z=lz+p.z
            if p.parent and p.parent~=0 then return localToWorld(p.parent,x,y,z) end
            return x,y,z
        end
        function getWorldTranslation(n)return localToWorld(n,0,0,0)end
        nodes[30]={x=0,y=.7,z=1.2,parent=1}
        local edge=createTransformGroup('terraFarmBladeEdge');link(30,edge);setTranslation(edge,0,-.605,.9375)
        tfEdge=edge
        function vehicle:getMachineType()return {useLeveler=true}end
        vehicle.spec_machine={hasLeveler=true,levelerNode={node=edge,width=2.23,yOffset=0,zOffset=0}}
        ''')
        self.lua.execute(reference.read_text())
        self.run_lua('''
        local area=MachineWorkArea.new(vehicle)
        area.width=2.23;area.referenceNode=tfEdge;area.offset={0,0,0};area.rotation={0,0,0}
        assert(area:initialize());assert(#area.areaNodes==5)
        setRotation(30,math.rad(-28),0,0);area:update();assert(not area.isAreaNodeActive)
        setRotation(30,math.rad(25),0,0);area:update();assert(area.isAreaNodeActive)
        for _,p in pairs(area.areaNodePosition)do assert(p[2]<0)end
        ''')
if __name__=='__main__':
    # Separate baseline regressions from on-foot state-machine fixtures.
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(c) for c in [PackageTests,RegressionTests,LoggingTests])
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report=json.loads((OUT/'validation.json').read_text())
    report.update(local_tests_run=result.testsRun,local_test_failures=len(result.failures),local_test_errors=len(result.errors),terrafarm_reference='scfmod/FS25_TerraFarm b50e677cdef062d605ab188f8982ae1faa2789e7')
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    with ZipFile(HERE.parent/'FS25_TWinch_v08.zip','w',ZIP_DEFLATED) as z:
        for f in sorted(OUT.rglob('*')):
            if f.is_file():z.write(f,f.relative_to(OUT))
    raise SystemExit(not result.wasSuccessful())
