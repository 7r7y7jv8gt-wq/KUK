"""Fresh left-mouse hydraulic binding and independent mouse/keyboard input channels."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import shutil,xml.etree.ElementTree as E,json
ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'FS25_Follvik_TVinsj_v25'
shutil.copytree(ROOT/'FS25_Follvik_TVinsj_v24',OUT,dirs_exist_ok=True)
p=OUT/'scripts/TWinch.lua';s=p.read_text().replace('twinchV24','twinchV25').replace('TWINCH_BLADE_LIFT_V13','TWINCH_BLADE_MOUSE_V25')
s=s.replace("'Hydraulic blade: left mouse + vertical / Page Up / Page Down'", "'Skjær: hold venstre museknapp og dra opp/ned'")
a=s.index('function TWinch.actionBlade(');b=s.index('function TWinch.saveToXMLFile',a)
s=s[:a]+'''function TWinch.actionBlade(self,actionName,value,callbackState,isAnalog,isMouse)
    local blade=self.spec_twinch~=nil and self.spec_twinch.blade or nil
    if blade==nil or not self.isServer then return end
    if value~=0 and self.startMotor~=nil and not self:getIsMotorStarted() then self:startMotor() end
    value=math.max(-1,math.min(1,value))
    if actionName=='TWINCH_BLADE_MOUSE_V25' or isMouse==true then
        -- Mouse deltas accumulate independently; keyboard zero callbacks cannot erase them.
        blade.mouseInput=math.max(-1,math.min(1,(blade.mouseInput or 0)+value))
        blade.mouseInputAge=0
    else
        blade.keyInputs=blade.keyInputs or {}
        blade.keyInputs[actionName]=value
        blade.keyInputAge=0
    end
end

function TWinch.updateBlade(self,dt)
    local blade=self.spec_twinch.blade
    if blade==nil or not self.isServer then return end
    local frame=g_currentMission~=nil and g_currentMission.time or nil
    if frame~=nil and blade.lastUpdateFrame==frame then return end
    blade.lastUpdateFrame=frame
    blade.mouseInputAge=(blade.mouseInputAge or 1000)+dt
    blade.keyInputAge=(blade.keyInputAge or 1000)+dt
    local mouse=blade.mouseInputAge<=250 and (blade.mouseInput or 0) or 0
    local keyboard=0
    if blade.keyInputAge<=250 then
        for _,value in pairs(blade.keyInputs or {}) do keyboard=keyboard+value end
    end
    local input=math.max(-1,math.min(1,mouse+keyboard))
    if self:getIsMotorStarted() and input~=0 then
        local angle=math.max(-28,math.min(25,blade.angle-input*12*math.min(dt,100)/1000))
        if angle~=blade.angle then
            blade.angle=angle;TWinch.applyBlade(self);self:raiseActive()
        end
    end
    -- Consume mouse movement once; holding the button without dragging does not move the blade.
    blade.mouseInput=0
end

''' +s[b:]
s=s.replace('if self.spec_twinch.blade ~= nil then self.spec_twinch.blade.input=0 end', 'if self.spec_twinch.blade~=nil then\n        local blade=self.spec_twinch.blade\n        blade.input=0;blade.mouseInput=0;blade.keyInputs={}\n    end')
p.write_text(s)
for name in ['modDesc.xml','twinch.xml','machineConfigurations.xml']:
 p=OUT/name;r=E.parse(p)
 if name=='modDesc.xml':
  r.find('version').text='0.25.0.0';r.find('vehicleTypes/type').set('name','twinchV25')
  for n in r.iter():
   for k,v in list(n.attrib.items()):
    if 'TWINCH_BLADE_LIFT_V13' in v:n.set(k,v.replace('TWINCH_BLADE_LIFT_V13','TWINCH_BLADE_MOUSE_V25'))
  for binding in r.findall("inputBinding/actionBinding[@action='TWINCH_BLADE_MOUSE_V25']/binding"):
   binding.set('inputComponent','-' if binding.get('axisComponent')=='+' else '+')
  r.find("l10n/text[@name='input_TWINCH_BLADE_MOUSE_V25']/en").text='Blade: hold left mouse and drag up/down'
 elif name=='twinch.xml':r.getroot().set('type','twinchV25')
 else:r.find('configuration').set('vehicle','FS25_Follvik_TVinsj_v25/twinch.xml')
 E.indent(r);r.write(p,encoding='utf-8',xml_declaration=True)
(OUT/'TESTING.txt').write_text((OUT/'TESTING.txt').read_text()+'\nV25: hold left mouse and drag vertically to move hydraulic blade.\nNew mouse binding avoids cached older binding; Page Up/Page Down remain available.\nMouse and keyboard channels are independent; idle keyboard events cannot erase mouse movement.\nMouse movement is consumed once; idle drag, leaving vehicle, timeout and limits stop motion.\nBoth 100-tonne winches and all supplied model assets retained.\n')
(OUT/'validation.json').write_text(json.dumps({'version':'0.25.0.0','game_test':'not run'},indent=2)+'\n')
with ZipFile(ROOT/'FS25_Follvik_TVinsj_v25.zip','w',ZIP_DEFLATED) as z:
 for p in sorted(OUT.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(OUT))
print(OUT)
