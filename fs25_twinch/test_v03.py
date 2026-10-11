"""Native camera/control configuration and hydraulic kinematics regressions.

Run with Pillow and lupa installed. Engine behavior still requires FS25 testing.
"""
from pathlib import Path
import xml.etree.ElementTree as E
from zipfile import ZipFile,ZIP_DEFLATED
import unittest,math,json,hashlib
import test_v02 as previous

HERE=Path(__file__).resolve().parent;OUT=HERE.parent/'FS25_TWinch_v03'
previous.OUT=OUT

class V03PackageTests(previous.PackageTests):
    def test_current_folding_and_sound_references(self):
        self.assertIsNone(self.v.find('foldable'))
        self.assertIsNone(self.v.find('animations'))
        self.assertIsNotNone(self.v.find('cylindered/movingTools/movingTool'))
        self.assertEqual(self.paths['wheelBackLeft'],self.paths['rearLeft'])
        self.assertEqual(self.paths['wheelBackRight'],self.paths['rearRight'])

    def test_archive(self):
        with ZipFile(HERE.parent/'FS25_TWinch_v03.zip') as z:
            self.assertIsNone(z.testzip())
            for name in ['modDesc.xml','twinch.xml','twinch.i3d','scripts/TWinch.lua']:self.assertIn(name,z.namelist())
        d=E.parse(OUT/'modDesc.xml').getroot()
        self.assertEqual(d.get('descVersion'),'114');self.assertEqual(d.find('version').text,'0.3.0.0')
        self.assertEqual(d.find('multiplayer').get('supported'),'false')
        typ=d.find('vehicleTypes/type');specs=[n.get('name') for n in typ]
        self.assertIn('cylindered',specs);self.assertNotIn('foldable',specs)

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
        action=next(n for n in d.find('actions') if n.get('name')=='TWINCH_BLADE')
        self.assertEqual(action.get('axisType'),'FULL')
        ab=next(n for n in d.find('inputBinding') if n.get('action')=='TWINCH_BLADE')
        self.assertEqual({n.get('axisComponent') for n in ab},{'+','-'})
        for n in ab:
            self.assertEqual(n.get('input'),'MOUSE_BUTTON_LEFT AXIS_MOUSE_Y')
            self.assertEqual(n.get('inputComponent'),n.get('axisComponent'))
        tool=self.v.find('cylindered/movingTools/movingTool')
        self.assertEqual(tool.find('controls').get('axis'),'TWINCH_BLADE')
        self.assertEqual(tool.get('allowSaving'),'true')

    def test_blade_rises_and_stays_clear(self):
        blade=self.resolve('bladeLift');pivot=list(map(float,blade.get('translation').split()))
        rot=self.v.find('cylindered/movingTools/movingTool/rotation')
        self.assertEqual(rot.get('rotationAxis'),'1')
        lo,hi=float(rot.get('rotMin')),float(rot.get('rotMax'));self.assertEqual((lo,hi),(-28,0))
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
        parts=self.v.findall('cylindered/movingParts/movingPart');self.assertEqual(len(parts),4)
        for p in parts:
            self.resolve(p.get('referenceFrame'));self.resolve(p.get('referencePoint'))
            self.assertEqual(p.get('isActiveDirty'),'true');self.assertEqual(p.get('scaleZ'),'false')
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
            body=next(p for p in parts if p.get('node')=='hydraulic'+side+'Barrel')
            rod=next(p for p in parts if p.get('node')=='hydraulic'+side+'Rod')
            self.assertEqual(body.get('referencePoint'),'hydraulic'+side+'BladePin')
            self.assertEqual(rod.get('referencePoint'),'hydraulic'+side+'BasePin')

    def test_winching_controller_unchanged(self):
        a=(OUT/'scripts/TWinch.lua').read_bytes();b=(HERE.parent/'FS25_TWinch_v02/scripts/TWinch.lua').read_bytes()
        self.assertEqual(hashlib.sha256(a).digest(),hashlib.sha256(b).digest())

if __name__=='__main__':
    suite=unittest.TestSuite([
        unittest.defaultTestLoader.loadTestsFromTestCase(V03PackageTests),
        unittest.defaultTestLoader.loadTestsFromTestCase(previous.LuaTests)])
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report=json.loads((OUT/'validation.json').read_text())
    report.update(local_tests_run=result.testsRun,local_test_failures=len(result.failures),local_test_errors=len(result.errors),native_engine_input_and_physics='not run')
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    with ZipFile(HERE.parent/'FS25_TWinch_v03.zip','w',ZIP_DEFLATED) as z:
        for f in sorted(OUT.rglob('*')):
            if f.is_file():z.write(f,f.relative_to(OUT))
    raise SystemExit(0 if result.wasSuccessful() else 1)
