/* pocket.js : the avatar's voice copied from a short recording, with the time of every sound measured.

   Pocket TTS (Kyutai, 100M parameters, CC BY 4.0) speaks in a voice it is given a few seconds of. It has no notion of
   when each sound happens, and the engine needs that for the lips. So every line it makes is listened to again by a
   small phone recogniser (ZIPA small, CC BY 4.0), and the line's known sounds are laid over what it hears.

     text -> pieces     the model's SentencePiece file is read here directly; text is cut by the usual best-path search
     pieces -> audio    text conditioner -> language model; then, 12.5 times per second of speech, the model gives a
                        conditioning vector and an end-of-speech score, one step of a flow network turns noise into the
                        next audio latent, and the latent is fed back. The latents go through the audio decoder (24 kHz)
     the voice          the recording, already through the audio encoder (a small file made beforehand), is fed to the
                        language model once; the state that leaves the model in is the voice, reused for every line
     audio -> times     16 kHz -> 80 log mel energies every 10 ms -> the recogniser says, every 20 ms, how likely each
                        of 127 IPA symbols is -> a Viterbi search lays the line's sounds over that -> each boundary is
                        moved to where the next sound becomes the likelier -> silences inside become pauses

   The language model remembers what it has heard and said in a cache per layer. As published the cache has room for
   1000 positions (49 MB in all) and every step copies all of it several times over, which costs more than the
   arithmetic does. A line needs a few hundred positions, so here each line gets a cache of the size it can need
   (freeCache, room): the same numbers come out, in about half the time.

   Both networks are ONNX files run by onnxruntime-web as WebAssembly. All the code that drives them is here. What a
   line ends as (sounds with times, words, pitch, levelled audio) is made by speech.js, as for the other voice.
   Messages in: init, say, cancel. Messages out: progress, need, ready, said, skipped, error. */
const CDN = 'https://cdn.jsdelivr.net/npm/', ORT = CDN + 'onnxruntime-web@1.31.1/dist/', PHON = CDN + 'phonemizer@1.2.1/dist/phonemizer.js';
// the files: what each is for, and its name where it is published
const FILES = { lm: 'flow_lm_main_int8.onnx', flow: 'flow_lm_flow_int8.onnx', dec: 'mimi_decoder_int8.onnx', txt: 'text_conditioner.onnx', tok: 'tokenizer.model', zipa: 'zipa.onnx' };
const SR = 24000, LD = 32, CD = 1024, FPS = 12.5, TEMP = 0.7;      // sample rate; size of a latent and of a conditioning vector; latents a second; how much chance in the voice
// the audio decoder's state between calls: [type, what it starts as (0 zeros, 1 ones), shape], in the order of its inputs
const MIMI = [["b",1,[1]],["f",0,[1,512,6]],["b",1,[1]],["f",0,[1,64,2]],["f",0,[1,256,6]],["b",1,[1]],["f",0,[1,256,2]],["b",1,[1]],["f",0,[1,128,0]],["f",0,[1,128,5]],["b",1,[1]],["f",0,[1,128,2]],["b",1,[1]],["f",0,[1,64,0]],["f",0,[1,64,4]],["b",1,[1]],["f",0,[1,64,2]],["b",1,[1]],["f",0,[1,32,0]],["f",0,[2,1,8,1000,64]],["i",0,[1]],["i",0,[1]],["f",0,[2,1,8,1000,64]],["i",0,[1]],["i",0,[1]],["b",1,[1]],["f",0,[1,512,16]],["b",1,[1]],["f",0,[1,1,6]],["b",1,[1]],["f",0,[1,64,2]],["b",1,[1]],["f",0,[1,32,0]],["b",1,[1]],["f",0,[1,512,2]],["b",1,[1]],["f",0,[1,64,4]],["b",1,[1]],["f",0,[1,128,2]],["b",1,[1]],["f",0,[1,64,0]],["b",1,[1]],["f",0,[1,128,5]],["b",1,[1]],["f",0,[1,256,2]],["b",1,[1]],["f",0,[1,128,0]],["b",1,[1]],["f",0,[1,256,6]],["f",0,[2,1,8,1000,64]],["i",0,[1]],["i",0,[1]],["f",0,[2,1,8,1000,64]],["i",0,[1]],["i",0,[1]],["f",0,[1,512,16]]];
// the recogniser's 127 symbols, in the order of its outputs
const ZTOK = ["<blk>", "<sos/eos>", "<unk>", "▁", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "æ", "ç", "ð", "ø", "ħ", "ŋ", "œ", "ǀ", "ǁ", "ǂ", "ǃ", "ɐ", "ɑ", "ɒ", "ɓ", "ɔ", "ɕ", "ɖ", "ɗ", "ɘ", "ə", "ɛ", "ɜ", "ɞ", "ɟ", "ɠ", "ɢ", "ɣ", "ɤ", "ɥ", "ɦ", "ɧ", "ɨ", "ɪ", "ɬ", "ɭ", "ɮ", "ɯ", "ɰ", "ɱ", "ɲ", "ɳ", "ɴ", "ɵ", "ɶ", "ɸ", "ɹ", "ɺ", "ɻ", "ɽ", "ɾ", "ʀ", "ʁ", "ʂ", "ʃ", "ʄ", "ʈ", "ʉ", "ʊ", "ʋ", "ʌ", "ʍ", "ʎ", "ʏ", "ʐ", "ʑ", "ʒ", "ʔ", "ʕ", "ʘ", "ʙ", "ʛ", "ʜ", "ʝ", "ʟ", "ʡ", "ʢ", "ʰ", "ʲ", "ʷ", "ʼ", "ː", "˞", "ˠ", "ˤ", "̃", "̚", "̥", "̩", "̪", "̴", "̺", "β", "θ", "χ", "ᶑ", "ⱱ"];
// which of them count as each sound of the engine's alphabet (it writes diphthongs and affricates as two symbols)
const CLS = { 'ɑ': 'ɑ a ɒ', 'æ': 'æ a ɛ', 'a': 'a æ ɑ', 'ʌ': 'ʌ ɐ ə', 'ɔ': 'ɔ ɒ o ɑ', 'ɒ': 'ɒ ɑ ɔ', 'ɛ': 'ɛ e', 'ɜ': 'ɜ ə ɹ ˞', 'ɪ': 'ɪ i ɨ', 'i': 'i ɪ', 'ʊ': 'ʊ u', 'u': 'u ʊ ʉ',
  'ə': 'ə ɐ ɨ ɪ ʌ', 'ɐ': 'ɐ ə ʌ', 'ᵊ': 'ə ɨ ̩', 'ᵻ': 'ɨ ɪ ə', 'A': 'e ɪ ɛ', 'I': 'a ɪ ɑ', 'W': 'a ʊ ɑ', 'Y': 'ɔ ɪ o', 'O': 'o ʊ ɔ', 'Q': 'ə ʊ o',
  'l': 'l ̩', 'n': 'n ̩', 't': 't ɾ ʔ ʰ', 'd': 'd ɾ', 'T': 'ɾ t d', 'ʔ': 'ʔ t', 'ɹ': 'ɹ ɻ ˞ r', 'ʤ': 'd ʒ', 'ʧ': 't ʃ', 'ɡ': 'g', 'p': 'p ʰ', 'k': 'k ʰ' };
