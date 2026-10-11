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
        spec.blade.angle=math.max(-28,math.min(0,savegame.xmlFile:getValue(savegame.key..'.'..name..'#bladeAngle',0)))
    end
    TWinch.applyBlade(self)
    if Logging ~= nil then
        if spec.blade.node == nil then
            Logging.error('T-Winch v06: blade node missing; hydraulic controls cannot move the blade')
        else
            Logging.info('T-Winch v06: hydraulic blade controller loaded; Page Up/Page Down and left mouse controls')
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
        local nextAngle=math.max(-28,math.min(0,blade.angle-blade.input*12*math.min(dt,100)/1000))
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
