/* worker.js : the avatar's own voice, made in the browser, with the time of every sound.

   A line of text goes in. Out come the audio (24 kHz) and exactly what the bulletin's engine wants for a line: every
   sound with its start and length, its loudness, the words with their start times and the pitch of the voice, 25 times
   a second. Nothing is guessed: the lengths are the ones the speech model itself used to make the audio.

     text -> sounds     eSpeak NG (through the phonemizer package) says how the words are pronounced; its symbols are
                        rewritten here into the alphabet Kokoro was trained on, which is also the engine's
     sounds -> audio    Kokoro as an ONNX file, run by onnxruntime-web: the 8-bit file on the processor (WebAssembly),
                        or the full-precision file on a GPU where the browser offers one (WebGPU). It returns the
                        waveform and one duration per sound, in steps of 25 ms
     audio -> pitch     measured here from the waveform (autocorrelation), for the nods and brows that follow the voice

   This runs in a worker so the picture keeps moving while a line is being made. The page starts two or three of these
   where the device has the cores: each makes one line at a time, so a reply of several lines is made side by side.

   Where the parts come from. Beside the page (the folder this file is in, filled by avatar/get_voice.py) if they are
   there: that is how the page runs from a disk or a server of one's own. A page published as a Claude artifact cannot
   carry the big ones, so there the two libraries are taken from the jsDelivr CDN, and the model and the voices are
   files the viewer adds once (the page keeps them in the browser and hands them over in `init`).
   Messages in: init, say, cancel. Messages out: progress, need, ready, said, skipped, error. */
const CDN = 'https://cdn.jsdelivr.net/npm/', ORT = CDN + 'onnxruntime-web@1.31.1/dist/', PHON = CDN + 'phonemizer@1.2.1/dist/phonemizer.js';
// the number the model uses for each sound (tokenizer.json of onnx-community/Kokoro-82M-v1.0-ONNX-timestamped)
const VOCAB = (() => { const ch = Array.from("$;:,.!?—…\"()“” ̃ʣʥʦʨᵝꭧAIOQSTWYᵊabcdefhijklmnopqrstuvwxyzɑɐɒæβɔɕçɖðʤəɚɛɜɟɡɥɨɪʝɯɰŋɳɲɴøɸθœɹɾɻʁɽʂʃʈʧʊʋʌɣɤχʎʒʔˈˌːʰʲ↓→↗↘ᵻ"), id = [0,1,2,3,4,5,6,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,31,33,35,36,39,41,42,43,44,45,46,47,48,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,75,76,77,78,80,81,82,83,85,86,87,90,92,99,101,102,103,110,111,112,113,114,115,116,118,119,120,123,125,126,128,129,130,131,132,133,135,136,138,139,140,142,143,147,148,156,157,158,162,164,169,171,172,173,177], v = {}; ch.forEach((c, i) => { v[c] = id[i]; }); return v; })();
const SR = 24000, FRAME = 600;                          // the model lays sounds out in 25 ms steps
const EARLY = 0.07;                                     // and its audio runs 70 ms ahead of the durations it reports: measured with a forced aligner
                                                        // (tests/voice_check.py: -67 ms over 337 sounds; the bulletin found the same, docs/12)
let ort, phonemize, S, sounds, session, base, threads = 1, least = 0, local = null, queue = Promise.resolve();
const vocab = VOCAB, voices = {}, pitches = {}, from = {};
const post = (m, t) => self.postMessage(m, t || []);
self.onmessage = e => {
  const m = e.data;
  if (m.type === 'cancel') { least = m.seq; return; }                     // lines of an abandoned reply are not made
  if (m.type === 'voice') { voices[m.name] = m.data; return; }            // a voice the viewer added later
  queue = queue.then(() => m.type === 'init' ? init(m) : m.type === 'say' ? say(m) : null)
    .catch(err => post({ type: 'error', id: m.id, seq: m.seq, at: m.type === 'init' ? stage : 'say', message: String(err && err.message || err) }));
};

