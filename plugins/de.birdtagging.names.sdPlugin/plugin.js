/* Rendering host supplies canvas, WebSocket, timers, and native tagging. */
const keys = new Map();
let socket;
let timer;

function send(event, context, payload) {
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({event, context, payload}));
  }
}

function render(key, now) {
  const clock = key.clock;
  const elapsed = clock.elapsed + (clock.paused ? 0 : now - clock.started);
  const legacyWide = key.settings.half === 'left' || key.settings.half === 'right';
  const cells = Math.max(1, Math.min(3, Number(key.settings.cells) || (legacyWide ? 2 : 1)));
  const wide = cells > 1;
  const segment = Math.max(0, Math.min(cells - 1, Number(key.settings.segment) || (key.settings.half === 'right' ? 1 : 0)));
  // Sample a wider virtual canvas, skipping the physical gaps between keys.
  const gap = 28;
  const viewport = cells * 72 + (cells - 1) * gap;
  const origin = segment * (72 + gap);
  const ctx = key.canvas.getContext('2d');
  ctx.setTransform(2, 0, 0, 2, 0, 0);
  ctx.fillStyle = '#000000';
  ctx.fillRect(0, 0, 72, 72);
  ctx.textBaseline = 'middle';
  const scientific = String(key.settings.scientificName || '').trim();
  const english = String(key.settings.englishName || '').trim();
  const common = BirdScroll.displayName(key.settings.commonName || 'Bird name');
  const lines = [{text: common, alternate: english,
    font: wide ? '20px Arial' : '16px Arial', y: scientific ? 25 : 36, color: '#ffffff'}];
  if (scientific) lines.push({text: scientific, font: wide ? 'italic 16px Arial' : 'italic 12px Arial', y: 48, color: '#d0d4d8'});
  for (const line of lines) {
    ctx.font = line.font;
    line.width = ctx.measureText(line.text).width;
    line.period = Math.max(viewport, line.width + 24);
    if (line.alternate) {
      line.alternateStart = line.period;
      line.period += Math.max(viewport, ctx.measureText(line.alternate).width + 24);
    }
  }
  // Repeat each line independently for continuous movement, even for short text.
  for (const line of lines) {
    ctx.font = line.font;
    const x = 4 - BirdScroll.offset(elapsed, line.period,
      line.alternate ? [line.alternateStart] : []);
    ctx.save();
    ctx.beginPath();
    ctx.rect(4 - origin, 0, viewport - 8, 72);
    ctx.clip();
    ctx.fillStyle = line.color;
    for (let copy = x; copy < viewport; copy += line.period) {
      ctx.fillText(line.text, copy - origin, line.y);
      if (line.alternate) ctx.fillText(line.alternate, copy + line.alternateStart - origin, line.y);
    }
    ctx.restore();
  }
  const image = key.canvas.toDataURL('image/png');
  if (image !== key.lastImage) {
    send('setImage', key.context, {image, target: 0});
    key.lastImage = image;
  }
  key.moving = true;
}

function stop() {
  if (timer) timer.terminate();
  timer = undefined;
  keys.clear();
}

window.connectElgatoStreamDeckSocket = function (port, uuid, registerEvent) {
  socket = new WebSocket(`ws://127.0.0.1:${port}`);
  socket.onopen = () => socket.send(JSON.stringify({event: registerEvent, uuid}));
  socket.onclose = stop;
  socket.onerror = stop;
  socket.onmessage = ({data}) => {
    const event = JSON.parse(data);
    if (event.action === 'de.birdtagging.names.tag') {
      if (event.event === 'keyDown') {
        const settings = event.payload.settings || {};
        BirdTagging.requestTag({catalog: settings.catalog, keywordId: settings.keywordId, keywordUuid: settings.keywordUuid}).then(result => {
          if (!result.ok) throw new Error(result.error || 'Tagging failed');
          send('showOk', event.context, {});
        }).catch(error => {
          console.error('BirdDeck tagging:', error);
          send('showAlert', event.context, {});
          send('logMessage', event.context, {message: String(error)});
        });
      }
      return;
    }
    const now = performance.now();
    if (event.event === 'willAppear') {
      const canvas = document.createElement('canvas');
      canvas.width = canvas.height = 144;
      const key = {context: event.context, device: event.device, canvas,
        settings: event.payload.settings || {}, clock: {started: now, elapsed: 0, paused: false}};
      const peer = [...keys.values()].find(other => key.settings.pair &&
        other.device === key.device && other.settings.pair === key.settings.pair);
      if (peer) key.clock = peer.clock;
      keys.set(event.context, key);
      send('setTitle', event.context, {title: '', target: 0});
      render(key, now);
      if (!timer) {
        timer = new Worker('ticker.js');
        timer.onmessage = () => {
          const time = performance.now();
          for (const key of keys.values()) if (key.moving && !key.clock.paused) render(key, time);
        };
      }
    } else if (event.event === 'willDisappear' || event.event === 'deviceDidDisconnect') {
      if (event.event === 'willDisappear') keys.delete(event.context);
      else for (const [context, key] of keys) if (key.device === event.device) keys.delete(context);
      if (!keys.size && timer) { timer.terminate(); timer = undefined; }
    } else if (event.event === 'didReceiveSettings') {
      const key = keys.get(event.context);
      if (key) {
        key.settings = event.payload.settings || {};
        key.clock.started = now;
        key.clock.elapsed = 0;
        for (const other of keys.values()) if (other.clock === key.clock) render(other, now);
      }
    } else if (event.event === 'keyDown') {
      const key = keys.get(event.context);
      if (key) {
        if (!key.clock.paused) key.clock.elapsed += now - key.clock.started;
        key.clock.paused = !key.clock.paused;
        key.clock.started = now;
        for (const other of keys.values()) if (other.clock === key.clock) render(other, now);
      }
    }
  };
};
