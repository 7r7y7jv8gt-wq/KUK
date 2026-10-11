"""Bundle the original logo texture and enable transparent decal rendering."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import shutil,xml.etree.ElementTree as E,json,hashlib
from PIL import Image
ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'FS25_Follvik_TVinsj_v27'
shutil.copytree(ROOT/'FS25_Follvik_TVinsj_v26',OUT,dirs_exist_ok=True)
source=ROOT/'FollvikLogo/adstrip_vierkant.dds'
target=OUT/'textures/follvik_logo.dds';shutil.copyfile(source,target)
im=Image.open(target)
assert im.mode=='RGBA' and im.getchannel('A').getextrema()==(0,255)
r=E.parse(OUT/'twinch.i3d');material=r.find("Materials/Material[@materialId='3647']")
material.set('alphaBlending','true');material.set('diffuseColor','1 1 1 1');material.set('specularColor','0 0 0')
fileId=material.find('Texture').get('fileId')
r.find("Files/File[@fileId='"+fileId+"']").set('filename','textures/follvik_logo.dds')
logos=[n for n in r.find('Scene').iter('Shape') if n.get('name')=='FollvikLogo']
assert len(logos)==3 and all(n.get('materialIds')=='3647' for n in logos)
blade=next(n for n in r.find('Scene').iter() if n.get('name')=='bladeLift')
assert next(n for n in logos if n.get('nodeId')=='665') in list(blade)
for f in r.find('Files'):
 name=f.get('filename')
 if not name.startswith('$'):assert (OUT/name).is_file(),name
E.indent(r);r.write(OUT/'twinch.i3d',encoding='utf-8',xml_declaration=True)
for name in ['modDesc.xml','twinch.xml','machineConfigurations.xml']:
 p=OUT/name;r=E.parse(p)
 if name=='modDesc.xml':r.find('version').text='0.27.0.0';r.find('vehicleTypes/type').set('name','twinchV27')
 elif name=='twinch.xml':r.getroot().set('type','twinchV27')
 else:r.find('configuration').set('vehicle','FS25_Follvik_TVinsj_v27/twinch.xml')
 E.indent(r);r.write(p,encoding='utf-8',xml_declaration=True)
p=OUT/'scripts/TWinch.lua';p.write_text(p.read_text().replace('twinchV26','twinchV27'))
p=OUT/'source_asset_hashes.json';hashes=json.loads(p.read_text());hashes['twinch.i3d']=hashlib.sha256((OUT/'twinch.i3d').read_bytes()).hexdigest();hashes['textures/follvik_logo.dds']=hashlib.sha256(source.read_bytes()).hexdigest();p.write_text(json.dumps(hashes,indent=2)+'\n')
(OUT/'validation.json').write_text(json.dumps({'version':'0.27.0.0','game_test':'not run','logo_texture_bundled':True,'original_texture_preserved':True,'alpha_range':[0,255],'transparent_logo_material':True,'logo_count':3,'all_main_i3d_local_assets_resolve':True,'front_logo_parent':'bladeLift'},indent=2)+'\n')
(OUT/'TESTING.txt').write_text((OUT/'TESTING.txt').read_text()+'\nV27: original logo DDS bundled in textures/follvik_logo.dds.\nRemoved external Ponsse texture dependency; alpha blending enabled on all three logos.\nFront logo remains parented to the hydraulic blade. Texture alpha and all main scene file references verified.\n')
with ZipFile(ROOT/'FS25_Follvik_TVinsj_v27.zip','w',ZIP_DEFLATED) as z:
 for p in sorted(OUT.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(OUT))
with ZipFile(ROOT/'FS25_Follvik_TVinsj_v27.zip') as z:
 assert z.testzip() is None
 assert z.read('textures/follvik_logo.dds')==source.read_bytes()
print('Verified bundled DDS alpha, transparent material, all three logos, blade parent and file references.')
