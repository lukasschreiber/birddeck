const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const {requestTag} = require('./de.birdtagging.names.sdPlugin/tagging.cjs');

test('native queue preserves catalog and ID and returns Lightroom acknowledgment', async () => {
  const queue = await fs.mkdtemp(path.join(os.tmpdir(), 'birddeck-test-'));
  let poll;
  try {
    const processing = new Promise((resolve, reject) => {
      poll = setInterval(async () => {
        try {
          const files = await fs.readdir(queue);
          const filename = files.find(f => f.endsWith('.request'));
          if (!filename) return;
          clearInterval(poll);
          const file = path.join(queue, filename);
          const [expiry, catalog, id] = (await fs.readFile(file, 'utf8')).split('\n');
          assert.ok(Number(expiry) > Date.now() / 1000);
          assert.equal(decodeURIComponent(catalog), 'E:\\Vögel.lrcat');
          assert.equal(id, '1970148');
          await fs.unlink(file);
          await fs.writeFile(file.replace('.request', '.response'), 'OK\t2');
          resolve();
        } catch (error) { clearInterval(poll); reject(error); }
      }, 10);
    });
    const result = await requestTag({catalog: 'E:\\Vögel.lrcat', keywordId: '1970148'}, {queue, timeout: 2000});
    await processing;
    assert.deepEqual(result, {ok: true, photos: 2});
    assert.deepEqual(await fs.readdir(queue), []);
  } finally { clearInterval(poll); await fs.rm(queue, {recursive: true, force: true}); }
});

test('timeout removes pending request and invalid IDs never get queued', async () => {
  const queue = await fs.mkdtemp(path.join(os.tmpdir(), 'birddeck-test-'));
  try {
    await assert.rejects(requestTag({catalog: 'E:\\Birds.lrcat', keywordId: '1970148'}, {queue, timeout: 100}), /did not respond/);
    assert.deepEqual(await fs.readdir(queue), []);
    await assert.rejects(requestTag({catalog: 'E:\\Birds.lrcat', keywordId: 'Star'}, {queue}), /numeric keyword ID/);
    assert.deepEqual(await fs.readdir(queue), []);
  } finally { await fs.rm(queue, {recursive: true, force: true}); }
});

test('UUID tagging omits catalog-specific IDs and rejects malformed UUIDs', async () => {
  const queue = await fs.mkdtemp(path.join(os.tmpdir(), 'birddeck-test-'));
  const uuid = 'ABCDEF12-3456-4789-ABCD-123456789ABC';
  try {
    const pending = requestTag({keywordUuid: uuid}, {queue, timeout: 2000});
    let request;
    while (!request) {
      request = (await fs.readdir(queue)).find(f => f.endsWith('.request'));
      if (!request) await new Promise(resolve => setTimeout(resolve, 10));
    }
    const body = await fs.readFile(path.join(queue, request), 'utf8');
    assert.match(body, new RegExp(`^UUIDTAG\\n\\d+\\n${uuid.toLowerCase()}\\n$`));
    await fs.writeFile(path.join(queue, request.replace('.request', '.response')), 'OK\t1');
    assert.deepEqual(await pending, {ok: true, photos: 1});
    await assert.rejects(requestTag({keywordUuid: 'Star'}, {queue}));
  } finally { await fs.rm(queue, {recursive: true, force: true}); }
});
