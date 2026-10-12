const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
// Install the test-only Lua VM: npm install --prefix .cache/lua-test fengari@0.1.5
const { lua, lauxlib, lualib, to_luastring, to_jsstring } = require('../.cache/lua-test/node_modules/fengari');

test('Lightroom hierarchy SDK contract: swaps, reparenting, creation, archive, stale plans and recovery', () => {
    const state = lauxlib.luaL_newstate();
    lualib.luaL_openlibs(state);
    lua.lua_pushstring(state, to_luastring(fs.readFileSync(path.join(__dirname, 'BirdDeckTagging.lrplugin/Hierarchy.lua'), 'utf8')));
    lua.lua_setglobal(state, to_luastring('hierarchySource'));
    lua.lua_pushstring(state, to_luastring(fs.readFileSync(path.join(__dirname, 'BirdDeckTagging.lrplugin/Init.lua'), 'utf8')));
    lua.lua_setglobal(state, to_luastring('initSource'));
    lua.lua_pushstring(state, to_luastring(fs.readFileSync(path.join(__dirname, 'BirdDeckTagging.lrplugin/CatalogBindings.lua'), 'utf8')));
    lua.lua_setglobal(state, to_luastring('bindingsSource'));
    const result = lauxlib.luaL_dostring(state, to_luastring(fs.readFileSync(path.join(__dirname, '../tests/hierarchy.lua'), 'utf8')));
    assert.equal(result, lua.LUA_OK, result === lua.LUA_OK ? '' : to_jsstring(lua.lua_tostring(state, -1)));
    const tagging = lauxlib.luaL_dostring(state, to_luastring(fs.readFileSync(path.join(__dirname, '../tests/uuid_tagging.lua'), 'utf8')));
    assert.equal(tagging, lua.LUA_OK, tagging === lua.LUA_OK ? '' : to_jsstring(lua.lua_tostring(state, -1)));
    lua.lua_close(state);
});
