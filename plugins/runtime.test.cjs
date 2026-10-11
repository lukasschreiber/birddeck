const test = require('node:test');
const assert = require('node:assert/strict');
const {spawn} = require('node:child_process');
const path = require('node:path');
const {once} = require('node:events');
const {WebSocketServer} = require('./de.birdtagging.names.sdPlugin/node_modules/ws');

test('real Node runtime registers, renders PNG, and exits when Stream Deck disconnects', {timeout: 10000}, async () => {
  const server = new WebSocketServer({port: 0, host: '127.0.0.1'});
  await once(server, 'listening');
  const child = spawn(process.execPath, [path.join(__dirname, 'de.birdtagging.names.sdPlugin/runtime.cjs'),
    '-port', String(server.address().port), '-pluginUUID', 'test-plugin', '-registerEvent', 'registerPlugin']);
  let errors = '';
  child.stderr.on('data', data => {errors += data;});
  const exit = once(child, 'exit');
  try {
    const [socket] = await once(server, 'connection');
    const [registration] = await once(socket, 'message');
    assert.deepEqual(JSON.parse(registration), {event: 'registerPlugin', uuid: 'test-plugin'});
    const image = new Promise(resolve => socket.on('message', raw => {
      const message = JSON.parse(raw);
      if (message.event === 'setImage') resolve(message.payload.image);
    }));
    socket.send(JSON.stringify({event: 'willAppear', action: 'de.birdtagging.names.scroll',
      context: 'star', device: 'deck', payload: {settings: {commonName: 'Star', scientificName: 'Sturnus vulgaris'}}}));
    const png = await image;
    assert.match(png, /^data:image\/png;base64,/);
    assert.equal(Buffer.from(png.split(',')[1], 'base64').subarray(1, 4).toString(), 'PNG');
    socket.close();
    const [code] = await exit;
    assert.equal(code, 0, errors);
  } finally {
    child.kill();
    for (const socket of server.clients) socket.terminate();
    await new Promise(resolve => server.close(resolve));
  }
});
