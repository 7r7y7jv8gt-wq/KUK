from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import unittest,xml.etree.ElementTree as E,json
import test_v22 as baseline
ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'FS25_Follvik_TVinsj_v23'
baseline.prior.OUT=OUT;baseline.prior.old.OUT=OUT;baseline.prior.old.previous.OUT=OUT
class WinchTests(baseline.WinchTests):
 def run_lua(self,text):return baseline.prior.old.previous.LuaTests.run_lua(self,text.replace('twinchV13','twinchV23'))
class WearTests(unittest.TestCase):
 def test_preserves_uploaded_shapes_and_geometry(self):
  with ZipFile(ROOT/'fs25_twinch/user_wear_v23.zip') as z:
   for n in z.namelist():
    if n.endswith('.shapes'):self.assertEqual(z.read(n),(OUT/n).read_bytes())
 def test_native_wear_dirt_channels_and_durations(self):
  v=E.parse(OUT/'twinch.xml');r=E.parse(OUT/'twinch.i3d')
  self.assertEqual(v.find('wearable').get('wearDuration'),'1200');self.assertEqual(v.find('washable').get('dirtDuration'),'60')
  shaders={n.get('fileId') for n in r.find('Files') if n.get('filename')=='$data/shaders/vehicleShader.xml'}
  for m in r.find('Materials'):
   if m.get('customShaderId') in shaders:self.assertIsNotNone(m.find("CustomParameter[@name='scratches_dirt_snow_wetness']"))
  self.assertEqual(v.find('storeData/name/en').text,'Føllvik t vinsj')
  self.assertEqual(v.find('storeData/specs/power').text,'800');self.assertEqual(v.find('storeData/specs/maxSpeed').text,'12')
 def test_progressive_silver_restores_on_repaint_and_ignores_body(self):
  from lupa import LuaRuntime
  lua=LuaRuntime();lua.execute('''
    TWinch={};nodes={[1]={name='root',children={2,6}},[2]={name='crawlerLeft',children={3,4,5}},[3]={name='LOD0',children={}},[4]={name='LOD1',children={}},[5]={name='crawlerLeft_mudMesh',children={}},[6]={name='GreenPanel',children={}}}
    function entityExists(n)return nodes[n]~=nil end
    function getName(n)return nodes[n].name end
    function getNumOfChildren(n)return #nodes[n].children end
    function getChildAt(n,i)return nodes[n].children[i+1] end
    function getHasShaderParameter()return true end
    colors={}
    function setShaderParameter(n,param,x,y,z) if param=='colorScale' then colors[n]={x,y,z}end end
    vehicle={isClient=true,spec_twinch={},components={{node=1}},wear=0,getWearTotalAmount=function(self)return self.wear end}
  ''');lua.execute((ROOT/'fs25_twinch/TrackWear.lua').read_text());lua.execute('''
    TWinch.updateTrackWear(vehicle,1000);assert(colors[3][1]==.035 and colors[4][1]==.035 and colors[5]==nil and colors[6]==nil)
    vehicle.wear=.5;TWinch.updateTrackWear(vehicle,1000);assert(colors[3][1]>.035 and colors[3][1]<.78)
    vehicle.wear=1;TWinch.updateTrackWear(vehicle,1000);assert(math.abs(colors[3][1]-.78)<1e-8)
    vehicle.wear=0;TWinch.updateTrackWear(vehicle,1000);assert(colors[3][1]==.035)
    nodes[3]=nil;TWinch.updateTrackWear(vehicle,1000)
  ''')
 def test_native_specs_added_once(self):
  case=WinchTests();case.setUp();case.run_lua('''
    Wearable={};Washable={};Crawlers={}
    SpecializationUtil={hasSpecialization=function(spec,list)for _,s in ipairs(list)do if s==spec then return true end end return false end}
    local t={specializations={}}
    local m={typeName='vehicle',types={['FS25_TWinch_v13.twinchV23']=t},calls=0}
    function m:addSpecialization(name,spec) self.calls=self.calls+1;table.insert(t.specializations,({wearable=Wearable,washable=Washable,crawlers=Crawlers})[spec])end
    TWinch.installVolvoCrawlers(m);assert(m.calls==3)
    TWinch.installVolvoCrawlers(m);assert(m.calls==3)
  ''')
 def test_archive_and_references(self):
  with ZipFile(ROOT/'FS25_Follvik_TVinsj_v23.zip') as z:self.assertIsNone(z.testzip())
  v=E.parse(OUT/'twinch.xml');r=E.parse(OUT/'twinch.i3d')
  for m in v.find('i3dMappings'):
   a,_,b=m.get('node').partition('>');n=r.find('Scene')[int(a)]
   for i in b.split('|') if b else []:n=n[int(i)]
  for model in [r,E.parse(OUT/'crawlers/volvo/ec380DLCrawler.i3d')]:
   for f in model.find('Files'):
    name=f.get('filename')
    if not name.startswith('$'):self.assertTrue((OUT/name).is_file(),name)
  self.assertEqual(E.parse(OUT/'machineConfigurations.xml').find('configuration').get('vehicle'),'FS25_Follvik_TVinsj_v23/twinch.xml')
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(c) for c in [WinchTests,WearTests]))
 report=json.loads((OUT/'validation.json').read_text());report.update(local_tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors));(OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
 with ZipFile(ROOT/'FS25_Follvik_TVinsj_v23.zip','w',ZIP_DEFLATED) as z:
  for f in sorted(OUT.rglob('*')):
   if f.is_file():z.write(f,f.relative_to(OUT))
 raise SystemExit(not result.wasSuccessful())
