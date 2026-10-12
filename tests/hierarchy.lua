-- Mock enforces catalog write access, committed parents, uniqueness and cycles.
local catalog = { nodes = {}, nextId = 100, writing = false, metadata = {} }
local failureName
local operations = { renames = {}, moves = {} }
local Keyword = {}
Keyword.__index = Keyword
function Keyword:getName() return self.name end
function Keyword:getParent() return self.parent end
function Keyword:getPhotos() return self.photos end
function Keyword:getChildren()
    local children = {}
    for _, node in ipairs(catalog.nodes) do if node.parent == self then children[#children+1] = node end end
    return children
end
local function unique(keyword, name, parent)
    for _, other in ipairs(catalog.nodes) do
        if other ~= keyword and other.name:lower() == name:lower() and other.parent == parent then return false end
    end
    local ancestor = parent
    while ancestor do
        if ancestor == keyword or ancestor.name:lower() == name:lower() then return false end
        ancestor = ancestor.parent
    end
    return true
end
function Keyword:setAttributes(attrs)
    assert(catalog.writing)
    if attrs.keywordName == failureName then failureName = nil; error('Injected SDK failure') end
    assert(attrs.synonyms == nil and attrs.includeOnExport == nil, 'Existing attributes must be preserved')
    if not unique(self, attrs.keywordName, self.parent) then return false end
    self.pendingName = attrs.keywordName
    operations.renames[#operations.renames+1] = {id=self.localIdentifier, name=attrs.keywordName}
    return true
end
function Keyword:setParent(parent)
    assert(not catalog.writing, 'setParent owns its write transaction; cannot nest it in a write gate')
    assert(not parent or parent.committed, 'Parent must be committed')
    if not unique(self, self.name, parent) then return false end
    self.parent = parent
    operations.moves[#operations.moves+1] = {id=self.localIdentifier, parent=parent and parent.localIdentifier or 0}
end
local function add(id, name, parent, count)
    local photos = {}
    for i=1,count or 0 do photos[i] = 'photo-' .. id .. '-' .. i end
    local keyword = setmetatable({localIdentifier=id, name=name, parent=parent, photos=photos,
        committed=true, synonyms={'original synonym'}, includeOnExport=false}, Keyword)
    catalog.nodes[#catalog.nodes+1] = keyword
    return keyword
end
function catalog:getKeywords()
    local roots = {}
    for _, node in ipairs(self.nodes) do if not node.parent then roots[#roots+1] = node end end
    return roots
end
function catalog:getPath() return 'E:\\Catalog.lrcat' end
function catalog:getPropertyForPlugin(plugin, field) return self.metadata[field] end
function catalog:setPropertyForPlugin(plugin, field, value)
    assert(self.writing)
    self.metadata[field] = value
end
function catalog:createKeyword(name, synonyms, export, parent, returnExisting)
    assert(self.writing)
    for _, node in ipairs(self.nodes) do
        if node.name == name and node.parent == parent then return returnExisting and node or false end
    end
    self.nextId = self.nextId + 1
    local keyword = add(self.nextId, name, parent, 0)
    keyword.committed = false
    return keyword
end
function catalog:withWriteAccessDo(title, fn, options)
    assert(not self.writing)
    self.writing = true
    local ok, result = pcall(fn)
    self.writing = false
    for _, node in ipairs(self.nodes) do
        node.committed = true
        if node.pendingName then node.name = node.pendingName; node.pendingName = nil end
    end
    if not ok then error(result) end
    return 'executed'
end
function import(name)
    if name == 'LrApplication' then return {activeCatalog=function() return catalog end} end
    if name == 'LrTasks' then return {pcall=pcall} end
    if name == 'LrPathUtils' then return {child=function(a,b) return a..'/'..b end} end
    error(name)
end
_PLUGIN = {path='plugin'}
dofile = function(path)
    assert(path:match('CatalogBindings%.lua$'))
    return assert(load(bindingsSource))()
end
local handler = assert(load(hierarchySource))()
local function reset()
    catalog.nodes, catalog.nextId = {}, 100
    failureName = nil
    catalog.metadata = {}
    operations = { renames = {}, moves = {} }
end
local function request(mode, body)
    return handler('HIERARCHY\n' .. (os.time()+120) .. '\n' .. mode .. '\nE%3A%5CCatalog.lrcat\n' .. (body or ''))
end
local function apply(rows)
    local snap = request('SNAPSHOT')
    local fingerprint = snap:match('^OK\tSNAPSHOT\tCATALOG%-3\n[^\n]+\n(.*)$')
    return request('APPLY', 'EXPECTED\n' .. fingerprint .. 'NODES\n' .. rows)
end

reset()
local root = add(1, 'Vogel')
local a = add(2, 'A', root, 17)
local b = add(3, 'B', a, 4)
local old = add(4, 'Old', root, 7)
local outside = add(5, 'People', nil, 3)
local photos = a.photos
local result = apply('1\t0\t1\tVogel\n2\t1\t3\tA\n3\t2\t2\tB\n4\t3\t0\tStra%C3%9Fentaube\n')
assert(result:match('OK\tAPPLIED'))
assert(b.parent == root and b.name == 'A' and a.parent == b and a.name == 'B')
assert(a.photos == photos and #a.photos == 17 and #b.photos == 4)
assert(a.synonyms[1] == 'original synonym' and a.includeOnExport == false)
assert(old.parent.name == '_BirdDeck Obsolete' and old.name == 'Old [4]' and #old.photos == 7)
assert(outside.name == 'People' and outside.parent == nil and #outside.photos == 3)
assert(#root:getChildren() == 1 and #a:getChildren() == 1)
assert(a:getChildren()[1].name == 'Straßentaube')
local writes = #catalog.nodes
local ok, err = pcall(function() request('APPLY', 'EXPECTED\nstale\nNODES\n1\t0\t1\tVogel\n') end)
assert(not ok and tostring(err):match('changed') and #catalog.nodes == writes)

reset()
root = add(1, 'Vogel')
a = add(2, 'A', root, 17)
b = add(3, 'B', a, 4)
failureName = 'Renamed'
ok, err = pcall(function() apply('1\t0\t1\tVogel\n2\t1\t2\tRenamed\n3\t2\t3\tB\n4\t3\t0\tNew\n') end)
assert(not ok and tostring(err):match('original hierarchy restored'), tostring(err))
assert(root.name == 'Vogel' and a.name == 'A' and a.parent == root and b.name == 'B' and b.parent == a)
assert(#a.photos == 17 and #b.photos == 4)

reset()
result = apply('1\t0\t0\tVogel\n2\t1\t0\tStar%20%28Gruppe%29\n3\t2\t0\tStar\n')
assert(result:match('OK\tAPPLIED'))
local vogel
for _, node in ipairs(catalog.nodes) do if node.name == 'Vogel' then vogel = node end end
assert(vogel and vogel:getChildren()[1]:getChildren()[1].name == 'Star')
ok = pcall(function() apply('1\t0\t' .. vogel.localIdentifier .. '\tVogel\n2\t1\t0\tStar\n3\t2\t0\tStar\n') end)
assert(not ok, 'Ancestor name conflict must be rejected')

-- Recovery must recognize saved identities even when every keyword is flat.
reset()
root = add(1, 'Vogel')
a = add(2, 'Adler', nil, 17)
b = add(3, 'Steinadler', nil, 4)
outside = add(5, 'People', nil, 3)
local staging = add(6, '_BirdDeck_new_123_456_9', nil, 0)
result = apply('1\t0\t1\tVogel\n2\t1\t2\tAdler\n3\t2\t3\tSteinadler\n')
assert(result:match('OK\tAPPLIED'))
assert(a.parent == root and b.parent == a and #a.photos == 17 and #b.photos == 4)
assert(staging.parent.name == '_BirdDeck Obsolete')
assert(outside.parent == nil and outside.name == 'People')

-- A simple rename must make exactly one attribute write and no parent writes,
-- regardless of how many other managed keywords are present.
reset()
root = add(1, 'Vogel')
a = add(2, 'Adler', root, 17)
b = add(3, 'Steinadler', a, 4)
local rows = '1\t0\t1\tVogel\n2\t1\t2\tAdler\n3\t2\t3\tRenamed\n'
for i=4,103 do
    add(i, 'Unchanged'..i, root, 1)
    rows = rows .. i .. '\t1\t' .. i .. '\tUnchanged' .. i .. '\n'
end
result = apply(rows)
assert(#operations.renames == 1 and operations.renames[1].id == 3)
assert(operations.renames[1].name == 'Renamed' and #operations.moves == 0)
assert(#a.photos == 17 and #b.photos == 4)

-- A group move must carry its descendants without rewriting them.
reset()
root = add(1, 'Vogel')
a = add(2, 'Adler', root, 17)
b = add(3, 'Steinadler', a, 4)
local destination = add(4, 'Destination', root)
result = apply('1\t0\t1\tVogel\n2\t1\t4\tDestination\n3\t2\t2\tAdler\n4\t3\t3\tSteinadler\n')
assert(#operations.renames == 0 and #operations.moves == 1 and operations.moves[1].id == 2)
assert(a.parent == destination and b.parent == a)

-- Conflicting siblings are staged, while unrelated managed keywords stay untouched.
reset()
root = add(1, 'Vogel')
a = add(2, 'A', root, 17)
b = add(3, 'B', root, 4)
local unchanged = add(4, 'Unchanged', root, 7)
result = apply('1\t0\t1\tVogel\n2\t1\t2\tB\n3\t1\t3\tA\n4\t1\t4\tUnchanged\n')
assert(#operations.renames == 4 and #operations.moves == 0)
for _, op in ipairs(operations.renames) do assert(op.id == 2 or op.id == 3) end
assert(unchanged.name == 'Unchanged' and unchanged.parent == root and #unchanged.photos == 7)

reset()
root = add(1, 'Vogel')
a = add(2, 'A', root, 17)
result = apply('1\t0\t1\tVogel\n2\t1\t2\tB\n3\t1\t0\tA\n')
assert(result:match('OK\tAPPLIED') and a.name == 'B' and #a.photos == 17)
assert(#root:getChildren() == 2)

-- Reproduce a one-bird addition to a large, already synchronized catalog.
reset()
root = add(1, 'Vogel')
local raptors = add(2, 'Greifvogel', root)
a = add(3, 'Adler', raptors)
rows = '1\t0\t1\tVogel\n2\t1\t2\tGreifvogel\n3\t2\t3\tAdler\n'
for i=4,448 do
    add(i, 'ExistingBird'..i, a, 1)
    rows = rows .. i .. '\t3\t' .. i .. '\tExistingBird' .. i .. '\n'
end
add(9000, '_BirdDeck Obsolete')
catalog.nextId = 10000
result = apply(rows .. '449\t3\t0\tSchreiseeadler\n')
assert(result:match('OK\tAPPLIED'))
assert(#operations.renames == 1 and operations.renames[1].id == 10001)
assert(#operations.moves == 1 and operations.moves[1].id == 10001)
assert(operations.renames[1].name == 'Schreiseeadler')

-- Catalog metadata travels with the catalog and writes never rename keywords.
reset()
root = add(1, 'Vogel')
a = add(2, 'Star', root, 17)
local identity = '00000000-0000-4000-8000-000000000001'
local replacement = '00000000-0000-4000-8000-000000000002'
local fingerprint = request('SNAPSHOT'):match('^OK\tSNAPSHOT\tCATALOG%-3\n[^\n]+\n(.*)$')
local function storeBody(id, expected)
    return id..'\nEXPECTED\n'..(expected or fingerprint)..'STATE\n%7B%7D\n'..identity..'\t2\n'
end
assert(request('STORE', storeBody(identity)) == 'OK\tSTORED\n')
assert(catalog.metadata.catalogUuid == identity)
assert(catalog.metadata.bindingState == '{}')
assert(request('STATE'):find(identity, 1, true))
assert(not pcall(function() request('STORE', storeBody(replacement)) end))
assert(not pcall(function() request('STORE', storeBody(identity, 'stale\n')) end))
assert(catalog.metadata.catalogUuid == identity)
assert(request('RESET', storeBody(replacement)) == 'OK\tSTORED\n')
assert(catalog.metadata.catalogUuid == replacement)
assert(#operations.renames == 0 and #operations.moves == 0 and #a.photos == 17)
