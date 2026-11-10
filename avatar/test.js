// test.js [outdir] : the live page in a headless browser, three ways.
//
//  1 own voice       the page as published: served over HTTP with avatar/voice/ beside it, and a stand-in for Claude's
//                    reply. Waits for the voice model, sends two messages, and records the state and the mouth as it goes.
//                    Saves the audio of each line, the times the voice reported and the jaw the engine draws for every
//                    10 ms of it (own_voice.json), so that tests/voice_check.py can measure the mouth against the sound.
//  2 borrowed voice  the same page with no voice folder and stand-ins for Claude's reply and Claude's voice (which
//                    "speaks" at 11 letters a second, slower than the page assumes, to exercise its clock)
//  3 bare page       opened from disk with nothing: checks the last fallbacks
// Run from the repository root:  node avatar/test.js
const { chromium } = require('playwright'), fs = require('fs'), http = require('http'), path = require('path');
const OUT = process.argv[2] || path.join(__dirname, '..', 'tests', 'output', 'voice'); fs.mkdirSync(OUT, { recursive: true });
const TYPES = { '.js': 'text/javascript', '.wasm': 'application/wasm', '.json': 'application/json', '.html': 'text/html', '.bin': 'application/octet-stream' };
const REPLY = ['Hello there, it is good to meet you. I am an avatar made from one photograph, and my mouth is following these words. What would you like to talk about?',
  'Peter Piper bought a big bag of brown bread, maybe more than my mother made. Bob and Pamompletely missed the bus.'.replace('ompletely', ' completely')];
