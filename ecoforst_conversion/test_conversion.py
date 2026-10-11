from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import unittest,json,hashlib,xml.etree.ElementTree as E
from lupa import LuaRuntime
ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'FS25_EcoforstTWinch'
class PackageTests(unittest.TestCase):
 def test_original_geometry_preserved_and_crc(self):
  for name,digest in json.loads((OUT/'geometry_checksums.json').read_text()).items():self.assertEqual(hashlib.sha256((OUT/name).read_bytes()).hexdigest(),digest)
  import zlib
  self.assertEqual(zlib.crc32((OUT/'T_Winch.i3d.shapes').read_bytes()),0xf76a4312)
 def test_all_local_assets_and_xml_scene_nodes(self):
  for p in OUT.rglob('*.i3d'):
   r=E.parse(p)
   self.assertTrue((p.parent/r.find('Shapes').get('externalShapesFile')).is_file())
   for n in r.find('Files'):
    name=n.get('filename')
    if not name.startswith('$'):self.assertTrue((p.parent/name).is_file(),(p,name))
  for filename in ['T_Winch.xml','TowHook.xml']:
   r=E.parse(OUT/filename);scene=E.parse(OUT/r.find('base/filename').text).find('Scene');maps={n.get('id'):n.get('node') for n in r.findall('i3dMappings/i3dMapping')}
   for n in r.iter():
    for k,value in n.attrib.items():
     value=maps.get(value,value)
     if value.startswith('0>'):
      a,_,b=value.partition('>');obj=scene[int(a)]
      for i in b.split('|') if b else []:obj=obj[int(i)]
  for p in OUT.rglob('*.xml'):
   if p.parent.name=='shaders':continue
   for n in E.parse(p).iter():
    for k,value in n.attrib.items():
     if k in ['file','filename','i3dFilename'] and value.endswith(('.wav','.ogg','.xml','.i3d','.dds','.gls')) and not value.startswith('$'):self.assertTrue((OUT/value).is_file(),(p,value))
 def test_all_six_wheels_powered_and_grouped_per_side(self):
  v=E.parse(OUT/'T_Winch.xml');d=v.findall('motorized/differentialConfigurations/differentialConfiguration/differentials/differential')
  def leaves(i):
   n=d[i-1];out=[]
   for side in ['1','2']:
    if n.get('wheelIndex'+side):out.append(int(n.get('wheelIndex'+side)))
    else:
     child=int(n.get('differentialIndex'+side));self.assertLess(child,i);out+=leaves(child)
   return out
  self.assertEqual(sorted(leaves(3)),[1,2,3]);self.assertEqual(sorted(leaves(4)),[4,5,6]);self.assertEqual(sorted(leaves(5)),list(range(1,7)))
  wheel=v.findall('wheels/wheelConfigurations/wheelConfiguration/wheels/wheel');self.assertEqual(len(wheel),6)
  self.assertEqual(v.find('motorized/exhaustEffects/exhaustEffect').get('maxRpmScale'),'0.12')
  for n in v.findall('motorized/motorConfigurations/motorConfiguration/motor/torque'):self.assertIn('normRpm',n.attrib);self.assertNotIn('rpm',n.attrib)
 def test_fs25_descriptor_shader_aliases_and_archive(self):
  d=E.parse(OUT/'modDesc.xml');self.assertEqual(d.getroot().get('descVersion'),'114')
  for t in d.findall('vehicleTypes/type'):
   names=[n.get('name') for n in t];self.assertEqual(len(names),len(set(names)))
  for p in OUT.rglob('*.i3d'):
   for n in E.parse(p).find('Materials'):self.assertNotIn('colorMask',n.get('customShaderVariation',''))
  with ZipFile(ROOT/'FS25_EcoforstTWinch.zip') as z:self.assertIsNone(z.testzip())
