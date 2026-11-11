// voice_test.js [outdir] : runs the avatar's voice worker in headless Chromium, as the page does, and saves what it makes.
//
// For each test sentence: the audio (24 kHz WAV) and a JSON with the sounds, their times, the words and the pitch track,
// plus how long the line took to make against how long it lasts. tests/voice_check.py then listens to the audio with a
// speech recogniser and a forced aligner and says whether the words and the reported times are right.
//   node avatar/voice_test.js            (from the repository root; needs avatar/voice/ filled by avatar/get_voice.py)
const { chromium } = require('playwright'), http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname), OUT = process.argv[2] || path.join(__dirname, '..', 'tests', 'output', 'voice'), DIR = process.env.VOICE_DIR || 'voice';      // VOICE_DIR=voice_full tries another model laid out the same way
const TYPES = { '.js': 'text/javascript', '.wasm': 'application/wasm', '.json': 'application/json', '.html': 'text/html', '.bin': 'application/octet-stream' };
const LINES = [
  ['af_heart', "Hi, I'm the avatar. Ask me anything you like."],
  ['af_heart', 'Good question. The lips you are watching are timed by the same model that makes my voice.'],
  ['am_michael', 'Sure, I can do that. Give me a moment to think about it.'],
  ['am_michael', 'The weather in Paris is usually mild in May, with a few rainy afternoons.'],
  ['am_puck', 'Peter Piper picked a peck of pickled peppers, and then he went home.'],
  ['am_fenrir', 'About forty-two percent of people say they would rather type than talk.'],
  ['af_bella', 'Why? Because a mouth that moves a tenth of a second late looks wrong to everybody.'],
  ['af_heart', 'I was made from one photograph, a voice model and some JavaScript.'],
];
(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const server = http.createServer((q, r) => {
    const u = decodeURIComponent(q.url.split('?')[0]);
    if (u === '/bench.html') { r.writeHead(200, { 'content-type': 'text/html' }); return r.end('<!DOCTYPE html><title>bench</title>'); }
    const f = path.join(ROOT, u); if (!f.startsWith(ROOT) || !fs.existsSync(f)) { r.writeHead(404); return r.end(); }
    r.writeHead(200, { 'content-type': TYPES[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(r);
  }).listen(0);
  const port = server.address().port, browser = await chromium.launch(), page = await browser.newPage();
  page.on('console', m => console.log('  page:', m.text())); page.on('pageerror', e => console.log('  page error:', e.message));
  await page.goto(`http://127.0.0.1:${port}/bench.html`);
  const t0 = Date.now();
  const ready = await page.evaluate(DIR => new Promise((done, fail) => {
    const w = window.w = new Worker(DIR + '/worker.js', { type: 'module' }), steps = []; window.waiting = {};
    w.onerror = e => fail(new Error('worker: ' + (e.message || 'failed to start')));
    w.onmessage = e => { const m = e.data;
      if (m.type === 'progress') { if (steps[steps.length - 1] !== m.step) steps.push(m.step); }
      else if (m.type === 'ready') done(Object.assign(m, { steps, isolated: self.crossOriginIsolated }));
      else if (m.type === 'error' && m.id == null) fail(new Error(m.at + ': ' + m.message));
      else if (window.waiting[m.id]) { window.waiting[m.id](m); delete window.waiting[m.id]; } };
    w.postMessage({ type: 'init', base: new URL(DIR + '/', location.href).href, voice: 'af_heart' });
  }), DIR);
  console.log(`ready in ${((Date.now() - t0) / 1000).toFixed(1)} s; steps: ${ready.steps.join(' > ')}; threads ${ready.threads}; isolated ${ready.isolated}; warm-up line made in ${ready.rtf.toFixed(2)} x its length`);
  const rows = [];
  for (let i = 0; i < LINES.length; i++) {
    const [voice, text] = LINES[i];
    const r = await page.evaluate(({ i, voice, text }) => new Promise(done => { window.waiting[i] = m => done(m.type === 'said' && !m.empty ? { ph: m.ph, took: m.took, secs: m.secs, sp: m.sp, audio: Array.from(new Int16Array(Array.from(m.audio, v => Math.max(-32768, Math.min(32767, Math.round(v * 32767)))))) } : m); window.w.postMessage({ type: 'say', id: i, seq: 1, text, voice }); }), { i, voice, text });
    if (!r.sp) { console.log(i, 'FAILED', JSON.stringify(r)); continue; }
    const pcm = Buffer.from(Int16Array.from(r.audio).buffer), h = Buffer.alloc(44);
    h.write('RIFF', 0); h.writeUInt32LE(36 + pcm.length, 4); h.write('WAVEfmt ', 8); h.writeUInt32LE(16, 16); h.writeUInt16LE(1, 20); h.writeUInt16LE(1, 22); h.writeUInt32LE(24000, 24); h.writeUInt32LE(48000, 28); h.writeUInt16LE(2, 32); h.writeUInt16LE(16, 34); h.write('data', 36); h.writeUInt32LE(pcm.length, 40);
    fs.writeFileSync(path.join(OUT, `line_${i}.wav`), Buffer.concat([h, pcm]));
    fs.writeFileSync(path.join(OUT, `line_${i}.json`), JSON.stringify({ voice, text, ph: r.ph, took: r.took, secs: r.secs, sp: r.sp }));
    rows.push({ took: r.took, secs: r.secs });
    console.log(`${i} ${voice.padEnd(10)} ${r.secs.toFixed(2)} s of speech made in ${r.took.toFixed(2)} s (${(r.took / r.secs).toFixed(2)} x)  ${r.ph}`);
  }
  const a = rows.reduce((s, r) => s + r.took, 0), b = rows.reduce((s, r) => s + r.secs, 0);
  console.log(`all lines: ${b.toFixed(1)} s of speech made in ${a.toFixed(1)} s: ${(a / b).toFixed(2)} x its length, on ${ready.threads} thread(s)`);
  fs.writeFileSync(path.join(OUT, 'summary.json'), JSON.stringify({ ready: { rtf: ready.rtf, threads: ready.threads, steps: ready.steps, seconds: (Date.now() - t0) / 1000 }, lines: rows, rtf: a / b }));
  await browser.close(); server.close();
})().catch(e => { console.error('FAILED:', e.message); process.exit(1); });