const mocks = (reply, withTts) => {
  const cbs = { line: [], pos: [], state: [] }; let stop = false;
  const tts = { onLine: f => cbs.line.push(f), onPosition: f => cbs.pos.push(f), onState: f => cbs.state.push(f), stop: () => { stop = true; },
    speak: async lines => { stop = false; cbs.state.forEach(f => f({ state: 'speaking' }));
      for (let i = 0; i < lines.length && !stop; i++) { cbs.line.forEach(f => f({ line: i, id: lines[i].id })); const dur = lines[i].text.replace(/[^a-z]/gi, '').length / 11 * 1000, t0 = performance.now();
        while (performance.now() - t0 < dur && !stop) { await new Promise(r => setTimeout(r, 200)); cbs.pos.forEach(f => f({ ms: Math.min(dur, performance.now() - t0), line: i })); }
        await new Promise(r => setTimeout(r, 250)); }
      cbs.state.forEach(f => f({ state: 'idle', reason: stop ? 'viewer_stopped' : 'completed' })); } };
  let asked = 0; const sample = async () => { await new Promise(r => setTimeout(r, 300)); return { text: reply[Math.min(asked++, reply.length - 1)] }; };
  window.claude = { use: async n => ({ sample, tts: withTts ? tts : null })[n] || null };
};
const wav = (f, pcm16) => { const pcm = Buffer.from(Int16Array.from(pcm16).buffer), h = Buffer.alloc(44); h.write('RIFF', 0); h.writeUInt32LE(36 + pcm.length, 4); h.write('WAVEfmt ', 8); h.writeUInt32LE(16, 16); h.writeUInt16LE(1, 20); h.writeUInt16LE(1, 22); h.writeUInt32LE(24000, 24); h.writeUInt32LE(48000, 28); h.writeUInt16LE(2, 32); h.writeUInt16LE(16, 34); h.write('data', 36); h.writeUInt32LE(pcm.length, 40); fs.writeFileSync(f, Buffer.concat([h, pcm])); };
(async () => {
  const server = http.createServer((q, r) => {
    let u = decodeURIComponent(q.url.split('?')[0]); const bare = u.startsWith('/novoice/'); if (bare) u = u.slice(8);
    const f = path.join(__dirname, u); if (!f.startsWith(__dirname) || (bare && u.startsWith('/voice/')) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { r.writeHead(404); return r.end(); }
    r.writeHead(200, { 'content-type': TYPES[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(r);
  }).listen(0); const origin = `http://127.0.0.1:${server.address().port}`;
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--autoplay-policy=no-user-gesture-required'] }); let failed = 0;
  for (const [name, url, withTts] of [['own voice', origin + '/index.html', false], ['borrowed voice', origin + '/novoice/index.html', true], ['bare page', 'file://' + __dirname + '/index.html', null]]) {
    const p = await b.newPage({ viewport: { width: 900, height: 1100 } }); const errs = []; p.on('pageerror', e => errs.push(e.message)); p.on('console', m => m.type() === 'error' && !/404|Failed to load resource|ERR_FILE_NOT_FOUND|Fetch API cannot load/.test(m.text()) && errs.push(m.text()));
    if (withTts !== null) await p.addInitScript(`(${mocks})(${JSON.stringify(REPLY)}, ${withTts})`);
    await p.goto(url);
    await p.waitForFunction(() => typeof pending !== 'undefined' && pending === 0 && live.state === 'idle', null, { timeout: 30000 });
    const t0 = Date.now(); await p.waitForFunction(() => kk.state === 'ready' || kk.state === 'failed', null, { timeout: 240000 });
    const voice = await p.evaluate(() => ({ state: kk.state, error: kk.error, rtf: kk.rtf, how: document.getElementById('how').textContent, options: [...document.getElementById('voice').options].map(o => o.value) })); voice.load = (Date.now() - t0) / 1000;
    await p.waitForTimeout(400); let rows = [], shots = 0, firstSound = null, firsts = []; const began = Date.now();
   for (const ask of name === 'own voice' ? ['Hi, who are you?', 'Say something with lots of lip sounds.'] : ['Hi, who are you?']) {
    await p.fill('#say', ask); const sent = Date.now(); let heard = null; await p.click('#send');
    for (let i = 0; i < 2400; i++) {
      const r = await p.evaluate(() => { const b = live.beat, bt = b ? PRE + planned() : 0, L = live.turn, l = L && live.cur >= 0 ? L[live.cur] : null; if (L) window.__lines = L;
        return { s: live.state, o: b ? speechAt(b, bt, WHO).o : 0, cur: live.cur, k: live.stretch, cap: document.getElementById('cap').textContent, mode: mode(), at: l && l.when != null ? actx.currentTime - lag() - l.when : null, held: live.q ? live.q.held : null }; }); r.t = (Date.now() - began) / 1000; rows.push(r);
      if (r.s === 'speaking' && heard == null && r.at != null && r.at >= 0) { heard = (Date.now() - sent) / 1000; firsts.push(heard); if (firstSound == null) firstSound = heard; }
      if (name === 'own voice' && r.s === 'speaking' && r.o > 0.45 && shots < 3 && (i % 20 === 0)) await p.screenshot({ path: `${__dirname}/test_${shots++}.png` });
      if (i > 60 && r.s === 'idle') break; await p.waitForTimeout(25);
    }
    await p.evaluate(() => { window.__all = (window.__all || []).concat(window.__lines || []); window.__lines = null; });
   }
    const sp = rows.filter(r => r.s === 'speaking'), open = sp.filter(r => r.o > 0.2).length, last = rows[rows.length - 1], secs = sp.length ? sp[sp.length - 1].t - sp[0].t : 0;
    const ok = !errs.length && sp.length > 20 && last.s === 'idle' && last.o < 0.05 && open > 0.2 * sp.length; if (!ok) failed++;
    console.log(`${ok ? 'ok  ' : 'FAIL'} ${name}: states ${[...new Set(rows.map(r => r.s))].join(' > ')} | spoken with: ${[...new Set(sp.map(r => r.mode))].join(', ')} | speaking for ${secs.toFixed(1)} s, mouth open (>0.2) in ${Math.round(100 * open / Math.max(1, sp.length))}% of it, widest ${Math.max(0, ...sp.map(r => r.o)).toFixed(2)}, lines reached ${Math.max(...rows.map(r => r.cur)) + 1} | mouth at the end ${last.o.toFixed(2)} | errors: ${errs.length ? errs.slice(0, 3) : 'none'}`);
    console.log(`     voice model: ${voice.state}${voice.error ? ' (' + voice.error + ')' : ''} after ${voice.load.toFixed(1)} s${voice.state === 'ready' ? `, a line made in ${voice.rtf.toFixed(2)} x its length; first sound ${firsts.length ? firsts.map(v => v.toFixed(1) + ' s').join(' and ') : 'never'} after Send (${await p.evaluate(() => kk.pool.length)} workers)` : ''} | voices offered: ${voice.options.join(' ') || 'none'}`);
    console.log(`     "${await p.evaluate(() => document.getElementById('how').textContent)}"`);
    if (name === 'own voice' && voice.state === 'ready') {                          // what was played, and what the mouth did against the audio clock
      const lines = await p.evaluate(() => (window.__all || []).map(l => ({ text: l.text, secs: l.secs, when: l.when, sp: l.sp, curve: (() => { if (!l.sp) return null; const b = { who: WHO, start: clock() + 30, lead: PRE, ai: 900, sp: l.sp, tail: 0.5 }; BREATH[WHO] = live.breath; buildSpeech(b); live.breath = BREATH[WHO]; breathe(); for (let i = 0; i < b.J.length; i++) b.J[i] *= OPEN; const o = []; for (let t = 0; t < l.secs; t += 0.01) { const q = speechAt(b, PRE + t, WHO); o.push([+q.o.toFixed(3), +(q.c || 0).toFixed(3)]); } return o; })(), pcm: l.buf ? Array.from(l.buf.getChannelData(0), v => Math.max(-32768, Math.min(32767, Math.round(v * 32767)))) : null })));
      lines.forEach((l, i) => { if (l.pcm) wav(path.join(OUT, `page_line_${i}.wav`), l.pcm); delete l.pcm; });
      fs.writeFileSync(path.join(OUT, 'own_voice.json'), JSON.stringify({ lines, firstSound, rtf: voice.rtf, held: rows.map(r => r.held).find(v => v != null) }));
      console.log(`     saved ${lines.length} lines (audio, reported times, and the jaw the engine draws for every 10 ms of them) to ${path.relative(process.cwd(), OUT)}/own_voice.json`);
    }
    await p.close();
  }
  await b.close(); server.close(); process.exit(failed ? 1 : 0);
})();