class LuaTests(unittest.TestCase):
 def setUp(self):
  self.lua=LuaRuntime(unpack_returned_tuples=True)
  self.lua.execute('''
    g_currentModDirectory='mod/';g_currentModName='FS25_EcoforstTWinch'
    PlayerInputComponent={INPUT_CONTEXT_NAME='PLAYER'};Vehicle={INPUT_CONTEXT_NAME='VEHICLE'}
    GS_PRIO_VERY_HIGH=3;GS_PRIO_HIGH=2;GS_PRIO_VERY_LOW=1
    InputBinding={NO_REGISTRATION_CONTEXT='NONE'}
    Event={new=function(mt)return setmetatable({},mt)end}
    function Class(t,base)local mt={__index=t};setmetatable(t,{__index=base});return mt end
    function InitEventClass()end
    TypeManager={validateTypes=function()end}
    Utils={getFilename=function(name,dir)return dir..name end,
      appendedFunction=function(a,b)return function(...)a(...);return b(...)end end,
      prependedFunction=function(a,b)return function(...)b(...);return a(...)end end,
      overwrittenFunction=function(a,b)return function(self,...)return b(self,a,...)end end}
    MathUtil={clamp=function(x,a,b)return math.max(a,math.min(b,x))end,vector3Length=function(x,y,z)return math.sqrt(x*x+y*y+z*z)end}
    SoundManager={registerSampleXMLPaths=function()end}
    AudioGroup={VEHICLE=1};CollisionFlag={TREE=1,DYNAMIC_OBJECT=2,VEHICLE=4}
    nodes={};nextNode=10000
    function entityExists(n)return nodes[n]~=nil end
    function getWorldTranslation(n)local v=nodes[n];return v.x or 0,v.y or 0,v.z or 0 end
    function setTranslation(n,x,y,z)nodes[n].x=x;nodes[n].y=y;nodes[n].z=z end
    function localToWorld(n,x,y,z)local a,b,c=getWorldTranslation(n);return x+a,y+b,z+c end
    function getParent(n)return nodes[n].parent or 0 end
    function createTransformGroup()nextNode=nextNode+1;nodes[nextNode]={x=0,y=0,z=0,children={}};return nextNode end
    function getChildAt(n,i)return nodes[n].children[i+1]end
    function getNumOfChildren(n)return #nodes[n].children end
    function getTranslation(n)return getWorldTranslation(n)end
    function setVisibility()end
    function setRotation()end
    function getRotation()return 0,0,0 end
    function setScale()end
    function worldToLocal(n,x,y,z)local a,b,c=getWorldTranslation(n);return x-a,y-b,z-c end
    function localDirectionToWorld(n,x,y,z)return x,y,z end
    function setWorldDirection()end
    function setDirection()end
    function getShaderParameter()return 0,0,0,0 end
    function setShaderParameter()end
    function getHasShaderParameter()return false end
    function getTerrainHeightAtWorldPos()return 0 end
    g_soundManager={loadSampleFromXML=function()return nil end,registerModifierType=function()return 1 end}
    g_i3DManager={loadSharedI3DFile=function()return 0,1 end}
    g_i18n={getText=function(_,key)if key=='info_activeWinchDetached' then return '%s. %s' else return key end end}
    SpecializationUtil={registerEventListener=function()end,hasSpecialization=function(s,l)for _,v in ipairs(l)do if s==v then return true end end return false end}
    I3DUtil={indexToObject=function(root,path)
      if path==nil then return nil end
      local a,b=path:match('^(%d+)>(.*)$');local n
      if a then n=root[tonumber(a)+1].node else n=root;b=path end
      for i in b:gmatch('%d+')do if n==nil then return nil end;n=getChildAt(n,tonumber(i))end
      return n
    end}
    vehicle={isServer=true,isClient=true,rootNode=118,components={{node=118}},configFileName='T_Winch.xml',isVehicleSaved=true,
      spec_powerConsumer={ptoRpm=450},getPtoRpm=function()return 450 end,getIsActiveForInput=function()return false end,
      getDoConsumePtoPower=function()return false end,raiseActive=function()end,getRootVehicle=function(self)return self end,getIsActive=function()return true end}
    g_storeManager={xmlFilenameToItem={['t_winch.xml']={name='T-Winch'}}}
    g_currentMission={terrainRootNode=0,connectedToDedicatedServer=false}
  ''')
  scene=E.parse(OUT/'T_Winch.i3d').find('Scene')
  for n in scene.iter():
   if n.get('nodeId'):
    coords=list(map(float,n.get('translation','0 0 0').split()));ident=int(n.get('nodeId'));node=self.lua.table_from(dict(x=coords[0],y=coords[1],z=coords[2]));node['children']=self.lua.table_from([int(c.get('nodeId')) for c in n]);self.lua.globals().nodes[ident]=node
  values={}
  def walk(n,key):
   for k,v in n.attrib.items():values[key+'#'+k]=v
   for c in n:walk(c,key+'.'+c.tag)
  walk(E.parse(OUT/'T_Winch.xml').getroot(),'vehicle');self.lua.globals().config=self.lua.table_from(values)
  self.lua.execute('''
    vehicle.xmlFile={getString=function(_,key)return config[key]end,getFloat=function(_,key)return tonumber(config[key])end,
      getInt=function(_,key)return tonumber(config[key])end,getBool=function(_,key)if config[key]==nil then return nil end;return config[key]=='true'end,
      hasProperty=function(_,key)if config[key]~=nil then return true end;for k in pairs(config)do if k:sub(1,#key)==key then return true end end;return false end}
  ''')
  self.lua.execute((OUT/'script/logsWinch.lua').read_text())
 def test_schema_registers_original_winch_configuration(self):
  self.lua.execute('''
    XMLValueType={FLOAT=1,INT=2,STRING=3,BOOL=4};registered={}
    Vehicle.xmlSchema={setXMLSpecializationType=function()end,register=function(_,kind,key)registered[key]=kind end}
    LogsWinch.initSpecialization()
    assert(registered['vehicle.logsWinch#jointRefNode']==3)
    assert(registered['vehicle.logsWinch#winchingSpeed']==1)
    assert(registered['vehicle.logsWinch.skinnedRope#jointsCount']==2)
  ''')
 def test_load_no_sound_failure_and_native_event_method_preserved(self):
  self.lua.execute('''
    local native=function()end;vehicle.onRegisterActionEvents=native
    LogsWinch.onLoad(vehicle,nil)
    assert(vehicle.lwInitialized and vehicle.lwJointRefNode~=nil)
    assert(vehicle.lwRopeLength==100 and vehicle.lwMaxWinchingMass==10 and vehicle.lwMaxChainLength==20)
    assert(#vehicle.lwSkinnedRopeJoints==21)
    assert(vehicle.onRegisterActionEvents==native and vehicle.lwRegisterActionEvents==LogsWinch.onRegisterActionEvents)
    assert(vehicle.lwSoundSample==nil)
    LogsWinch.onLoadFinished(vehicle,nil)
  ''')
 def test_server_update_without_local_player_or_sound(self):
  self.lua.execute("""
    LogsWinch.onLoad(vehicle,nil)
    vehicle.isClient=false;vehicle.getIsTurnedOn=function()return true end
    g_localPlayer=nil
    LogsWinch.onUpdate(vehicle,16)
    assert(vehicle.lwInitialized)
  """)
 def test_player_bridge_and_distance_without_old_mission_player(self):
  self.lua.execute('''
    assert(g_currentMission.player==nil and LogsWinch:lwGetPlayerDistanceTo(118)>0)
    nodes[9999]={x=1,y=2,z=3,children={}};nodes[9998]={x=0,y=0,z=0,children={}}
    g_localPlayer={rootNode=9998,userId=7,getCurrentCameraNode=function()return 9999 end,getIsInVehicle=function()return false end}
    local p=LogsWinch.getPlayer();assert(p.isObjectInRange and p.cameraNode==9999)
    local x,y,z=getWorldTranslation(p.model.pickUpKinematicHelperNode);assert(x==1 and y==2 and z==1)
    assert(LogsWinch.getPlayerNode()==9998)
    assert(LogsWinch:lwGetPlayerDistanceTo(118)>=0)
  ''')
 def test_player_and_vehicle_action_contexts_and_nil_ids(self):
  self.lua.execute('''
    LogsWinch.onLoad(vehicle,nil);events={};context=nil
    g_inputBinding={registrationContext='NONE',removeActionEvent=function()end,
      beginActionEventsModification=function(_,c)context=c end,endActionEventsModification=function()context=nil end,
      registerActionEvent=function(_,name,obj,callback)events[name]={context=context,callback=callback};return true,name end,
      setActionEventText=function()end,setActionEventTextPriority=function()end,setActionEventTextVisibility=function()end,
      setActionEventActive=function(_,id)assert(id~=nil)end}
    LogsWinch.onRegisterActionEvents(vehicle,false);assert(events.LOGSWINCH_ATTACH_DETACH.context=='PLAYER')
    assert(events.LOGSWINCH_WINCH_PLAYER.context=='PLAYER' and events.LOGSWINCH_WINCH_VEHICLE==nil)
    LogsWinch.setEventActive(vehicle,'LOGSWINCH_WINCH_VEHICLE',true)
    events={};LogsWinch.onRegisterActionEvents(vehicle,true)
    assert(events.LOGSWINCH_WINCH_VEHICLE.context=='VEHICLE' and events.LOGSWINCH_ATTACH_DETACH==nil)
  ''')
 def test_types_add_native_specs_once(self):
  self.lua.execute('''
    Wheels={};Crawlers={};Cylindered={};Foldable={};Wearable={};Washable={};PowerConsumer={};TurnOnVehicle={};Attachable={}
    local t={specializations={Wheels}}
    local m={typeName='vehicle',types={['FS25_EcoforstTWinch.ecoforstTWinch']=t},calls={}}
    function m:addSpecialization(name,spec)
      assert(self.calls[spec]==nil);self.calls[spec]=true
      local classes={wheels=Wheels,crawlers=Crawlers,cylindered=Cylindered,foldable=Foldable,wearable=Wearable,washable=Washable,powerConsumer=PowerConsumer,turnOnVehicle=TurnOnVehicle,attachable=Attachable}
      table.insert(t.specializations,classes[spec])
    end
    EcoforstFS25.installTypes(m);assert(m.calls.wheels==nil and m.calls.crawlers and m.calls.powerConsumer)
    EcoforstFS25.installTypes(m)
  ''')
 def test_fs25_raycast_signature_and_winching_joint_limit(self):
  self.lua.execute('''
    LogsWinch.onLoad(vehicle,nil)
    local calls=0
    function raycastClosest(x,y,z,dx,dy,dz,length,callback,object,mask)
      assert(type(length)=='number' and type(callback)=='string' and mask==7);calls=calls+1
    end
    vehicle:lwAttachDetachObject(0,0,-2,0,0,0,false);assert(calls==2)
    vehicle.getIsTurnedOn=function()return true end
    local ref=createTransformGroup('target');setTranslation(ref,0,0,10)
    vehicle.lwAttachedShapesRefNodes={ref};vehicle.lwJoints={1};vehicle.lwCurrAttachedShapesMass=5;vehicle.lwCurrJointZLimit=20
    jointCalls=0;function setJointTranslationLimit(id,axis,enabled,min,max)assert(id==1 and axis==2 and min<0);jointCalls=jointCalls+1 end
    lwWinchFeedbackEvent.sendEvent=function()end
    LogsWinch.WinchingTimer=0;vehicle:lwWinch(false,7);assert(jointCalls==1 and vehicle.lwCurrJointZLimit<20)
    local limit=vehicle.lwCurrJointZLimit;vehicle.lwCurrAttachedShapesMass=11
    LogsWinch.WinchingTimer=0;vehicle:lwWinch(false,7);assert(vehicle.lwCurrJointZLimit==limit)
  ''')
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(c) for c in [PackageTests,LuaTests]))
 (OUT/'validation.json').write_text(json.dumps({'source':'Original FS22 Ecoforst T-Winch','conversion':'FS25 candidate','local_tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'game_test':'not run','original_geometry_crc32':'f76a4312'},indent=2)+'\n')
 with ZipFile(ROOT/'FS25_EcoforstTWinch.zip','w',ZIP_DEFLATED) as z:
  for p in sorted(OUT.rglob('*')):
   if p.is_file():z.write(p,p.relative_to(OUT))
 raise SystemExit(not result.wasSuccessful())
