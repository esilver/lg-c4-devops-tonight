// record.js [out.mp4] [voice] : a short video of the avatar speaking with its own voice, to look at and listen to.
//
// The page is loaded as usual (served with avatar/voice/ beside it), but its clock is taken over: time moves one
// thirtieth of a second per frame, however long a frame takes to draw. The lines are made by the page's own voice
// worker; each is started on that clock exactly as the page starts it on the audio clock, the canvas is saved every
// frame, and the same audio is laid at the same times in the sound track. So picture and sound are as far apart in
// the video as they are on the page when it plays live, apart from the time sound takes to leave a real device.
//   node avatar/record.js demo/avatar.mp4 am_michael        (from the repository root; needs ffmpeg)
// AVATAR_PAGE=index.<face>.html records a page built from a face file; AVATAR_LINES="one|two" sets what is said;
// AVATAR_FPS=60 records sixty pictures a second (the page itself draws as often as the screen asks);
// AVATAR_CRF=12 AVATAR_JPEG=0.98 keep more of the fine detail (a larger file), for judging sharpness from the clip.
const { chromium } = require('playwright'), fs = require('fs'), http = require('http'), path = require('path'), { spawn } = require('child_process');
const OUT = process.argv[2] || path.join(__dirname, '..', 'demo', 'avatar.mp4'), VOICE = process.argv[3] || '', FPS = +process.env.AVATAR_FPS || 30;
const LINES = (process.env.AVATAR_LINES || "Hi. I'm an avatar made from one photograph.|The voice is a stock one, made on this machine, and my lips are timed by the same model that makes it.|Peter Piper picked a peck of pickled peppers, maybe more.|So, what would you like to talk about?").split('|');
const TYPES = { '.js': 'text/javascript', '.wasm': 'application/wasm', '.json': 'application/json', '.html': 'text/html', '.bin': 'application/octet-stream' };
(async () => {
  const server = http.createServer((q, r) => { const f = path.join(__dirname, decodeURIComponent(q.url.split('?')[0])); if (!f.startsWith(__dirname) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { r.writeHead(404); return r.end(); } r.writeHead(200, { 'content-type': TYPES[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(r); }).listen(0);
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] }), p = await b.newPage({ viewport: { width: 900, height: 1100 } });
  p.on('pageerror', e => console.log('page error:', e.message));
  await p.addInitScript(() => { window.__vt = 0; const real = performance.now.bind(performance); window.__real = real; performance.now = () => window.__vt * 1000; });      // the page's clock is ours
  await p.goto(`http://127.0.0.1:${server.address().port}/${process.env.AVATAR_PAGE || 'index.html'}`);
  await p.waitForFunction(() => typeof pending !== 'undefined' && pending === 0 && live.state === 'idle' && kk.state === 'ready', null, { timeout: 240000 });
  const made = await p.evaluate(async ({ LINES, VOICE }) => {
    window.requestAnimationFrame = () => 0;                                   // frames are drawn when asked for, not when the browser likes
    const voice = VOICE || FACE.voice, out = [];
    for (const text of LINES) out.push(await new Promise(done => { const id = ++kk.id; kk.wait[id] = m => done(m); kk.pool[0].w.postMessage({ type: 'say', id, seq: live.seq, text, voice }); }));
    window.__made = out.map((m, i) => ({ text: LINES[i], sp: m.sp, secs: m.secs, audio: m.audio }));
    return window.__made.map(l => ({ text: l.text, secs: l.secs, ok: !!l.sp }));
  }, { LINES, VOICE });
  if (made.some(l => !l.ok)) throw new Error('a line was not made');
  // the plan: a moment of listening, a breath, the lines with a short pause between them, a moment after
  let t = 1.5; const T = made.map(l => { const at = t; t += l.secs + 0.35; return at; }), total = t + 0.9, frames = Math.round(total * FPS);
  const pcm = await p.evaluate(({ T, total }) => { const n = Math.round(total * 24000), a = new Int16Array(n); window.__made.forEach((l, k) => { const o = Math.round(T[k] * 24000); for (let i = 0; i < l.audio.length && o + i < n; i++) a[o + i] = Math.max(-32768, Math.min(32767, Math.round(l.audio[i] * 32767))); }); let s = ''; const u = new Uint8Array(a.buffer); for (let i = 0; i < u.length; i += 32768) s += String.fromCharCode.apply(null, u.subarray(i, i + 32768)); return btoa(s); }, { T, total });
  fs.mkdirSync(path.dirname(OUT), { recursive: true }); const raw = OUT + '.pcm'; fs.writeFileSync(raw, Buffer.from(pcm, 'base64'));
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-', '-f', 's16le', '-ar', '24000', '-ac', '1', '-i', raw, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', process.env.AVATAR_CRF || '18', '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart', '-shortest', OUT], { stdio: ['pipe', 'inherit', 'inherit'] });
  const closed = new Promise(r => ff.on('close', r));
  for (let f = 0; f < frames; f++) {
    const jpg = await p.evaluate(({ f, FPS, T, Q }) => {
      const vt = window.__vt = f / FPS, L = window.__made;
      if (!window.__span && vt >= T[0] - 0.5) { const span = window.__span = [vt + 0.45, 1e9]; (SPOKE[WHO] = SPOKE[WHO] || []).push(span); live.breath.push([vt, -1], [vt + 0.4, 1]); breathe(); L[0].first = true; live.turn = L; live.cur = -1; setState('speaking', 'Speaking'); }
      for (let k = live.cur + 1; k < L.length; k++) { if (vt >= T[k] - PRE - 0.03) { reach(k, T[k]); sync.plan = vt - T[k]; sync.at = wall(); } break; }
      if (window.__span && window.__span[1] > 1e8 && vt > T[L.length - 1] + L[L.length - 1].secs + 0.3) { window.__span[1] = vt; finish(); live.turn = null; rest(vt); setState('idle', 'Ready'); }
      frame(); return scr.toDataURL('image/jpeg', Q).slice(23);
    }, { f, FPS, T, Q: +process.env.AVATAR_JPEG || 0.93 });
    if (!ff.stdin.write(Buffer.from(jpg, 'base64'))) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end(); await closed; fs.unlinkSync(raw);
  fs.writeFileSync(OUT.replace(/\.mp4$/, '.json'), JSON.stringify({ fps: FPS, lines: (await p.evaluate(() => window.__made.map(l => l.sp))).map((sp, k) => ({ text: made[k].text, at: T[k], secs: made[k].secs, sp })) }));
  console.log(`${OUT}: ${frames} frames, ${total.toFixed(1)} s; lines at ${T.map(v => v.toFixed(2)).join(', ')} s`);
  await b.close(); server.close();
})().catch(e => { console.error('FAILED:', e.message); process.exit(1); });
