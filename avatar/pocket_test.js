// pocket_test.js [outdir] [voice.pvoice] : runs the copied-voice worker (voice/pocket.js) in headless Chromium and saves what it makes.
//
// For each test sentence: the audio (24 kHz WAV) and a JSON with the sounds and the times measured for them, the words
// and the pitch, in the same form avatar/voice_test.js writes, so tests/voice_check.py can check the words with a
// speech recogniser and the times with the large aligner. Prints how long each line took and where the time went.
// The voice defaults to a test voice made from a synthetic recording (avatar/voice/src/pocket/demo.pvoice).
//   node avatar/pocket_test.js          (from the repository root; needs avatar/voice/ and avatar/voice/pocket/ filled)
// To compare ways of running it:  POCKET_FIT=0 (caches at the published 1000 positions)  POCKET_ISOLATED=1 (the page is
// served so that threads are allowed)  POCKET_THREADS=n  POCKET_FULL=1 (the full-precision files, from avatar/voice/src/pocket_full/)
// POCKET_LINES='One line.|Another.' says those in place of the test sentences.
const { chromium } = require('playwright'), http = require('http'), fs = require('fs'), path = require('path');
const ROOT = __dirname, OUT = process.argv[2] || path.join(__dirname, '..', 'tests', 'output', 'pocket'), VOICE = process.argv[3] || path.join(__dirname, 'voice', 'src', 'pocket', 'demo.pvoice');
const TYPES = { '.js': 'text/javascript', '.wasm': 'application/wasm', '.json': 'application/json', '.html': 'text/html' };
const LINES = process.env.POCKET_LINES ? process.env.POCKET_LINES.split('|') : ["Hi, I'm the avatar. Ask me anything you like.", 'Good question. The lips you are watching are timed by a small recogniser that listens to my voice.',
  'Sure, I can do that. Give me a moment to think about it.', 'The weather in Paris is usually mild in May, with a few rainy afternoons.',
  'Maybe my mouth moves better now, but both of us will be able to tell.', 'About forty-two percent of people say they would rather type than talk.'];
