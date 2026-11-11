/* speech.js : what the avatar's voices share, whichever model makes the sound.

   Two workers use it: worker.js (Kokoro, which reports how long each sound lasts) and pocket.js (Pocket TTS, a voice
   copied from a recording, whose sounds are timed afterwards by a small recogniser). Both end with the same thing: a
   waveform, the sounds in it, and when each one happens. From there on the work is the same and is done here:

     text -> sounds     eSpeak NG (through the phonemizer package) says how the words are pronounced; its symbols are
                        rewritten into the alphabet the bulletin's engine uses (it is Kokoro's)
     audio -> pitch     measured from the waveform (autocorrelation), for the nods and brows that follow the voice
     a line, packed     every sound with its start, length and loudness; the words with their start times; the pitch,
                        25 times a second; the silence before and after trimmed; every line at one loudness */
export const SR = 24000;
export const VOWEL = 'AIOWYQaiuæɐɑɒɔəɛɜɪʊʌᵻᵊ', VOICED = VOWEL + 'bdɡvzðʒʤmnŋlɹwjT', STRESS = 'ˈˌ', MARKS = ';:,.!?—…';
export const KNOWN = VOWEL + 'pbmfvwɹljtdnTszθðʃʒʧʤkɡŋhʔ';    // every sound the engine has a mouth for

/* ── text -> sounds ── */
const SPELL = { '&': ' and ', '%': ' percent ', '+': ' plus ', '@': ' at ', '=': ' equals ' };
const ABBR = [[/\bDr\.(?=\s)/g, 'Doctor'], [/\bMr\.(?=\s)/g, 'Mister'], [/\bMrs\.(?=\s)/g, 'Missus'], [/\bMs\.(?=\s)/g, 'Miz'], [/\bvs\.?(?=\s)/g, 'versus'], [/\betc\.?/g, 'et cetera'], [/\be\.g\./g, 'for example'], [/\bi\.e\./g, 'that is']];
// eSpeak's symbols -> Kokoro's: diphthongs and affricates become one letter, r-coloured vowels are spelled out, length marks go.
export function recode(s) {
  return s.replace(/\([a-z-]+\)/g, '').replace(/[ʲ‍͡]/g, '').replace(/r/g, 'ɹ').replace(/[xç]/g, 'k').replace(/ɬ/g, 'l')
    .replace(/ʔˌ?n̩/g, 'tᵊn').replace(/ʔn/g, 'tᵊn').replace(/(\S)̩/g, 'ᵊ$1').replace(/̩/g, '').replace(/ʔ/g, 't')
    .replace(/aɪ/g, 'I').replace(/aʊ/g, 'W').replace(/eɪ/g, 'A').replace(/ɔɪ/g, 'Y').replace(/oʊ/g, 'O').replace(/əʊ/g, 'O').replace(/dʒ/g, 'ʤ').replace(/tʃ/g, 'ʧ')
    .replace(/ɜːɹ/g, 'ɜɹ').replace(/ɜː/g, 'ɜɹ').replace(/ɝ/g, 'ɜɹ').replace(/ɚ/g, 'əɹ').replace(/ɐ/g, 'ə').replace(/oːɹ/g, 'ɔɹ').replace(/o/g, 'ɔ').replace(/e/g, 'ɛ').replace(/a/g, 'ɑ')
    .replace(/ɾ/g, 'T').replace(/ɪə/g, 'iə').replace(/ː/g, '').replace(/ɹɹ/g, 'ɹ').replace(/əl(?![ˈˌɑæʌɔɛɜɪiʊuəAIWYOᵻ])/g, 'ᵊl');
}
// A line becomes clauses (the words up to a comma or a full stop). Each clause is pronounced as a whole, so little words
// are reduced as they are in speech, and its words are matched back to the caption's words for their times.
export const soundsWith = phonemize => async function sounds(text) {
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
};

