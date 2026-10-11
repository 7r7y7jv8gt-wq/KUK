-- Single-player vehicle recovery winch and geometric track animation.
-- Engine units: mass in tonnes, force in kN, dt in milliseconds.
TWinch = {}
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
end

function TWinch.prerequisitesPresent(specializations)
    return SpecializationUtil.hasSpecialization(Drivable, specializations)
        and SpecializationUtil.hasSpecialization(Wheels, specializations)
end

function TWinch.initSpecialization()
    local schema = Vehicle.xmlSchema
    schema:setXMLSpecializationType("TWinch")
    schema:register(XMLValueType.NODE_INDEX,"vehicle.twinch.rearWinch#anchor","Rear winch fairlead")
    schema:register(XMLValueType.NODE_INDEX, "vehicle.twinch#anchor", "Winch fairlead")
    schema:register(XMLValueType.NODE_INDEX, "vehicle.twinch#cable", "Visible cable")
    schema:register(XMLValueType.NODE_INDEX, "vehicle.twinch.track(?)#node", "Track links")
    schema:register(XMLValueType.FLOAT, "vehicle.twinch.track(?)#offsetX", "Track side offset")
    schema:register(XMLValueType.NODE_INDEX, "vehicle.twinch.track(?).roller(?)#node", "Roller pivot")
    schema:register(XMLValueType.FLOAT, "vehicle.twinch.track(?).roller(?)#radius", "Roller radius")

    for _,key in ipairs({'node','RightBarrel','RightPin','RightRod','RightBase','LeftBarrel','LeftPin','LeftRod','LeftBase'}) do
        schema:register(XMLValueType.NODE_INDEX,'vehicle.twinch.blade#'..key,'Hydraulic blade endpoint')
    end
    Vehicle.xmlSchemaSavegame:register(XMLValueType.FLOAT,'vehicles.vehicle(?).'..TWinch.MOD_NAME..'.twinch#bladeAngle','Blade angle in degrees',0)
    for _,name in ipairs({"winching","chainAttach","chainDetach"}) do SoundManager.registerSampleXMLPaths(schema,"vehicle.twinch.logging.sounds",name) end
    schema:setXMLSpecializationType()

end

function TWinch.registerEventListeners(vehicleType)
    for _, name in ipairs({"onLoad", "onUpdate", "onUpdateTick", "onDelete", "onLeaveVehicle", "onRegisterActionEvents"}) do
        SpecializationUtil.registerEventListener(vehicleType, name, TWinch)
    end
end

function TWinch.onLoad(self, savegame)
    local spec = {tracks={}, actionEvents={}, target=nil, reel=false, payout=false, tension=0}
    self.spec_twinch = spec
    local ok,err=pcall(TWinch.registerTerraFarm,self)
    if not ok and Logging~=nil then Logging.warning('T-Winch: TerraFarm registration failed; continuing vehicle load: %s',tostring(err)) end
    spec.anchor = self.xmlFile:getValue("vehicle.twinch#anchor", nil, self.components, self.i3dMappings)
    spec.cable = self.xmlFile:getValue("vehicle.twinch#cable", nil, self.components, self.i3dMappings)
    self.xmlFile:iterate("vehicle.twinch.track", function(index, key)
        local track = {
            node=self.xmlFile:getValue(key.."#node", nil, self.components, self.i3dMappings),
            offsetX=self.xmlFile:getValue(key.."#offsetX", 0), phase=0, rollers={}
        }
        if track.node ~= nil then
            track.count = math.min(74,getNumOfChildren(track.node))
            self.xmlFile:iterate(key..".roller", function(i, rk)
                local node = self.xmlFile:getValue(rk.."#node", nil, self.components, self.i3dMappings)
                if node ~= nil then
                    table.insert(track.rollers, {node=node, radius=self.xmlFile:getValue(rk.."#radius", 0.17), angle=0})
                end
            end)
            table.insert(spec.tracks, track)
        end
    end)
    if spec.cable ~= nil then setVisibility(spec.cable, false) end
    TWinch.loadBlade(self,savegame)
    BladeWinch.load(self)
    local rear=self.xmlFile:getValue('vehicle.twinch.rearWinch#anchor',nil,self.components,self.i3dMappings)
    if rear~=nil then BladeWinch.load(self,rear) end
end

-- Uniform arc-length stadium: top, front curve, bottom, rear curve.
function TWinch.trackPose(distance)
    local radius, straight, centerY, rear = 0.37, 2.34, 0.415, -1.22
    local arc = math.pi * radius
    local length = 2 * straight + 2 * arc
    local s = distance % length
    if s < straight then return centerY+radius, rear+s, 0 end
    s = s-straight
    if s < arc then
        local theta = s/radius
        return centerY+radius*math.cos(theta), rear+straight+radius*math.sin(theta), theta
    end
    s = s-arc
    if s < straight then return centerY-radius, rear+straight-s, math.pi end
    local theta = math.pi+(s-straight)/radius
    return centerY+radius*math.cos(theta), rear+radius*math.sin(theta), theta
end

function TWinch.updateTracks(self)
    local spec, root = self.spec_twinch, self.components[1].node
    local circumference = 4.68+2*math.pi*0.37
    for _, track in ipairs(spec.tracks) do
        local x,y,z = localToWorld(root, track.offsetX, 0.415, 0)
        local travel = 0
        if track.last ~= nil then
            local _,_,dz = worldDirectionToLocal(root, x-track.last[1], y-track.last[2], z-track.last[3])
            -- Spawn and reset teleports must not spin the belts violently.
            if math.abs(dz) < 2 then travel=dz end
        end
        track.last={x,y,z}
        track.phase=(track.phase+travel)%circumference
        for i=0,track.count-1 do
            local ly,lz,angle=TWinch.trackPose(track.phase+i*circumference/track.count)
            local node=getChildAt(track.node,i)
            setTranslation(node,0,ly,lz)
            setRotation(node,angle,0,0)
        end
        for _,roller in ipairs(track.rollers) do
            roller.angle=(roller.angle+travel/roller.radius)%(2*math.pi)
            setRotation(roller.node,roller.angle,0,0)
        end
    end