(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const server = http.createServer((q, r) => {
    const u = decodeURIComponent(q.url.split('?')[0]);
    if (u === '/bench.html') { r.writeHead(200, Object.assign({ 'content-type': 'text/html' }, process.env.POCKET_ISOLATED ? { 'Cross-Origin-Opener-Policy': 'same-origin', 'Cross-Origin-Embedder-Policy': 'credentialless' } : {})); return r.end('<!DOCTYPE html><title>bench</title>'); }
    const f = path.join(ROOT, u); if (!f.startsWith(ROOT) || !fs.existsSync(f)) { r.writeHead(404); return r.end(); }
    const h = { 'content-type': TYPES[path.extname(f)] || 'application/octet-stream', 'content-length': fs.statSync(f).size };
    if (process.env.POCKET_ISOLATED) { h['Cross-Origin-Opener-Policy'] = 'same-origin'; h['Cross-Origin-Embedder-Policy'] = 'credentialless'; }
    r.writeHead(200, h); fs.createReadStream(f).pipe(r);
  }).listen(0);
  const browser = await chromium.launch(), page = await browser.newPage();
  page.on('console', m => console.log('  page:', m.text())); page.on('pageerror', e => console.log('  page error:', e.message));
  await page.goto(`http://127.0.0.1:${server.address().port}/bench.html`);
  const t0 = Date.now(), voice = fs.readFileSync(VOICE).toString('base64');
  const opt = { fit: process.env.POCKET_FIT !== '0', threads: +process.env.POCKET_THREADS || 0, full: !!process.env.POCKET_FULL };
  const ready = await page.evaluate(({ voice, opt }) => new Promise((done, fail) => {
    const w = window.w = new Worker('voice/pocket.js', { type: 'module' }), steps = []; window.waiting = {};
    const bin = atob(voice), u8 = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i);
    w.onerror = e => fail(new Error('worker: ' + (e.message || 'failed to start')));
    w.onmessage = e => { const m = e.data;
      if (m.type === 'progress') { if (steps[steps.length - 1] !== m.step) steps.push(m.step); }
      else if (m.type === 'ready') done(Object.assign(m, { steps }));
      else if (m.type === 'need') fail(new Error('needs ' + m.what.join(', ')));
      else if (m.type === 'error' && m.id == null) fail(new Error(m.at + ': ' + m.message));
      else if (window.waiting[m.id]) { window.waiting[m.id](m); delete window.waiting[m.id]; } };
    const full = new URL('voice/src/pocket_full/', location.href).href;
    w.postMessage({ type: 'init', base: new URL('voice/', location.href).href, voice: 'test', voices: { test: new Float32Array(u8.buffer) }, fit: opt.fit, threads: opt.threads,
      from: opt.full ? { lm: full + 'flow_lm_main.onnx', flow: full + 'flow_lm_flow.onnx', dec: full + 'mimi_decoder.onnx' } : null });
  }), { voice, opt });
  const a = ready.about, p = a.parts;
  console.log(`${a.full ? 'full precision' : '8-bit'}; caches ${a.fits ? 'made to measure' : 'at 1000 positions'}; ${a.isolated ? 'isolated page' : 'not isolated'}`);
  console.log(`ready in ${((Date.now() - t0) / 1000).toFixed(1)} s; steps: ${ready.steps.join(' > ')}; threads ${ready.threads}; voice primed in ${a.primed.toFixed(2)} s; first line ${a.cold.toFixed(2)} s; then ${a.secs.toFixed(2)} s of speech in ${a.made.toFixed(2)} s (${ready.rtf.toFixed(2)} x): text ${p.text.toFixed(2)}, voice ${p.voice.toFixed(2)}, audio ${p.audio.toFixed(2)}`);
  const rows = [];
  for (let i = 0; i < LINES.length; i++) {
    const r = await page.evaluate(({ i, text }) => new Promise(done => { window.waiting[i] = m => done(m.type === 'said' && !m.empty ? { ph: m.ph, took: m.took, secs: m.secs, sp: m.sp, parts: m.parts, audio: Array.from(m.audio, v => Math.max(-32768, Math.min(32767, Math.round(v * 32767)))) } : m); window.w.postMessage({ type: 'say', id: i, seq: 1, text, voice: 'test' }); }), { i, text: LINES[i] });
    if (!r.sp) { console.log(i, 'FAILED', JSON.stringify(r).slice(0, 300)); continue; }
    const pcm = Buffer.from(Int16Array.from(r.audio).buffer), h = Buffer.alloc(44);
    h.write('RIFF', 0); h.writeUInt32LE(36 + pcm.length, 4); h.write('WAVEfmt ', 8); h.writeUInt32LE(16, 16); h.writeUInt16LE(1, 20); h.writeUInt16LE(1, 22); h.writeUInt32LE(24000, 24); h.writeUInt32LE(48000, 28); h.writeUInt16LE(2, 32); h.writeUInt16LE(16, 34); h.write('data', 36); h.writeUInt32LE(pcm.length, 40);
    fs.writeFileSync(path.join(OUT, `line_${i}.wav`), Buffer.concat([h, pcm]));
    fs.writeFileSync(path.join(OUT, `line_${i}.json`), JSON.stringify({ voice: 'pocket', text: LINES[i], ph: r.ph, took: r.took, secs: r.secs, sp: r.sp, parts: r.parts }));
    rows.push(r); const q = r.parts;
    console.log(`${i} ${r.secs.toFixed(2)} s of speech in ${r.took.toFixed(2)} s (${(r.took / r.secs).toFixed(2)} x): pronouncing ${q.text.toFixed(2)}, voice ${q.voice.toFixed(2)}, audio ${q.audio.toFixed(2)}, timing ${q.timing.toFixed(2)}  ${r.ph.slice(0, 70)}`);
  }
  const A = rows.reduce((s, r) => s + r.took, 0), B = rows.reduce((s, r) => s + r.secs, 0);
  console.log(`all lines: ${B.toFixed(1)} s of speech made in ${A.toFixed(1)} s: ${(A / B).toFixed(2)} x its length, on ${ready.threads} thread(s)`);
  fs.writeFileSync(path.join(OUT, 'summary.json'), JSON.stringify({ rtf: A / B, ready: { rtf: ready.rtf, about: a, seconds: (Date.now() - t0) / 1000 } }));
  await browser.close(); server.close();
})().catch(e => { console.error('FAILED:', e.message); process.exit(1); });
