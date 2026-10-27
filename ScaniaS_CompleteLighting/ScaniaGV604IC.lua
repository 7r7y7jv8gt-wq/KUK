-- Small bridge for the optional FS25 Interactive Control add-on.
-- IC controller 2 owns the mode, including savegame and multiplayer state.
-- This file registers only a momentary button function; it owns no state/event.
ScaniaGV604IC = {}

local FUNCTION_NAME = "SCANIA_GV604_CYCLE_MODE"
local MODE_CONTROLLER_INDEX = 2

function ScaniaGV604IC.register()
    local environment = _G["FS25_interactiveControl"]
    if environment == nil and g_currentMission ~= nil then
        local manager = g_currentMission.interactiveControl
        if manager ~= nil and manager.modName ~= nil then
            environment = _G[manager.modName]
        end
    end
    local functions = environment ~= nil and environment.InteractiveFunctions or nil
    if functions == nil or functions.addFunction == nil then
        return false -- The truck still loads normally without the optional add-on.
    end
    if functions.getFunctionData(FUNCTION_NAME) ~= nil then
        return true
    end

    return functions.addFunction(FUNCTION_NAME, {
        posFunc = function(target, data, noEventSend)
            -- The button's native IC event reaches the server. Only the server
            -- chooses a new mode, then the mode controller broadcasts it.
            -- Join-stream replays on clients must never advance the mode.
            if target == nil or not target.isServer or target.getInteractiveControllerByIndex == nil then
                return
            end
            local controller = target:getInteractiveControllerByIndex(MODE_CONTROLLER_INDEX)
            if controller == nil then
                return
            end
            local index = math.floor(math.clamp(controller:getStateValue(), 0, 1) * 2 + 0.5)
            local nextValue = ((index + 1) % 3) / 2
            controller:setStateValue(nextValue, true, false, false)
        end,
        negFunc = function(target, data, noEventSend)
            -- Initial state and momentary reset do not execute the action.
        end,
        updateFunc = function(target, data)
            -- IC resets the button to false without another event or actor call.
            return false
        end
    })
end

-- Called after IC's prepended type-installation hook, once all selected mods
-- have loaded. The loadMap fallback is idempotent and covers late initialization.
if TypeManager ~= nil and TypeManager.validateTypes ~= nil then
    TypeManager.validateTypes = Utils.appendedFunction(TypeManager.validateTypes, function(typeManager)
        if typeManager.typeName == "vehicle" then
            ScaniaGV604IC.register()
        end
    end)
end

function ScaniaGV604IC:loadMap()
    ScaniaGV604IC.register()
end
addModEventListener(ScaniaGV604IC)