end

function TWinch.disconnect(self)
    local spec=self.spec_twinch
    spec.target=nil; spec.reel=false; spec.payout=false; spec.tension=0
    if spec.cable ~= nil then setVisibility(spec.cable,false) end
end

function TWinch.actionConnect(self)
    local spec=self.spec_twinch
    if not self.isServer or spec.anchor == nil then return end
    if spec.target ~= nil then TWinch.disconnect(self); return end
    local ax,ay,az=getWorldTranslation(spec.anchor)
    local nearest,nearestDistance=nil,25
    local vehicles=g_currentMission.vehicleSystem.vehicles
    for _,vehicle in pairs(vehicles) do
        if vehicle ~= self and vehicle.components ~= nil and vehicle.components[1] ~= nil
            and vehicle.isAddedToPhysics and not vehicle.isDeleted
            and vehicle:getRootVehicle() ~= self:getRootVehicle()
            and vehicle:getOwnerFarmId() == self:getOwnerFarmId() then
            local node=vehicle.components[1].node
            if entityExists(node) and getRigidBodyType(node) == RigidBodyType.DYNAMIC then
                local x,y,z=localToWorld(node,getCenterOfMass(node))
                local d=math.sqrt((x-ax)^2+(y-ay)^2+(z-az)^2)
                if d>2 and d<nearestDistance and BladeWinch.targetMass({vehicle=vehicle,node=node})<=TWinch.MAX_WINCH_LOAD then nearest=vehicle; nearestDistance=d end
            end
        end
    end
    if nearest ~= nil then
        spec.target=nearest; spec.length=nearestDistance+0.25
        spec.reel=false; spec.payout=false
        self:raiseActive()
    elseif g_currentMission.addIngameNotification ~= nil then
        g_currentMission:addIngameNotification(FSBaseMission.INGAME_NOTIFICATION_INFO,
            "T-Winch: no vehicle from your farm within 25 m. Move closer to the vehicle you want to recover.")
    end
end

function TWinch.actionReel(self)
    local spec=self.spec_twinch
    if self.isServer and spec.target ~= nil then
        spec.reel=not spec.reel; spec.payout=false
    end
end

function TWinch.actionPayout(self)
    local spec=self.spec_twinch
    if self.isServer and spec.target ~= nil then
        spec.payout=not spec.payout; spec.reel=false
    end
end

-- A unilateral, damped rope: tension only, never a pushing or teleporting force.
function TWinch.ropeTension(distance, length, separationSpeed, limit)
    if distance <= length then return 0 end
    return math.min(limit,math.max(0,(distance-length)*8+separationSpeed*4))
end

function TWinch.updateWinch(self, dt)
    local spec=self.spec_twinch
    if spec.target == nil then return end
    local target=spec.target
    if target.isDeleted or not target.isAddedToPhysics or target.components == nil
        or target.components[1] == nil or not entityExists(target.components[1].node) then
        TWinch.disconnect(self); return
    end
    local ownNode,targetNode=self.components[1].node,target.components[1].node
    -- Keep the tether simulation ticking even with the engine off and a slack line.
    self:raiseActive()
    local ax,ay,az=getWorldTranslation(spec.anchor)
    local tx,ty,tz=localToWorld(targetNode,getCenterOfMass(targetNode))
    local dx,dy,dz=tx-ax,ty-ay,tz-az
    local distance=math.sqrt(dx*dx+dy*dy+dz*dz)
    if distance<0.01 or distance>45 then TWinch.disconnect(self); return end
    dx,dy,dz=dx/distance,dy/distance,dz/distance
    local seconds=math.min(math.max(dt/1000,0),0.1)
    if spec.payout then
        spec.length=math.min(40,spec.length+0.8*seconds)
    elseif spec.reel and self:getIsMotorStarted() then
        -- Stall the drum when there is excessive stretch, rather than storing unbounded energy.
        if distance-spec.length<1 then spec.length=math.max(2,spec.length-0.6*seconds) end
    end
    local vx,vy,vz=getLinearVelocity(ownNode)
    local ux,uy,uz=getLinearVelocity(targetNode)
    local separation=(ux-vx)*dx+(uy-vy)*dy+(uz-vz)*dz
    local tension=TWinch.winchTension(distance,spec.length,separation,getMass(ownNode),getMass(targetNode))
    spec.tension=tension
    if tension>0 then
        local cx,cy,cz=getCenterOfMass(ownNode)
        local px,py,pz=getCenterOfMass(targetNode)
        -- Equal reaction on the winch chassis. Forces applied at COM avoid artificial roll torque.
        addForce(targetNode,-dx*tension,-dy*tension,-dz*tension,px,py,pz,true)
        addForce(ownNode,dx*tension,dy*tension,dz*tension,cx,cy,cz,true)
        target:raiseActive(); self:raiseActive()
    end
end

function TWinch.onUpdateTick(self, dt)
    if self.spec_twinch==nil then return end
    if self.isServer and self.isAddedToPhysics then TWinch.updateBlade(self,dt); TWinch.updateWinch(self,dt); BladeWinch.tick(self,dt) end
end

