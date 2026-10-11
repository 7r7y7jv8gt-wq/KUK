"""Preserve the supplied mod; upgrade both winches to 100-tonne vehicle recovery."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import sys, hashlib, json, xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'FS25_Follvik_TVinsj_v24'
OUT.mkdir(exist_ok=True)
with ZipFile(sys.argv[1]) as z:
 for name in z.namelist():
  p=OUT/name
  if not p.resolve().is_relative_to(OUT.resolve()):raise ValueError(name)
  if not name.endswith('/'):
   p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(name))
p=OUT/'scripts/TWinch.lua';s=p.read_text().replace('twinchV23','twinchV24')
s=s.replace('TWinch = {}','''TWinch = {}
-- GIANTS physics: tonnes and kN. 100 tonne-force = 980.665 kN.
TWinch.MAX_WINCH_LOAD = 100
TWinch.MAX_WINCH_FORCE = 980.665
function TWinch.winchTension(distance,length,separationSpeed,ownMass,targetMass)
    if distance<=length then return 0 end
    local reduced=math.max(.01,ownMass)
    if targetMass~=nil and targetMass>0 then reduced=1/(1/reduced+1/targetMass) end
    local stiffness=1250
    local damping=2*math.sqrt(stiffness*reduced)
    return math.min(TWinch.MAX_WINCH_FORCE,math.max(0,(distance-length)*stiffness+separationSpeed*damping))
end''',1)
s=s.replace('local limit=math.min(25,math.max(0,getMass(targetNode))*3,math.max(0,getMass(ownNode))*3)\n    local tension=TWinch.ropeTension(distance,spec.length,separation,limit)', 'local tension=TWinch.winchTension(distance,spec.length,separation,getMass(ownNode),getMass(targetNode))')
a=s.index('function W.raycastCallback(');b=s.index('function W.findTarget',a)
s=s[:a]+'''-- Resolve vehicle colliders (including child/component nodes) to their rigid body.
function W.vehicleAtNode(shape)
    local mission=g_currentMission
    if mission==nil then return nil end
    local n=shape
    while exists(n) do
        local object=mission.getNodeObject~=nil and mission:getNodeObject(n) or nil
        if object~=nil and object.components~=nil then return object end
        n=getParent(n)
    end
    for _,object in pairs(mission.vehicleSystem~=nil and mission.vehicleSystem.vehicles or {}) do
        for _,component in ipairs(object.components or {}) do
            if descendant(shape,component.node) then return object end
        end
    end
end
function W.targetMass(t)
    if t.static then return 0 end
    if t.vehicle~=nil then
        local mass=0
        for _,component in ipairs(t.vehicle.components or {}) do
            if exists(component.node) then mass=mass+math.max(0,getMass(component.node)) end
        end
        return mass
    end
    return math.max(0,getMass(t.node))
end
function W.raycastCallback(self,shape,x,y,z,hitDistance)
    local s=W.selected
    if s==nil or not exists(shape) then return true end
    for _,component in ipairs(s.vehicle.components or {}) do
        if descendant(shape,component.node) then return true end
    end
    local vehicle=W.vehicleAtNode(shape)
    local actor
    if vehicle~=nil then
        if vehicle==s.vehicle or vehicle.isDeleted or not vehicle.isAddedToPhysics then return true end
        if vehicle.getRootVehicle~=nil and s.vehicle.getRootVehicle~=nil
            and vehicle:getRootVehicle()==s.vehicle:getRootVehicle() then return true end
        for _,component in ipairs(vehicle.components) do
            if descendant(shape,component.node) and getRigidBodyType(component.node)==RigidBodyType.DYNAMIC then actor=component.node;break end
        end
        if actor==nil then
            for _,component in ipairs(vehicle.components) do
                if exists(component.node) and getRigidBodyType(component.node)==RigidBodyType.DYNAMIC then actor=component.node;break end
            end
        end
        if actor==nil then return true end
    else
        local tree=bitAND(getCollisionFilterGroup(shape),CollisionFlag.TREE)~=0
        actor=shape
        while exists(actor) and getRigidBodyType(actor)~=RigidBodyType.DYNAMIC do actor=getParent(actor) end
        if not exists(actor) then if not tree then return true end;actor=shape end
    end
    if W.hit==nil or hitDistance<W.hit.distance then
        W.hit={node=actor,shape=shape,vehicle=vehicle,x=x,y=y,z=z,distance=hitDistance,static=getRigidBodyType(actor)~=RigidBodyType.DYNAMIC}
    end
    return true
end
''' +s[b:]
s=s.replace('local mass=hit.static and 0 or getMass(hit.node)','local mass=W.targetMass(hit)').replace('mass=mass+getMass(t.node)','mass=mass+W.targetMass(t)')
s=s.replace("if mass>8 then message('Winch load exceeds eight tonnes.');return end", "if mass>TWinch.MAX_WINCH_LOAD+.0001 then message('Winch load exceeds 100 tonnes.');return end")
s=s.replace('static=hit.static}', 'static=hit.static,vehicle=hit.vehicle}')
s=s.replace('    W.wrapChain(s,t)','    if t.vehicle==nil then W.wrapChain(s,t) end')
s=s.replace('Hook taken. Walk to a tree or object and press R.', 'Hook taken. Walk to a machine, tree or object and press R.')
s=s.replace('local cap=math.min(25,getMass(to)*3,t.static and 25 or getMass(t.node)*3)\n    local force=TWinch.ropeTension(d,length,(ux-vx)*dx+(uy-vy)*dy+(uz-vz)*dz,cap)', 'local force=TWinch.winchTension(d,length,(ux-vx)*dx+(uy-vy)*dy+(uz-vz)*dz,getMass(to),t.static and nil or getMass(t.node))')
s=s.replace('if not exists(t.node) or not exists(t.ref) then W.clear(s);return end', 'if not exists(t.node) or not exists(t.ref) or (t.vehicle~=nil and (t.vehicle.isDeleted or not t.vehicle.isAddedToPhysics)) then W.clear(s);return end')
s=s.replace('        if not t.static then\n            local cx', '        if t.vehicle~=nil then t.vehicle:raiseActive() end\n        if not t.static then\n            local cx')
s=s.replace('if t.node==hit.node then', 'if t.node==hit.node or (hit.vehicle~=nil and t.vehicle==hit.vehicle) then')
s=s.replace('if d>2 and d<nearestDistance then nearest=vehicle; nearestDistance=d end', 'if d>2 and d<nearestDistance and BladeWinch.targetMass({vehicle=vehicle,node=node})<=TWinch.MAX_WINCH_LOAD then nearest=vehicle; nearestDistance=d end')
p.write_text(s)
for name in ['modDesc.xml','twinch.xml','machineConfigurations.xml']:
 path=OUT/name;r=E.parse(path)
 if name=='modDesc.xml':r.find('version').text='0.24.0.0';r.find('vehicleTypes/type').set('name','twinchV24')
 elif name=='twinch.xml':r.getroot().set('type','twinchV24')
 else:r.find('configuration').set('vehicle','FS25_Follvik_TVinsj_v24/twinch.xml')
 E.indent(r);r.write(path,encoding='utf-8',xml_declaration=True)
(OUT/'TESTING.txt').write_text('V24: front and rear hook winches each accept 100 tonnes total and deliver up to 980.665 kN (100 tonne-force).\nWalk up to either winch, R to take hook; walk to a machine and aim at its collider within 4m; R attaches.\nHold Z to pull, X to pay out, Shift+R releases. Start the engine before pulling. Cable range 60m.\nEqual reaction force remains on the 40-tonne chassis: traction, brakes and anchoring affect recovery.\nVehicle attachments use a direct hook instead of wrapping a log chain around the entire machine.\nVehicles must be loaded in physics; same vehicle/attached own equipment and static scenery are rejected.\nSingle-player mod; in-game physics and visuals not tested in this environment.\nDisable previous T-Winch versions before loading.\n')
with ZipFile(sys.argv[1]) as source:
 hashes={n:hashlib.sha256(source.read(n)).hexdigest() for n in source.namelist() if n.endswith(('.i3d','.shapes','.dds'))}
(OUT/'source_asset_hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
with ZipFile(ROOT/'FS25_Follvik_TVinsj_v24.zip','w',ZIP_DEFLATED) as z:
 for f in sorted(OUT.rglob('*')):
  if f.is_file():z.write(f,f.relative_to(OUT))
print(OUT)
