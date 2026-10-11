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
