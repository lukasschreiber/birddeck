-- Catalog-owned metadata travels with the .lrcat file across computers.
local M = {}
function M.read(catalog)
    return catalog:getPropertyForPlugin(_PLUGIN, 'catalogUuid') or '',
        catalog:getPropertyForPlugin(_PLUGIN, 'bindingState') or '',
        catalog:getPropertyForPlugin(_PLUGIN, 'keywordBindings') or ''
end
function M.resolve(catalog, identity)
    local _, _, bindings = M.read(catalog)
    for row in bindings:gmatch('[^\n]+') do
        local uuid, id = row:match('^([%x%-]+)\t(%d+)$')
        if uuid == identity:lower() then return id end
    end
end
function M.store(catalog, identity, state, bindings)
    -- Caller owns the write gate; strings are supported catalog metadata values.
    catalog:setPropertyForPlugin(_PLUGIN, 'catalogUuid', identity)
    catalog:setPropertyForPlugin(_PLUGIN, 'bindingState', state)
    catalog:setPropertyForPlugin(_PLUGIN, 'keywordBindings', bindings)
end
return M