function TWinch.onUpdate(self, dt)
    if self.spec_twinch==nil then return end
    local blade=self.spec_twinch.blade
    if self.isClient and blade~=nil and self.getIsActiveForInput~=nil and self:getIsActiveForInput(true) then
        if blade.eventId==nil then TWinch.onRegisterActionEvents(self,true,true) end
        if blade.eventId~=nil then g_inputBinding:setActionEventActive(blade.eventId,true) end
    end
    -- Apply visual hydraulics in the frame update too; they do not need a physics tick.
    if self.isServer then TWinch.updateBlade(self,dt) end
    if not self.isClient then return end
    BladeWinch.update(BladeWinch,dt)
    TWinch.updateTrackWear(self,dt)
    TWinch.updateTracks(self)
    local spec=self.spec_twinch
    if spec.cable ~= nil and spec.target ~= nil and spec.target.components ~= nil
        and spec.target.components[1] ~= nil and entityExists(spec.target.components[1].node) then
        local ax,ay,az=getWorldTranslation(spec.anchor)
        local tx,ty,tz=localToWorld(spec.target.components[1].node,getCenterOfMass(spec.target.components[1].node))
        local dx,dy,dz=tx-ax,ty-ay,tz-az
        local length=math.sqrt(dx*dx+dy*dy+dz*dz)
        if length>0.01 then
            setVisibility(spec.cable,true)
            setWorldTranslation(spec.cable,ax,ay,az)
            -- The cable mesh runs along local +Z, from 0 to 1 metre.
            local upX,upY=0,1
            if math.abs(dy/length)>0.99 then upX,upY=1,0 end
            setWorldDirection(spec.cable,dx/length,dy/length,dz/length,upX,upY,0)
            setScale(spec.cable,1,1,length)
        end
    elseif spec.cable ~= nil then setVisibility(spec.cable,false) end
end

function TWinch.onRegisterActionEvents(self, isActiveForInput, isActiveForInputIgnoreSelection)
    if self.spec_twinch==nil then return end
    if not self.isClient then return end
    local spec=self.spec_twinch
    self:clearActionEventsTable(spec.actionEvents)
    if spec.blade~=nil then spec.blade.eventId=nil end
    if not (isActiveForInput or isActiveForInputIgnoreSelection) then return end

    if spec.blade ~= nil then
        local _,id=self:addActionEvent(spec.actionEvents,'TWINCH_BLADE_MOUSE_V25',self,TWinch.actionBlade,true,true,true,true)
        spec.blade.eventId=id
        if id ~= nil then
            if g_inputBinding.setActionEventActive~=nil then g_inputBinding:setActionEventActive(id,true) end
            g_inputBinding:setActionEventText(id,'Skjær: hold venstre museknapp og dra opp/ned')
            g_inputBinding:setActionEventTextPriority(id,GS_PRIO_HIGH)
            g_inputBinding:setActionEventTextVisibility(id,true)
        else
            Logging.warning('T-Winch: could not register an input action; check input bindings')
        end
    end
    for _,entry in ipairs({{'TWINCH_BLADE_RAISE_V13',1,'Raise blade'},{'TWINCH_BLADE_LOWER_V13',-1,'Lower blade'}}) do
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
    for _,action in ipairs({

        {'TWINCH_CONNECT',TWinch.actionConnect,"T-Winch: attach / release nearest vehicle (25 m)"},
        {'TWINCH_REEL',TWinch.actionReel,"T-Winch: start / stop reeling in"},
        {'TWINCH_PAYOUT',TWinch.actionPayout,"T-Winch: start / stop paying out"}
    }) do
        local _,id=self:addActionEvent(spec.actionEvents,action[1],self,action[2],false,true,false,true)
        if id ~= nil then
            g_inputBinding:setActionEventText(id,action[3])
            g_inputBinding:setActionEventTextPriority(id,GS_PRIO_HIGH)
            g_inputBinding:setActionEventTextVisibility(id,true)
        else
            Logging.warning('T-Winch: could not register an input action; check input bindings')
        end
    end
end

function TWinch.onLeaveVehicle(self)
    if self.spec_twinch.blade~=nil then
        local blade=self.spec_twinch.blade
        blade.input=0;blade.mouseInput=0;blade.keyInputs={}
    end
    self.spec_twinch.reel=false; self.spec_twinch.payout=false
end

function TWinch.onDelete(self)
    if self.spec_twinch==nil then return end
    BladeWinch.delete(self)
    TWinch.disconnect(self)
end

-- Explicit single-player hydraulic blade input and endpoint alignment.
-- Loaded after TWinch; avoids native arm-selection/easy-arm-control filtering.
TWinch.MOD_NAME = g_currentModName
TWinch.MOD_DIRECTORY = g_currentModDirectory

function TWinch.loadBlade(self, savegame)
    local spec = self.spec_twinch
    local function node(key)
        return self.xmlFile:getValue('vehicle.twinch.blade#'..key, nil, self.components, self.i3dMappings)
    end
    spec.blade = {node=node('node'), input=0, angle=0, parts={}}
    for _,side in ipairs({'Right','Left'}) do
        table.insert(spec.blade.parts,{node=node(side..'Barrel'),target=node(side..'Pin')})
        table.insert(spec.blade.parts,{node=node(side..'Rod'),target=node(side..'Base')})
    end
    if savegame ~= nil and not savegame.resetVehicles then
        local name=(self.customEnvironment or TWinch.MOD_NAME)..'.twinch'
        spec.blade.angle=math.max(-28,math.min(25,savegame.xmlFile:getValue(savegame.key..'.'..name..'#bladeAngle',0)))
    end
    TWinch.applyBlade(self)
    if Logging ~= nil then
        if spec.blade.node == nil then
            Logging.error('T-Winch v07: blade node missing; hydraulic controls cannot move the blade')
        else
            Logging.info('T-Winch v07: hydraulic blade controller loaded; Page Up/Page Down and left mouse controls')
        end
    end
