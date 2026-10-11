/* Stream Deck owns this Node process: rendering and tagging share its lifecycle. */
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {performance} = require('node:perf_hooks');
const WebSocket = require('ws');
const {createCanvas} = require('@napi-rs/canvas');
const {requestTag} = require('./tagging.cjs');

function start(args = process.argv.slice(2)) {
  const options = {};
  for (let i = 0; i < args.length; i += 2) options[args[i]] = args[i + 1];
  if (!options['-port'] || !options['-pluginUUID'] || !options['-registerEvent']) {
    throw new Error('Stream Deck connection arguments are required');
  }
  const workers = new Set();
  const sandbox = {window: {}, console, performance, WebSocket,
    document: {createElement: () => createCanvas(144, 144)},
    Worker: class {
      constructor() {
        this.timer = setInterval(() => this.onmessage?.(), 50);
        workers.add(this);
      }
      terminate() { clearInterval(this.timer); workers.delete(this); }
    },
    BirdTagging: {requestTag}
  };
  sandbox.globalThis = sandbox;
  vm.createContext(sandbox);
  for (const filename of ['scroll.js', 'plugin.js']) {
    vm.runInContext(fs.readFileSync(path.join(__dirname, filename), 'utf8'), sandbox, {filename});
  }
  sandbox.window.connectElgatoStreamDeckSocket(options['-port'], options['-pluginUUID'], options['-registerEvent']);
}
if (require.main === module) start();
module.exports = {start};
