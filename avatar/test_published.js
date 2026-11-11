// test_published.js : the page as a Claude artifact holds it, in a headless browser.
//
// A published page carries only index.html and voice/worker.js. The two libraries then come from the jsDelivr CDN and
// the model and voices are files the viewer adds. This test serves exactly those two files, answers the CDN's addresses
// from the copies in avatar/voice/ (the test machine has no route to the CDN), and walks through it:
//   1  first visit: the page should say what it needs (model, voice) and speak with a borrowed voice meanwhile
//   2  the viewer adds model_quantized.onnx and am_michael.bin: the voice should start, and a reply be spoken with it
//   3  the page is loaded again: the files should still be there (kept in the browser), with nothing to add
//   4  a browser where the CDN will not hand over the runtime's .wasm file: the page should ask for that file too
//   6  a worker told there is a GPU, in a view that refuses the GPU runtime's files: the page should say so and offer
//      the file; once it is added the GPU start is attempted (and fails here, there being no GPU) and the processor takes over
//   5  the viewer adds the full-precision model (the one a GPU can run): the voice should start again with it, and only
//      that model be kept. There is no GPU here, so this shows the fall-back to the processor, not the GPU itself.
// What it cannot show is whether the real viewer's frame allows any of this (WebAssembly, the CDN, storage).
// Run from the repository root:  node avatar/test_published.js
const { chromium } = require('playwright'), fs = require('fs'), http = require('http'), path = require('path');
const V = path.join(__dirname, 'voice'), SRC = path.join(V, 'src');
const CDN = { 'onnxruntime-web@1.31.1/dist/ort.jspi.min.mjs': ['ort-jspi.js', 'text/javascript'], 'onnxruntime-web@1.31.1/dist/ort-wasm-simd-threaded.jspi.mjs': ['ort-jspi-wasm.js', 'text/javascript'], 'onnxruntime-web@1.31.1/dist/ort-wasm-simd-threaded.jspi.wasm': ['ort-jspi.wasm', 'application/wasm'],
  'onnxruntime-web@1.31.1/dist/ort.webgpu.min.mjs': ['ort-gpu.js', 'text/javascript'], 'onnxruntime-web@1.31.1/dist/ort-wasm-simd-threaded.asyncify.mjs': ['ort-gpu-wasm.js', 'text/javascript'], 'onnxruntime-web@1.31.1/dist/ort-wasm-simd-threaded.asyncify.wasm': ['ort-gpu.wasm', 'application/wasm'],
  'onnxruntime-web@1.31.1/dist/ort.wasm.min.mjs': ['ort.js', 'text/javascript'], 'onnxruntime-web@1.31.1/dist/ort-wasm-simd-threaded.mjs': ['ort-wasm.js', 'text/javascript'],
  'onnxruntime-web@1.31.1/dist/ort-wasm-simd-threaded.wasm': ['ort-wasm.wasm', 'application/wasm'], 'phonemizer@1.2.1/dist/phonemizer.js': ['phonemizer.js', 'text/javascript'] };