end

function TWinch.applyBlade(self)
    local blade=self.spec_twinch.blade
    if blade == nil or blade.node == nil then return end
    setRotation(blade.node,math.rad(blade.angle),0,0)
    for _,part in ipairs(blade.parts) do
        if part.node ~= nil and part.target ~= nil then
            local x,y,z=getWorldTranslation(part.node)
            local tx,ty,tz=getWorldTranslation(part.target)
            local dx,dy,dz=tx-x,ty-y,tz-z
            local length=math.sqrt(dx*dx+dy*dy+dz*dz)
            if length>0.001 then
                -- Chassis-relative up prevents roll when working on a hillside.
                local ux,uy,uz=localDirectionToWorld(self.components[1].node,0,1,0)
                setWorldDirection(part.node,dx/length,dy/length,dz/length,ux,uy,uz)
            end
        end
    end
end

function TWinch.actionBlade(self,actionName,value,callbackState,isAnalog,isMouse)
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

function TWinch.saveToXMLFile(self,xmlFile,key,usedModNames)
    if self.spec_twinch.blade ~= nil then xmlFile:setValue(key..'#bladeAngle',self.spec_twinch.blade.angle) end
end

-- Single-player blade-mounted logging winch. Original integration code.
-- Chain shader, hook mesh and sounds: 50keda, supplied Tajfun EGV80 AHK mod.
BladeWinch={instances={},events={},selected=nil,modDirectory=g_currentModDirectory}
local W=BladeWinch
W.actions={
    {name='TWINCH_HOOK_V13',text='Take / attach winch hook',hold=false},
    {name='TWINCH_LOG_REEL_V13',text='Winch: hold to reel in',hold=true},
    {name='TWINCH_LOG_FAST_V13',text='Winch: hold to reel in fast',hold=true},
    {name='TWINCH_LOG_OUT_V13',text='Winch: hold to pay out',hold=true},
    {name='TWINCH_LOG_CLEAR_V13',text='Winch: release all / return hook',hold=false}
}
local function distance(a,b)
    local x,y,z=getWorldTranslation(a);local u,v,w=getWorldTranslation(b)
    return math.sqrt((x-u)^2+(y-v)^2+(z-w)^2)
end
local function exists(n) return n~=nil and n~=0 and entityExists(n) end
local function destroy(n) if exists(n) then delete(n) end end
local function descendant(n,root)
    while exists(n) do if n==root then return true end;n=getParent(n) end
    return false
end
local function message(text)
    if g_currentMission~=nil then g_currentMission:addIngameNotification(FSBaseMission.INGAME_NOTIFICATION_INFO,text) end
end
function W.load(vehicle,anchor)
    local s={vehicle=vehicle,anchor=anchor or vehicle.spec_twinch.anchor,targets={},segments={},carrying=false,reel=0,payout=0,clock=0,lastInput=-1000,length=0}
    vehicle.spec_twinch.loggingWinches=vehicle.spec_twinch.loggingWinches or {}
    table.insert(vehicle.spec_twinch.loggingWinches,s)
    if anchor==nil then vehicle.spec_twinch.logging=s end
    if not vehicle.isClient then return end
    -- Clone the steel cable; legacy recovery rendering cannot overwrite these nodes.
    for i=1,24 do
        local n=clone(vehicle.spec_twinch.cable,false,false,false)
        link(vehicle.components[1].node,n);setVisibility(n,false);s.segments[i]=n
    end
    local root,request=g_i3DManager:loadSharedI3DFile(Utils.getFilename('winch/chainMaterialHolder.i3d',W.modDirectory),false,false)
    s.assetRoot=root;s.assetRequest=request
    if exists(root) then
        s.chainMaterial=I3DUtil.indexToObject(root,'0|0')
        s.hook=I3DUtil.indexToObject(root,'0|2')
        setVisibility(I3DUtil.indexToObject(root,'0|0'),false)
        setVisibility(I3DUtil.indexToObject(root,'0|1'),false)
        s.hookPivot=createTransformGroup('bladeWinchHookPose')
        link(s.anchor,s.hookPivot);link(s.hookPivot,s.hook)
        setTranslation(s.hook,0,0,0);setRotation(s.hook,0,0,0);setScale(s.hook,.014,.014,.014)
        s.extraHookPivot=createTransformGroup('bladeWinchExtraHookPose')
        link(s.anchor,s.extraHookPivot)
        s.extraHook=clone(s.hook,false,false,false);link(s.extraHookPivot,s.extraHook)
        setTranslation(s.extraHook,0,0,0);setRotation(s.extraHook,0,0,0);setScale(s.extraHook,.014,.014,.014);setVisibility(s.extraHook,false)
    else Logging.warning('T-Winch: logging hook asset could not be loaded') end
    if g_soundManager~=nil then
        s.samples={}
        for _,name in ipairs({'winching','chainAttach','chainDetach'}) do
            s.samples[name]=g_soundManager:loadSampleFromXML(vehicle.xmlFile,'vehicle.twinch.logging.sounds',name,vehicle.baseDirectory,vehicle.components[1].node,1,AudioGroup.VEHICLE,nil,vehicle)
        end
    end
    table.insert(W.instances,s)
end
function W.sound(s,name)
    if s.samples~=nil and s.samples[name]~=nil then g_soundManager:playSample(s.samples[name]) end
