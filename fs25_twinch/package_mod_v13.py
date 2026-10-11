"""Dark steel undercarriage finish and independent, refreshed blade inputs."""
from pathlib import Path
import shutil,xml.etree.ElementTree as E,json,copy,io,struct
from zipfile import ZipFile,ZIP_DEFLATED
from PIL import Image
import numpy as np
HERE=Path(__file__).resolve().parent;OUT=HERE.parent/'FS25_TWinch_v13'
shutil.copytree(HERE.parent/'FS25_TWinch_v12',OUT,dirs_exist_ok=True)
p=OUT/'scripts/TWinch.lua';s=p.read_text()
s=s.replace('twinchV12','twinchV13').replace('_V12','_V13').replace('TWINCH_BLADE_LIFT','TWINCH_BLADE_LIFT_V13')
s=s.replace('TWinch.actionBlade,true,false,true,true','TWinch.actionBlade,true,true,true,true')
s=s.replace("        if id ~= nil then\n            g_inputBinding:setActionEventText(id,'Hydraulic blade", "        spec.blade.eventId=id\n        if id ~= nil then\n            if g_inputBinding.setActionEventActive~=nil then g_inputBinding:setActionEventActive(id,true) end\n            g_inputBinding:setActionEventText(id,'Hydraulic blade",1)
s=s.replace('    if not (isActiveForInput or isActiveForInputIgnoreSelection) then return end','    if spec.blade~=nil then spec.blade.eventId=nil end\n    if not (isActiveForInput or isActiveForInputIgnoreSelection) then return end')
pos=s.index('    for _,action in ipairs({',s.index('function TWinch.onRegisterActionEvents'))
s=s[:pos]+'''    for _,entry in ipairs({{'TWINCH_BLADE_RAISE_V13',1,'Raise blade'},{'TWINCH_BLADE_LOWER_V13',-1,'Lower blade'}}) do
        local direction=entry[2]
        local _,id=self:addActionEvent(spec.actionEvents,entry[1],self,function(v,a,value,state,analog,mouse)
            TWinch.actionBlade(v,a,value*direction,state,analog,false)
        end,true,true,true,true)
        if id~=nil then
            g_inputBinding:setActionEventText(id,entry[3])
            g_inputBinding:setActionEventTextVisibility(id,true)
            g_inputBinding:setActionEventTextPriority(id,GS_PRIO_HIGH)
        end
    end
'''+s[pos:]
s=s.replace('function TWinch.onUpdate(self, dt)\n','''function TWinch.onUpdate(self, dt)
    local blade=self.spec_twinch.blade
    if self.isClient and blade~=nil and self.getIsActiveForInput~=nil and self:getIsActiveForInput(true) then
        if blade.eventId==nil then TWinch.onRegisterActionEvents(self,true,true) end
        if blade.eventId~=nil then g_inputBinding:setActionEventActive(blade.eventId,true) end
    end
    -- Apply visual hydraulics in the frame update too; they do not need a physics tick.
    if self.isServer then TWinch.updateBlade(self,dt) end
''')
s=s.replace('    local blade=self.spec_twinch.blade\n    if blade == nil or not self.isServer then return end\n    blade.inputAge=', '''    local blade=self.spec_twinch.blade
    if blade == nil or not self.isServer then return end
    local frame=g_currentMission~=nil and g_currentMission.time or nil
    if frame~=nil and blade.lastUpdateFrame==frame then return end
    blade.lastUpdateFrame=frame
    blade.inputAge=''')
s=s.replace('W.draw(', 'W.drawWinch(')
p.write_text(s)
v=E.parse(OUT/'twinch.xml').getroot();d=E.parse(OUT/'modDesc.xml').getroot();r=E.parse(OUT/'twinch.i3d').getroot()
v.set('type','twinchV13');d.find('vehicleTypes/type').set('name','twinchV13');d.find('version').text='0.13.0.0'
d.find('description/en').text='Independent hydraulic blade raise/lower actions, fresh mouse bindings, input registration recovery and frame update fallback. Dark crawler steel and carrier finish. Corrected winch mod-listener callback collision. Configured total mass remains 40 tonnes.'
d.find('title/en').text='T-Winch v13 - Blade controls and dark steel tracks'
for n in v.findall('storeData/name/*'):n.text='T-Winch 30.2 v13'
for n in d.iter():
 for key,val in list(n.attrib.items()):n.set(key,val.replace('_V12','_V13').replace('TWINCH_BLADE_LIFT','TWINCH_BLADE_LIFT_V13'))