for (const c of 'bfhjmsvwzŋʃʒðθ') CLS[c] = c;
const ZID = {}; ZTOK.forEach((t, i) => { ZID[t] = i; }); const CID = {}; for (const [k, v] of Object.entries(CLS)) CID[k] = v.split(' ').map(t => ZID[t]).filter(i => i != null);
const LATE = 0.02;                                      // the aligner places sounds 20 ms late (measured twice against known timing: gen/align_small.py check)
let ort, phonemize, S, sounds, base, least = 0, stage = 'start', queue = Promise.resolve(), tokenizer = null, NS = 18, lines = 0, fits = false, full = false;      // fits: caches are made to measure; full: the full-precision files are in use
const ses = {}, voices = {}, pitches = {};
const post = (m, t) => self.postMessage(m, t || []);
self.onmessage = e => {
  const m = e.data;
  if (m.type === 'cancel') { least = m.seq; return; }                     // lines of an abandoned reply are not made
  queue = queue.then(() => m.type === 'init' ? init(m) : m.type === 'say' ? say(m) : null)
    .catch(err => post({ type: 'error', id: m.id, seq: m.seq, at: m.type === 'init' ? stage : 'say', message: String(err && err.message || err) }));
};

/* ── protobuf, read by hand: the fields of a message that lies in b[from, to), as [number, wire type, value or start, end] ── */
function* fields(b, from, to) {
  let i = from; const varint = () => { let v = 0, s = 0; for (;;) { const c = b[i++]; v += (c & 127) * 2 ** s; s += 7; if (c < 128) return v; } };
  while (i < to) { const key = varint(), no = Math.floor(key / 8), wt = key % 8;
    if (wt === 0) yield [no, wt, varint()]; else if (wt === 1) { yield [no, wt, i]; i += 8; } else if (wt === 5) { yield [no, wt, i]; i += 4; }
    else if (wt === 2) { const n = varint(); yield [no, wt, i, i + n]; i += n; } else throw new Error('not a file of the expected kind'); }
}
// The language model's file says its caches hold 1000 positions, but only in the notes on its inputs, outputs and the
// values between: the arithmetic inside takes the size from the cache it is given. Each such note, `dim_value: 1000`
// (bytes 08 E8 07), is rewritten in place as `dim_param: "c"` (12 01 63), a size left open. It is three bytes for
// three, so nothing else in the file moves. Returns how many were changed (0: not that file, and the size stays 1000).
function freeCache(b) {
  let n = 0; const sub = (a, z, no) => { const out = []; for (const f of fields(b, a, z)) if (f[0] === no && f[1] === 2) out.push(f); return out; };
  for (const [, , a, z] of sub(0, b.length, 7))                         // the graph
    for (const f of fields(b, a, z)) if (f[1] === 2 && (f[0] === 11 || f[0] === 12 || f[0] === 13))      // its inputs, outputs and notes on values
      for (const [, , a2, z2] of sub(f[2], f[3], 2)) for (const [, , a3, z3] of sub(a2, z2, 1)) for (const [, , a4, z4] of sub(a3, z3, 2))      // type > tensor > shape
        for (const [, , a5, z5] of sub(a4, z4, 1)) if (z5 - a5 === 3 && b[a5] === 0x08 && b[a5 + 1] === 0xE8 && b[a5 + 2] === 0x07) { b[a5] = 0x12; b[a5 + 1] = 0x01; b[a5 + 2] = 0x63; n++; }
  return n;
}

