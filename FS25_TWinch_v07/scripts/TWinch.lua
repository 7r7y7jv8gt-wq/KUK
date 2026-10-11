-- Single-player vehicle recovery winch and geometric track animation.
-- Engine units: mass in tonnes, force in kN, dt in milliseconds.
TWinch = {}

function TWinch.prerequisitesPresent(specializations)
    return SpecializationUtil.hasSpecialization(Drivable, specializations)
        and SpecializationUtil.hasSpecialization(Wheels, specializations)
end

function TWinch.initSpecialization()
    local schema = Vehicle.xmlSchema
    schema:setXMLSpecializationType("TWinch")
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
    spec.anchor = self.xmlFile:getValue("vehicle.twinch#anchor", nil, self.components, self.i3dMappings)
    spec.cable = self.xmlFile:getValue("vehicle.twinch#cable", nil, self.components, self.i3dMappings)
    self.xmlFile:iterate("vehicle.twinch.track", function(index, key)
        local track = {
            node=self.xmlFile:getValue(key.."#node", nil, self.components, self.i3dMappings),
            offsetX=self.xmlFile:getValue(key.."#offsetX", 0), phase=0, rollers={}
        }
        if track.node ~= nil then
            track.count = getNumOfChildren(track.node)
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
                if d>2 and d<nearestDistance then nearest=vehicle; nearestDistance=d end
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
    local limit=math.min(25,math.max(0,getMass(targetNode))*3,math.max(0,getMass(ownNode))*3)
    local tension=TWinch.ropeTension(distance,spec.length,separation,limit)
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
    if self.isServer and self.isAddedToPhysics then TWinch.updateBlade(self,dt); TWinch.updateWinch(self,dt) end
end

function TWinch.onUpdate(self, dt)
    if not self.isClient then return end
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
    if not self.isClient then return end
    local spec=self.spec_twinch
    self:clearActionEventsTable(spec.actionEvents)
    if not (isActiveForInput or isActiveForInputIgnoreSelection) then return end

    if spec.blade ~= nil then
        local _,id=self:addActionEvent(spec.actionEvents,'TWINCH_BLADE_LIFT',self,TWinch.actionBlade,true,false,true,true)
        if id ~= nil then
            g_inputBinding:setActionEventText(id,'Hydraulic blade: left mouse + vertical / Page Up / Page Down')
            g_inputBinding:setActionEventTextPriority(id,GS_PRIO_HIGH)
            g_inputBinding:setActionEventTextVisibility(id,true)
        else
            Logging.warning('T-Winch: could not register an input action; check input bindings')
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
    if self.spec_twinch.blade ~= nil then self.spec_twinch.blade.input=0 end
    self.spec_twinch.reel=false; self.spec_twinch.payout=false
end

function TWinch.onDelete(self)
    TWinch.disconnect(self)
end

-- Explicit single-player hydraulic blade input and endpoint alignment.
-- Loaded after TWinch; avoids native arm-selection/easy-arm-control filtering.
TWinch.MOD_NAME = g_currentModName

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
    local blade=self.spec_twinch.blade
    if blade == nil or not self.isServer then return end
    blade.input=math.max(-1,math.min(1,value))
    blade.isMouse=isMouse == true
    blade.inputAge=0
end

function TWinch.updateBlade(self,dt)
    local blade=self.spec_twinch.blade
    if blade == nil or not self.isServer then return end
    blade.inputAge=(blade.inputAge or 1000)+dt
    if blade.inputAge>250 then blade.input=0 end
    if self:getIsMotorStarted() and blade.input ~= 0 then
        local nextAngle=math.max(-28,math.min(25,blade.angle-blade.input*12*math.min(dt,100)/1000))
        if nextAngle ~= blade.angle then
            blade.angle=nextAngle
            TWinch.applyBlade(self)
            self:raiseActive()
        end
    end
    -- Mouse input is a delta; never keep a stale delta after movement stops.
    if blade.isMouse then blade.input=0 end
end

function TWinch.saveToXMLFile(self,xmlFile,key,usedModNames)
    if self.spec_twinch.blade ~= nil then xmlFile:setValue(key..'#bladeAngle',self.spec_twinch.blade.angle) end
end