binding=d.find("inputBinding/actionBinding[@action='TWINCH_BLADE_LIFT_V13']")
for n in list(binding):
 if 'KEY_page' in n.get('input',''):binding.remove(n)
for name,key in [('RAISE','pageup'),('LOWER','pagedown')]:
 action='TWINCH_BLADE_'+name+'_V13'
 E.SubElement(d.find('actions'),'action',name=action,axisType='HALF')
 b=E.SubElement(d.find('inputBinding'),'actionBinding',action=action)
 E.SubElement(b,'binding',device='KB_MOUSE_DEFAULT',input='KEY_'+key)
 text=E.SubElement(d.find('l10n'),'text',name='input_'+action);E.SubElement(text,'en').text=name.title()+' blade'
# Keep the original mesh and motion-path shader, tint its base steel dark.
c=E.parse(OUT/'crawlers/volvo/ec380DLCrawler.i3d').getroot()
for m in c.find('Materials'):
 if m.get('customShaderVariation')=='motionPath_vmaskUV2':
  m.set('diffuseColor','.12 .13 .14 1')
  for n in m.findall('CustomParameter'):
   if n.get('name')=='colorScale':n.set('value','.035 .04 .045')
# A dedicated dark material for exposed carriers avoids repainting the blade.
material=copy.deepcopy(r.find("Materials/Material[@materialId='3']"));material.set('materialId','15');material.set('name','UndercarriageDarkSteel');r.find('Materials').append(material)
for n in r.find('Scene').iter('Shape'):
 if any(k in n.get('name','') for k in ['Carrier','WheelAxle','EndWheelHub','TensionCylinder','ReturnRollerMount','SlideRail']):n.set('materialIds','15')
# Deterministic restrained cast steel grain replaces the brown mottled texture.
rng=np.random.default_rng(13);size=1024;grain=rng.normal(0,.8,(size,size,1));rgb=np.clip(np.array([36,39,42])[None,None,:]+grain,0,255).astype('uint8')
im=Image.fromarray(rgb).convert('RGBA');b=io.BytesIO();im.save(b,format='DDS',pixel_format='DXT5');data=bytearray(b.getvalue());level=im;mips=1
while level.width>1 or level.height>1:
 level=level.resize((max(1,level.width//2),max(1,level.height//2)),Image.Resampling.LANCZOS);b=io.BytesIO();level.save(b,format='DDS',pixel_format='DXT5');data.extend(b.getvalue()[128:]);mips+=1
struct.pack_into('<I',data,8,struct.unpack_from('<I',data,8)[0]|0x20000);struct.pack_into('<I',data,28,mips);struct.pack_into('<I',data,108,0x401008)
(OUT/'textures/m3_diffuse.dds').write_bytes(data)
index=E.parse(OUT/'machineConfigurations.xml').getroot();index.find('configuration').set('vehicle','FS25_TWinch_v13/twinch.xml')
for tree,name in [(v,'twinch.xml'),(d,'modDesc.xml'),(r,'twinch.i3d'),(c,'crawlers/volvo/ec380DLCrawler.i3d'),(index,'machineConfigurations.xml')]:E.indent(tree);E.ElementTree(tree).write(OUT/name,encoding='utf-8',xml_declaration=True)
(OUT/'TESTING.txt').write_text('V13: disable earlier versions, install unopened ZIP and buy fresh v13.\nPage Up raises; Page Down lowers. Left mouse plus vertical drag moves blade.\nIndependent versioned keyboard actions, refreshed active registration and frame update fallback.\nBoth hydraulic cylinders follow blade endpoints. Mass remains 40,000kg including support wheels.\nDark track shader tint, dark carrier material and restrained cast steel wheel texture.\nVolvo crawler geometry retained; main Volvo drivetrain geometry still not supplied.\nFS25 unavailable: verify motion, visuals and handling in game.\n')
(OUT/'validation.json').write_text(json.dumps({'version':'0.13.0.0','game_test':'not run','total_mass_kg':40000,'changes':['fresh blade bindings','independent keyboard raise/lower actions','active registration refresh','frame update hydraulic fallback','dark crawler tint and carrier steel','restrained wheel finish'],'volvo_drivetrain':'main model not supplied'},indent=2)+'\n')
with ZipFile(HERE.parent/'FS25_TWinch_v13.zip','w',ZIP_DEFLATED) as z:
 for f in sorted(OUT.rglob('*')):
  if f.is_file():z.write(f,f.relative_to(OUT))
print('Built',OUT)
