const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const vm = require('node:vm');
const {displayName, offset} = require('./de.birdtagging.names.sdPlugin/scroll.js');

test('display formatting preserves uppercase hyphens', () => {
  assert.equal(displayName('China-Fleck-schnabelente'), 'China-Fleckschnabelente');
  assert.equal(displayName('Orient-elster'), 'Orientelster');
});
test('each loop pauses at left alignment for two seconds', () => {
  assert.equal(offset(10000, 0), 0);
  assert.equal(offset(0, 72), 0);
  assert.equal(offset(1999, 72), 0);
  assert.equal(offset(2000, 72), 0);
  assert.equal(offset(2500, 72), 12);
  assert.equal(offset(3000, 72), 24);
  assert.equal(offset(5000, 72), 0);
  assert.equal(offset(6999, 72), 0);
  assert.equal(offset(7500, 72), 12);
  assert.equal(offset(5000, 144, [72]), 72);
  assert.equal(offset(6999, 144, [72]), 72);
  assert.equal(offset(7500, 144, [72]), 84);
});
test('contexts stay independent, settings update, and timers stop after disappearance', () => {
  let now = 0, tick, cleared = 0;
  const sent = [];
  class Socket {
    static OPEN = 1;
    readyState = 1;
    constructor() { Socket.instance = this; }
    send(data) { sent.push(JSON.parse(data)); }
  }
  function canvas() {
    let lines = [];
    const ctx = {setTransform(){}, fillRect(){lines=[];}, save(){}, restore(){},
      beginPath(){}, rect(){}, clip(){}, measureText(text){return {width:text.length*8};},
      fillText(text,x,y){lines.push([text,x,y]);}};
    return {getContext(){return ctx;}, toDataURL(){return JSON.stringify(lines);}};
  }
  const sandbox = {window:{}, WebSocket:Socket, performance:{now:()=>now},
    document:{createElement:canvas}, BirdScroll:{displayName,offset},
    Worker:class {
      constructor(path){assert.equal(path,'ticker.js');}
      set onmessage(fn){tick=fn;}
      terminate(){cleared++;}
    }};
  vm.runInNewContext(fs.readFileSync(__dirname+'/de.birdtagging.names.sdPlugin/plugin.js','utf8'),sandbox);
  sandbox.window.connectElgatoStreamDeckSocket(1234,'plugin','registerPlugin');
  Socket.instance.onopen();
  assert.deepEqual(sent[0], {event:'registerPlugin',uuid:'plugin'});
  function event(event,context,settings={}) {
    Socket.instance.onmessage({data:JSON.stringify({event,context,device:'deck',payload:{settings}})});
  }
  event('willAppear','a',{commonName:'Orient-elster',englishName:'Oriental Magpie',scientificName:'Pica serica'});
  assert.ok(sent.some(e=>e.event==='setImage' && e.context==='a' && e.payload.image.includes('Oriental Magpie')));
  event('willAppear','b',{commonName:'China-Fleckschnabelente'});
  event('keyDown','a');
  sent.length=0;
  now=2500;tick();
  assert.ok(sent.some(e=>e.context==='b'));
  assert.ok(!sent.some(e=>e.context==='a'));
  event('didReceiveSettings','a',{commonName:'Amsel'});
  assert.ok(sent.some(e=>e.context==='a' && e.payload.image.includes('Amsel')));
  event('willDisappear','a');
  assert.equal(cleared,0);
  event('willDisappear','b');
  assert.equal(cleared,1);
  const shared = {commonName:'A very long bird name spanning three cells', scientificName:'Anas zonorhyncha',pair:'test',cells:3};
  event('willAppear','left',{...shared,segment:0});
  now += 500;
  event('willAppear','middle',{...shared,segment:1});
  event('willAppear','right',{...shared,segment:2});
  now += 2500;
  sent.length=0;
  tick();
  const left = JSON.parse(sent.find(e=>e.event==='setImage' && e.context==='left').payload.image);
  const right = JSON.parse(sent.find(e=>e.event==='setImage' && e.context==='right').payload.image);
  const middle = JSON.parse(sent.find(e=>e.event==='setImage' && e.context==='middle').payload.image);
  assert.equal(left[0][1]-middle[0][1],100);
  assert.equal(left[0][1]-right[0][1],200);
  const leftScience = left.find(line=>line[2]===48);
  const rightScience = right.find(line=>line[2]===48);
  assert.equal(leftScience[1]-rightScience[1],200);
  assert.ok(left[0][1]<4,'the long common name scrolls');
  assert.ok(leftScience[1]<4,'the short scientific name also scrolls');
  event('keyDown','right');
  sent.length=0;
  now+=500;
  tick();
  assert.equal(sent.length,0,'pressing either half pauses both');
});