/* ── the tokenizer: SentencePiece's model file (a small protobuf: pieces with a score and a kind) ── */
function readPieces(buf) {
  const b = new Uint8Array(buf), dv = new DataView(b.buffer, b.byteOffset, b.byteLength), dec = new TextDecoder();
  const pieces = []; let unk = 0, dummy = true, kind = 1;
  for (const [no, wt, a, z] of fields(b, 0, b.length)) {
    if (no === 1) { let piece = '', score = 0, typ = 1; for (const [n2, w2, a2, z2] of fields(b, a, z)) { if (n2 === 1) piece = dec.decode(b.subarray(a2, z2)); else if (n2 === 2) score = dv.getFloat32(a2, true); else if (n2 === 3) typ = a2; } if (typ === 2) unk = pieces.length; pieces.push([piece, score, typ]); }
    else if (no === 2) { for (const [n2, w2, a2] of fields(b, a, z)) if (n2 === 3) kind = a2; }
    else if (no === 3) { for (const [n2, w2, a2] of fields(b, a, z)) if (n2 === 3) dummy = !!a2; }
  }
  if (kind !== 1 || pieces.length < 100) throw new Error('that tokenizer file is not the one for this model');
  const id = new Map(); let longest = 1, floor = 0; pieces.forEach(([p, s, t], i) => { id.set(p, i); longest = Math.max(longest, p.length); if (t === 1) floor = Math.min(floor, s); });
  return { pieces, id, unk, dummy, longest, floor: floor - 10 };
}
function encode(tk, text) {
  const t = (tk.dummy ? '▁' : '') + text.replace(/ /g, '▁'), n = t.length, best = new Float64Array(n + 1).fill(-1e30), back = new Array(n + 1); best[0] = 0;
  for (let i = 0; i < n; i++) {
    if (best[i] < -1e29) continue; let hit = false;
    for (let L = 1; L <= Math.min(tk.longest, n - i); L++) {
      const k = tk.id.get(t.substr(i, L)); if (k == null) continue; const [p, s, typ] = tk.pieces[k]; if (typ !== 1 && typ !== 4) continue;
      if (L === 1) hit = true; const v = best[i] + (typ === 1 ? s : 0); if (v > best[i + L]) { best[i + L] = v; back[i + L] = [i, k]; }
    }
    if (!hit && best[i] + tk.floor > best[i + 1]) { best[i + 1] = best[i] + tk.floor; back[i + 1] = [i, tk.unk]; }
  }
  const out = []; for (let i = n; i > 0;) { const [j, k] = back[i]; out.push(k); i = j; }
  return out.reverse();
}

