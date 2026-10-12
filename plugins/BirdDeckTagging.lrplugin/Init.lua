local Tasks = import 'LrTasks'
local Files = import 'LrFileUtils'
local Paths = import 'LrPathUtils'
local Application = import 'LrApplication'
local Dialogs = import 'LrDialogs'
local queue = Paths.child(Paths.getStandardFilePath('home'), 'AppData/Local/BirdDeckTagging')
Files.createAllDirectories(queue)
if _G.BirdDeckState then _G.BirdDeckState.running = false end
local state = { running = true }
_G.BirdDeckState = state
local function status(message)
    local f = io.open(Paths.child(queue, 'lightroom-status.txt'), 'wb')
    if f then f:write(message); f:close() end
end
status('Starting BirdDeck Tagging')

local function decode(s)
    return (s:gsub('%%(%x%x)', function(h) return string.char(tonumber(h, 16)) end))
end
local function normalized(s) return s:gsub('/', '\\'):lower() end
local function apply(contents)
    -- Load per request so updating the hierarchy code cannot leave an older
    -- full-rebuild implementation cached for the lifetime of the listener.
    if contents:match('^HIERARCHY\n') then
        return dofile(Paths.child(_PLUGIN.path, 'Hierarchy.lua'))(contents)
    end
    local expiry, catalogPath, id = contents:match('^(%d+)\n([^\n]+)\n(%d+)\n')
    if contents:match('^UUIDTAG\n') then
        local identity
        expiry, identity = contents:match('^UUIDTAG\n(%d+)\n([%x%-]+)\n$')
        if not identity then error('Invalid keyword UUID request') end
        catalogPath = Application.activeCatalog():getPath()
        id = dofile(Paths.child(_PLUGIN.path, 'CatalogBindings.lua')).resolve(Application.activeCatalog(), identity)
        if not id then error('Keyword UUID is not bound in the active catalog; run lightroom-sync --apply') end
        catalogPath = catalogPath:gsub('%%', '%%25') -- normal tagging validation decodes below
    end
    if not expiry or os.time() >= tonumber(expiry) then error('Request expired or invalid') end
    local catalog = Application.activeCatalog()
    if normalized(catalog:getPath()) ~= normalized(decode(catalogPath)) then
        error('Wrong Lightroom catalog is open')
    end
    if not catalog:getTargetPhoto() then error('Select photos in Lightroom first') end
    local photos = catalog:getTargetPhotos()
    local keywords = catalog:getKeywordsByLocalId({tonumber(id)})
    local keyword
    for _, candidate in pairs(keywords) do
        if candidate.localIdentifier == tonumber(id) then keyword = candidate end
    end
    if not keyword then error('Keyword ID not found; run lightroom-sync again') end
    if contents:match('^UUIDTAG\n') then
        local root = keyword
        while root:getParent() do root = root:getParent() end
        if root:getName() ~= 'Vogel' then error('Bound keyword is outside Vogel; synchronize the hierarchy again') end
    end
    local status = catalog:withWriteAccessDo('BirdDeck: ' .. keyword:getName(), function()
        if os.time() >= tonumber(expiry) then error('Request expired before write access') end
        for _, photo in ipairs(photos) do photo:addKeyword(keyword) end
    end, { timeout = 5 })
    if status ~= 'executed' then error('Lightroom is busy; tagging was not applied') end
    return #photos
end

Tasks.startAsyncTask(function()
    while state.running do
        local healthy, failure = Tasks.pcall(function()
        status('Running; catalog: ' .. Application.activeCatalog():getPath())
        for path in Files.directoryEntries(queue) do
            if path:match('%.request$') then
                local ok, result = Tasks.pcall(function()
                    local contents = Files.readFile(path)
                    -- Claim once before applying, including failed requests.
                    if not Files.delete(path) then error('Could not claim tagging request') end
                    return apply(contents)
                end)
                local response = path:gsub('%.request$', '.response')
                if not ok then
                    local log = io.open(Paths.child(queue, 'lightroom-errors.log'), 'ab')
                    if log then log:write(tostring(result) .. '\n'); log:close() end
                end
                local staging = response .. '.tmp'
                local f = io.open(staging, 'wb')
                if f then
                    f:write(ok and (type(result) == 'string' and result or 'OK\t' .. tostring(result)) or ('ERROR\t' .. tostring(result)))
                    f:close()
                    Files.move(staging, response)
                end
            end
        end
        end)
        if not healthy then
            status('Listener error: ' .. tostring(failure))
            state.running = false
            Dialogs.message('BirdDeck Tagging stopped', tostring(failure), 'critical')
        end
        Tasks.sleep(0.2)
    end
end)