let stage = 'start';
async function init(m) {
  base = m.base; const step = (s, x) => { stage = s; post(Object.assign({ type: 'progress', step: s }, x)); };
  const grab = async url => { const r = await fetch(url); if (!r.ok) throw new Error('HTTP ' + r.status); return r.arrayBuffer(); };
  const why = e => String(e && e.message || e).slice(0, 120);
  // Is the voice folder beside the page? (manifest.json is the last thing get_voice.py writes.)
  // A published page says it has no such folder (m.folder === false), which saves asking for a file that is not there.
  step('files'); const man = local = m.folder === false ? null : await fetch(base + 'manifest.json').then(r => r.ok ? r.json() : null).catch(() => null);
  for (const [k, v] of Object.entries(m.voices || {})) voices[k] = v;
  // Which engine. The full-precision model (326 MB; the 8-bit one is 92 MB) can run on a GPU where the browser offers
  // one (WebGPU), and that is many times faster than the processor. The 8-bit model only runs on the processor.
  const size = m.model ? m.model.length : man ? man.bytes : 0, full = size > 2e8;
  const adapter = navigator.gpu ? await navigator.gpu.requestAdapter({ powerPreference: 'high-performance' }).catch(() => null) : null;
  const gpu = navigator.gpu ? (adapter ? 'yes' : 'no adapter') : 'no'; let engine = full && adapter && m.gpu !== false ? 'gpu' : 'cpu', gpuWhy = '';
  // One engine's runtime: the library, its WebAssembly file, and where its glue code is. The GPU runtime comes in two
  // builds: a smaller one (18 MB) for browsers that can suspend WebAssembly (JSPI), and a larger one (29 MB) for the
  // rest. A viewer's frame may refuse to fetch the larger; then the smaller is tried, and failing both the viewer can
  // add the file by hand (m.gpuWasm). null if no WebAssembly file can be had.
  const BUILDS = { cpu: ['ort.js', 'ort.wasm.min.mjs', 'ort-wasm.js', 'ort-wasm-simd-threaded.mjs', 'ort-wasm.wasm', 'ort-wasm-simd-threaded.wasm'],
    jspi: ['ort-jspi.js', 'ort.jspi.min.mjs', 'ort-jspi-wasm.js', 'ort-wasm-simd-threaded.jspi.mjs', 'ort-jspi.wasm', 'ort-wasm-simd-threaded.jspi.wasm'],
    asyncify: ['ort-gpu.js', 'ort.webgpu.min.mjs', 'ort-gpu-wasm.js', 'ort-wasm-simd-threaded.asyncify.mjs', 'ort-gpu.wasm', 'ort-wasm-simd-threaded.asyncify.wasm'] };
  const kinds = typeof WebAssembly.Suspending === 'function' ? ['jspi', 'asyncify'] : ['asyncify']; let gpuKind = '', gpuNeed = '';
  const build = async kind => {
    const f = BUILDS[kind], given = kind === 'cpu' ? m.wasm : m.gpuWasm && m.gpuWasm.kind === kind ? m.gpuWasm.data : null;
    const wasm = given || await grab(man ? base + f[4] : ORT + f[5]).catch(() => null);
    if (!wasm) return null;
    let o; try { o = await import(man ? base + f[0] : ORT + f[1]); } catch (e) { throw new Error('the speech runtime could not be loaded from the ' + (man ? 'page' : 'CDN') + ' (' + why(e) + ')'); }
    o.env.wasm.wasmPaths = { mjs: man ? base + f[2] : ORT + f[3] }; o.env.wasm.wasmBinary = wasm; o.env.wasm.numThreads = threads;
    return o;
  };
  const runtime = async eng => { if (eng === 'cpu') return build('cpu'); for (const k of kinds) { const o = await build(k); if (o) { gpuKind = k; return o; } } gpuNeed = kinds[0]; return null; };
  threads = self.crossOriginIsolated ? Math.min(4, navigator.hardwareConcurrency || 1) : 1;      // more than one thread needs an isolated page
  step('runtime'); from.runtime = man ? 'page' : 'cdn';
  if (engine === 'gpu') { ort = await runtime('gpu').catch(e => { gpuWhy = why(e); return null; }); if (!ort) { engine = 'cpu'; gpuWhy = gpuWhy || 'its runtime file could not be fetched'; } }
  if (engine === 'cpu') ort = await runtime('cpu');
  step('pronouncer');
  try { ({ phonemize } = await import(man ? base + 'phonemizer.js' : PHON)); await phonemize('ready', 'en-us'); } catch (e) { throw new Error('the pronouncer could not be loaded (' + why(e) + ')'); }
  S = await import(base + 'speech.js'); sounds = S.soundsWith(phonemize);                 // what both voices share: pronouncing, pitch, packing a line
  // What only the viewer can supply: the model, at least one voice, and the runtime's WebAssembly file if the CDN would not give it.
  const need = []; if (!ort) need.push('wasm'); if (!m.model && !man) need.push('model'); if (!man && !Object.keys(voices).length) need.push('voice');
  if (need.length) { stage = 'need'; return post({ type: 'need', what: need }); }
  let bytes = m.model;                                                      // from the viewer's file, or handed on by the first worker
  if (!bytes) {
  step('model', { got: 0, of: man.bytes });
  bytes = new Uint8Array(man.bytes); let got = 0, at = 0; const offs = [];
  const sizes = await Promise.all(Array.from({ length: man.parts }, async (_, i) => {
    const r = await fetch(base + 'model.' + i + '.bin'); if (!r.ok) throw new Error('model part ' + i + ': HTTP ' + r.status);
    const chunks = []; let n = 0;
    if (r.body && r.body.getReader) { const rd = r.body.getReader(); for (;;) { const { done, value } = await rd.read(); if (done) break; chunks.push(value); n += value.length; got += value.length; post({ type: 'progress', step: 'model', got, of: man.bytes }); } }
    else { const b = new Uint8Array(await r.arrayBuffer()); chunks.push(b); n = b.length; got += n; post({ type: 'progress', step: 'model', got, of: man.bytes }); }
    return { chunks, n };
  }));
  for (const s of sizes) { offs.push(at); for (const c of s.chunks) { bytes.set(c, at); at += c.length; } }
  if (at !== man.bytes) throw new Error('the model arrived as ' + at + ' bytes, not ' + man.bytes);
  }
  const names = man ? man.voices : Object.keys(voices), v0 = names.includes(m.voice) ? m.voice : names[0];
  const start = async () => {
    session = await ort.InferenceSession.create(bytes, { executionProviders: [engine === 'gpu' ? 'webgpu' : 'wasm'] });
    if (!session.outputNames.includes('durations')) throw new Error('that model file does not report durations; the one needed is from the Kokoro "timestamped" repository');
    await voice(v0); const t = performance.now(), r = await run('ðɪs ɪz ə tˈɛst.', v0);      // the first run is slow: it sets things up (on a GPU it compiles its programs)
    let e = 0, bad = r.wave.length < SR / 2; for (let i = 0; i < r.wave.length; i += 7) { const v = r.wave[i]; if (!(Math.abs(v) < 4)) bad = true; e += v * v; }
    if (bad || !(e > 0) || r.dur.some(d => !(d > 0))) throw new Error('the test line came out wrong');      // a GPU that computes this model badly gives noise or nothing
    return (performance.now() - t) / 1000;
  };
  // (a GPU start that never finishes is given up after two minutes)
  const limited = p => Promise.race([p, new Promise((_, no) => setTimeout(() => no(new Error('it did not start within two minutes')), 120000))]);
  step('starting'); let cold;
  try { cold = await (engine === 'gpu' ? limited(start()) : start()); }
  catch (e) {
    if (engine !== 'gpu') throw new Error('the model could not be started (' + why(e) + ')');
    gpuWhy = why(e); engine = 'cpu'; ort = await runtime('cpu'); if (!ort) throw new Error('the GPU could not run the model (' + gpuWhy + ') and the processor runtime could not be fetched');
    try { cold = await start(); } catch (e2) { throw new Error('the model could not be started (' + why(e2) + ')'); }
  }
  step('warming');
  const t = performance.now(), r = await run('ænd ðɪs ɪz ɐnˈʌðəɹ wˈʌn, tə sˈi hW fˈæst ɪt ɡˈOz.', v0);
  const made = (performance.now() - t) / 1000;
  // two things worth knowing when the voice is slow: how fast this worker's core is at plain arithmetic, and whether a GPU is on offer
  const tl = performance.now(); let acc = 0; for (let i = 0; i < 3e7; i++) acc += Math.sqrt(i) * 1.0000001; const loop = performance.now() - tl + (acc < 0 ? 1 : 0);
  stage = 'ready'; post({ type: 'ready', rtf: (performance.now() - t) / 1000 / (r.wave.length / SR), threads, voices: names, from: from.runtime, model: bytes,
    about: { cold, made, secs: r.wave.length / SR, cores: navigator.hardwareConcurrency || 0, isolated: !!self.crossOriginIsolated, gpu, engine, gpuWhy, gpuKind, gpuNeed, full, loop, bytes: bytes.length } }, [bytes.buffer]);      // the runtime has its own copy now; the page may pass this one on
}
async function voice(name) {
  if (!voices[name]) { if (!local) throw new Error('the voice ' + name + ' has not been added'); const r = await fetch(base + 'v_' + name + '.bin'); if (!r.ok) throw new Error('voice ' + name + ': HTTP ' + r.status); voices[name] = new Float32Array(await r.arrayBuffer()); }
  return voices[name];
}
// The model: sounds in, waveform and one duration per sound out.
async function run(ph, name, speed) {
  const chars = []; for (const ch of ph) if (vocab[ch] != null && chars.length < 508) chars.push(ch);
  const ids = new BigInt64Array(chars.length + 2); chars.forEach((ch, i) => { ids[i + 1] = BigInt(vocab[ch]); });
  const V = await voice(name), row = Math.min(Math.max(chars.length - 1, 0), V.length / 256 - 1);
  const out = await session.run({ input_ids: new ort.Tensor('int64', ids, [1, ids.length]), style: new ort.Tensor('float32', V.slice(row * 256, row * 256 + 256), [1, 256]), speed: new ort.Tensor('float32', Float32Array.of(speed || 1), [1]) });
  const wave = out.waveform.data, dur = Array.from(out.durations.data, d => Math.max(1, Math.round(d)));      // as the model rounds them itself
  const k = wave.length / (dur.reduce((a, b) => a + b, 0) * FRAME);        // 1, give or take a frame
  return { chars, wave, dur: dur.map(d => d * FRAME / SR * k) };
}

