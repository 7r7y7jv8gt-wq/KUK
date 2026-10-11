-- Run during native vehicle loading, before TerraFarm's Vehicle.load wrapper
-- resolves the machine profile after its superFunc returns.
function TWinch.registerTerraFarm(vehicle)
    local core=_G and _G.FS25_0_TerraFarm or nil
    local manager=core and core.g_machineManager or g_machineManager
    local helpers=core and core.MachineUtils or nil
    local directory=g_currentModDirectory
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