/* ── starting ── */
// A file published somewhere else (the full-precision model): fetched once, told about as it arrives, and kept in the
// browser's own cache for the next time and for the next worker.
async function far(url, tell) {
  let c = null; try { c = await caches.open('avatar-voice'); const hit = await c.match(url); if (hit) return hit.arrayBuffer(); } catch (e) {}
  const r = await fetch(url); if (!r.ok || !r.body) throw new Error('HTTP ' + r.status);
  const total = +r.headers.get('content-length') || 0, rd = r.body.getReader(), parts = []; let n = 0;
  for (;;) { const { done, value } = await rd.read(); if (done) break; parts.push(value); n += value.length; tell(n, total); }
  const buf = new Uint8Array(n); let at = 0; for (const p of parts) { buf.set(p, at); at += p.length; }
  try { if (c) await c.put(url, new Response(buf, { headers: { 'content-type': 'application/octet-stream' } })); } catch (e) {}
  return buf.buffer;
}
async function init(m) {
  base = m.base; const step = (s, x) => { stage = s; post(Object.assign({ type: 'progress', step: s }, x)); };
  const grab = async url => { const r = await fetch(url); if (!r.ok) throw new Error('HTTP ' + r.status); return r.arrayBuffer(); };
  const why = e => String(e && e.message || e).slice(0, 120);
  // Are the files in a folder beside the page (a page run from a disk), or does the viewer bring them (a published page)?
  step('files'); const man = m.folder === false ? null : await fetch(base + 'pocket/manifest.json').then(r => r.ok ? r.json() : null).catch(() => null);
  step('runtime');
  try { ort = await import(man ? base + 'ort.js' : ORT + 'ort.wasm.min.mjs'); } catch (e) { throw new Error('the speech runtime could not be loaded from the ' + (man ? 'page' : 'CDN') + ' (' + why(e) + ')'); }
  const wasm = m.wasm || await grab(man ? base + 'ort-wasm.wasm' : ORT + 'ort-wasm-simd-threaded.wasm').catch(() => null);
  step('pronouncer');
  try { ({ phonemize } = await import(man ? base + 'phonemizer.js' : PHON)); await phonemize('ready', 'en-us'); } catch (e) { throw new Error('the pronouncer could not be loaded (' + why(e) + ')'); }
  S = await import(base + 'speech.js'); sounds = S.soundsWith(phonemize);
  const have = m.files || {}, far0 = m.from || {}, need = wasm ? [] : ['wasm']; for (const k of Object.keys(FILES)) if (!have[k] && !far0[k] && !man) need.push(k);
  if (!Object.keys(m.voices || {}).length) need.push('voice');
  if (need.length) { stage = 'need'; return post({ type: 'need', what: need }); }
  const threads = !self.crossOriginIsolated ? 1 : m.threads || Math.max(1, Math.min(4, Math.floor((navigator.hardwareConcurrency || 2) / 2)));      // two workers share the cores
  ort.env.wasm.wasmPaths = { mjs: man ? base + 'ort-wasm.js' : ORT + 'ort-wasm-simd-threaded.mjs' }; ort.env.wasm.wasmBinary = wasm; ort.env.wasm.numThreads = threads;
  let got = 0; const total = Object.keys(FILES).length;
  for (const k of Object.keys(FILES)) {
    step('model', { got: got++, of: total });
    let bytes; try { bytes = new Uint8Array(have[k] || (far0[k] ? await far(far0[k], (n, of) => post({ type: 'progress', step: 'model', got: got - 1, of: total, mb: n / 1e6, ofmb: of / 1e6 })) : await grab(base + 'pocket/' + FILES[k]))); }
    catch (e) { throw new Error('the file for "' + k + '" could not be fetched (' + why(e) + ')'); }
    if (k === 'tok') tokenizer = readPieces(bytes);
    else try { if (k === 'lm') { fits = m.fit !== false && freeCache(bytes) > 0; full = bytes.length > 2e8; } ses[k] = await ort.InferenceSession.create(bytes, { executionProviders: ['wasm'] }); } catch (e) { throw new Error('the file for "' + k + '" could not be started (' + why(e) + ')'); }
  }
  NS = ses.lm.inputNames.filter(n => n.startsWith('state_')).length;
  step('starting'); const names = Object.keys(m.voices), t0 = performance.now();
  for (const name of names) voices[name] = await prime(m.voices[name]);
  const primed = (performance.now() - t0) / 1000, v0 = names.includes(m.voice) ? m.voice : names[0];
  step('warming'); const tw = performance.now(); await speak('This is a test.', v0); const cold = (performance.now() - tw) / 1000;      // the first run sets things up
  const t = performance.now(), r = await speak('And this is another one, to see how fast it goes.', v0), made = (performance.now() - t) / 1000;
  const tl = performance.now(); let acc = 0; for (let i = 0; i < 3e7; i++) acc += Math.sqrt(i) * 1.0000001; const loop = performance.now() - tl + (acc < 0 ? 1 : 0);
  stage = 'ready'; post({ type: 'ready', rtf: made / (r.wave.length / SR), threads, voices: names, from: man ? 'page' : 'cdn',
    about: { fits, full, cold, made, secs: r.wave.length / SR, primed, parts: r.parts, cores: navigator.hardwareConcurrency || 0, isolated: !!self.crossOriginIsolated, loop } });
}

