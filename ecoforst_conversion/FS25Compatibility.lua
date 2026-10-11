-- FS25 player bridge for the original LogsWinch implementation.
local function valid(node) return node~=nil and node~=0 and entityExists(node) end
function LogsWinch.getPlayer()
    local player=g_localPlayer
    local camera=player~=nil and player.getCurrentCameraNode~=nil and player:getCurrentCameraNode() or nil
    local proxy={cameraNode=camera,model={},isObjectInRange=false}
    if valid(camera) then
        -- A temporary target four metres along the current view replaces the FS22 pickup helper.
        if LogsWinch.aimNode==nil or not valid(LogsWinch.aimNode) then LogsWinch.aimNode=createTransformGroup('FS25WinchAim') end
        local x,y,z=localToWorld(camera,0,0,-2)
        setTranslation(LogsWinch.aimNode,x,y,z)
        proxy.model.pickUpKinematicHelperNode=LogsWinch.aimNode
        proxy.isObjectInRange=not player:getIsInVehicle()
    end
    return proxy
end
function LogsWinch.getPlayerNode()
    local player=g_localPlayer
    if player==nil then return nil end
    if valid(player.rootNode) then return player.rootNode end
    if player.getCurrentCameraNode~=nil then return player:getCurrentCameraNode() end
end
function LogsWinch.setEventActive(self,name,active)
    local id=self.lwActionEventIds~=nil and self.lwActionEventIds[name] or nil
    if id~=nil then g_inputBinding:setActionEventActive(id,active) end
end
function LogsWinch.readWear(node)
    if getHasShaderParameter(node,'scratches_dirt_snow_wetness') then return getShaderParameter(node,'scratches_dirt_snow_wetness') end
    return 0,0,0,0
end
function LogsWinch.writeWear(node,x,y,z,w)
    if getHasShaderParameter(node,'scratches_dirt_snow_wetness') then setShaderParameter(node,'scratches_dirt_snow_wetness',x,y,z,w,false) end
end
-- Player registration is rebuilt when FS25 recreates its player input context.
function LogsWinch.refreshPlayerEvents()
    local entry=LogsWinch.AvailableWinches[LogsWinch.ActiveWinchIdx]
    if entry~=nil and entry[1]~=nil then entry[1]:lwRegisterActionEvents(entry[1]:getIsActiveForInput(true)) end
end
if PlayerInputComponent~=nil and PlayerInputComponent.registerActionEvents~=nil then
    PlayerInputComponent.registerActionEvents=Utils.appendedFunction(PlayerInputComponent.registerActionEvents,LogsWinch.refreshPlayerEvents)
end
-- Add native specializations only when they are not already inherited.
EcoforstFS25={MOD_NAME=g_currentModName}
function EcoforstFS25.installTypes(manager)
    if manager.typeName~='vehicle' then return end
    local lists={
        ecoforstTWinch={{'cover',Cover},{'foldable',Foldable},{'foliageBending',FoliageBending},{'washable',Washable},{'wearable',Wearable},{'animatedVehicle',AnimatedVehicle},{'vehicleSettings',VehicleSettings},{'cylindered',Cylindered},{'mountable',Mountable},{'wheels',Wheels},{'crawlers',Crawlers},{'speedRotatingParts',SpeedRotatingParts},{'attachable',Attachable},{'powerTakeOffs',PowerTakeOffs},{'powerConsumer',PowerConsumer},{'attacherJoints',AttacherJoints},{'cylinderedFoldable',CylinderedFoldable},{'attacherJointControl',AttacherJointControl},{'turnOnVehicle',TurnOnVehicle},{'connectionHoses',ConnectionHoses},{'suspensions',Suspensions}},
        ecoforstTowHook={{'attachable',Attachable},{'fillTriggerVehicle',FillTriggerVehicle},{'dischargeable',Dischargeable},{'tensionBelts',TensionBelts},{'tensionBeltObject',TensionBeltObject}}
    }
    for suffix,list in pairs(lists) do
        local name=EcoforstFS25.MOD_NAME..'.'..suffix
        local t=manager.types[name]
        if t~=nil then
            for _,entry in ipairs(list) do
                if entry[2]~=nil and not SpecializationUtil.hasSpecialization(entry[2],t.specializations) then manager:addSpecialization(name,entry[1]) end
            end
        end
    end
end
TypeManager.validateTypes=Utils.prependedFunction(TypeManager.validateTypes,EcoforstFS25.installTypes)