end
function W.clear(s)
    for _,t in ipairs(s.targets) do destroy(t.chain);destroy(t.ref) end
    s.targets={};s.carrying=false;s.reel=0;s.payout=0;s.length=0
    if s.playing and s.samples~=nil and s.samples.winching~=nil then g_soundManager:stopSample(s.samples.winching) end
    s.playing=false
    for _,n in ipairs(s.segments) do setVisibility(n,false) end
    if exists(s.hook) then
        link(s.anchor,s.hookPivot);setTranslation(s.hookPivot,0,0,0);setRotation(s.hookPivot,0,0,0)
        setTranslation(s.hook,0,0,0);setRotation(s.hook,0,0,0);setScale(s.hook,.014,.014,.014)
    end
    if exists(s.extraHook) then setVisibility(s.extraHook,false) end
    W.sound(s,'chainDetach')
end
function W.deleteOne(vehicle,s)
    if s==nil then return end
    W.clear(s)
    for _,n in ipairs(s.segments) do destroy(n) end
    destroy(s.extraHook);destroy(s.hook);destroy(s.extraHookPivot);destroy(s.hookPivot);destroy(s.assetRoot)
    if s.assetRequest~=nil then g_i3DManager:releaseSharedI3DFile(s.assetRequest) end
    if s.samples~=nil then for _,sample in pairs(s.samples) do g_soundManager:deleteSample(sample) end end
    for i=#W.instances,1,-1 do if W.instances[i]==s then table.remove(W.instances,i) end end
    if W.selected==s then W.selected=nil end
end
-- Resolve vehicle colliders (including child/component nodes) to their rigid body.
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
function W.findTarget(s)
    W.hit=nil
    local camera=g_localPlayer:getCurrentCameraNode()
    if not exists(camera) then return nil end
    local x,y,z=getWorldTranslation(camera)
    local dx,dy,dz=localDirectionToWorld(camera,0,0,-1)
    raycastAll(x,y,z,dx,dy,dz,4,'raycastCallback',W,CollisionFlag.TREE+CollisionFlag.DYNAMIC_OBJECT+CollisionFlag.VEHICLE)
    return W.hit
end
-- Chain geometry wraps the actual collider, rather than an arbitrary bounding box.
function W.chainHit(self,shape,x,y,z)
    if shape==self.chainShape then table.insert(self.chainPoints,{x,y,z});return false end
    return true
end
function W.wrapChain(s,t)
    if not exists(s.chainMaterial) then return end
    local beltData=g_tensionBeltManager:getBeltData('basic')
    local belt=TensionBeltGeometryConstructor:new()
    belt:setWidth(.05);belt:setMaxEdgeLength(.1);belt:setMaterial(getMaterial(s.chainMaterial,0));belt:setUVscale(beltData.dummyMaterial.uvScale)
    local origin=createTransformGroup('bladeWinchChainOrigin');link(t.shape,origin)
    local x,y,z=getWorldTranslation(t.ref);setWorldTranslation(origin,x,y,z)
    -- Chain plane follows the target's local horizontal cross-section (log longitudinal axis is Y).
    local start=createTransformGroup('chainStart');local finish=createTransformGroup('chainEnd')
    link(origin,start);link(origin,finish)
    setTranslation(start,.01,0,0);setTranslation(finish,-.01,0,0)
    setRotation(start,0,math.pi/2,-math.pi/2);setRotation(finish,0,math.pi/2,-math.pi/2)
    belt:setFixedPoints(finish,start);belt:setGeometryBias(.02);belt:setLinkNode(t.shape)
    W.chainShape=t.shape;W.chainPoints={}
    for i=0,63 do
        local a=i*math.pi/32
        local sx,sy,sz=localToWorld(origin,math.cos(a)*2,0,math.sin(a)*2)
        local dx,dy,dz=localDirectionToWorld(origin,-math.cos(a),0,-math.sin(a))
        raycastAll(sx,sy,sz,dx,dy,dz,2.1,'chainHit',W,CollisionFlag.TREE+CollisionFlag.DYNAMIC_OBJECT+CollisionFlag.VEHICLE)
    end
    local dx,dy,dz=localDirectionToWorld(start,1,0,0)
    for _,p in ipairs(W.chainPoints) do belt:addIntersectionPoint(p[1],p[2],p[3],dx,dy,dz) end
    if #W.chainPoints>2 then t.chain=belt:finalize() end
    W.chainShape=nil;W.chainPoints=nil;destroy(origin)
