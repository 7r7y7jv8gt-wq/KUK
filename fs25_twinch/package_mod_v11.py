"""Install the supplied Volvo EC380 crawler mesh and native crawler controller."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import shutil,xml.etree.ElementTree as E,json
HERE=Path(__file__).resolve().parent;OUT=HERE.parent/'FS25_TWinch_v11'
shutil.copytree(HERE.parent/'FS25_TWinch_v10',OUT,dirs_exist_ok=True)
assets=OUT/'crawlers/volvo';assets.mkdir(parents=True,exist_ok=True)
source=HERE.parent/'../attachments'
sources={
 'ec380DLCrawler.i3d':Path('/workspace/attachments/6704c172-f3a3-420c-87a1-b6e86aeb70ee/ec380DLCrawler.i3d'),
 'ec380DLCrawler.i3d.shapes':Path('/workspace/attachments/95b7ac1f-9289-40ef-83cf-9023d15deb32/ec380DLCrawler.i3d.shapes'),
 'ec380DLCrawler.xml':Path('/workspace/attachments/ba51f5c4-5f4c-4bac-894a-f7cbd89d5233/ec380DLCrawler.xml')}
for name,path in sources.items():shutil.copy2(path,assets/name)
i=E.parse(assets/'ec380DLCrawler.i3d').getroot()
# Initial fit of the large-excavator crawler to the existing 3.08m T-Winch
# loop. Compiled motion-path geometry needs an in-game size check.
for group in i.find('Scene'):group.set('scale','.65 .8 .65')
c=E.parse(assets/'ec380DLCrawler.xml').getroot();c.find('file').set('name','crawlers/volvo/ec380DLCrawler.i3d')
c.find('scrollerNodes/scrollerNode').set('scrollSpeed',str(-.09*.96/.65))
for tree,name in [(i,'ec380DLCrawler.i3d'),(c,'ec380DLCrawler.xml')]:E.indent(tree);E.ElementTree(tree).write(assets/name,encoding='utf-8',xml_declaration=True)
v=E.parse(OUT/'twinch.xml').getroot();d=E.parse(OUT/'modDesc.xml').getroot();r=E.parse(OUT/'twinch.i3d').getroot()
for node in r.find('Scene').iter():
 if node.get('name') in ['trackLeft','trackRight']:
  # Keep internal linkage nodes for wheel animation, but only show Volvo shoes.
  for link in node:link.set('visibility','false')
configuration=v.find('wheels/wheelConfigurations/wheelConfiguration');crawlers=E.SubElement(configuration,'crawlers')
for side,wheels in [('Left','1 3'),('Right','2 4')]:
 E.SubElement(crawlers,'crawler',filename='crawlers/volvo/ec380DLCrawler.xml',linkNode='track'+side,isLeft=str(side=='Left').lower(),wheelIndices=wheels,trackWidth='1',offset='0 0 0')
script=(OUT/'scripts/TWinch.lua').read_text().replace('track.count = getNumOfChildren(track.node)','track.count = math.min(74,getNumOfChildren(track.node))')
script+='''
-- Add native crawler support exactly once, before type validation. Some base
-- types already inherit Crawlers; redeclaring it would reject the vehicle.
local volvoCrawlerVehicleType=g_currentModName..'.twinchV11'
function TWinch.installVolvoCrawlers(manager)
    if manager.typeName~='vehicle' then return end
    local vehicleType=manager.types[volvoCrawlerVehicleType]
    if vehicleType~=nil and not SpecializationUtil.hasSpecialization(Crawlers,vehicleType.specializations) then
        manager:addSpecialization(volvoCrawlerVehicleType,'crawlers')
    end
end
if TypeManager~=nil then
    TypeManager.validateTypes=Utils.prependedFunction(TypeManager.validateTypes,TWinch.installVolvoCrawlers)
end
'''
(OUT/'scripts/TWinch.lua').write_text(script)
v.set('type','twinchV11');d.find('vehicleTypes/type').set('name','twinchV11');d.find('version').text='0.11.0.0';d.find('title/en').text='T-Winch v11 - Volvo Crawler Tracks'
for n in v.findall('storeData/name/*'):n.text='T-Winch 30.2 v11'
d.find('description/en').text='Uploaded Volvo EC380 DLC crawler mesh, native scrolling/motion-path materials and mud meshes fitted to T-Winch. Blade, protected small hooks, drivetrain and TerraFarm retained. In-game fit validation pending.'
index=E.parse(OUT/'machineConfigurations.xml').getroot();index.find('configuration').set('vehicle','FS25_TWinch_v11/twinch.xml')
for tree,name in [(v,'twinch.xml'),(d,'modDesc.xml'),(r,'twinch.i3d'),(index,'machineConfigurations.xml')]:E.indent(tree);E.ElementTree(tree).write(OUT/name,encoding='utf-8',xml_declaration=True)
(OUT/'TESTING.txt').write_text('''T-Winch v11: supplied Volvo EC380 DLC crawler tracks
Disable older T-Winch versions, install unopened ZIP and buy a fresh v11.
The supplied external I3D and compiled shapes provide both track LODs and
mud meshes; all materials use stock FS25 shader/detail/track-array resources.
Native Crawlers scrolls each track using its own side's powered wheels.
Old procedural shoes are hidden; T-Winch still animates its running wheels.
A 74-node limit keeps the asynchronous native track out of the old animator.
Initial crawler fitting scale: .65 width, .8 height, .65 length. This is an
estimate because compiled motion-path shapes cannot be inspected here.
Check track width/height/length, orientation, frame clearance, ground contact,
forward/reverse and skid steering in FS25. Stock resource availability also
requires actual engine verification. No GIANTS Editor / FS25 test run here.
Blade, small protected hook and logging controls are retained: R at blade,
R at tree/log, hold Z to reel, X to pay out, Shift+R release; engine on.
TerraFarm work edge remains on the moving blade. Existing Engelsen pack can
remain installed: this vehicle includes its own equivalent v11 registry.
''')
(OUT/'CREDITS.txt').write_text((OUT/'CREDITS.txt').read_text()+'Volvo EC380 DLC crawler I3D/XML/compiled geometry supplied by user from excavator mod; original mesh/material names retained. Stock textures/shaders referenced, not redistributed.\n')
(OUT/'validation.json').write_text(json.dumps({'version':'0.11.0.0','game_test':'not run','crawler':'user-supplied ec380DLCrawler.i3d/.shapes/XML','initial_fit_scale':[.65,.8,.65],'native_controller':'Crawlers, separate wheel indices per side','compiled_geometry_fit':'unverified in engine'},indent=2)+'\n')
with ZipFile(HERE.parent/'FS25_TWinch_v11.zip','w',ZIP_DEFLATED) as z:
 for f in sorted(OUT.rglob('*')):
  if f.is_file():z.write(f,f.relative_to(OUT))
print('Built',OUT)
