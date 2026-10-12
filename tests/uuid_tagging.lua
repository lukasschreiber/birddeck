-- Exercise the actual listener dispatch without touching a real catalog/photo.
local uuid = '00000000-0000-4000-8000-000000000001'
local active = 'E:\\Old.lrcat'
local photosAdded, response = {}, nil
local queueRequest
local metadata = {keywordBindings=uuid..'\t7\n'}
local task
local roots = {}
local function keyword(id)
    return {localIdentifier=id, getName=function() return 'Star' end,
        getParent=function() return roots[id] end}
end
local catalog = {
    getPropertyForPlugin=function(_, plugin, field) return metadata[field] end,
    getPath=function() return active end,
    getTargetPhoto=function() return {} end,
    getTargetPhotos=function() return {{addKeyword=function(_, k) photosAdded[#photosAdded+1]=k.localIdentifier end}} end,
    getKeywordsByLocalId=function(_, ids) return {keyword(ids[1])} end,
    withWriteAccessDo=function(_, title, callback) callback(); return 'executed' end,
}
local root = {getName=function() return 'Vogel' end, getParent=function() return nil end}
roots[7], roots[99] = root, root
local Files = {
    createAllDirectories=function() end,
    readFile=function(path) assert(not path:match('keyword%-bindings')); return queueRequest end,
    delete=function() return true end,
    move=function() _G.BirdDeckState.running = false end,
    directoryEntries=function()
        local returned = false
        return function()
            if not returned then returned = true; return 'queue/test.request' end
        end
    end,
}
function import(name)
    if name == 'LrTasks' then return {pcall=pcall, sleep=function() end, startAsyncTask=function(callback) task=callback end} end
    if name == 'LrFileUtils' then return Files end
    if name == 'LrPathUtils' then return {child=function(a,b) return a..'/'..b end, getStandardFilePath=function() return 'home' end} end
    if name == 'LrApplication' then return {activeCatalog=function() return catalog end} end
    if name == 'LrDialogs' then return {message=function(_, msg) error(msg) end} end
    error(name)
end
_PLUGIN = {path='plugin'}
local previousDofile, previousOpen = dofile, io.open
dofile = function(path)
    assert(path:match('CatalogBindings%.lua$'))
    return assert(load(bindingsSource))()
end
io.open = function(path)
    return {write=function(_, text) if path:match('%.response%.tmp$') then response=text end end, close=function() end}
end
local function run(identity)
    response = nil
    queueRequest = 'UUIDTAG\n'..(os.time()+60)..'\n'..identity..'\n'
    assert(load(initSource))()
    task()
    return response
end
assert(run(uuid) == 'OK\t1')
assert(photosAdded[1] == 7)
-- Moving the same catalog requires no local bindings file or synchronization.
active = 'F:\\Old.lrcat'
assert(run(uuid) == 'OK\t1')
assert(photosAdded[2] == 7)
active = 'F:\\Fresh.lrcat'
metadata = {keywordBindings=uuid..'\t99\n'}
assert(run(uuid) == 'OK\t1')
assert(photosAdded[3] == 99)
active = 'G:\\Unbound.lrcat'
metadata = {}
assert(run(uuid):match('not bound in the active catalog'))
assert(#photosAdded == 3)
active = 'F:\\Fresh.lrcat'
metadata = {keywordBindings=uuid..'\t99\n'}
assert(run('00000000-0000-4000-8000-000000000002'):match('not bound'))
assert(#photosAdded == 3)
roots[99] = {getName=function() return '_BirdDeck Obsolete' end,getParent=function() return nil end}
assert(run(uuid):match('outside Vogel'))
assert(#photosAdded == 3)
dofile, io.open = previousDofile, previousOpen