end
function W.attach(s,hit)
    for _,t in ipairs(s.targets) do if t.node==hit.node or (hit.vehicle~=nil and t.vehicle==hit.vehicle) then message('This object is already attached. Shift+R releases the winch.');return end end
    if #s.targets>=8 then message('Maximum eight winch objects.');return end
    if #s.targets>0 and (hit.static or s.targets[1].static) then message('A fixed tree anchor must be used alone.');return end
    local mass=W.targetMass(hit)
    for _,t in ipairs(s.targets) do if not t.static then mass=mass+W.targetMass(t) end end
    if mass>TWinch.MAX_WINCH_LOAD+.0001 then message('Winch load exceeds 100 tonnes.');return end
    local ref=createTransformGroup('bladeWinchAttachment');link(hit.node,ref);setWorldTranslation(ref,hit.x,hit.y,hit.z)
    local t={node=hit.node,shape=hit.shape,ref=ref,static=hit.static,vehicle=hit.vehicle}
    local from=#s.targets==0 and s.anchor or s.targets[1].ref
    t.length=distance(from,ref)
    if t.length>(#s.targets==0 and 60 or 15) then destroy(ref);message('Target is beyond the available cable / chain.');return end
    table.insert(s.targets,t);s.carrying=false
    if #s.targets==1 then s.length=t.length end
    if t.vehicle==nil then W.wrapChain(s,t) end
    W.sound(s,'chainAttach');s.vehicle:raiseActive()
    message('Hook attached. Hold Z to winch, X to pay out; Shift+R releases all.')
end
-- Use the actual player root/camera for proximity, not the tool-hand helper.
function W.playerNode()
    local p=g_localPlayer;if p==nil then return nil end
    if exists(p.rootNode) then return p.rootNode end
    if p.getCurrentCameraNode~=nil then local n=p:getCurrentCameraNode();if exists(n) then return n end end
    if p.getHandsKinematicNode~=nil then return p:getHandsKinematicNode() end
end
function W.nearBlade(s,node)
    if not exists(node) then return math.huge end
    local x,y,z=getWorldTranslation(node);local a,b,c=getWorldTranslation(s.anchor)
    return math.sqrt((x-a)^2+(z-c)^2)
end
function W.unregisterPlayerEvents()
    for _,id in pairs(W.events) do g_inputBinding:removeActionEvent(id) end
    W.events={}
end

function W.safePlayer()
    return g_localPlayer~=nil and not g_localPlayer:getIsInVehicle()
        and g_currentMission~=nil and not g_currentMission.isPlayerFrozen
        and (g_gui==nil or not g_gui:getIsGuiVisible())
end
function W.action(self,name,value)
    local s=W.selected
    if s==nil or not W.safePlayer() then return end
    local hand=W.playerNode()
    if not exists(hand) then return end
    if name=='TWINCH_HOOK_V13' then
        if s.carrying then
            local hit=W.findTarget(s)
            if hit~=nil then W.attach(s,hit) else message('Look at a tree, log or movable object within four metres.') end
        elseif W.nearBlade(s,hand)<=3.0 then
            TWinch.disconnect(s.vehicle);s.carrying=true;s.vehicle:raiseActive()
            message(#s.targets==0 and 'Hook taken. Walk to a machine, tree or object and press R.' or 'Chain taken. Walk to another log and press R.')
        end
    elseif name=='TWINCH_LOG_CLEAR_V13' then W.clear(s)
    else
        s.lastInput=s.clock
        if name=='TWINCH_LOG_REEL_V13' then s.reel=value>0 and 1 or 0
        elseif name=='TWINCH_LOG_FAST_V13' then s.reel=value>0 and 4 or 0
        elseif name=='TWINCH_LOG_OUT_V13' then s.payout=value end
        if (name=='TWINCH_LOG_REEL_V13' or name=='TWINCH_LOG_FAST_V13') and value>0 and s.vehicle.startMotor~=nil and not s.vehicle:getIsMotorStarted() then s.vehicle:startMotor() end
        s.vehicle:raiseActive()
    end
end
function W.registerPlayerEvents()
    if g_inputBinding==nil or PlayerInputComponent==nil or not W.safePlayer() then return end
    if g_inputBinding.currentContextName~=nil and g_inputBinding.currentContextName~=PlayerInputComponent.INPUT_CONTEXT_NAME then return end
    if W.inputPlayer~=g_localPlayer then W.unregisterPlayerEvents();W.inputPlayer=g_localPlayer end
    if next(W.events)~=nil then return end
    local failed=false
    g_inputBinding:beginActionEventsModification(PlayerInputComponent.INPUT_CONTEXT_NAME)
    for _,a in ipairs(W.actions) do
        local _,id=g_inputBinding:registerActionEvent(a.name,W,W.action,a.hold,not a.hold,a.hold,true)
        if id~=nil then
            W.events[a.name]=id
            g_inputBinding:setActionEventText(id,a.text)
            g_inputBinding:setActionEventTextPriority(id,(GS_PRIO_VERY_HIGH or GS_PRIO_HIGH))
            g_inputBinding:setActionEventActive(id,false)
        else failed=true;Logging.warning('T-Winch: unable to register player action '..a.name) end
    end
    g_inputBinding:endActionEventsModification()
    if failed then W.unregisterPlayerEvents() end
end
function W.update(self,dt)
    -- Vehicle-update fallback and global listener share one mission frame.
    local time=g_currentMission~=nil and g_currentMission.time or nil
    if time~=nil and W.lastFrame==time then return end
    W.lastFrame=time
    W.registerPlayerEvents()
    local playerOK=W.safePlayer()
    local hand=playerOK and W.playerNode() or nil
    local selected=nil;local nearest=3.0
    if exists(hand) then
        for _,s in ipairs(W.instances) do
            if s.carrying then selected=s;break end
            local d=W.nearBlade(s,hand)
            if d<nearest then selected=s;nearest=d end
        end
        if selected==nil and W.selected~=nil and #W.selected.targets>0 and distance(hand,W.selected.anchor)<=60 then selected=W.selected end
    end
    W.selected=selected
    for _,a in ipairs(W.actions) do
        local id=W.events[a.name]
        if id~=nil then
            local active=selected~=nil and (a.name=='TWINCH_HOOK_V13' and (selected.carrying or W.nearBlade(selected,hand)<=3.0) or a.name=='TWINCH_LOG_CLEAR_V13' or #selected.targets>0 and a.name~='TWINCH_HOOK_V13')
            g_inputBinding:setActionEventActive(id,active)
            g_inputBinding:setActionEventTextVisibility(id,active)
            if a.name=='TWINCH_HOOK_V13' and selected~=nil then
                g_inputBinding:setActionEventText(id,selected.carrying and 'Attach winch hook to object (look at target)' or (#selected.targets>0 and 'Take additional log chain' or 'Take winch hook from blade'))
            end
        end
    end
    for _,s in ipairs(W.instances) do
        s.clock=s.clock+dt
        if s.clock-s.lastInput>250 or selected~=s then s.reel=0;s.payout=0 end
        if s.carrying or #s.targets>0 then s.vehicle:raiseActive() end
        local carryNode=hand
        if playerOK and g_localPlayer.getHandsKinematicNode~=nil then
            local n=g_localPlayer:getHandsKinematicNode();if exists(n) then carryNode=n end
        end
        W.drawWinch(s,carryNode)
    end
end
function W.span(n,ax,ay,az,bx,by,bz)
    local dx,dy,dz=bx-ax,by-ay,bz-az;local length=math.sqrt(dx*dx+dy*dy+dz*dz)
    setVisibility(n,length>.001)
    if length>.001 then
        setWorldTranslation(n,ax,ay,az)
        local ux,uy=0,1;if math.abs(dy/length)>.99 then ux,uy=1,0 end
        setWorldDirection(n,dx/length,dy/length,dz/length,ux,uy,0);setScale(n,1,1,length)
    end
end
function W.drawWinch(s,hand)
    local endNode=#s.targets>0 and s.targets[1].ref or (s.carrying and exists(hand) and hand or nil)
    if not exists(endNode) then for _,n in ipairs(s.segments) do setVisibility(n,false) end;return end
    local ax,ay,az=getWorldTranslation(s.anchor)
    local bx,by,bz=getWorldTranslation(endNode)
    if distance(s.anchor,endNode)>60 then W.clear(s);message('Winch cable reached its maximum length.');return end
    local straight=math.sqrt((bx-ax)^2+(by-ay)^2+(bz-az)^2)
    local slack=s.carrying and .05 or math.min(2,math.max(0,s.length-straight)*.5)
    local px,py,pz=ax,ay,az
    -- First sixteen segments form the rope; remaining eight join additional chained logs.
    for i=1,16 do
        local f=i/16;local x,y,z=ax+(bx-ax)*f,ay+(by-ay)*f-slack*4*f*(1-f),az+(bz-az)*f
        local ground=getTerrainHeightAtWorldPos(g_currentMission.terrainRootNode,x,0,z)
        y=math.max(y,ground+.025)
        W.span(s.segments[i],px,py,pz,x,y,z);px,py,pz=x,y,z
    end
    if exists(s.hook) then
        setWorldTranslation(s.hookPivot,bx,by,bz)
        local dx,dy,dz=ax-bx,ay-by,az-bz;local length=math.sqrt(dx*dx+dy*dy+dz*dz)
        if length>.001 then
            local ux,uy=0,1;if math.abs(dy/length)>.99 then ux,uy=1,0 end
            setWorldDirection(s.hookPivot,dx/length,dy/length,dz/length,ux,uy,0)
        end
        setScale(s.hook,.014,.014,.014)
    end
    if exists(s.extraHook) then
        local carryingExtra=s.carrying and #s.targets>0 and exists(hand)
        setVisibility(s.extraHook,carryingExtra)
        if carryingExtra then local x,y,z=getWorldTranslation(hand);setWorldTranslation(s.extraHookPivot,x,y,z);setScale(s.extraHook,.014,.014,.014) end
    end
    for i=17,24 do
        local t=s.targets[i-15]
        if t~=nil and exists(t.ref) and #s.targets>0 then
            local x,y,z=getWorldTranslation(s.targets[1].ref);local u,v,w=getWorldTranslation(t.ref)
            W.span(s.segments[i],x,y,z,u,v,w)
        elseif i==24 and s.carrying and #s.targets>0 and exists(hand) then
            local x,y,z=getWorldTranslation(s.targets[1].ref);local u,v,w=getWorldTranslation(hand)
            W.span(s.segments[i],x,y,z,u,v,w)
        else setVisibility(s.segments[i],false) end
    end
end
function W.pull(s,from,to,t,length)
    local ax,ay,az=getWorldTranslation(from);local bx,by,bz=getWorldTranslation(t.ref)
    local dx,dy,dz=bx-ax,by-ay,bz-az;local d=math.sqrt(dx*dx+dy*dy+dz*dz)
    if d<.01 then return d end
    dx,dy,dz=dx/d,dy/d,dz/d
    local vx,vy,vz=getLinearVelocity(to)
    local ux,uy,uz=0,0,0;if not t.static then ux,uy,uz=getLinearVelocity(t.node) end
    local force=TWinch.winchTension(d,length,(ux-vx)*dx+(uy-vy)*dy+(uz-vz)*dz,getMass(to),t.static and nil or getMass(t.node))
    if force>0 then
        local cx,cy,cz=getCenterOfMass(to)
        addForce(to,dx*force,dy*force,dz*force,cx,cy,cz,true)
        if t.vehicle~=nil then t.vehicle:raiseActive() end
        if not t.static then
            local cx,cy,cz=getCenterOfMass(t.node)
            addForce(t.node,-dx*force,-dy*force,-dz*force,cx,cy,cz,true)
        end
    end
    return d
end
function W.tickOne(vehicle,s,dt)
    if s==nil or #s.targets==0 then return end
    for _,t in ipairs(s.targets) do if not exists(t.node) or not exists(t.ref) or (t.vehicle~=nil and (t.vehicle.isDeleted or not t.vehicle.isAddedToPhysics)) then W.clear(s);return end end
    if vehicle.spec_twinch.target~=nil then W.clear(s);return end
    local t=s.targets[1];local d=distance(s.anchor,t.ref)
    if d>60 then W.clear(s);return end
    local seconds=math.min(math.max(dt/1000,0),.1)
    if s.payout>0 then s.length=math.min(60,s.length+.8*seconds)
    elseif s.reel>0 and vehicle:getIsMotorStarted() and d-s.length<1 then s.length=math.max(1.2,s.length-.6*s.reel*seconds) end
    W.pull(s,s.anchor,vehicle.components[1].node,t,s.length)
    for i=2,#s.targets do W.pull(s,t.ref,t.node,s.targets[i],s.targets[i].length) end
    local winching=s.reel>0 and vehicle:getIsMotorStarted()
    if s.samples~=nil and s.samples.winching~=nil then
        if winching and not s.playing then g_soundManager:playSample(s.samples.winching,0)
        elseif not winching and s.playing then g_soundManager:stopSample(s.samples.winching) end
    end
    s.playing=winching;vehicle:raiseActive()
end
function W.tick(vehicle,dt)
    for _,s in ipairs(vehicle.spec_twinch.loggingWinches or {vehicle.spec_twinch.logging}) do W.tickOne(vehicle,s,dt) end
end
function W.delete(vehicle)
    for _,s in ipairs(vehicle.spec_twinch.loggingWinches or {vehicle.spec_twinch.logging}) do W.deleteOne(vehicle,s) end
    vehicle.spec_twinch.loggingWinches={}
end
function W.deleteMap(self)
    for _,id in pairs(W.events) do g_inputBinding:removeActionEvent(id) end
    W.events={};W.selected=nil;W.instances={}
end
-- Rebuild events after the player component registers its input context.
-- This also covers respawn/input-context rebuilding during a mission.
if PlayerInputComponent~=nil and Utils~=nil and Utils.appendedFunction~=nil then
    PlayerInputComponent.registerActionEvents=Utils.appendedFunction(PlayerInputComponent.registerActionEvents,function()
        if g_inputBinding~=nil then W.unregisterPlayerEvents();W.inputPlayer=nil end
    end)
end
if addModEventListener~=nil then addModEventListener(W) end

-- Add native crawler support exactly once, before type validation. Some base
-- types already inherit Crawlers; redeclaring it would reject the vehicle.
local volvoCrawlerVehicleType=g_currentModName..'.twinchV30'
function TWinch.installVolvoCrawlers(manager)
    if manager.typeName~='vehicle' then return end
    local vehicleType=manager.types[volvoCrawlerVehicleType]
    if vehicleType~=nil then
        for _,entry in ipairs({{'wearable',Wearable},{'washable',Washable}}) do
            if entry[2]~=nil and not SpecializationUtil.hasSpecialization(entry[2],vehicleType.specializations) then manager:addSpecialization(volvoCrawlerVehicleType,entry[1]) end
        end
    end
    if vehicleType~=nil and not SpecializationUtil.hasSpecialization(Crawlers,vehicleType.specializations) then
        manager:addSpecialization(volvoCrawlerVehicleType,'crawlers')
    end
end
if TypeManager~=nil then
    TypeManager.validateTypes=Utils.prependedFunction(TypeManager.validateTypes,TWinch.installVolvoCrawlers)
end

-- Run during native vehicle loading, before TerraFarm's Vehicle.load wrapper
-- resolves the machine profile after its superFunc returns.
function TWinch.registerTerraFarm(vehicle)
    local core=_G and _G.FS25_0_TerraFarm or nil
    local manager=core and core.g_machineManager or g_machineManager
    local helpers=core and core.MachineUtils or nil
    local directory=vehicle.baseDirectory or TWinch.MOD_DIRECTORY or g_currentModDirectory
    if directory==nil or directory=='' then
        if Logging~=nil then Logging.warning('T-Winch: TerraFarm profile base directory unavailable') end
        return false
    end
    local filename=vehicle.configFileName
    if manager==nil or manager.registerConfiguration==nil then
        if Logging~=nil then Logging.warning('T-Winch: TerraFarm machine manager unavailable during vehicle load') end
        return false
    end
    local key=nil
    if helpers~=nil and helpers.getVehicleModFilename~=nil then key=helpers.getVehicleModFilename(vehicle)
    elseif filename~=nil and g_modsDirectory~=nil and filename:sub(1,#g_modsDirectory)==g_modsDirectory then key=filename:sub(#g_modsDirectory+1) end
    if key==nil then
        if Logging~=nil then Logging.warning('T-Winch: cannot resolve TerraFarm vehicle registry key') end
        return false
    end
    local profile=directory..'xml/terraFarmBlade.xml'
    manager:registerConfiguration(profile,key)
    if Logging~=nil and Logging.info~=nil then Logging.info('T-Winch: registered TerraFarm blade profile for %s',key) end
    return true
end

-- Native Wearable/Washable own progression, washing, repainting and save data.
-- Only crawler steel tint is extended: worn paint exposes silver metal.
function TWinch.updateTrackWear(self,dt)
    if not self.isClient or self.spec_twinch==nil or self.getWearTotalAmount==nil then return end
    local spec=self.spec_twinch
    spec.trackWearTimer=(spec.trackWearTimer or 2000)+(dt or 0)
    if spec.trackWearTimer<1000 then return end
    spec.trackWearTimer=0
    local wear=math.max(0,math.min(1,self:getWearTotalAmount() or 0))
    local t=wear*wear*(3-2*wear)
    local function scan(node,crawler)
        if not entityExists(node) then return end
        local name=getName(node)
        crawler=crawler or name=='crawlerLeft' or name=='crawlerRight'
        if crawler and (name=='LOD0' or name=='LOD1') and getHasShaderParameter(node,'colorScale') then
            setShaderParameter(node,'colorScale',.035+(.78-.035)*t,.04+(.8-.04)*t,.045+(.82-.045)*t,nil,false)
            if getHasShaderParameter(node,'smoothnessScale') then setShaderParameter(node,'smoothnessScale',.3+.35*t,nil,nil,nil,false) end
        end
        for i=0,getNumOfChildren(node)-1 do scan(getChildAt(node,i),crawler) end
    end
    for _,component in ipairs(self.components) do scan(component.node,false) end
end