/* ── audio -> pitch: one value every 20 ms, by autocorrelation at half the sample rate ── */
export function pitch(wave) {
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

/* ── a line, packed for the engine ──
   wave: the audio as the model made it. chars: the line's sounds and marks, one character each. times: for each, its
   start and length in seconds of that audio. wmap: for each, the caption word it belongs to (or -1). toks: the caption's
   words. pitches: the voice's earlier pitch values, by voice (kept by the caller, so its middle is remembered).
   Returns null if there is no sound in it. */
export function pack({ wave, chars, times, wmap, toks, voice, pitches }) {
  const seg = [], wt = new Array(toks.length).fill(null); let first = -1, last = 0;
  chars.forEach((ch, i) => {
    const [t, d] = times[i], a = Math.max(0, Math.round(t * SR)), b = Math.min(wave.length, Math.round((t + d) * SR)); let e = 0; for (let k = a; k < b; k++) e += wave[k] * wave[k];
    const real = KNOWN.includes(ch); seg.push([real || STRESS.includes(ch) || !/\S/.test(ch) || MARKS.includes(ch) ? ch : ' ', t, d, b > a ? Math.sqrt(e / (b - a)) : 0]);
    if (real) { if (first < 0) first = t; last = t + d; }
    if (wmap[i] >= 0 && wt[wmap[i]] == null) wt[wmap[i]] = t;
  });
  if (first < 0) return null;
  // trim the silence the model leaves before and after, fade the cuts, and bring every line to the same loudness
  const cut0 = Math.max(0, first - 0.06), cut1 = Math.min(wave.length / SR, last + 0.24), a0 = Math.round(cut0 * SR), audio = wave.slice(a0, Math.round(cut1 * SR)), n = audio.length;
  const vow = seg.filter(s => VOWEL.includes(s[0]) && s[2] > 0).map(s => s[3]).sort((p, q) => p - q), mv = vow.length ? vow[vow.length >> 1] : 0.1, gain = Math.min(12, Math.max(0.4, 0.11 / (mv || 0.1)));
  for (let i = 0; i < n; i++) { let v = audio[i] * gain; const av = Math.abs(v); if (av > 0.6) v = Math.sign(v) * (0.6 + 0.35 * Math.tanh((av - 0.6) / 0.35)); audio[i] = v; }
  for (let i = 0; i < 120 && i < n; i++) audio[i] *= i / 120; for (let i = 0; i < 480 && i < n; i++) audio[n - 1 - i] *= i / 480;
  // pitch, kept only inside voiced sounds, in semitones about this voice's middle, one character per 40 ms as the engine reads it
  const hz = pitch(wave), on = new Uint8Array(hz.length); for (const [ch, at, d] of seg) if (d > 0 && VOICED.includes(ch)) for (let k = Math.max(0, Math.round(at / 0.02) - 1); k <= Math.round((at + d) / 0.02) && k < on.length; k++) on[k] = 1;
  const P = pitches[voice] = pitches[voice] || []; for (let k = 0; k < hz.length; k++) { if (!on[k]) hz[k] = 0; else if (hz[k]) P.push(hz[k]); } if (P.length > 3000) P.splice(0, P.length - 3000);
  const sorted = P.slice().sort((p, q) => p - q), mid = sorted.length ? sorted[sorted.length >> 1] : 150, st = hz.map(f => f ? 12 * Math.log2(f / mid) : NaN).map(v => Math.abs(v) > 10 ? NaN : v);
  const clean = st.map((v, i) => { if (isNaN(v)) return v; const w = st.slice(Math.max(0, i - 3), i + 4).filter(q => !isNaN(q)).sort((p, q) => p - q); return w.length >= 3 && Math.abs(v - w[w.length >> 1]) > 4 ? NaN : v; });
  let f0 = ''; for (let x = cut0; x < cut1; x += 0.04) { const k = Math.round(x / 0.02), w = [clean[k], clean[k + 1]].filter(v => v != null && !isNaN(v)); f0 += w.length ? String.fromCharCode(78 + Math.max(-24, Math.min(24, Math.round(2 * w.reduce((p, q) => p + q, 0) / w.length)))) : '-'; }
  for (let i = wt.length - 1, nx = last; i >= 0; i--) { if (wt[i] == null) wt[i] = nx; nx = wt[i]; }                 // a word with no sound of its own starts with the next
  const chr = []; { let c = 0; for (const tk of toks) { chr.push(c); c += tk.length + 1; } }
  const r3 = v => Math.round(v * 1000) / 1000;
  return { audio, ph: chars.join(''), secs: n / SR,
    sp: { words: toks.map((tk, i) => [tk, r3(Math.max(0, wt[i] - cut0))]), chars: chr, seg: seg.map(s => [s[0], r3(s[1] - cut0), r3(s[2]), Math.round(Math.min(2, s[3] / (mv || 1)) * 100) / 100]), len: r3(n / SR), f0 } };
}
