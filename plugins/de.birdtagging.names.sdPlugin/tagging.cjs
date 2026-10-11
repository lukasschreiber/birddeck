const fs = require('node:fs/promises');
const path = require('node:path');
const os = require('node:os');
const {randomUUID} = require('node:crypto');

async function requestTag({catalog, keywordId, keywordUuid}, {queue = path.join(os.homedir(), 'AppData', 'Local', 'BirdDeckTagging'), timeout = 10000} = {}) {
  if (keywordUuid !== undefined ? !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(keywordUuid) :
      typeof catalog !== 'string' || !catalog || !/^\d+$/.test(String(keywordId))) {
    throw new Error('A catalog path and numeric keyword ID are required');
  }
  await fs.mkdir(queue, {recursive: true});
  const id = randomUUID().replaceAll('-', '');
  const request = path.join(queue, id + '.request');
  const response = path.join(queue, id + '.response');
  const staging = path.join(queue, id + '.tmp');
  const deadline = Date.now() + timeout;
  try {
    const payload = keywordUuid !== undefined ? `UUIDTAG\n${Math.floor(deadline / 1000)}\n${keywordUuid.toLowerCase()}\n` :
      `${Math.floor(deadline / 1000)}\n${encodeURIComponent(catalog)}\n${keywordId}\n`;
    await fs.writeFile(staging, payload, 'utf8');
    await fs.rename(staging, request);
    while (Date.now() < deadline) {
      let result;
      try { result = await fs.readFile(response, 'utf8'); }
      catch (error) { if (error.code !== 'ENOENT') throw error; }
      if (result !== undefined) {
        if (!/^OK\t\d+$/.test(result)) throw new Error(result.replace(/^ERROR\t/, ''));
        return {ok: true, photos: Number(result.split('\t')[1])};
      }
      await new Promise(resolve => setTimeout(resolve, 50));
    }
    throw new Error('Lightroom did not respond. Enable BirdDeck Tagging and select photos.');
  } finally {
    await Promise.all([request, response, staging].map(file => fs.rm(file, {force: true})));
  }
}
module.exports = {requestTag};
