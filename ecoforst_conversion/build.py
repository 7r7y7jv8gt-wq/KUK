"""Convert the supplied original Ecoforst/Tajfun FS22 asset set to an FS25 candidate."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import sys,shutil,re,json,hashlib,xml.etree.ElementTree as E
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;SRC=Path(sys.argv[1]);OUT=ROOT/'FS25_EcoforstTWinch'
assert (SRC/'T_Winch.i3d.shapes').stat().st_size==37588676
shutil.copytree(SRC,OUT,dirs_exist_ok=True)
(OUT/'conversion_audit.json').unlink(missing_ok=True)
(OUT/'script/FS25Compatibility.lua').unlink(missing_ok=True)
def save(tree,path):E.indent(tree);tree.write(path,encoding='utf-8',xml_declaration=True)
d=E.parse(OUT/'modDesc.xml');d.getroot().set('descVersion','114');d.find('version').text='1.0.0.1'
d.find('title/en').text='Ecoforst T-Winch 30.2 – FS25'
d.find('description/en').text='FS25 conversion of the original PauloModding / Paul Redshaw T-Winch. Original model, crawlers, hydraulic blade, lights, sounds and logging winch retained. Requires in-game validation.'
# Original custom brand/category images were not supplied: use a stock brand and supplied shop image.
brands=d.find('brands');d.getroot().remove(brands)
for t in d.findall('vehicleTypes/type'):
 t.set('name','ecoforstTWinch' if t.get('name')=='T_Winch' else 'ecoforstTowHook')
 for n in list(t):t.remove(n)
 if t.get('name')=='ecoforstTWinch':E.SubElement(t,'specialization',name='logsWinch')
# Native type inheritance is inspected before adding required specializations.
# Compatibility bridge is appended to the specialization so its class exists before helpers load.
for key,text in [('function_towHook','Tethering hook for winch recovery'),('typeDesc_towHook','Tethering Hook')]:
 if d.find("l10n/text[@name='"+key+"']") is None:E.SubElement(E.SubElement(d.find('l10n'),'text',name=key),'en').text=text
save(d,OUT/'modDesc.xml')
# Correct local sound case/extensions and eliminate references to missing source-only assets.
localFiles={str(p.relative_to(OUT)).lower():str(p.relative_to(OUT)) for p in OUT.rglob('*') if p.is_file()}
def normalize_local(name):
 if name.startswith('$'):return name
 normalized=name.replace('\\','/')
 if normalized.lower() in localFiles:return localFiles[normalized.lower()]
 if normalized.lower().endswith('.wav') and normalized[:-4].lower()+'.ogg' in localFiles:return localFiles[normalized[:-4].lower()+'.ogg']
 return name
for name in ['T_Winch.xml','TowHook.xml','Sounds/D11T.xml']:
 r=E.parse(OUT/name)
 for n in r.iter():
  for k,value in list(n.attrib.items()):
   if k in ['file','filename','image']:n.set(k,normalize_local(value))
  if n.tag=='sound' and n.get('file')=='$data/sounds/horn.wav':n.set('file','Sounds/train_horn_loop.ogg')
 if name=='T_Winch.xml':
  r.getroot().set('type','ecoforstTWinch');r.find('storeData/brand').text='LIZARD'
  r.find('base/components/component').set('solverIterationCount','30')
  r.find('motorized/exhaustEffects/exhaustEffect').set('maxRpmScale','0.12')
  # Explicit normalized curve avoids reliance on the deprecated FS22 rpm attribute.
  motor=r.find('motorized/motorConfigurations/motorConfiguration/motor')
  for n in motor:
   n.set('normRpm',str(float(n.attrib.pop('rpm'))/float(motor.get('maxRpm'))))
  # Pair all three wheels on each physical side correctly.
  wheels=r.findall('wheels/wheelConfigurations/wheelConfiguration/wheels/wheel')
  for i,wheel in enumerate(wheels):wheel.set('isLeft','true' if i<3 else 'false');wheel.set('hasTireTracks','false');wheel.find('physics').set('tireType','crawler')
  diff=r.find('motorized/differentialConfigurations/differentialConfiguration/differentials')
  for n in list(diff):diff.remove(n)
  for attrs in [dict(wheelIndex1='1',wheelIndex2='3',torqueRatio='.5',maxSpeedRatio='1'),dict(wheelIndex1='4',wheelIndex2='6',torqueRatio='.5',maxSpeedRatio='1'),dict(differentialIndex1='1',wheelIndex2='2',torqueRatio=str(2/3),maxSpeedRatio='1'),dict(differentialIndex1='2',wheelIndex2='5',torqueRatio=str(2/3),maxSpeedRatio='1'),dict(differentialIndex1='3',differentialIndex2='4',torqueRatio='.5',maxSpeedRatio='2')]:E.SubElement(diff,'differential',**attrs)
  crawlers=r.findall('wheels/wheelConfigurations/wheelConfiguration/crawlers/crawler')
  crawlers[0].set('wheelIndices','1 2 3');crawlers[1].set('wheelIndices','4 5 6')
  # Input dependencies absent from source are not mandatory for this conversion.
  ic=r.find('interactiveControl');r.getroot().remove(ic)
  lw=r.find('logsWinch');lw.set('maxChainLength',lw.attrib.pop('maxLength'))
  removable=lw.find('removableTrailerHook');removable.attrib.pop('switchAnimation',None);removable.set('spawnRemoved','false')
  # Original animation removeHook does not exist; retain mounted towing hook.
  # Native power consumer is required by the winch PTO and motor load calculations.
  pc=E.SubElement(r.getroot(),'powerConsumer',ptoRpm='450',neededMinPtoPower='1',neededMaxPtoPower='10')
 elif name=='TowHook.xml':r.getroot().set('type','ecoforstTowHook');r.find('storeData/image').text='storeT_Winch.dds'
 else:
  for n in r.iter():
   if n.get('file','').endswith('bigX1180_loop.gls'):n.set('file','Sounds/bulldozerIdle.ogg')
   if n.get('file','').endswith('transmissionLoop.wav'):n.set('file','Sounds/transmissionOld.ogg')
 save(r,OUT/name)
# Remove duplicated crawler rollers; same-relative-node entries otherwise animate twice.
r=E.parse(OUT/'leitwolfCrawler/leitwolfCrawler.xml');seen=set()
for n in list(r.find('rotatingParts')):
 if n.get('node') in seen:r.find('rotatingParts').remove(n)
 else:seen.add(n.get('node'))
save(r,OUT/'leitwolfCrawler/leitwolfCrawler.xml')
# Modern collision filters and FS25 shader variants; geometry binaries are preserved.
shaderVariants={'colorMask':'','Decal':'decal','Decal_colorMask':'decal','uvScale_colorMask':'uvScale','uvScroll_colorMask':'uvScroll','motionPathRubber_secondUV_colorMask':'motionPath_vmaskUV2','motionPath_secondUV_colorMask':'motionPath_vmaskUV2'}
for p in OUT.rglob('*.i3d'):
 r=E.parse(p);files=r.find('Files');mats=r.find('Materials');nextId=max((int(n.get('fileId')) for n in files),default=0)
 def file(path):
  global nextId
  found=next((n for n in files if n.get('filename')==path),None)
  if found is not None:return found.get('fileId')
  nextId+=1;E.SubElement(files,'File',fileId=str(nextId),filename=path);return str(nextId)
 shaders={n.get('fileId') for n in files if n.get('filename')=='$data/shaders/vehicleShader.xml'}
 for m in mats:
  if m.get('customShaderId') not in shaders:continue
  variant=m.get('customShaderVariation','');new=shaderVariants.get(variant,variant)
  if new:m.set('customShaderVariation',new)
  else:m.attrib.pop('customShaderVariation',None)
  for n in list(m):
   if n.tag=='CustomParameter' and n.get('name')=='RDT':n.set('name','scratches_dirt_snow_wetness')
   if n.tag=='Custommap' and n.get('name')=='mTrackArray':n.set('name','trackArray')
  if m.find("CustomParameter[@name='scratches_dirt_snow_wetness']") is None:E.SubElement(m,'CustomParameter',name='scratches_dirt_snow_wetness',value='0 0 0 0')
  if 'colorMask' in variant:
   color=m.find("CustomParameter[@name='colorMat0']")
   if color is not None:
    rgb=color.get('value').split()[:3];m.set('diffuseColor','1 1 1 1');E.SubElement(m,'CustomParameter',name='colorScale',value=' '.join(rgb))
   for n in list(m):
    if n.tag=='CustomParameter' and n.get('name','').startswith('colorMat'):m.remove(n)
   for key,path in [('detailDiffuse','calibrated/calibratedPaint_diffuse.png'),('detailNormal','flat_normal.png'),('detailSpecular','calibrated/calibratedPaint_specular.png')]:E.SubElement(m,'Custommap',name=key,fileId=file('$data/shared/detailLibrary/'+path))
  if variant=='staticLight':
   for n in list(m):
    if n.tag=='CustomParameter' and n.get('name','').startswith('colorMat'):m.remove(n)
   E.SubElement(m,'CustomParameter',name='lightIds',value='1 1 1 1');E.SubElement(m,'CustomParameter',name='lightControl',value='0 0 0 0')
  if variant.startswith('Decal'):m.set('alphaBlending','true')
 for n in r.find('Scene').iter():
  if 'collisionMask' in n.attrib:
   n.attrib.pop('collisionMask');n.set('collisionFilterGroup','0x10004');n.set('collisionFilterMask','0xfe3ffb83')
  if n.get('trigger')=='true':n.set('collisionFilterGroup','0x40000000');n.set('collisionFilterMask','0x00100000')
 save(r,p)
# Repair references reported by the real FS25 purchase log.
for name in ['T_Winch.xml','TowHook.xml','Sounds/D11T.xml']:
 r=E.parse(OUT/name)
 for n in r.iter('category'):n.text='forestryMachines'
 invalid={'DEFAULT_BLOW_OFF_VALVE','WATER_SPLASH_01','SWITCH_01','SWITCH_TURNLIGHT','defaultHydraulicSound','ATTACH_01'}
 for parent in r.iter():
  for n in list(parent):
   if n.get('template') in invalid:parent.remove(n)
 save(r,OUT/name)
for p in OUT.rglob('Lizard_RKLE_150_*.xml'):
 r=E.parse(p)
 for n in r.iter():
  for key in ['node','shaderNode']:
   if n.get(key,'').startswith('0|'):n.set(key,'0>'+n.get(key)[2:])
 save(r,p)
for p in [OUT/'T_Winch.i3d',OUT/'leitwolfCrawler/leitwolfCrawler.i3d']:
 r=E.parse(p)
 for n in r.find('Files'):
  if 'raptor300_vmask' in n.get('filename',''):n.set('filename','$data/shared/default_diffuse.png')
  if 'raptor300_normal' in n.get('filename',''):n.set('filename','$data/shared/detailLibrary/flat_normal.png')
 save(r,p)
# Port the original script's inputs, player API, raycasts, and custom XML schema.
p=OUT/'script/logsWinch.lua';s=p.read_text(encoding='utf-8-sig')
s=s.replace('Player.INPUT_CONTEXT_NAME','PlayerInputComponent.INPUT_CONTEXT_NAME')
s=s.replace('MathUtil.clamp','lwClamp')
s=s.replace('Utils.getNoNil','lwValue').replace('unpack(','lwUnpack(').replace('math.atan2','lwAtan2')
s=s.replace('g_currentMission.playerUserId','(g_localPlayer~=nil and g_localPlayer.userId or 0)')
s=s.replace('g_currentMission.player','LogsWinch.getPlayer()')
s=s.replace('g_currentMission.controlPlayer','(g_localPlayer~=nil and not g_localPlayer:getIsInVehicle())')
s=s.replace('g_currentMission.isPlayerFrozen','(g_localPlayer==nil)')
s=s.replace('callback, 4, self, 0x1000000','4, callback, self, CollisionFlag.TREE+CollisionFlag.DYNAMIC_OBJECT+CollisionFlag.VEHICLE')
s=s.replace('callback, 3, self, 0x1000000','3, callback, self, CollisionFlag.TREE+CollisionFlag.DYNAMIC_OBJECT+CollisionFlag.VEHICLE')
s=s.replace('"lwChainInterstRaycastCallback", 2, self, 0x1000','2, "lwChainInterstRaycastCallback", self, CollisionFlag.TREE+CollisionFlag.DYNAMIC_OBJECT+CollisionFlag.VEHICLE')
s=s.replace('self.lwSoundSample.winchingLoad = 0','if self.lwSoundSample~=nil then self.lwSoundSample.winchingLoad = 0 end')
s=s.replace('-- update winching sound samples\n\tif self:getIsTurnedOn() then','-- update winching sound samples\n\tif self:getIsTurnedOn() and self.lwSoundSample~=nil then')
s=s.replace('self:playAnimation(self.lwTrailerHookAnim, 1, animTime)','self:playAnimation(self.lwTrailerHookAnim, 1, 0)')
s=s.replace('getShaderParameter(self.lwRopeShape, "RDT")','LogsWinch.readWear(self.lwRopeShape)')
s=s.replace('setShaderParameter(self.lwAttachedShapesChainNodes[idx], "RDT", x, y, z, w)','LogsWinch.writeWear(self.lwAttachedShapesChainNodes[idx],x,y,z,w)')
s=s.replace('setShaderParameter(hook, "RDT", x, y, z, w)','LogsWinch.writeWear(hook,x,y,z,w)')
s=s.replace('local playerNode = LogsWinch.getPlayer().model.pickUpKinematicHelperNode','local playerNode = LogsWinch.getPlayerNode()')
s=s.replace('if playerNode == nil then','if playerNode == nil or node==nil or not entityExists(node) then')
s=s.replace('self.onRegisterActionEvents\t\t\t= LogsWinch.onRegisterActionEvents','self.lwRegisterActionEvents = LogsWinch.onRegisterActionEvents')
s=s.replace('self:onRegisterActionEvents(', 'self:lwRegisterActionEvents(')
s=s.replace('winchSpec:onRegisterActionEvents(', 'winchSpec:lwRegisterActionEvents(')
# Nil action IDs are normal when on-foot and vehicle controls use different contexts.
s=re.sub(r'g_inputBinding:setActionEventActive\(self.lwActionEventIds\["([A-Z_]+)"\], ([^\n]+)\)',r'LogsWinch.setEventActive(self,"\1", \2)',s)
s=s.replace('if canAttachDetach then','if canAttachDetach and self.lwActionEventIds["LOGSWINCH_ATTACH_DETACH"]~=nil then')
s=s.replace('if oldRegistrationContext ~= InputBinding.NO_REGISTRATION_CONTEXT then','if oldRegistrationContext~=nil and oldRegistrationContext~=InputBinding.NO_REGISTRATION_CONTEXT then')
s=s.replace('g_soundManager:stopSample(self.lwSoundSample)', 'if self.lwSoundSample~=nil then g_soundManager:stopSample(self.lwSoundSample) end')
s=s.replace('g_soundManager:stopSample(self.lwChainAttachSndSample)','if self.lwChainAttachSndSample~=nil then g_soundManager:stopSample(self.lwChainAttachSndSample) end')
s=s.replace('g_soundManager:stopSample(self.lwChainDetachSndSample)','if self.lwChainDetachSndSample~=nil then g_soundManager:stopSample(self.lwChainDetachSndSample) end')
# Failed loads must be safe to update and delete without masking the original error.
s=s.replace('function LogsWinch:onLoadFinished(savegame)', 'function LogsWinch:onLoadFinished(savegame)\n if self.lwSkinnedRopeJoints==nil then return end')
s=s.replace('function LogsWinch:onUpdate(dt)', 'function LogsWinch:onUpdate(dt)\n if self.lwAttachedShapes==nil then return end')
s=s.replace('function LogsWinch:onPreDelete()', 'function LogsWinch:onPreDelete()\n if self.lwAttachedShapes==nil then return end')
s=s.replace('function lwDetachAllEvent.sendEvent(vehicle, noEventSend)', 'function lwDetachAllEvent.sendEvent(vehicle, noEventSend)\n if vehicle.lwAttachedShapes==nil then return end')
# Dedicated server does not have a local player: keep network physics, skip local input.
marker='\tlocal isThisActiveWinch = (self.lwWinchIdx == LogsWinch.ActiveWinchIdx)'
# Insert a context refresh before the existing client UI branch, not before the physics update.
needle='\t-- keep currently active whinch alive all the time,'
s=s.replace(needle,"\tif not self.isClient or g_localPlayer==nil then return end\n\tlocal playerMode=not g_localPlayer:getIsInVehicle()\n\tif self.lwInputPlayerMode~=playerMode then self.lwInputPlayerMode=playerMode;self:lwRegisterActionEvents(isActiveForInput) end\n\n"+needle)
# Original RDT reads are guarded above; all remaining legacy helper names are local.
s='local lwClamp=function(x,a,b) return math.max(a,math.min(b,x)) end\nlocal lwValue=function(value,default) if value==nil then return default end return value end\nlocal lwUnpack=unpack or table.unpack\nlocal lwAtan2=math.atan2 or math.atan\n'+s
# Build typed schema registrations directly from all the original XML reads.
regs=[];varPaths={'key':'vehicle.logsWinch','skinnedRopeKey':'vehicle.logsWinch.skinnedRope','dynamicChainKey':'vehicle.logsWinch.dynamicChain','attacherKey':'vehicle.logsWinch.overridenInputAttacher','trailerHookKey':'vehicle.logsWinch.removableTrailerHook'}
for method,var,suffix in re.findall(r'self\.xmlFile:get(Float|Int|Bool|String)\((\w+)\s*\.\.\s*"([^"]+)"\)',s):
 if var in varPaths:regs.append(({'Float':'FLOAT','Int':'INT','Bool':'BOOL','String':'STRING'}[method],varPaths[var]+suffix))
regs += [('INT','vehicle.logsWinch.skinnedRope#jointsCount'),('STRING','vehicle.logsWinch.ropesUVScroll.rope1#index'),('STRING','vehicle.logsWinch.ropesUVScroll.rope2#index')]
s+='\nfunction LogsWinch.initSpecialization()\n local schema=Vehicle.xmlSchema\n schema:setXMLSpecializationType("LogsWinch")\n'
for typ,path in sorted(set(regs)):s+=f' schema:register(XMLValueType.{typ},"{path}","Original winch configuration")\n'
s+=' SoundManager.registerSampleXMLPaths(schema,"vehicle.logsWinch.sounds","winching")\n SoundManager.registerSampleXMLPaths(schema,"vehicle.logsWinch.sounds","chainAttach")\n SoundManager.registerSampleXMLPaths(schema,"vehicle.logsWinch.sounds","chainDetach")\n schema:setXMLSpecializationType()\nend\n'
s+='\n'+(HERE/'FS25Compatibility.lua').read_text()
p.write_text(s,encoding='utf-8')
hashes={str(p.relative_to(SRC)):hashlib.sha256(p.read_bytes()).hexdigest() for p in SRC.rglob('*.shapes')}
(OUT/'geometry_checksums.json').write_text(json.dumps(hashes,indent=2)+'\n')
(OUT/'CONVERSION_README.txt').write_text('Original Ecoforst T-Winch 30.2 FS22-to-FS25 conversion candidate.\nOriginal authors: PauloModding and Paul Redshaw; source assets supplied by user.\nZIP geometry restored from split archive; original CRC f76a4312 verified.\nAll compiled .shapes files preserved exactly; XML/Lua adaptations do not replace the original machine with the earlier Follvik model.\nFS25 native type inheritance, player input contexts, raycast argument order, collision filters, motor curve schema, crawler shaders, six-wheel drive and sound references updated.\nB attaches/detaches an object you aim at; Z winches, Shift+Z fast winches, X releases rope, Shift+B detaches all in vehicle, Shift+G switches active winch.\nTurn on the winch with native implement control first. Hydraulic blade uses native frontloader arm controls.\nTethering Hook remains a separate store item.\nOriginal 10t logging winch load and original engine/speed/weight configuration retained.\nMissing source brand/category icons use Lizard and the supplied machine store image.\nOptional FS22 Interactive Control plugin section removed; native central-cover folding remains. Missing removeHook animation is disabled; towing hook remains mounted.\nFS25 runtime, compiled geometry loading, stock texture availability, visual shader appearance and multiplayer require in-game verification; GIANTS Editor/FS25 are unavailable here.\nInstall FS25_EcoforstTWinch.zip unchanged in mods; disable the original FS22 mod.\n')
with ZipFile(ROOT/'FS25_EcoforstTWinch.zip','w',ZIP_DEFLATED) as z:
 for p in sorted(OUT.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(OUT))
print('Built',OUT,'archive bytes', (ROOT/'FS25_EcoforstTWinch.zip').stat().st_size)
