-- Direct catalog keyword synchronization. Never deletes keywords or photo links.
local Application = import 'LrApplication'
local Tasks = import 'LrTasks'
local Paths = import 'LrPathUtils'
local Bindings = dofile(Paths.child(_PLUGIN.path, 'CatalogBindings.lua'))
local function decode(s)
    return (s:gsub('%%(%x%x)', function(h) return string.char(tonumber(h, 16)) end))
end
local function encode(s)
    return (s:gsub('[^%w_.~-]', function(c) return string.format('%%%02X', string.byte(c)) end))
end
local function normalized(s) return s:gsub('/', '\\'):lower() end
local function snapshot(catalog)
    local nodes, rows = {}, {}
    local function walk(keywords, parent, scoped)
        for _, keyword in ipairs(keywords) do
            local name = keyword:getName()
            local node = { keyword = keyword, id = tostring(keyword.localIdentifier),
                parent = parent, name = name, photos = #keyword:getPhotos(),
                scoped = scoped or (not parent and name == 'Vogel') }
            nodes[#nodes + 1] = node
            walk(keyword:getChildren(), keyword, node.scoped)
        end
    end
    walk(catalog:getKeywords(), nil, false)
    table.sort(nodes, function(a, b) return tonumber(a.id) < tonumber(b.id) end)
    for _, node in ipairs(nodes) do
        rows[#rows + 1] = node.id .. '\t' .. (node.parent and tostring(node.parent.localIdentifier) or '0')
            .. '\t' .. encode(node.name) .. '\t' .. node.photos .. '\n'
    end
    return nodes, table.concat(rows)
end
local function write(catalog, title, fn)
    if catalog:withWriteAccessDo(title, fn, { timeout = 15 }) ~= 'executed' then
        error('Lightroom is busy; hierarchy write was not executed')
    end
end
local function rename(keyword, name)
    if keyword:getName() == name then return end
    if keyword:setAttributes({ keywordName = name, ignoreCase = false }) == false then
        error('Keyword name conflict: ' .. name)
    end
end
local function move(keyword, parent)
    local current = keyword:getParent()
    if (current and current.localIdentifier or 0) == (parent and parent.localIdentifier or 0) then return end
    if keyword:setParent(parent) == false then error('Keyword parent change failed') end
    local actual = keyword:getParent()
    if (actual and actual.localIdentifier or 0) ~= (parent and parent.localIdentifier or 0) then
        error('Lightroom did not apply the parent change for keyword ' .. keyword.localIdentifier)
    end
end
return function(contents)
    local expiry, mode, catalogPath, body = contents:match('^HIERARCHY\n(%d+)\n([^\n]+)\n([^\n]*)\n(.*)$')
    if not expiry or os.time() >= tonumber(expiry) then error('Hierarchy request expired or invalid') end
    local catalog = Application.activeCatalog()
    if mode == 'STATE' then
        if normalized(catalog:getPath()) ~= normalized(decode(catalogPath)) then error('Wrong Lightroom catalog is open') end
        local identity, state = Bindings.read(catalog)
        return 'OK\tSTATE\n' .. identity .. '\n' .. encode(state) .. '\n'
    end
    local live, fingerprint = snapshot(catalog)
    if mode == 'SNAPSHOT' then return 'OK\tSNAPSHOT\tCATALOG-3\n' .. encode(catalog:getPath()) .. '\n' .. fingerprint end
    if mode == 'STORE' or mode == 'RESET' then
        if normalized(catalog:getPath()) ~= normalized(decode(catalogPath)) then error('Wrong Lightroom catalog is open') end
        local identity, expected, serialized, mappings = body:match('^([%x%-]+)\nEXPECTED\n(.-)STATE\n([^\n]*)\n(.*)$')
        if not identity or #identity ~= 36 or expected ~= fingerprint then error('Catalog changed before storing bindings') end
        local existing = Bindings.read(catalog)
        if mode ~= 'RESET' and existing ~= '' and existing ~= identity then error('Catalog identity changed; synchronize again') end
        local seenUuids, seenIds = {}, {}
        for row in mappings:gmatch('[^\n]+') do
            local uuid, id = row:match('^([%x%-]+)\t(%d+)$')
            if not uuid or #uuid ~= 36 or seenUuids[uuid] or seenIds[id] then error('Invalid or repeated binding') end
            seenUuids[uuid], seenIds[id] = true, true
            local found
            for _, node in ipairs(live) do if node.id == id and node.scoped then found = true end end
            if not found then error('Cannot bind a keyword missing from Vogel: ' .. id) end
        end
        write(catalog, 'BirdDeck: store catalog identity and bindings', function()
            local _, current = snapshot(catalog)
            if current ~= expected then error('Catalog changed before metadata write') end
            local currentIdentity = Bindings.read(catalog)
            if currentIdentity ~= existing then error('Catalog identity changed before metadata write') end
            Bindings.store(catalog, identity, decode(serialized), mappings)
        end)
        return 'OK\tSTORED\n'
    end
    if mode ~= 'APPLY' then error('Unknown hierarchy operation') end
    if normalized(catalog:getPath()) ~= normalized(decode(catalogPath)) then error('Wrong Lightroom catalog is open') end
    local expected, rows = body:match('^EXPECTED\n(.-)NODES\n(.*)$')
    if expected ~= fingerprint then error('Catalog changed since preview; run synchronization again') end
    local byId, plan, used = {}, {}, {}
    for _, node in ipairs(live) do
        byId[node.id] = node
        -- Empty staging keywords from an interrupted BirdDeck creation are ours.
        if node.photos == 0 and node.name:match('^_BirdDeck_new_%d+_%d+_%d+$') then node.scoped = true end
    end
    for row in rows:gmatch('[^\n]+') do
        local index, parent, id, name = row:match('^(%d+)\t(%d+)\t(%d+)\t(.+)$')
        index, parent, name = tonumber(index), tonumber(parent), name and decode(name)
        if not index or index ~= #plan + 1 or parent >= index or (index > 1 and parent == 0)
            or (index == 1 and (parent ~= 0 or name ~= 'Vogel')) or name:find('[\r\n\t]') then
            error('Invalid hierarchy plan')
        end
        local node = { index = index, parent = parent, name = name, id = id }
        if id ~= '0' then
            if used[id] or not byId[id] then error('Invalid or repeated catalog keyword ID') end
            used[id] = true
            -- Explicit UUID bindings also recover our keywords stranded outside Vogel.
            byId[id].scoped = true
            node.keyword = byId[id].keyword
        end
        local ancestor = parent
        while ancestor > 0 do
            if plan[ancestor].name:lower() == name:lower() then error('Ancestor name conflict: ' .. name) end
            ancestor = plan[ancestor].parent
        end
        for _, sibling in ipairs(plan) do
            if sibling.parent == parent and sibling.name:lower() == name:lower() then error('Duplicate sibling name: ' .. name) end
        end
        plan[#plan + 1] = node
    end
    if #plan == 0 then error('Empty hierarchy plan') end
    -- An existing Vogel root must be reused, never hidden by a new root.
    for _, node in ipairs(live) do
        if not node.parent and node.name == 'Vogel' and plan[1].id ~= node.id then error('Vogel root binding missing') end
    end
    -- Compare local names and immediate parent IDs. Moving a group carries its
    -- unchanged descendants; those descendants must not be rewritten.
    local affected, reparent, complex = {}, {}, false
    for _, node in ipairs(plan) do
        local original = byId[node.id]
        local targetParent = node.parent > 0 and plan[node.parent].id or '0'
        if original then
            local oldParent = original.parent and tostring(original.parent.localIdentifier) or '0'
            reparent[node.id] = oldParent ~= targetParent
            if reparent[node.id] or original.name ~= node.name then
                affected[node.id] = true
                -- Reserve names only for collisions. Include current names
                -- because Lightroom reads committed state during a rename gate.
                for _, other in ipairs(live) do
                    if other.id ~= node.id and other.name:lower() == node.name:lower() then complex = true end
                    local otherParent = other.parent and tostring(other.parent.localIdentifier) or '0'
                    if reparent[node.id] and other.id ~= node.id and otherParent == targetParent
                        and other.name:lower() == original.name:lower() then complex = true end
                end
                local ancestor = node.parent > 0 and plan[node.parent].keyword or nil
                while ancestor do
                    if ancestor.localIdentifier == original.keyword.localIdentifier
                        or ancestor:getName():lower() == original.name:lower() then complex = true end
                    ancestor = ancestor:getParent()
                end
            end
        else
            -- A new node may claim a name being vacated by a rename/archive.
            for _, other in ipairs(live) do
                if other.name:lower() == node.name:lower() then complex = true end
            end
        end
    end
    for _, node in ipairs(live) do
        if node.scoped and not used[node.id] then affected[node.id], reparent[node.id] = true, true end
    end
    local token = tostring(os.time()) .. '_' .. tostring(math.random(100000, 999999))
    local archive, created = nil, {}
    for _, node in ipairs(live) do
        if not node.parent and node.name == '_BirdDeck Obsolete' then archive = node.keyword end
    end
    -- Commit all new objects before using them as parents.
    write(catalog, 'BirdDeck: create hierarchy keywords', function()
        if os.time() >= tonumber(expiry) then error('Hierarchy request expired before write') end
        local _, current = snapshot(catalog)
        if current ~= expected then error('Catalog changed before write; run synchronization again') end
        if not archive then archive = catalog:createKeyword('_BirdDeck Obsolete', {}, false, nil, true) end
        for _, node in ipairs(plan) do
            if not node.keyword then
                node.keyword = catalog:createKeyword('_BirdDeck_new_' .. token .. '_' .. node.index, {}, true, nil, false)
                if not node.keyword then error('Could not create keyword') end
                created[#created + 1] = node.keyword
            end
        end
    end)
    local function temporaryNames()
        -- Commit names before reparenting or restoring final names. Lightroom
        -- does not expose pending attribute changes reliably within one gate.
        write(catalog, 'BirdDeck: reserve keyword names', function()
            for _, node in ipairs(live) do
                if affected[node.id] and node.id ~= plan[1].id then
                    rename(node.keyword, '_BirdDeck_' .. token .. '_' .. node.id)
                end
            end
            for i, keyword in ipairs(created) do rename(keyword, '_BirdDeck_created_' .. token .. '_' .. i) end
        end)
        -- setParent performs its own write. Never nest it in withWriteAccessDo.
        for _, node in ipairs(live) do
            if reparent[node.id] and node.id ~= plan[1].id then move(node.keyword, nil) end
        end
        for _, keyword in ipairs(created) do move(keyword, nil) end
    end
    local ok, failure = Tasks.pcall(function()
        if os.time() >= tonumber(expiry) then error('Hierarchy request expired before update') end
        if complex then temporaryNames() end
        for _, node in ipairs(plan) do
            if node.id == '0' or reparent[node.id] then
                move(node.keyword, node.parent > 0 and plan[node.parent].keyword or nil)
            end
        end
        for _, node in ipairs(live) do
            if node.scoped and not used[node.id] then move(node.keyword, archive) end
        end
        write(catalog, 'BirdDeck: finalize keyword names', function()
            for _, node in ipairs(plan) do
                if affected[node.id] or node.id == '0' then rename(node.keyword, node.name) end
            end
            for _, node in ipairs(live) do
                if node.scoped and not used[node.id] then rename(node.keyword, node.name .. ' [' .. node.id .. ']') end
            end
        end)
        -- Verify committed SDK state, not just the return values of setters.
        for _, node in ipairs(plan) do
            local parent = node.keyword:getParent()
            local expectedParent = node.parent > 0 and plan[node.parent].keyword.localIdentifier or 0
            if (parent and parent.localIdentifier or 0) ~= expectedParent or node.keyword:getName() ~= node.name then
                error('Hierarchy verification failed for ' .. node.name)
            end
        end
        for _, node in ipairs(live) do
            if #node.keyword:getPhotos() ~= node.photos then error('Photo count changed for ' .. node.id) end
        end
    end)
    if not ok then
        local recovered, recoveryError = Tasks.pcall(function()
            temporaryNames()
            local restored = {}
            local function restore(node)
                if restored[node.id] then return end
                if node.parent then
                    local parent = byId[tostring(node.parent.localIdentifier)]
                    if affected[parent.id] then restore(parent) end
                end
                move(node.keyword, node.parent)
                restored[node.id] = true
            end
            for _, node in ipairs(live) do if affected[node.id] then restore(node) end end
            for _, keyword in ipairs(created) do move(keyword, archive) end
            write(catalog, 'BirdDeck: restore original keyword names', function()
                for _, node in ipairs(live) do
                    if affected[node.id] and node.id ~= plan[1].id then rename(node.keyword, node.name) end
                end
            end)
        end)
        error(tostring(failure) .. (recovered and '; original hierarchy restored' or '; recovery failed: ' .. tostring(recoveryError)))
    end
    local assigned = { 'OK\tAPPLIED\n' }
    for _, node in ipairs(plan) do assigned[#assigned + 1] = node.index .. '\t' .. node.keyword.localIdentifier .. '\n' end
    return table.concat(assigned)
end
