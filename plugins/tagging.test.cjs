const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

test('bound tagging sends ID and catalog, acknowledges success and exposes errors', async () => {
  const sent = [], calls = [];
  let fail = false;
  class Socket {
    constructor() { Socket.instance = this; }
    send(data) { sent.push(JSON.parse(data)); }
  }
  const sandbox = {window: {}, WebSocket: Socket, performance: {now: () => 0},
    console: {error() {}}, BirdTagging: {requestTag: async request => {
      calls.push(JSON.parse(JSON.stringify(request)));
      if (fail) throw new Error('Wrong catalog');
      return {ok: true, photos: 2};
    }}};
  vm.runInNewContext(fs.readFileSync(__dirname + '/de.birdtagging.names.sdPlugin/plugin.js', 'utf8'), sandbox);
  sandbox.window.connectElgatoStreamDeckSocket(1234, 'plugin', 'registerPlugin');
  Socket.instance.onopen();
  const event = {event: 'keyDown', action: 'de.birdtagging.names.tag', context: 'star',
    payload: {settings: {keywordId: '1970148', catalog: 'E:\\Birds.lrcat'}}};
  Socket.instance.onmessage({data: JSON.stringify(event)});
  await new Promise(resolve => setImmediate(resolve));
  assert.deepEqual(calls[0], {keywordId: '1970148', catalog: 'E:\\Birds.lrcat'});
  assert.ok(sent.some(e => e.event === 'showOk' && e.context === 'star'));
  fail = true;
  Socket.instance.onmessage({data: JSON.stringify(event)});
  await new Promise(resolve => setImmediate(resolve));
  assert.ok(sent.some(e => e.event === 'showAlert' && e.context === 'star'));
  assert.ok(sent.some(e => e.event === 'logMessage' && e.payload.message.includes('Wrong catalog')));
});