/* ── the model ── */
const T = (type, data, dims) => new ort.Tensor(type, data, dims);
const ROW = 16 * 64;                                    // one position in a cache: 16 heads of 64 numbers, kept twice (keys, then values)
const blank = cap => { const s = {}; for (let i = 0; i < NS; i += 3) { s['state_' + i] = T('float32', new Float32Array(2 * cap * ROW).fill(NaN), [2, 1, cap, 16, 64]); s['state_' + (i + 1)] = T('float32', new Float32Array(0), [0]); s['state_' + (i + 2)] = T('int64', new BigInt64Array(1), [1]); } return s; };
const keep = (out, n) => { const s = {}; for (let i = 0; i < n; i++) s['state_' + i] = out['out_state_' + i]; return s; };
// The voice: the language model's state after it has been fed the recording (as the audio encoder wrote it down).
// Its caches are exactly as long as the recording; room() makes the copy a line works in, with space for what follows,
// and makes it longer again whenever the line has filled it (MORE positions at a time).
const MORE = 32;
async function prime(emb) { const n = emb.length / CD, cap = fits ? n : 1000; return { used: n, cap, state: keep(await ses.lm.run(Object.assign({ sequence: T('float32', new Float32Array(0), [1, 0, LD]), text_embeddings: T('float32', emb, [1, n, CD]) }, blank(cap))), NS) }; }
function room(st, used, from, to) {                     // the same state with caches of `to` positions in place of `from`; `used` of them are filled
  if (!fits) return st; const s = Object.assign({}, st);
  for (let i = 0; i < NS; i += 3) { const a = st['state_' + i].data, b = new Float32Array(2 * to * ROW).fill(NaN);
    b.set(a.subarray(0, used * ROW), 0); b.set(a.subarray(from * ROW, (from + used) * ROW), to * ROW); s['state_' + i] = T('float32', b, [2, 1, to, 16, 64]); }
  return s;
}
const tidy = text => { text = text.trim().replace(/\s+/g, ' '); text = text[0].toUpperCase() + text.slice(1); return /[\p{L}\p{N}]$/u.test(text) ? text + '.' : text; };
// One line -> its waveform. Chance comes from a counter, so the same line in the same place comes out the same.
async function speak(text, name) {
  const t0 = performance.now(), ids = encode(tokenizer, tidy(text)), seed = { a: (0x9e3779b9 * (++lines + 1)) >>> 0 };
  const rnd = () => { let t = seed.a += 0x6D2B79F5; t = Math.imul(t ^ t >>> 15, t | 1); t ^= t + Math.imul(t ^ t >>> 7, t | 61); return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  const te = (await ses.txt.run({ token_ids: T('int64', BigInt64Array.from(ids, BigInt), [1, ids.length]) })).embeddings;
  const limit = Math.ceil((ids.length / 3 + 2) * FPS), v = voices[name], said = v.used + ids.length; let cap = said + MORE;      // the most steps this line may take; what the caches hold once the words are in
  let out = await ses.lm.run(Object.assign({ sequence: T('float32', new Float32Array(0), [1, 0, LD]), text_embeddings: T('float32', te.data, [1, ids.length, CD]) }, room(v.state, v.used, v.cap, cap))), state = keep(out, NS);
  const after = (text.trim().split(/\s+/).length <= 4 ? 3 : 1) + 2, none = T('float32', new Float32Array(0), [1, 0, CD]), s0 = T('float32', Float32Array.of(0), [1, 1]), s1 = T('float32', Float32Array.of(1), [1, 1]);
  let cur = T('float32', new Float32Array(LD).fill(NaN), [1, 1, LD]), eos = -1; const lat = [], sd = Math.sqrt(TEMP), t1 = performance.now();
  for (let k = 0; k < limit; k++) {
    if (fits && said + k >= cap) { state = room(state, said + k, cap, cap + MORE); cap += MORE; }
    out = await ses.lm.run(Object.assign({ sequence: cur, text_embeddings: none }, state)); state = keep(out, NS);
    if (out.eos_logit.data[0] > -4 && eos < 0) eos = k;                   // the model says the speech is over; a few more frames let it die away
    if (eos >= 0 && k >= eos + after) break;
    const x = new Float32Array(LD); for (let i = 0; i < LD; i += 2) { const u = Math.max(1e-12, rnd()), v = rnd(), r = sd * Math.sqrt(-2 * Math.log(u)); x[i] = r * Math.cos(2 * Math.PI * v); if (i + 1 < LD) x[i + 1] = r * Math.sin(2 * Math.PI * v); }
    const f = (await ses.flow.run({ c: out.conditioning, s: s0, t: s1, x: T('float32', x, [1, LD]) })).flow_dir.data;      // one step of the flow: noise -> latent
    for (let i = 0; i < LD; i++) x[i] += f[i];
    cur = T('float32', x, [1, 1, LD]); lat.push(x);
  }
  const t2 = performance.now(); let ms = {}; MIMI.forEach(([ty, fill, shape], i) => { const n = shape.reduce((a, b) => a * b, 1); ms['state_' + i] = ty === 'b' ? T('bool', new Uint8Array(n).fill(fill), shape) : ty === 'i' ? T('int64', new BigInt64Array(n), shape) : T('float32', new Float32Array(n).fill(fill), shape); });
  const chunks = []; let total = 0;
  for (let i = 0; i < lat.length; i += 12) { const part = lat.slice(i, i + 12), buf = new Float32Array(part.length * LD); part.forEach((x, j) => buf.set(x, j * LD));
    const o = await ses.dec.run(Object.assign({ latent: T('float32', buf, [1, part.length, LD]) }, ms)); ms = keep(o, MIMI.length); chunks.push(o.audio_frame.data); total += o.audio_frame.data.length; }
  const wave = new Float32Array(total); let at = 0; for (const c of chunks) { wave.set(c, at); at += c.length; }
  const t3 = performance.now(); return { wave, pieces: ids.length, frames: lat.length, parts: { text: (t1 - t0) / 1000, voice: (t2 - t1) / 1000, audio: (t3 - t2) / 1000 } };
}

/* ── when each sound happens ── */
function to16k(x) {                                       // 24 kHz -> 16 kHz: every 1.5 samples, through a low-pass (windowed sinc, 32 taps)
  const n = Math.floor(x.length / 1.5), y = new Float32Array(n), H = 16, fc = 0.62;
  for (let i = 0; i < n; i++) { const t = i * 1.5, k0 = Math.floor(t); let a = 0; for (let k = Math.max(0, k0 - H + 1); k <= k0 + H && k < x.length; k++) { const d = t - k; a += x[k] * (d === 0 ? fc : Math.sin(Math.PI * fc * d) / (Math.PI * d)) * (0.5 + 0.5 * Math.cos(Math.PI * d / H)); } y[i] = a; }
  return y;
}
let MEL = null;
function fbank(a) {                                       // 80 log mel energies every 10 ms, the Kaldi way: 25 ms povey window, pre-emphasis 0.97, 20 to 7600 Hz
  const N = 400, HOP = 160, NF = 512, NM = 80, B = NF / 2 + 1, n = a.length, frames = Math.floor((n + HOP / 2) / HOP), out = new Float32Array(frames * NM);
  if (!MEL) { const mel = f => 1127 * Math.log(1 + f / 700), lo = mel(20), hi = mel(7600); MEL = { w: new Float32Array(NM * B), win: new Float32Array(N), cos: new Float32Array(NF / 2), sin: new Float32Array(NF / 2), rev: new Uint16Array(NF) };
    for (let m = 0; m < NM; m++) { const l = lo + (hi - lo) * m / (NM + 1), c = lo + (hi - lo) * (m + 1) / (NM + 1), r = lo + (hi - lo) * (m + 2) / (NM + 1); for (let k = 0; k < B; k++) { const f = mel(k * 16000 / NF); MEL.w[m * B + k] = Math.max(0, Math.min((f - l) / (c - l), (r - f) / (r - c))); } }
    for (let i = 0; i < N; i++) MEL.win[i] = Math.pow(0.5 - 0.5 * Math.cos(2 * Math.PI * i / (N - 1)), 0.85);
    for (let i = 0; i < NF / 2; i++) { MEL.cos[i] = Math.cos(2 * Math.PI * i / NF); MEL.sin[i] = Math.sin(2 * Math.PI * i / NF); }
    for (let i = 0; i < NF; i++) { let r = 0; for (let b = 0; b < 9; b++) r |= ((i >> b) & 1) << (8 - b); MEL.rev[i] = r; } }
  const re = new Float64Array(NF), im = new Float64Array(NF), fr = new Float64Array(N), pw = new Float64Array(B);
  const at = i => a[i < 0 ? -i : i >= n ? 2 * n - 2 - i : i] || 0;       // the ends are mirrored: frame t is centred on sample t * 160 + 80
  for (let t = 0; t < frames; t++) {
    let mean = 0; for (let i = 0; i < N; i++) { fr[i] = at(t * HOP - 120 + i); mean += fr[i]; } mean /= N;
    for (let i = N - 1; i > 0; i--) fr[i] = (fr[i] - mean) - 0.97 * (fr[i - 1] - mean); fr[0] = (fr[0] - mean) * (1 - 0.97);
    re.fill(0); im.fill(0); for (let i = 0; i < N; i++) re[MEL.rev[i]] = fr[i] * MEL.win[i];
    for (let size = 2; size <= NF; size *= 2) { const half = size / 2, stepk = NF / size; for (let s = 0; s < NF; s += size) for (let j = 0; j < half; j++) { const c = MEL.cos[j * stepk], si = -MEL.sin[j * stepk], p = s + j, q = p + half, xr = re[q] * c - im[q] * si, xi = re[q] * si + im[q] * c; re[q] = re[p] - xr; im[q] = im[p] - xi; re[p] += xr; im[p] += xi; } }
    for (let k = 0; k < B; k++) pw[k] = re[k] * re[k] + im[k] * im[k];
    for (let m = 0; m < NM; m++) { let e = 0; const o = m * B; for (let k = 0; k < B; k++) e += pw[k] * MEL.w[o + k]; out[t * NM + m] = Math.log(Math.max(e, 1.1920929e-07)); }
  }
  return { x: out, frames };
}
// The line's sounds (engine alphabet), in order -> [start, end] in seconds for each.
async function align(wave, phones) {
  const a16 = to16k(wave), { x, frames } = fbank(a16);
  const o = await ses.zipa.run({ x: T('float32', x, [1, frames, 80]), x_lens: T('int64', BigInt64Array.of(BigInt(frames)), [1]) });
  const lp = o.log_probs.data, V = ZTOK.length, TT = Number(o.log_probs_len.data[0]), hop = frames * 0.01 / TT, N = phones.length, NEG = -1e30, Sn = 2 * N + 1;
  const tok = new Float64Array(TT * N); for (let t = 0; t < TT; t++) for (let i = 0; i < N; i++) { let m = NEG; for (const k of CID[phones[i]]) m = Math.max(m, lp[t * V + k]); let s = 0; for (const k of CID[phones[i]]) s += Math.exp(lp[t * V + k] - m); tok[t * N + i] = m + Math.log(s); }
  const E = (t, s) => s % 2 ? tok[t * N + (s >> 1)] : lp[t * V];
  let dp = new Float64Array(Sn).fill(NEG), nx = new Float64Array(Sn); const bp = new Int8Array(TT * Sn); dp[0] = E(0, 0); if (Sn > 1) dp[1] = E(0, 1);
  for (let t = 1; t < TT; t++) { for (let s = 0; s < Sn; s++) { let best = dp[s], k = 0; if (s > 0 && dp[s - 1] > best) { best = dp[s - 1]; k = 1; } if (s > 2 && s % 2 && dp[s - 2] > best) { best = dp[s - 2]; k = 2; } nx[s] = best + E(t, s); bp[t * Sn + s] = k; } const sw = dp; dp = nx; nx = sw; }
  let s = Sn > 1 && dp[Sn - 2] > dp[Sn - 1] ? Sn - 2 : Sn - 1; const path = new Int32Array(TT); path[TT - 1] = s; for (let t = TT - 1; t > 0; t--) { s -= bp[t * Sn + s]; path[t - 1] = s; }
  const first = new Int32Array(N).fill(-1), last = new Int32Array(N).fill(-1); for (let t = 0; t < TT; t++) if (path[t] % 2) { const i = path[t] >> 1; if (first[i] < 0) first[i] = t; last[i] = t; }
  for (let i = 0; i < N; i++) if (first[i] < 0) { let p = 0; for (let j = i - 1; j >= 0; j--) if (last[j] >= 0) { p = last[j]; break; } first[i] = last[i] = p; }      // a sound given no frame of its own sits where the one before it ends
  // the boundary between two neighbours: where, between the frames each is surest of, the second becomes the likelier
  const rel = (t, i) => tok[t * N + i] - Math.log1p(-Math.min(Math.exp(lp[t * V]), 1 - 1e-6)), bounds = [0];
  for (let i = 0; i < N - 1; i++) { const a = last[i], b = first[i + 1]; let cut;
    if (b - a <= 1) cut = b; else { let pos = -1; for (let t = a; t <= b; t++) if (rel(t, i + 1) - rel(t, i) > 0) { pos = t; break; } cut = 0.5 * (pos < 0 ? a + (b - a + 1) / 2 : pos) + 0.5 * (a + b + 1) / 2; }
    bounds.push(Math.max(0, cut * hop - LATE)); }
  bounds.push(wave.length / SR);
  return phones.map((p, i) => [bounds[i], Math.max(bounds[i], bounds[i + 1])]);
}
// Lays the aligner's spans back onto the line as written (with its stress marks, spaces and punctuation). Silence inside
// a sound's stretch is not sound, so its edges are pulled in to where there is signal. Two exceptions: the silence
// before a stop's burst is the stop itself (lips or tongue closed), and a sound too quiet to register at all (an h)
// belongs right against the sound after it. A gap that is still left becomes the pause of the punctuation there, or, if
// it is long and nothing was written, a pause of its own; a short one is shared out.
const STOP = 'pbtdkɡʧʤ';
function settle(wave, ph, word, spans) {
  const F = 240, nf = Math.floor(wave.length / F), rms = new Float32Array(nf); for (let f = 0; f < nf; f++) { let e = 0; for (let i = f * F; i < f * F + F; i++) e += wave[i] * wave[i]; rms[f] = Math.sqrt(e / F); }
  const thr = 0.035 * Array.from(rms).sort((a, b) => a - b)[Math.floor(nf * 0.95)], loud = t => { const f = Math.floor(t * 100); return f >= 0 && f < nf && rms[f] > thr; };
  const all = Array.from(ph), snd = all.filter(ch => CID[ch]);
  const sp = spans.map(([a, b], i) => {
    let heard = false; for (let t = a; t < b; t += 0.01) if (loud(t)) { heard = true; break; }
    if (!heard) return [a, b, false];
    const a0 = a; while (b - a > 0.03 && !loud(a)) a += 0.01; while (b - a > 0.03 && !loud(b - 0.005)) b -= 0.01;
    if (STOP.includes(snd[i])) a = Math.max(a0, a - 0.1);                 // up to a tenth of a second of closure stays with the stop
    return [a, b, true];
  });
  for (let i = sp.length - 2; i >= 0; i--) if (!sp[i][2]) { const nx = sp[i + 1][0], len = Math.min(0.06, Math.max(0.03, sp[i][1] - sp[i][0])); if (nx - sp[i][1] > 0.04 || sp[i][1] > nx) { sp[i][1] = nx; sp[i][0] = Math.max(i ? sp[i - 1][0] : 0, nx - len); } }
  const chars = [], times = [], wmap = []; let k = 0, prevEnd = 0, pending = [];
  const flush = start => {                                // the marks, spaces and stress signs waiting between two sounds
    const gap = Math.max(0, start - prevEnd), mark = pending.findIndex(p => S.MARKS.includes(p.ch)), stop = STOP.includes(snd[k]);
    if (mark < 0 && gap >= (stop ? 0.2 : 0.12) && k > 0) { chars.push(','); times.push([prevEnd, gap]); wmap.push(-1); }
    else if (mark < 0 && gap > 0 && k > 0) { const mid = stop ? prevEnd : prevEnd + gap / 2; for (let j = times.length - 1; j >= 0; j--) if (S.KNOWN.includes(chars[j])) { times[j][1] = mid - times[j][0]; break; } start = mid; }
    pending.forEach((p, j) => { chars.push(p.ch); times.push(j === mark ? [prevEnd, gap] : [start, 0]); wmap.push(p.w); }); pending = []; return start;
  };
  for (let i = 0; i < all.length; i++) {
    const ch = all[i];
    if (CID[ch]) { let [a, b] = sp[k]; a = Math.max(a, prevEnd); b = Math.max(b, a); const st = flush(a); chars.push(ch); times.push([st, Math.max(0, b - st)]); wmap.push(word[i]); prevEnd = Math.max(b, st); k++; }
    else pending.push({ ch, w: word[i] });
  }
  const tail = Math.min(0.3, Math.max(0, wave.length / SR - prevEnd)); pending.forEach(p => { chars.push(p.ch); times.push(S.MARKS.includes(p.ch) ? [prevEnd, tail] : [prevEnd, 0]); wmap.push(p.w); });
  return { chars, times, wmap };
}

/* ── a line ── */
async function say(m) {
  if (m.seq < least) return post({ type: 'skipped', id: m.id, seq: m.seq });
  const t0 = performance.now(), { ph, word, toks } = await sounds(m.text), t1 = performance.now();
  const phones = Array.from(ph).filter(ch => CID[ch]); if (!phones.length) return post({ type: 'said', id: m.id, seq: m.seq, empty: true });
  const r = await speak(m.text, m.voice), t2 = performance.now(), spans = await align(r.wave, phones), t3 = performance.now();
  const out = S.pack(Object.assign({ wave: r.wave, toks, voice: m.voice, pitches }, settle(r.wave, ph, word, spans)));
  if (!out) return post({ type: 'said', id: m.id, seq: m.seq, empty: true });
  post(Object.assign({ type: 'said', id: m.id, seq: m.seq, took: (performance.now() - t0) / 1000, g2p: (t1 - t0) / 1000, parts: Object.assign({ timing: (t3 - t2) / 1000 }, r.parts) }, out), [out.audio.buffer]);
}