const mocks = () => { const sample = async (input, opts) => { const text = 'Maybe my mouth moves better now. Both of us will be able to tell.'; for (let i = 1; i <= 4; i++) { await new Promise(r => setTimeout(r, 120)); if (opts && opts.onText) opts.onText({ text: text.slice(0, Math.round(text.length * i / 4)), delta: '' }); } return { text }; }; window.claude = { use: async n => ({ sample })[n] || null }; };
(async () => {
  const server = http.createServer((q, r) => {
    let u = q.url.split('?')[0]; const fake = u.startsWith('/fakegpu/'); if (fake) u = u.slice(8);
    const f = u === '/index.html' ? path.join(__dirname, 'index.html') : u === '/voice/worker.js' ? path.join(V, 'worker.js') : null;
    if (!f) { r.writeHead(404); return r.end(); }
    // 6: a worker that is told a GPU is on offer when none is, to run the GPU branch as far as it goes without one
    if (fake && u === '/voice/worker.js') { r.writeHead(200, { 'content-type': 'text/javascript' }); return r.end("Object.defineProperty(self.navigator, 'gpu', { value: { requestAdapter: async () => ({ pretend: true }) }, configurable: true });\n" + fs.readFileSync(f, 'utf8')); }
    r.writeHead(200, { 'content-type': u.endsWith('.js') ? 'text/javascript' : 'text/html' }); fs.createReadStream(f).pipe(r);
  }).listen(0); const url = `http://127.0.0.1:${server.address().port}/index.html`;
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--autoplay-policy=no-user-gesture-required'] }); let failed = 0;
  const check = (ok, text) => { if (!ok) failed++; console.log(`${ok ? 'ok  ' : 'FAIL'} ${text}`); };
  for (const noWasm of [false, true]) {
    const ctx = await b.newContext({ viewport: { width: 900, height: 1200 } }); const asked = [];
    await ctx.route('https://cdn.jsdelivr.net/npm/**', route => { const k = route.request().url().split('/npm/')[1], hit = CDN[k]; asked.push(k);
      if (!hit || (noWasm && k.endsWith('.wasm'))) return route.abort(); route.fulfill({ status: 200, contentType: hit[1], headers: { 'access-control-allow-origin': '*' }, body: fs.readFileSync(path.join(V, hit[0])) }); });
    await ctx.route(/fonts\.(googleapis|gstatic)\.com/, route => route.abort());
    const p = await ctx.newPage(); const errs = []; p.on('pageerror', e => errs.push(e.message)); await p.addInitScript(mocks);
    const settle = async () => { await p.waitForFunction(() => typeof pending !== 'undefined' && pending === 0 && live.state === 'idle', null, { timeout: 30000 }); await p.waitForFunction(() => ['ready', 'failed', 'needs'].includes(kk.state), null, { timeout: 240000 }); return p.evaluate(() => ({ state: kk.state, need: kk.need, error: kk.error, from: kk.from, kept: kk.kept, voices: kk.voices, add: document.getElementById('add').hidden ? '' : document.getElementById('addWhy').textContent, how: document.getElementById('how').textContent })); };
    await p.goto(url); let s = await settle();
    if (noWasm) {
      check(s.state === 'needs' && s.need.join() === 'wasm,model,voice', `4 no .wasm from the CDN: the page asks for ${s.need.join(', ')} | "${s.add.slice(0, 90)}…"`);
      await p.setInputFiles('#files', [path.join(V, 'ort-wasm.wasm'), path.join(SRC, 'model_quantized.onnx'), path.join(SRC, 'af_heart.bin')]); await p.waitForFunction(() => kk.state !== 'needs', null, { timeout: 60000 }); s = await settle();
      check(s.state === 'ready', `4 after adding the three files: voice ${s.state}${s.error ? ' (' + s.error + ')' : ''}, voices ${s.voices.join(' ')}`);
      await ctx.close(); continue;
    }
    check(s.state === 'needs' && s.need.join() === 'model,voice', `1 first visit: voice ${s.state}, the page asks for ${s.need.join(', ')}; libraries asked of the CDN: ${[...new Set(asked)].length}`);
    console.log(`     "${s.how}"\n     "${s.add}"`);
    await p.screenshot({ path: path.join(__dirname, 'test_needs.png'), fullPage: true });
    await p.setInputFiles('#files', [path.join(SRC, 'model_quantized.onnx'), path.join(SRC, 'am_michael.bin')]); const t0 = Date.now(); await p.waitForFunction(() => kk.state !== 'needs', null, { timeout: 60000 }); s = await settle();
    check(s.state === 'ready' && s.from === 'cdn' && s.voices.join() === 'am_michael', `2 after adding the model and one voice: voice ${s.state}${s.error ? ' (' + s.error + ')' : ''} in ${((Date.now() - t0) / 1000).toFixed(1)} s, runtime from the ${s.from}, voices ${s.voices.join(' ')}, files kept in the browser: ${s.kept}`);
    await p.fill('#say', 'Is it better?'); await p.click('#send'); const modes = new Set(); let open = 0, n = 0;
    for (let i = 0; i < 1600; i++) { const r = await p.evaluate(() => ({ s: live.state, m: mode(), o: live.beat ? speechAt(live.beat, PRE + planned(), WHO).o : 0 })); if (r.s === 'speaking') { modes.add(r.m); n++; if (r.o > 0.2) open++; } if (i > 60 && r.s === 'idle') break; await p.waitForTimeout(25); }
    check(modes.has('own') && modes.size === 1 && open > 5, `2 a reply was spoken with: ${[...modes].join(', ') || 'nothing'}; mouth open in ${open} of ${n} samples`);
    await p.setInputFiles('#files', [path.join(SRC, 'af_bella.bin')]); await p.waitForFunction(() => kk.voices.length === 2, null, { timeout: 20000 });
    check(true, `2 a second voice added afterwards: ${await p.evaluate(() => [...document.getElementById('voice').options].map(o => o.textContent).join(', '))}`);
    await p.reload(); s = await settle();
    check(s.state === 'ready' && s.voices.length === 2, `3 loaded again: voice ${s.state} with nothing added, voices ${s.voices.join(' ')}`);
    await p.setInputFiles('#files', [path.join(SRC, 'model.onnx')]); await p.waitForFunction(() => kk.state === 'loading', null, { timeout: 120000 }); s = await settle();
    const a = await p.evaluate(() => kk.about), keys = await p.evaluate(() => new Promise(ok => { const r = indexedDB.open('avatar-voice', 1); r.onsuccess = () => { const q = r.result.transaction('f').objectStore('f').getAllKeys(); q.onsuccess = () => ok(q.result); }; }));
    check(s.state === 'ready' && a && a.full && a.engine === 'cpu' && keys.filter(k => /\.onnx$/.test(k)).join() === 'model.onnx', `5 the full-precision model added in place of the 8-bit one: voice ${s.state}${s.error ? ' (' + s.error + ')' : ''}, run on the ${a ? a.engine : '?'} (GPU offered here: ${a ? a.gpu : '?'}); kept in the browser: ${keys.join(', ')}`);
    console.log(`     "${s.add}"`);
    check(!errs.length, `page errors: ${errs.length ? errs.slice(0, 3).join(' | ') : 'none'}`);
    await ctx.close();
  }
  { // 6: the worker believes there is a GPU; the view refuses both GPU runtime files; then the viewer adds one by hand
    const ctx = await b.newContext({ viewport: { width: 900, height: 1200 } });
    await ctx.route('https://cdn.jsdelivr.net/npm/**', route => { const k = route.request().url().split('/npm/')[1], hit = CDN[k]; if (!hit || /(jspi|asyncify)\.wasm$/.test(k)) return route.abort(); route.fulfill({ status: 200, contentType: hit[1], headers: { 'access-control-allow-origin': '*' }, body: fs.readFileSync(path.join(V, hit[0])) }); });
    await ctx.route(/fonts\.(googleapis|gstatic)\.com/, route => route.abort());
    const p = await ctx.newPage(); const errs = []; p.on('pageerror', e => errs.push(e.message)); await p.addInitScript(mocks);
    const settle = async () => { await p.waitForFunction(() => typeof pending !== 'undefined' && pending === 0 && live.state === 'idle', null, { timeout: 30000 }); await p.waitForFunction(() => ['ready', 'failed', 'needs'].includes(kk.state), null, { timeout: 300000 }); return p.evaluate(() => ({ state: kk.state, error: kk.error, about: kk.about, add: document.getElementById('add').hidden ? '' : document.getElementById('addWhy').textContent })); };
    await p.goto(url.replace('/index.html', '/fakegpu/index.html')); let s = await settle();
    await p.setInputFiles('#files', [path.join(SRC, 'model.onnx'), path.join(SRC, 'am_michael.bin')]); await p.waitForFunction(() => kk.state !== 'needs', null, { timeout: 120000 }); s = await settle();
    check(s.state === 'ready' && s.about.engine === 'cpu' && !!s.about.gpuNeed && /GPU runtime/.test(s.add), `6 a GPU on offer but its runtime refused by the view: voice ${s.state} on the ${s.about && s.about.engine}; the page offers the ${s.about && s.about.gpuNeed} file | "${s.add.slice(0, 150)}…"`);
    const kind = s.about.gpuNeed; await p.setInputFiles('#files', [path.join(V, kind === 'jspi' ? 'ort-jspi.wasm' : 'ort-gpu.wasm')].map(f => { const t = path.join(require('os').tmpdir(), 'ort-wasm-simd-threaded.' + kind + '.wasm'); fs.copyFileSync(f, t); return t; }));
    await p.waitForFunction(() => kk.state === 'loading', null, { timeout: 120000 }); s = await settle();
    check(s.state === 'ready' && !s.about.gpuNeed && s.about.engine === 'cpu' && !!s.about.gpuWhy, `6 after adding that file: the GPU runtime loaded and the GPU start was tried (${s.about && s.about.gpuWhy}), then the processor took over: voice ${s.state}${s.error ? ' (' + s.error + ')' : ''}`);
    check(!errs.length, `6 page errors: ${errs.length ? errs.slice(0, 3).join(' | ') : 'none'}`);
    await ctx.close();
  }
  await b.close(); server.close(); process.exit(failed ? 1 : 0);
})().catch(e => { console.error('FAILED:', e.message); process.exit(1); });
