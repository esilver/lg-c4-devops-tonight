/* worker.js : the avatar's own voice, made in the browser, with the time of every sound.

   A line of text goes in. Out come the audio (24 kHz) and exactly what the bulletin's engine wants for a line: every
   sound with its start and length, its loudness, the words with their start times and the pitch of the voice, 25 times
   a second. Nothing is guessed: the lengths are the ones the speech model itself used to make the audio.

     text -> sounds     eSpeak NG (through the phonemizer package) says how the words are pronounced; its symbols are
                        rewritten here into the alphabet Kokoro was trained on, which is also the engine's
     sounds -> audio    Kokoro, 8-bit ONNX, run by onnxruntime-web on the processor (WebAssembly); it returns the
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
const VOWEL = 'AIOWYQaiuæɐɑɒɔəɛɜɪʊʌᵻᵊ', VOICED = VOWEL + 'bdɡvzðʒʤmnŋlɹwjT', STRESS = 'ˈˌ';
const KNOWN = VOWEL + 'pbmfvwɹljtdnTszθðʃʒʧʤkɡŋhʔ';    // every sound the engine has a mouth for
let ort, phonemize, session, base, threads = 1, least = 0, local = null, queue = Promise.resolve();
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
  step('files'); const man = local = await fetch(base + 'manifest.json').then(r => r.ok ? r.json() : null).catch(() => null);
  for (const [k, v] of Object.entries(m.voices || {})) voices[k] = v;
  step('runtime');
  if (man) { ort = await import(base + 'ort.js'); from.runtime = 'page'; }
  else { try { ort = await import(ORT + 'ort.wasm.min.mjs'); from.runtime = 'cdn'; } catch (e) { throw new Error('the speech runtime could not be loaded from the CDN (' + why(e) + ')'); } }
  let wasm = m.wasm || null;
  if (!wasm) wasm = await grab(man ? base + 'ort-wasm.wasm' : ORT + 'ort-wasm-simd-threaded.wasm').catch(() => null);
  step('pronouncer');
  try { ({ phonemize } = await import(man ? base + 'phonemizer.js' : PHON)); await phonemize('ready', 'en-us'); } catch (e) { throw new Error('the pronouncer could not be loaded (' + why(e) + ')'); }
  // What only the viewer can supply: the model, at least one voice, and the runtime's WebAssembly file if the CDN would not give it.
  const need = []; if (!wasm) need.push('wasm'); if (!m.model && !man) need.push('model'); if (!man && !Object.keys(voices).length) need.push('voice');
  if (need.length) { stage = 'need'; return post({ type: 'need', what: need }); }
  ort.env.wasm.wasmPaths = { mjs: man ? base + 'ort-wasm.js' : ORT + 'ort-wasm-simd-threaded.mjs' }; ort.env.wasm.wasmBinary = wasm;
  threads = self.crossOriginIsolated ? Math.min(4, navigator.hardwareConcurrency || 1) : 1; ort.env.wasm.numThreads = threads;      // more than one thread needs an isolated page
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
  step('starting'); try { session = await ort.InferenceSession.create(bytes, { executionProviders: ['wasm'] }); } catch (e) { throw new Error('the model could not be started (' + why(e) + ')'); }
  if (!session.outputNames.includes('durations')) throw new Error('that model file does not report durations; the one needed is model_quantized.onnx from the Kokoro "timestamped" repository');
  const names = man ? man.voices : Object.keys(voices), v0 = names.includes(m.voice) ? m.voice : names[0];
  step('warming'); await voice(v0);
  await run('ðɪs ɪz ə tˈɛst.', v0);                                        // the first run is slow (it sets things up); the second is the measure
  const t = performance.now(), r = await run('ænd ðɪs ɪz ɐnˈʌðəɹ wˈʌn, tə sˈi hW fˈæst ɪt ɡˈOz.', v0);
  stage = 'ready'; post({ type: 'ready', rtf: (performance.now() - t) / 1000 / (r.wave.length / SR), threads, voices: names, from: from.runtime, model: bytes }, [bytes.buffer]);      // the runtime has its own copy now; the page may pass this one on
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

/* ── text -> sounds ── */
const SPELL = { '&': ' and ', '%': ' percent ', '+': ' plus ', '@': ' at ', '=': ' equals ' };
const ABBR = [[/\bDr\.(?=\s)/g, 'Doctor'], [/\bMr\.(?=\s)/g, 'Mister'], [/\bMrs\.(?=\s)/g, 'Missus'], [/\bMs\.(?=\s)/g, 'Miz'], [/\bvs\.?(?=\s)/g, 'versus'], [/\betc\.?/g, 'et cetera'], [/\be\.g\./g, 'for example'], [/\bi\.e\./g, 'that is']];
// eSpeak's symbols -> Kokoro's: diphthongs and affricates become one letter, r-coloured vowels are spelled out, length marks go.
function recode(s) {
  return s.replace(/\([a-z-]+\)/g, '').replace(/[ʲ‍͡]/g, '').replace(/r/g, 'ɹ').replace(/[xç]/g, 'k').replace(/ɬ/g, 'l')
    .replace(/ʔˌ?n̩/g, 'tᵊn').replace(/ʔn/g, 'tᵊn').replace(/(\S)̩/g, 'ᵊ$1').replace(/̩/g, '').replace(/ʔ/g, 't')
    .replace(/aɪ/g, 'I').replace(/aʊ/g, 'W').replace(/eɪ/g, 'A').replace(/ɔɪ/g, 'Y').replace(/oʊ/g, 'O').replace(/əʊ/g, 'O').replace(/dʒ/g, 'ʤ').replace(/tʃ/g, 'ʧ')
    .replace(/ɜːɹ/g, 'ɜɹ').replace(/ɜː/g, 'ɜɹ').replace(/ɝ/g, 'ɜɹ').replace(/ɚ/g, 'əɹ').replace(/ɐ/g, 'ə').replace(/oːɹ/g, 'ɔɹ').replace(/o/g, 'ɔ').replace(/e/g, 'ɛ').replace(/a/g, 'ɑ')
    .replace(/ɾ/g, 'T').replace(/ɪə/g, 'iə').replace(/ː/g, '').replace(/ɹɹ/g, 'ɹ').replace(/əl(?![ˈˌɑæʌɔɛɜɪiʊuəAIWYOᵻ])/g, 'ᵊl');
}
// A line becomes clauses (the words up to a comma or a full stop). Each clause is pronounced as a whole, so little words
// are reduced as they are in speech, and its words are matched back to the caption's words for their times.
async function sounds(text) {
  const toks = text.trim().split(/\s+/).filter(Boolean), clauses = []; let cur = { words: [], mark: '' };
  toks.forEach((tok, i) => {
    const core = tok.replace(/^[^\p{L}\p{N}$]+|[^\p{L}\p{N}%]+$/gu, ''), end = tok.slice(tok.lastIndexOf(core) + core.length);
    if (core) cur.words.push({ i, core });
    const mark = (end.match(/[.!?…]/) || end.match(/[,;:—–]/) || (/^[—–-]+$/.test(tok) ? ['—'] : null) || [''])[0];
    if (mark && cur.words.length) { cur.mark = mark === '–' ? '—' : mark; clauses.push(cur); cur = { words: [], mark: '' }; }
  });
  if (cur.words.length) clauses.push(cur);
  let ph = ''; const word = [];                           // for every character of ph: the caption word it belongs to, or -1
  for (const c of clauses) {
    let say = c.words.map(w => w.core).join(' '); for (const [re, to] of ABBR) say = (say + ' ').replace(re, to).trim();
    say = say.replace(/\$(\d[\d,.]*)/g, '$1 dollars').replace(/[&%+@=]/g, ch => SPELL[ch]).replace(/[“”"()\[\]{}*_#`<>|\\]/g, ' ').replace(/[‘’]/g, "'");
    const groups = recode((await phonemize(say, 'en-us')).join(' ')).split(/\s+/).filter(Boolean), G = groups.length, W = c.words.length;
    groups.forEach((g, k) => { const w = c.words[G === W ? k : Math.min(W - 1, Math.floor(k * W / G))].i; if (ph && !ph.endsWith(' ')) { ph += ' '; word.push(-1); } for (const ch of g) { ph += ch; word.push(w); } });
    if (c.mark) { ph += c.mark; word.push(-1); }
  }
  return { ph, word, toks };
}

/* ── audio -> pitch: one value every 20 ms, by autocorrelation at half the sample rate ── */
function pitch(wave) {
  const n = wave.length >> 1, x = new Float32Array(n); for (let i = 0; i < n; i++) x[i] = 0.5 * (wave[2 * i] + wave[2 * i + 1]);
  const sr = SR / 2, W = 600, HOP = 240, lo = Math.floor(sr / 440), hi = Math.ceil(sr / 60), out = [];
  for (let s = 0; s + W + hi < n; s += HOP) {
    let e = 0; for (let i = 0; i < W; i++) e += x[s + i] * x[s + i];
    if (e / W < 1e-5) { out.push(0); continue; }
    let best = 0, lag = 0; const r = new Float32Array(hi + 1);
    for (let L = lo; L <= hi; L++) { let a = 0, b = 0; for (let i = 0; i < W; i++) { a += x[s + i] * x[s + i + L]; b += x[s + i + L] * x[s + i + L]; } r[L] = a / Math.sqrt(e * b + 1e-12); if (r[L] > best) { best = r[L]; lag = L; } }
    for (let d = 2; d <= 4 && lag; d++) { const h = Math.round(lag / d); if (h >= lo && r[h] > 0.88 * best) { lag = h; break; } }      // the same wave fits at twice the period too: prefer the shorter
    out.push(best > 0.5 ? sr / lag : 0);
  }
  return out;                                              // Hz at 20 ms steps; 0 where there is no pitch
}

/* ── a line ── */
async function say(m) {
  if (m.seq < least) return post({ type: 'skipped', id: m.id, seq: m.seq });
  const t0 = performance.now(), { ph, word, toks } = await sounds(m.text);
  if (!ph) return post({ type: 'said', id: m.id, seq: m.seq, empty: true });
  const { chars, wave, dur } = await run(ph, m.voice, m.speed), took = (performance.now() - t0) / 1000;
  // ph and chars are the same characters unless one was unknown to the model; walk them together
  const wmap = []; { let j = 0; const all = Array.from(ph); for (let i = 0; i < all.length && j < chars.length; i++) if (all[i] === chars[j]) { wmap.push(word[i]); j++; } while (wmap.length < chars.length) wmap.push(-1); }
  let t = Math.max(0, dur[0] - EARLY); const seg = [], wt = new Array(toks.length).fill(null); let first = -1, last = 0;
  chars.forEach((ch, i) => {
    const d = dur[i + 1], a = Math.round(t * SR), b = Math.min(wave.length, Math.round((t + d) * SR)); let e = 0; for (let k = a; k < b; k++) e += wave[k] * wave[k];
    const real = KNOWN.includes(ch); seg.push([real || STRESS.includes(ch) || !/\S/.test(ch) || ';:,.!?—…'.includes(ch) ? ch : ' ', t, d, b > a ? Math.sqrt(e / (b - a)) : 0]);
    if (real) { if (first < 0) first = t; last = t + d; }
    if (wmap[i] >= 0 && wt[wmap[i]] == null) wt[wmap[i]] = t;
    t += d;
  });
  if (first < 0) return post({ type: 'said', id: m.id, seq: m.seq, empty: true });
  // trim the silence the model leaves before and after, fade the cuts, and bring every line to the same loudness
  const cut0 = Math.max(0, first - 0.06), cut1 = Math.min(wave.length / SR, last + 0.24), a0 = Math.round(cut0 * SR), audio = wave.slice(a0, Math.round(cut1 * SR)), n = audio.length;
  const vow = seg.filter(s => VOWEL.includes(s[0]) && s[2] > 0).map(s => s[3]).sort((p, q) => p - q), mv = vow.length ? vow[vow.length >> 1] : 0.1, gain = Math.min(3, Math.max(0.4, 0.11 / (mv || 0.1)));
  for (let i = 0; i < n; i++) { let v = audio[i] * gain; const av = Math.abs(v); if (av > 0.6) v = Math.sign(v) * (0.6 + 0.35 * Math.tanh((av - 0.6) / 0.35)); audio[i] = v; }
  for (let i = 0; i < 120 && i < n; i++) audio[i] *= i / 120; for (let i = 0; i < 480 && i < n; i++) audio[n - 1 - i] *= i / 480;
  // pitch, kept only inside voiced sounds, in semitones about this voice's middle, one character per 40 ms as the engine reads it
  const hz = pitch(wave), on = new Uint8Array(hz.length); for (const [ch, at, d] of seg) if (d > 0 && VOICED.includes(ch)) for (let k = Math.max(0, Math.round(at / 0.02) - 1); k <= Math.round((at + d) / 0.02) && k < on.length; k++) on[k] = 1;
  const P = pitches[m.voice] = pitches[m.voice] || []; for (let k = 0; k < hz.length; k++) { if (!on[k]) hz[k] = 0; else if (hz[k]) P.push(hz[k]); } if (P.length > 3000) P.splice(0, P.length - 3000);
  const sorted = P.slice().sort((p, q) => p - q), mid = sorted.length ? sorted[sorted.length >> 1] : 150, st = hz.map(f => f ? 12 * Math.log2(f / mid) : NaN).map(v => Math.abs(v) > 10 ? NaN : v);
  const clean = st.map((v, i) => { if (isNaN(v)) return v; const w = st.slice(Math.max(0, i - 3), i + 4).filter(q => !isNaN(q)).sort((p, q) => p - q); return w.length >= 3 && Math.abs(v - w[w.length >> 1]) > 4 ? NaN : v; });
  let f0 = ''; for (let x = cut0; x < cut1; x += 0.04) { const k = Math.round(x / 0.02), w = [clean[k], clean[k + 1]].filter(v => v != null && !isNaN(v)); f0 += w.length ? String.fromCharCode(78 + Math.max(-24, Math.min(24, Math.round(2 * w.reduce((p, q) => p + q, 0) / w.length)))) : '-'; }
  for (let i = wt.length - 1, nx = last; i >= 0; i--) { if (wt[i] == null) wt[i] = nx; nx = wt[i]; }                 // a word with no sound of its own starts with the next
  const chr = []; { let c = 0; for (const tk of toks) { chr.push(c); c += tk.length + 1; } }
  const r3 = v => Math.round(v * 1000) / 1000;
  post({ type: 'said', id: m.id, seq: m.seq, audio, ph: chars.join(''), took, secs: n / SR,
    sp: { words: toks.map((tk, i) => [tk, r3(Math.max(0, wt[i] - cut0))]), chars: chr, seg: seg.map(s => [s[0], r3(s[1] - cut0), r3(s[2]), Math.round(Math.min(2, s[3] / (mv || 1)) * 100) / 100]), len: r3(n / SR), f0 } }, [audio.buffer]);
}