/* ── a line ── */
async function say(m) {
  if (m.seq < least) return post({ type: 'skipped', id: m.id, seq: m.seq });
  const t0 = performance.now(), { ph, word, toks } = await sounds(m.text), t1 = performance.now();
  if (!ph) return post({ type: 'said', id: m.id, seq: m.seq, empty: true });
  const { chars, wave, dur } = await run(ph, m.voice, m.speed), took = (performance.now() - t0) / 1000, g2p = (t1 - t0) / 1000;
  // ph and chars are the same characters unless one was unknown to the model; walk them together
  const wmap = []; { let j = 0; const all = Array.from(ph); for (let i = 0; i < all.length && j < chars.length; i++) if (all[i] === chars[j]) { wmap.push(word[i]); j++; } while (wmap.length < chars.length) wmap.push(-1); }
  let t = Math.max(0, dur[0] - EARLY); const times = chars.map((ch, i) => { const r = [t, dur[i + 1]]; t += dur[i + 1]; return r; });
  const out = S.pack({ wave, chars, times, wmap, toks, voice: m.voice, pitches });
  if (!out) return post({ type: 'said', id: m.id, seq: m.seq, empty: true });
  post(Object.assign({ type: 'said', id: m.id, seq: m.seq, took, g2p }, out), [out.audio.buffer]);
}
