/* ── DevOps Tonight: photographic stills, brought to life in plain JavaScript ──
   Every frame is composited here: a background plate, a cut-out presenter, mouth and eye poses blended from a
   dense set of renders of the same face, a mesh that turns and nods the head, moves the brows, lets the torso
   breathe and shift and the hair swing, camera moves, grain and graphics. The voice drives it: each line carries a
   recording, the timing of every sound in it and the pitch of the voice, which become jaw, lip, brow, head and
   body movement. */
const ACC = '#2ee6a6';
const ASSETS = /*ASSETS*/{ img: {}, cast: {} };
const SPEECH = /*SPEECH*/[];         // per spoken line: the audio, caption words with start times, every phoneme with start, length, loudness, and the voice's pitch
const FW = 1024, FH = 576;
const CAST = {
  paige: { name: 'PAIGE DUTY', role: 'Anchor · on call tonight' },
  cy:    { name: 'CY DEKAR', role: 'Anchor' },
  dee:   { name: 'DEE PLOY', role: 'Reporting live from us-east-1' },
  sunny: { name: 'SUNNY UPTIME', role: 'Cloud forecast' },
  mel:   { name: 'Y. A. MEL', role: 'Staff YAML Engineer' },
};
// Each line may add: lead (seconds of listening before the voice starts; a live cross has a satellite delay),
// sm [who, from, to, strength] smiles as fractions of the line, look [fromWord, toWord, eyes x, eyes y, head turn],
// shake [fromWord, toWord] a slow shake of the head, grave [fromWord, toWord] lowered brows.
const SHOW = [
  { intro: 5 },
  { who: 'paige', sm: [['paige', 0, 0.24, 0.9], ['paige', 0.88, 1, 1]], text: "Good evening, this is DevOps Tonight. I'm Paige Duty, and yes, I am on call." },
  { who: 'cy', lead: 0.22, sm: [['cy', 0.86, 1, 1]], text: "And I'm Cy Dekar. It is 2026, and production is, for the moment, up." },
  { who: 'paige', lead: 0.45, ots: ['office', 'AGENTS REVIEW AGENTS'], cuts: [[16, null, 'paged']], text: 'Our top story: an AI agent opened forty pull requests overnight. A second agent approved them. A human is now being paged.' },
  { who: 'cy', lead: 0.4, ots: ['dcext', 'FRIDAY DEPLOY'], look: [[16, 17, -0.85, 0.1, -0.45]], text: 'Meanwhile, a routine Friday deploy is under way in us-east-1. Dee Ploy is at the scene. Dee?' },
  { who: 'dee', lead: 0.95, live: 'us-east-1', cuts: [[0, 2, 'dcext']], shake: [[14, 17]], text: 'Thanks, Cy. The pipeline behind me has been green for nine minutes, and nobody here trusts it.' },
  { who: 'dee', live: 'us-east-1', cuts: [[0, 10, 'servers']], text: 'Engineers have checked the dashboards, the rollback plan, and DNS. Sources say it is always DNS.' },
  { who: 'cy', lead: 0.35, split: ['cy', 'dee'], title: 'LIVE · us-east-1', text: 'Dee, did anyone suggest waiting until Monday?' },
  { who: 'dee', lead: 0.85, split: ['cy', 'dee'], title: 'LIVE · us-east-1', sm: [['cy', 0.5, 1, 1], ['dee', 0.8, 1, 0.8]], text: 'One person did, Cy. They have been moved to the platform team. Back to you.' },
  { who: 'paige', lead: 0.4, ots: ['sat', 'CLOUD FORECAST'], sm: [['paige', 0, 0.2, 1], ['paige', 0.72, 1, 0.9]], look: [[7, 9, 0.8, 0.05, 0.4]], text: 'Brave work. Now the cloud forecast, with Sunny Uptime.' },
  { who: 'sunny', wx: 0, sm: [['sunny', 0, 0.2, 1]], look: [[5, 9, 0.8, 0.05, 0.5]], text: 'Thanks, Paige. Pods are stuck Pending across the north while the autoscaler thinks about it.' },
  { who: 'sunny', wx: 1, sm: [['sunny', 0.78, 1, 1]], look: [[1, 3, 0.8, 0.1, 0.5], [10, 13, 0.8, 0.02, 0.45]], text: 'In the south, scattered 503s with a chance of retries. Four nines along the coast, and a high of nine thousand dollars in egress.' },
  { who: 'cy', lead: 0.45, split: ['cy', 'mel'], title: 'THE BIG INTERVIEW', text: 'Joining us is Y. A. Mel, Staff YAML Engineer. With agents writing the config now, is your job safe?' },
  { who: 'mel', lead: 0.6, split: ['cy', 'mel'], title: 'THE BIG INTERVIEW', sm: [['cy', 0.75, 1, 0.8]], text: 'Cy, the agent writes four thousand lines of YAML a day. Someone still has to find the one wrong indent.' },
  { who: 'cy', lead: 0.5, split: ['cy', 'mel'], title: 'THE BIG INTERVIEW', shake: [[0, 1]], grave: [[0, 1]], sm: [['mel', 0.45, 1, 0.8]], text: 'Chilling. Thank you for your time.' },
  { who: 'paige', lead: 0.45, sm: [['paige', 0.9, 1, 1]], text: "That's all for tonight. Remember: you build it, you run it, and FinOps will ask what it cost." },
  { who: 'cy', lead: 0.3, sm: [['cy', 0.42, 1, 1]], text: 'From all of us in the control plane, good night, and may your pager stay quiet.' },
  { outro: 4.5 },
];
const ease = p => p * p * (3 - 2 * p), clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const frac = v => v - Math.floor(v), hash = (a, b) => frac(Math.sin(a * 12.9898 + b * 78.233) * 43758.5453);
const wob = (t, s) => Math.sin(t * 1.3 + s) * 0.6 + Math.sin(t * 2.9 + s * 1.7) * 0.3 + Math.sin(t * 5.1 + s * 0.3) * 0.1;
const gauss = (x, s) => Math.exp(-x * x / (s * s)), rise = (x, a, b) => ease(clamp((x - a) / (b - a), 0, 1));

/* ── speech ──
   Three things move a mouth, at different speeds, and they are kept apart here:
     the jaw    opens for vowels and follows syllables; consonants only pull it part of the way;
     the lips   close fully for p, b, m and almost for f, v: short, crisp, and exactly on time;
     the shape  rounds (oo, w, sh) or spreads (ee), and starts changing a sound early.
   Each sound has: [jaw 0..1, shape -1 round .. +1 spread, how firmly it holds its jaw, how firmly its shape,
   second target for diphthongs, lip closure]. The symbols are the phoneme alphabet of the speech model that voiced
   the first recordings (capital letters are diphthongs, T is a flapped t). */
const VIS = {
  'ɑ': [.85, 0, 1, .6], 'æ': [.74, .35, 1, .8], 'a': [.78, .2, 1, .7], 'ʌ': [.5, 0, 1, .5], 'ɔ': [.62, -.5, 1, 1], 'ɒ': [.66, -.35, 1, .9], 'ɛ': [.5, .4, 1, .8],
  'ɜ': [.3, -.45, 1, .9], 'ɪ': [.32, .5, 1, .8], 'i': [.24, .9, 1, 1], 'ʊ': [.26, -.75, 1, 1], 'u': [.2, -1, 1, 1],
  'ə': [.3, 0, .8, .4], 'ɐ': [.36, 0, .8, .4], 'ᵊ': [.2, 0, .5, .3], 'ᵻ': [.26, .4, .8, .6],
  'A': [.46, .5, 1, .9, [.26, .8]], 'I': [.78, .05, 1, .7, [.3, .7]], 'W': [.75, .1, 1, .7, [.25, -.9]], 'Y': [.55, -.7, 1, 1, [.28, .7]],
  'O': [.5, -.6, 1, 1, [.22, -1]], 'Q': [.4, -.2, 1, .8, [.22, -1]],
  'p': [.1, 0, .2, .15, 0, 1], 'b': [.1, 0, .2, .15, 0, 1], 'm': [.1, 0, .2, .15, 0, 1], 'f': [.12, .2, .3, .5, 0, .72], 'v': [.12, .2, .3, .5, 0, .72],
  'w': [.14, -1, .6, 1], 'ɹ': [.24, -.45, .35, .7], 'l': [.3, .1, .3, .3], 'j': [.2, .7, .4, .7], 't': [.16, .3, .45, .4], 'd': [.16, .3, .45, .4], 'n': [.16, .3, .45, .4], 'T': [.22, .2, .25, .2],
  's': [.1, .35, .6, .5], 'z': [.1, .35, .6, .5], 'θ': [.2, .15, .4, .3], 'ð': [.2, .15, .4, .3], 'ʃ': [.16, -.55, .55, .9], 'ʒ': [.16, -.55, .55, .9],
  'ʧ': [.16, -.55, .55, .9], 'ʤ': [.16, -.55, .55, .9], 'k': [.3, 0, .15, .1], 'ɡ': [.3, 0, .15, .1], 'ŋ': [.25, 0, .2, .1], 'h': [.35, 0, .1, .1], 'ʔ': [.2, 0, .2, .1],
};
const FULL = 'ɑæaʌɔɒɛɜɪiʊuAIWYOQ', WEAK = 'əɐᵊᵻ', LEAD = 0.28, TAIL = 0.26, DT = 1 / 120;
const STYLE = { paige: 1, cy: 0.9, dee: 1.2, sunny: 1.25, mel: 0.85 };       // how much each presenter moves
// How each one carries the body: sway (how far the torso drifts and shifts; more when standing), the spring that free
// hair hangs on (cycles a second, damping) and how far it swings, and wind for the reporter outdoors.
const BODY = {
  paige: { sway: 1, hz: 1.8, damp: 0.32, hair: 1.6 }, cy: { sway: 0.75, hz: 4, damp: 0.5, hair: 0.8 }, dee: { sway: 2, hz: 3.4, damp: 0.42, hair: 1.1, wind: 1 },
  sunny: { sway: 1.8, hz: 2.4, damp: 0.38, hair: 1.5 }, mel: { sway: 0.9, hz: 4, damp: 0.5, hair: 0 },
};
// Monotone cubic interpolation: the curve glides through every target without overshooting.
function slopes(T, Y) {
  const n = T.length, d = [], m = new Array(n).fill(0);
  for (let i = 0; i < n - 1; i++) d.push((Y[i + 1] - Y[i]) / (T[i + 1] - T[i]));
  for (let i = 1; i < n - 1; i++) if (d[i - 1] * d[i] > 0) { const a = T[i] - T[i - 1], z = T[i + 1] - T[i], w1 = 2 * z + a, w2 = z + 2 * a; m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i]); }
  return m;
}
function curve(T, Y, M, t) {
  const n = T.length; if (t <= T[0]) return Y[0]; if (t >= T[n - 1]) return Y[n - 1];
  let lo = 0, hi = n - 1; while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (T[mid] <= t) lo = mid; else hi = mid; }
  const h = T[hi] - T[lo], u = (t - T[lo]) / h, u2 = u * u, u3 = u2 * u;
  return (2 * u3 - 3 * u2 + 1) * Y[lo] + (u3 - 2 * u2 + u) * h * M[lo] + (3 * u2 - 2 * u3) * Y[hi] + (u3 - u2) * h * M[hi];
}
// A track sampled 120 times a second: built from targets, then smoothed forwards and backwards so nothing moves faster than a face can.
function track(T, Y, n, tau) {
  for (let i = 1; i < T.length; i++) if (T[i] <= T[i - 1]) T[i] = T[i - 1] + 0.004;
  const M = slopes(T, Y), v = new Float32Array(n); for (let i = 0; i < n; i++) v[i] = curve(T, Y, M, i * DT);
  return smooth(v, tau);
}
function smooth(v, tau) {
  const k = 1 - Math.exp(-DT / tau); for (let i = 1; i < v.length; i++) v[i] = v[i - 1] + k * (v[i] - v[i - 1]);
  for (let i = v.length - 2; i >= 0; i--) v[i] = v[i + 1] + k * (v[i] - v[i + 1]); return v;
}
const samp = (v, t) => { const x = clamp(t / DT, 0, v.length - 1.001), i = Math.floor(x); return v[i] + (v[i + 1] - v[i]) * (x - i); };
// The voice's pitch: one character per 40 ms, in half semitones about the speaker's median ('-' where there is no voice).
// Gaps are bridged and the contour smoothed; brows and head follow it.
function pitchTrack(str) {
  const n = str.length, p = new Float32Array(n + 1); let last = -1;
  for (let i = 0; i < n; i++) {
    const c = str.charCodeAt(i); if (c === 45) continue; p[i] = (c - 78) / 2;
    if (last >= 0 && i - last > 1) for (let j = last + 1; j < i; j++) p[j] = i - last > 12 ? 0 : p[last] + (p[i] - p[last]) * (j - last) / (i - last);
    last = i;
  }
  for (let k = 0; k < 2; k++) { let a = p[0]; for (let i = 0; i < n; i++) { const b = p[i]; p[i] = (a + 2 * b + p[i + 1]) / 4; a = b; } }
  return p;
}
const pitchAt = (b, bt) => { const x = (bt - b.lead) * 25, i = Math.floor(x); return x < 0 || i >= b.pc.length - 1 ? 0 : b.pc[i] + (b.pc[i + 1] - b.pc[i]) * (x - i); };
// Per presenter, on the show's clock: where head and body rest, phrase by phrase; the breath; and when they speak.
const POSE = {}, BREATH = {}, SPOKE = {}, BLINK = {}, POSE0 = [{ t: -9, y: 0, p: 0, r: 0, x: 0, w: 0, l: 0 }];
function buildSpeech(b) {
  const sp = b.sp, L = b.lead, segs = [], pauses = [], acc = [], who = b.who, sty = STYLE[who] || 1;
  b.words = sp.words.map(w => w[0]); b.wt = sp.words.map(w => w[1] + L); b.text = b.words.join(' '); b.pc = pitchTrack(sp.f0 || '');
  let st = 0, carry = 0;                                         // stress of the coming vowel; time taken by its stress mark
  for (const [ch, at, len, loud] of sp.seg) {
    if (ch === 'ˈ' || ch === 'ˌ') { st = ch === 'ˈ' ? 1 : 2; carry += len; continue; }
    if (ch === ' ') continue;                                    // word gaps: time simply passes
    const t0 = at - carry + L, d = len + carry, k = VIS[ch]; carry = 0;
    if (ch === 'ː') { if (segs.length) segs[segs.length - 1].d += d; continue; }                // a length mark stretches the vowel before it
    if (!k) {                                                    // punctuation is a pause, if it lasts
      if (d > 0.04) segs.push({ t0, d, o: 0, s: 0, wo: 0.6, ws: 0.3, c: 0, pause: true });
      if (d >= 0.1 || '.?!:'.includes(ch)) pauses.push([t0, t0 + d, ch]); st = 0; continue;
    }
    if (d <= 0) continue;
    const g = { t0, d, o: k[0], s: k[1], wo: k[2], ws: k[3], c: k[5] || 0, ch };
    if (FULL.includes(ch) || WEAK.includes(ch)) {
      // louder syllables open wider; unstressed ones are reduced;
      // and a vowel that is over in a few hundredths of a second never gets as far as its full opening
      const amp = (WEAK.includes(ch) ? 0.85 : st === 1 ? 1 : st === 2 ? 0.86 : 0.66) * clamp(0.74 + 0.32 * loud, 0.62, 1.25) * clamp(0.45 + 0.55 * d / 0.12, 0.5, 1);
      if (st) {                                                  // how much this syllable stands out: loudness, pitch, length
        let pk = -9; for (let t = t0; t <= t0 + d + 0.001; t += 0.02) pk = Math.max(pk, pitchAt(b, t));
        acc.push([t0 + d * 0.4, clamp(0.5 * (loud - 0.6) / 0.9 + 0.35 * (pk + 1) / 6 + 0.15 * d / 0.16, 0, 1) * (st === 1 ? 1 : 0.7), pk]);
      }
      g.o *= amp; g.vowel = true; segs.push(g);
      if (k[4]) { g.d = d * 0.55; segs.push({ t0: t0 + d * 0.55, d: d * 0.45, o: k[4][0] * amp, s: k[4][1], wo: 0.9, ws: k[3], c: 0, ch, vowel: true }); }
      st = 0;
    } else segs.push(g);
  }
  const said = segs.filter(g => !g.pause), first = said[0].t0, lastEnd = said[said.length - 1].t0 + said[said.length - 1].d, end = L + sp.len;
  b.t0 = first; b.t1 = lastEnd; b.dur = end + (b.tail == null ? TAIL : b.tail); const n = Math.ceil(b.dur / DT) + 2;
  // jaw and shape: a weakly articulated sound takes most of its value from its neighbours
  const T = [0, Math.max(0.02, first - 0.3), Math.max(0.04, first - 0.07)], O = [0, 0, 0.07], S = [0, 0, 0];             // lips part for a breath
  segs.forEach((g, i) => {
    const nb = (k, w) => { let v = 0, dn = 0; for (const q of [segs[i - 1], segs[i + 1]]) if (q) { v += q[k] * q[w]; dn += q[w]; } return dn ? v / dn : g[k]; };
    const o = g.wo * g.o + (1 - g.wo) * nb('o', 'wo'), sh = g.ws * g.s + (1 - g.ws) * nb('s', 'ws');
    if (g.pause && g.d > 0.12) {                                 // the mouth comes to rest, and parts again just before the next phrase
      T.push(g.t0 + Math.min(0.09, g.d * 0.4)); O.push(0); S.push(0);
      if (g.d >= 0.3) { T.push(g.t0 + g.d - 0.2, g.t0 + g.d - 0.06); O.push(0, 0.07); S.push(0, 0); } else { T.push(g.t0 + g.d - 0.04); O.push(0.02); S.push(0); }
    } else if (g.vowel && g.d > 0.14) { T.push(g.t0 + g.d * 0.3, g.t0 + g.d * 0.72); O.push(o, o); S.push(sh, sh); }
    else { T.push(g.t0 + g.d * (g.vowel ? 0.45 : 0.5) - (Math.abs(g.s) > 0.5 && g.ws > 0.8 ? 0.03 : 0)); O.push(o); S.push(sh); }      // rounding arrives early
  });
  T.push(Math.max(lastEnd, T[T.length - 1] + 0.05) + 0.12); O.push(0); S.push(0);
  b.J = track(T.slice(), O, n, 0.014); b.S = track(T, S, n, 0.02); b.taught = false;
  if (sp.lip) {
    // A learned reference takes over from the rules above. A lip-sync network (trained on real talking faces) was shown this
    // recording and this face; its mouth was measured 50 times a second and translated into this presenter's own poses, so
    // the opening and the lip shape here are what that network drew, not what a table of sounds says. One character a sample.
    const f = sp.lip.fps, dec = (str, span, lo) => Float32Array.from(str, ch => (ch.charCodeAt(0) - 40) / 85 * span + lo), to = dec(sp.lip.o, 1.42, -0.12), ts = dec(sp.lip.s, 2, -1);
    const at = (v, t) => { const x = clamp((t - L) * f, 0, v.length - 1.001), i = Math.floor(x); return v[i] + (v[i + 1] - v[i]) * (x - i); };
    for (let i = 0; i < n; i++) { const t = i * DT, on = t >= L && t <= L + sp.len, br = 0.07 * rise(t, first - 0.3, first - 0.07) * (1 - rise(t, first - 0.02, first + 0.06)); b.J[i] = on ? Math.max(at(to, t), br) : br; b.S[i] = on ? at(ts, t) : 0; }
    // In a pause the mouth comes to rest whatever the reference drew (it tends to leave the lips apart): nearly shut in a
    // long pause, a little parted in a short one, shut before the first sound and after the last.
    for (const g of segs) if (g.pause) {
      const keep = g.d > 0.5 ? 0.1 : 0.4;
      for (let i = Math.max(0, Math.floor((g.t0 - 0.02) / DT)); i < Math.min(n, Math.ceil((g.t0 + g.d + 0.02) / DT)); i++) { const t = i * DT; b.J[i] *= 1 - (1 - keep) * rise(t, g.t0, g.t0 + 0.09) * (1 - rise(t, g.t0 + g.d - 0.09, g.t0 + g.d)); }
    }
    for (let i = 0; i < n; i++) { const t = i * DT; if (t < first) b.J[i] = Math.min(b.J[i], 0.07 + 0.6 * rise(t, first - 0.06, first)); if (t > lastEnd) b.J[i] *= 1 - rise(t, lastEnd + 0.03, lastEnd + 0.2); }
    smooth(b.J, 0.01); smooth(b.S, 0.025); b.taught = true;
  }
  // lip closures: shut by the time the sound starts, held to the release, never shorter than two frames of video
  const C = b.C = new Float32Array(n);
  for (const g of segs) if (g.c) {
    let h0 = g.t0, h1 = Math.max(g.t0 + g.d * (g.ch === 'm' ? 1 : g.ch === 'p' ? 0.7 : 0.85), g.t0 + 0.055);
    let rin = 0.05 + 0.07 * Math.min(1, samp(b.J, h0 - 0.05)), rout = 0.04 + 0.05 * Math.min(1, samp(b.J, h1 + 0.05));          // a wide-open mouth needs longer to shut
    if (b.taught) {
      // With a reference the mouth already closes for these sounds, in its own time. All that is added is the guarantee
      // that the lips truly meet for m, b and p: a short press in the middle of the sound, quick in and out so that a
      // short vowel next to it is not swallowed. (The long ramps above did swallow them: the "o" of "DevOps" vanished.)
      // For p and b the press sits just before the release at the end of the sound (the timing gives a "p" after a pause
      // the whole pause, and a press in the middle of that shut an open mouth a fifth of a second early).
      if (g.c < 1) continue;
      if (g.ch === 'm') { h0 = g.t0 + 0.12 * g.d; h1 = Math.min(g.t0 + 0.85 * g.d, h0 + 0.12); } else { h1 = g.t0 + g.d - 0.025; h0 = Math.max(g.t0 + 0.12 * g.d, h1 - 0.07); }
      if (h1 - h0 < 0.04) h0 = h1 - 0.04;
      rin = 0.03 + 0.06 * clamp(samp(b.J, h0), 0, 1); rout = 0.03 + 0.04 * clamp(samp(b.J, h1), 0, 1);       // slower where the reference still has the mouth open
    }
    for (let i = Math.max(0, Math.floor((h0 - rin) / DT)); i < Math.min(n, Math.ceil((h1 + rout) / DT)); i++) { const t = i * DT; C[i] = Math.max(C[i], g.c * rise(t, h0 - rin, h0) * (1 - rise(t, h1, h1 + rout))); }
  }
  smooth(C, 0.005);
  // ── movement that follows the voice ──
  // phrases: stretches of speech between pauses
  const phr = []; let ps = first;
  for (const p of pauses) { if (p[0] - ps > 0.25) phr.push([ps, p[0], p[2]]); ps = Math.max(ps, p[1]); }
  if (lastEnd - ps > 0.25) phr.push([ps, lastEnd, '.']);
  if (!phr.length) phr.push([first, lastEnd, '.']);
  const mo = b.mo = { nods: [], brows: [], frowns: [], back: [], blinks: [], phr, first };
  // the syllables that stand out most carry a nod; the highest and strongest of them lift the brows
  for (const a of acc) if (a[1] >= 0.45 && !acc.some(q => q !== a && Math.abs(q[0] - a[0]) < 0.45 && q[1] > a[1])) mo.nods.push([a[0], a[1], hash(a[0], b.ai) < 0.5 ? -1 : 1]);
  // the other stressed syllables are felt in the head too, a third as far: it keeps time with the speech between the nods
  for (const a of acc) if (a[1] >= 0.2 && !mo.nods.some(q => Math.abs(q[0] - a[0]) < 0.3)) mo.nods.push([a[0], 0.32 * a[1], hash(a[0], b.ai + 1) < 0.5 ? -1 : 1, 1]);
  for (const a of acc) {
    const far = k => !k.some(q => Math.abs(q[0] - a[0]) < 1.3);
    if (a[1] >= 0.7 && a[2] >= 1.5 && far(mo.brows)) mo.brows.push([a[0], 0.3 + 0.35 * clamp((a[1] - 0.7) / 0.3, 0, 1), 0.1 + 0.25 * hash(a[0], 3)]);
    else if (a[1] >= 0.6 && a[2] <= -1 && far(mo.frowns)) mo.frowns.push([a[0], 0.3, 0.15]);
  }
  for (const p of phr) if (p[2] === '?') mo.brows.push([p[1] - 0.3, 0.7, 0.5]);                                    // a question ends with the brows up
  if (L >= 0.7) mo.nods.push([L * 0.42, 0.5, 1]);                                                                  // down a satellite link the question arrives late: a small nod as it lands, then the answer
  for (const [w0, w1] of b.grave || []) mo.frowns.push([b.wt[w0] + 0.05, 0.55, (w1 < b.wt.length ? b.wt[w1] : lastEnd) - b.wt[w0]]);
  // blinks gather at the ends of phrases and at glances; listeners nod at some phrase ends
  // (never two close together, and never in the last moments of a line, where a cut would land on closed eyes)
  // BLINK keeps them on the show's clock, so that a blink is not followed at once by another from the next line or a stray one
  const BL = BLINK[who] = BLINK[who] || [], blinkAt = t => { if (t < b.dur - 0.5 && !BL.some(q => Math.abs(q - b.start - t) < 1.1)) { mo.blinks.push(t); BL.push(b.start + t); if (BL.length > 400) BL.shift(); } };
  mo.looks = (b.look || []).map(([w0, w1, gx, gy, turn]) => { const t0 = b.wt[w0] - 0.12, t1 = w1 < b.wt.length ? b.wt[w1] - 0.05 : b.dur + 1; blinkAt(t0 - 0.03); blinkAt(t1 + 0.02); return [t0, t1, gx, gy, turn || 0]; });
  phr.forEach((p, k) => { if (hash(k, b.ai + 2) < 0.5) blinkAt(p[1] + 0.03 + 0.1 * hash(k, b.ai)); if (k < phr.length - 1 && hash(k, b.ai + 5) < 0.5) mo.back.push([p[1] + 0.2, 0.5]); });
  // A speaker does not hold the listener's eye throughout: finding the words of a phrase the eyes go aside (a little
  // down, some of the time) from just before it starts, the head a touch after them, and they are back well before the
  // phrase ends. About half the longer phrases; a blink often rides on the way out, as it does on any large movement of the eyes.
  mo.glances = []; phr.forEach((p, k) => {
    const t0 = p[0] - 0.3 + 0.2 * hash(k, b.ai + 7), t1 = Math.min(t0 + 0.5 + 0.6 * hash(k + 0.2, b.ai + 7), p[1] - 0.35);
    if (p[1] - p[0] < 0.9 || t1 - t0 < 0.35 || hash(k + 0.6, b.ai + 6) > 0.55 || mo.looks.some(l => l[0] < t1 + 0.6 && l[1] > t0 - 0.6)) return;
    mo.glances.push([t0, t1, (hash(k + 0.4, b.ai + 7) < 0.5 ? -1 : 1) * (0.45 + 0.4 * hash(k + 0.8, b.ai + 7)), hash(k + 0.1, b.ai + 8) < 0.4 ? 0.14 : 0]);
    if (hash(k + 0.3, b.ai + 8) < 0.45) blinkAt(t0 - 0.03);
  });
  mo.shakes = (b.shake || []).map(([w0, w1]) => [b.wt[w0] - 0.05, w1 < b.wt.length ? b.wt[w1] : lastEnd + 0.1]);
  // where the head rests during each phrase: it shifts as a new phrase begins, and settles when the line is over
  // The body resettles too, on some phrases, to the side the head turns: x a shift of weight (in eye distances), w a turn
  // of the shoulders, l a lean towards the camera.
  const P = POSE[who] = POSE[who] || POSE0.slice(); let sgn = P[P.length - 1].y > 0 ? 1 : -1;
  phr.forEach((p, k) => {
    sgn = hash(k + 0.5, b.ai) < 0.72 ? -sgn : sgn; const z = P[P.length - 1], mv = hash(k + 0.7, b.ai) < 0.45;       // the head resettles for every phrase, the body for fewer than half
    P.push({ t: b.start + p[0] - 0.22, y: sgn * (0.1 + 0.3 * hash(k, b.ai + 1)) * sty, p: (hash(k + 0.2, b.ai) - 0.5) * 0.22 * sty, r: (hash(k + 0.4, b.ai) - 0.5) * 0.07 * sty,
      x: mv ? sgn * (0.02 + 0.05 * hash(k + 0.9, b.ai)) * sty : z.x, w: mv ? sgn * (0.15 + 0.4 * hash(k + 0.1, b.ai + 3)) : z.w, l: (hash(k + 0.3, b.ai + 4) - 0.35) * 0.7 });
  });
  const z = P[P.length - 1]; P.push({ t: b.start + lastEnd + 0.1, y: z.y * 0.35, p: 0, r: z.r * 0.35, x: z.x * 0.5, w: z.w * 0.4, l: 0 });
  for (const id of b.split || []) if (id !== who) {                // someone listening on screen takes up an attentive tilt, and leans in a little
    const Q = POSE[id] = POSE[id] || POSE0.slice(), u = Q[Q.length - 1];
    Q.push({ t: b.start + 0.15, y: (hash(b.ai, 7) - 0.5) * 0.3, p: (hash(b.ai, 8) - 0.5) * 0.12, r: (hash(b.ai, 9) < 0.5 ? -1 : 1) * (0.008 + 0.012 * hash(b.ai, 10)), x: u.x * 0.5 + (hash(b.ai, 11) - 0.5) * 0.03, w: u.w * 0.4, l: 0.3 });
  }
  // Breath: in through the gap before each phrase (deeper after a longer gap), slowly out while it is spoken. A level of
  // -1 means "wherever the quiet breathing between lines has got to" (filled in when the whole show is laid out).
  const B = BREATH[who] = BREATH[who] || []; let lv = 0;
  phr.forEach((p, k) => {
    const gap = k ? p[0] - phr[k - 1][1] : 1, tin = clamp(0.8 * gap, 0.14, 0.6), top = k ? Math.min(1, lv + clamp(1.1 * tin + 0.9 * Math.max(0, gap - 0.3), 0.12, 0.85)) : 1;     // a short gap allows only a quick top-up
    B.push([b.start + p[0] - 0.04 - tin, k ? lv : -1], [b.start + p[0] - 0.04, top]);
    lv = Math.max(0.1, top - 0.03 - 0.1 * (p[1] - p[0])); B.push([b.start + p[1], lv]);
  });
  (SPOKE[who] = SPOKE[who] || []).push([b.start + first, b.start + lastEnd]);
}
// Lays the bulletin out on its clock from a set of recordings. Called once here; the demo page calls it again to switch voices.
const BEATS = []; let SHOW_LEN = 0;
function buildShow(speech) {
  BEATS.length = 0; SHOW_LEN = 0; for (const o of [POSE, BREATH, SPOKE, BLINK]) for (const k in o) delete o[k]; const seen = {}; let phi = 0;
  SHOW.forEach(L => {
    const b = Object.assign({ start: SHOW_LEN }, L);
    if (L.text && !L.split) { b.strap = !seen[L.who]; seen[L.who] = true; }      // name strap the first time someone is on camera
    if (L.text) {
      b.ai = phi; b.sp = speech[phi++]; b.lead = L.lead == null ? LEAD : L.lead; buildSpeech(b);
      b.kind = L.split ? 'split' + L.split.join() : L.wx != null ? 'wx' : 'solo' + L.who;
    } else { b.dur = L.intro || L.outro; b.kind = L.intro ? 'intro' : 'outro'; }
    const p = BEATS[BEATS.length - 1];
    b.shot0 = p && p.kind === b.kind ? p.shot0 : b.start;      // lines that share a camera set-up form one shot
    BEATS.push(b); SHOW_LEN += b.dur;
  });
  BEATS.forEach(b => { let e = b.start + b.dur; for (const o of BEATS) if (o.shot0 === b.shot0) e = Math.max(e, o.start + o.dur); b.shotLen = e - b.shot0; });
  // Between lines everyone breathes quietly (in for about a second and a half, out for two and a half); those breaths are
  // joined to the ones taken for speech, so a presenter who stays on screen never skips a beat.
  for (const who in BREATH) {
    const T = [-8], Y = [0.4]; let n = 0;
    const idle = until => { for (;;) { const k = T.length - 1, up = Y[k] < 0.5, d = (up ? 1.5 : 2.4) * (0.85 + 0.3 * hash(n, who.length)); if (T[k] + d > until) return; n++; T.push(T[k] + d); Y.push(up ? 0.62 + 0.08 * hash(n, 3) : 0.34 + 0.06 * hash(n, 5)); } };
    for (const [t, lv] of BREATH[who]) {
      if (lv < 0) { idle(t - 0.3); const k = T.length - 1, up = Y[k] < 0.5, f = clamp((t - T[k]) / (up ? 1.5 : 2.4), 0, 1); T.push(Math.max(t, T[k] + 0.05)); Y.push(up ? Y[k] + 0.2 * f : Y[k] - 0.25 * f); }
      else { T.push(Math.max(t, T[T.length - 1] + 0.02)); Y.push(lv); }
    }
    idle(SHOW_LEN + 8); BREATH[who] = { T, Y, M: slopes(T, Y) };
  }
}
buildShow(SPEECH);
const TICKER = '  ●  Kubernetes still the answer, question unclear  ●  platform team renames itself again  ●  terraform plan: 1 to add, 0 to change, 312 to destroy  ●  OpenTelemetry now observing the observers  ●  SBOM found to contain another SBOM  ●  cloud bill arrives, CFO joins incident channel  ●  change freeze begins, three hotfixes ship  ●  MTTR down, vibes mixed';


/* ── assets ── */
function mkCanvas(w, h) { const k = document.createElement('canvas'); k.width = w; k.height = h; return k; }
let pending = 0, readyAt = -1;
function loadImg(src) { const im = new Image(); pending++; im.onload = im.onerror = () => { pending--; }; im.src = src; return im; }
const STILL = {}; for (const k in ASSETS.img) STILL[k] = loadImg(ASSETS.img[k]);
const ACT = {};
for (const k in ASSETS.cast) {
  const m = ASSETS.cast[k], pf = mkCanvas(FW, FH), mo = m.mouth, ey = m.eyes, eye = {};
  for (const n of ['half', 'closed', 'gl', 'gr', 'gd', 'smile']) eye[n] = loadImg(ey[n]);
  ACT[k] = { m, bg: loadImg(m.bg), fg: loadImg(m.fg), pf, px: pf.getContext('2d'),
    mx: mkCanvas(mo.w, mo.h).getContext('2d'), ex: mkCanvas(ey.w, ey.h).getContext('2d'), mMask: loadImg(mo.mask), eMask: loadImg(ey.mask),          // small canvases where poses are blended
    mN: mo.n.map(loadImg), rows: { e1: mo.e1.map(loadImg), e2: mo.e2.map(loadImg), w1: mo.w1.map(loadImg), w2: mo.w2.map(loadImg), sg: mo.sg.map(loadImg) }, mP: loadImg(mo.p), mH: loadImg(mo.sh), eye };
}
const grain = mkCanvas(256, 256);
{ const g = grain.getContext('2d'), d = g.createImageData(256, 256); for (let i = 0; i < d.data.length; i += 4) { const v = 128 + (Math.random() - 0.5) * 150; d.data[i] = d.data[i + 1] = d.data[i + 2] = v; d.data[i + 3] = 255; } g.putImageData(d, 0, 0); }
const soft = mkCanvas(64, 36), softx = soft.getContext('2d');          // tiny copy = cheap blur
const lofi = mkCanvas(308, 227), lofix = lofi.getContext('2d'); let lofiTick = -1;

function rr(x, y, w, h, r) {
  c.beginPath(); c.moveTo(x + r, y); c.arcTo(x + w, y, x + w, y + h, r); c.arcTo(x + w, y + h, x, y + h, r);
  c.arcTo(x, y + h, x, y, r); c.arcTo(x, y, x + w, y, r); c.closePath();
}
function ell(x, y, rx, ry) { c.beginPath(); c.ellipse(x, y, rx, ry, 0, 0, 6.2832); }
function opsLogo(x, y, s, col) {
  if (s < 2) return;
  c.fillStyle = col || ACC; rr(x, y, s, s, s * 0.16); c.fill();
  c.strokeStyle = '#06281d'; c.lineWidth = s * 0.085; c.lineCap = 'round'; c.beginPath();
  for (let i = 0; i <= 48; i++) { const a = i / 48 * 6.2832, d = 1 + Math.sin(a) * Math.sin(a), px = x + s / 2 + s * 0.36 * Math.cos(a) / d, py = y + s / 2 + s * 0.36 * Math.sin(a) * Math.cos(a) / d; i ? c.lineTo(px, py) : c.moveTo(px, py); }
  c.stroke();
}
function lines(text, maxW) {
  const out = []; let line = '';
  for (const w of text.split(' ')) { if (line && c.measureText(line + ' ' + w).width > maxW) { out.push(line); line = w; } else line = line ? line + ' ' + w : w; }
  out.push(line); return out;
}

/* ── the mouth at a moment of a line: jaw opening (negative = lips pressed), lip shape, and whether the voice is on ── */
function speechAt(b, bt, id) {
  const J = samp(b.J, bt) * (b.taught ? 1 : ACT[id].m.gain || 1), C = samp(b.C, bt);      // the reference is already fitted to each face
  return { o: clamp(C > 0.9 ? -0.12 * (C - 0.9) / 0.1 : J * (1 - C / 0.9), -0.12, 1.3), s: clamp(samp(b.S, bt), -1, 1), on: bt > b.t0 - 0.1 && bt < b.t1 + 0.1 };
}
// Smiles: a line may list [who, from, to, strength] as fractions of its length; the smile eases in and, unless it runs to the end, out.
function smileAt(b, bt, id) {
  let w = 0;
  if (b.sm) for (const [who, f0, f1, amp] of b.sm) if (who === id) { const t0 = f0 * b.dur, t1 = f1 * b.dur; w = Math.max(w, (amp || 1) * rise(bt, t0 - 0.05, t0 + 0.4) * (f1 >= 1 ? 1 : 1 - rise(bt, t1, t1 + 0.5))); }
  return w;
}
function blinkShape(ph) { return ph <= 0 || ph >= 0.27 ? 0 : ph < 0.065 ? ease(ph / 0.065) : ph < 0.105 ? 1 : 1 - ease((ph - 0.105) / 0.165); }
function postureAt(P, ts) {                  // every shift eases in over about half a second; shifts that overlap simply add up
  let y = P[0].y, p = P[0].p, r = P[0].r;
  for (let k = 1; k < P.length && P[k].t < ts; k++) { const e = rise(ts, P[k].t, P[k].t + 0.55); y += (P[k].y - P[k - 1].y) * e; p += (P[k].p - P[k - 1].p) * e; r += (P[k].r - P[k - 1].r) * e; }
  return [y, p, r];
}
function bodyPostureAt(P, ts) {              // the body takes about a second over what the head does in half
  let x = P[0].x, w = P[0].w, l = P[0].l;
  for (let k = 1; k < P.length && P[k].t - 0.05 < ts; k++) { const e = rise(ts, P[k].t - 0.05, P[k].t + 1.05); x += (P[k].x - P[k - 1].x) * e; w += (P[k].w - P[k - 1].w) * e; l += (P[k].l - P[k - 1].l) * e; }
  return [x, w, l];
}
const breathAt = (id, ts) => { const B = BREATH[id]; return B && B.T ? curve(B.T, B.Y, B.M, ts) : 0.45; };      // how full the lungs are, 0..1
// A presenter who is not speaking wears the photograph's own slight smile; it lets go just before they speak and comes back after.
function restAt(id, ts) { let w = 1; for (const [t0, t1] of SPOKE[id] || []) w = Math.min(w, 1 - rise(ts, t0 - 0.45, t0 - 0.15) * (1 - rise(ts, t1 + 0.35, t1 + 1.1))); return w; }
const nodShape = x => gauss(x - 0.03, 0.085) - 0.3 * gauss(x + 0.17, 0.07);               // a small lift, the drop on the syllable, the return
const holdShape = (x, hold) => rise(x, -0.18, -0.02) * (1 - rise(x, hold, hold + 0.32));
/* Everything about one face at one moment. b / bt: the line on air and how far into it; ts: the show's clock.
   Returns mouth (o, s, g = smile: 0 relaxed for speech, 0.5 the photograph's own expression, 1 a broad smile), eyes
   (blink, gx, gy), brows (bu, bd) and head (yaw, pit, roll: yaw and pit in units of the measured turn and nod, roll
   in radians), plus how animated the speaker is (emph) for the body. */
function faceAt(id, b, bt, ts, still) {
  const a = ACT[id], sd = a.m.seed, sty = STYLE[id] || 1, talk = b.sp && b.who === id, mo = b.mo, sp = talk ? speechAt(b, bt, id) : null;
  const P = postureAt(POSE[id] || POSE0, ts), q = { o: sp ? sp.o : 0, s: sp ? sp.s : 0, g: Math.max(b.sp ? smileAt(b, bt, id) : 0, 0.5 * restAt(id, ts)), on: !!(sp && sp.on) };
  let yaw = P[0] + 0.1 * wob(ts * 0.5, sd), pit = P[1] + 0.07 * wob(ts * 0.6, sd + 3), roll = P[2] + 0.005 * wob(ts * 0.45, sd + 7), bu = 0, bd = 0, emph = 0, blink = 0;
  // Nobody holds a pose for long, speaking or not: every few seconds, at no fixed interval, the head resettles a little
  // (a slight turn, tilt and lift, taken up over most of a second). Without it a listener is a photograph that blinks.
  { const k = Math.floor(ts / 4.7), e = rise(ts, k * 4.7 + 2.6 * hash(k + 0.4, sd), k * 4.7 + 2.6 * hash(k + 0.4, sd) + 0.85), v = (j, n) => hash(j, sd + n) - 0.5;
    yaw += 0.5 * (v(k - 1, 31) + (v(k, 31) - v(k - 1, 31)) * e); pit += 0.28 * (v(k - 1, 33) + (v(k, 33) - v(k - 1, 33)) * e); roll += 0.03 * (v(k - 1, 35) + (v(k, 35) - v(k - 1, 35)) * e); }
  // the eyes dart a little all the time (sideways mostly: the downward pose lowers the lids, and looks sleepy if it is used often)
  const slot = Math.floor(ts / 0.85), tg = k => [(hash(k, sd) - 0.5) * 0.5, hash(k + 0.3, sd) < 0.12 ? 0.14 * hash(k + 0.7, sd) : 0], g0 = tg(slot - 1), g1 = tg(slot);
  const ge = clamp((ts - (slot * 0.85 + hash(slot + 0.1, sd) * 0.5)) / 0.045, 0, 1); let gx = g0[0] + (g1[0] - g0[0]) * ge, gy = g0[1] + (g1[1] - g0[1]) * ge;
  if (talk) {
    const x0 = bt - mo.first;                                    // just before speaking: a breath, chin and brows lift slightly
    const prep = rise(x0, -0.42, -0.14) * (1 - rise(x0, -0.06, 0.16)); pit -= 0.1 * prep; bu += 0.1 * prep;
    for (const [t, A, side, minor] of mo.nods) { const n = A * nodShape(bt - t); pit += 0.55 * sty * n; yaw += 0.12 * side * n; roll += 0.006 * side * n; if (!minor) emph += A * gauss(bt - t, 0.22); }
    if (sp.on) pit -= 0.028 * clamp(pitchAt(b, bt), -5, 6) + 0.05 * Math.max(0, sp.o);         // the head rides the pitch of the voice, and tips back a touch as the jaw drops
    // and it is never still while its owner talks: it wanders, faster and further than at rest, eased in and out with the line
    const live = rise(bt, mo.first - 0.2, mo.first + 0.5) * (1 - rise(bt, b.t1 - 0.3, b.t1 + 0.5)) * sty;
    yaw += 0.13 * live * wob(ts * 1.15, sd + 21); pit += 0.09 * live * wob(ts * 1.4, sd + 25); roll += 0.007 * live * wob(ts * 0.9, sd + 29);
    for (const [t, A, hold] of mo.brows) { const h = A * holdShape(bt - t, hold); bu += h * Math.min(1.15, sty); if (hold > 0.4) { pit -= 0.14 * h; roll += 0.012 * h; } }
    for (const [t, A, hold] of mo.frowns) bd += A * holdShape(bt - t, hold);
    if (sp.on) bu += 0.02 * clamp(pitchAt(b, bt), 0, 6);
    for (const [t0, t1] of mo.shakes) yaw += 0.3 * Math.sin((bt - t0) * 11.5) * rise(bt, t0, t0 + 0.15) * (1 - rise(bt, t1 - 0.2, t1 + 0.1));
    for (const [t0, t1, lx, ly, turn] of mo.looks) { const e = rise(bt, t0, t0 + 0.08) * (1 - rise(bt, t1, t1 + 0.08)), h = rise(bt, t0 - 0.05, t0 + 0.4) * (1 - rise(bt, t1 - 0.05, t1 + 0.45)); gx += (lx - gx) * e; gy += (ly - gy) * e; yaw += turn * h; }
    for (const [t0, t1, lx, ly] of mo.glances) { const e = rise(bt, t0, t0 + 0.06) * (1 - rise(bt, t1, t1 + 0.07)), h = rise(bt, t0 + 0.03, t0 + 0.4) * (1 - rise(bt, t1, t1 + 0.4)); gx += (lx - gx) * e; gy += (ly - gy) * e; yaw += 0.1 * lx * h; }
    for (const t of mo.blinks) blink = Math.max(blink, blinkShape(bt - t));
  } else {
    if (mo) for (const [t, A] of mo.back) pit += 0.34 * A * (nodShape(bt - t) + 0.6 * nodShape(bt - t - 0.3));      // a listener's small double nod
    // someone who is not speaking looks away now and then, briefly, and the head starts after the eyes
    const k = Math.floor(ts / 6.1), t0 = k * 6.1 + 4 * hash(k + 0.2, sd + 41), t1 = t0 + 0.35 + 0.5 * hash(k + 0.5, sd + 41);
    if (hash(k, sd + 43) < 0.55) { const lx = (hash(k + 0.7, sd + 41) < 0.5 ? -1 : 1) * (0.35 + 0.3 * hash(k + 0.9, sd + 41)), e = rise(ts, t0, t0 + 0.06) * (1 - rise(ts, t1, t1 + 0.07)); gx += (lx - gx) * e; gy *= 1 - e; yaw += 0.07 * lx * rise(ts, t0 + 0.03, t0 + 0.4) * (1 - rise(ts, t1, t1 + 0.4)); }
  }
  // other blinks fall irregularly, but not right next to one that belongs to the speech: one in every stretch of about
  // three seconds, anywhere in it, so they come one to five seconds apart (they used to be drawn with a small chance
  // every second or so, which now and then left the eyes open for a quarter of a minute)
  for (let k = Math.floor(ts / 3.1) - 1; k <= Math.floor(ts / 3.1); k++) {
    const at = k * 3.1 + hash(k + 0.5, sd) * 2.2;
    if (at - b.start > b.dur - 0.5) continue;
    if ((BLINK[id] || []).some(t => Math.abs(t - at) < 1.4)) continue;
    blink = Math.max(blink, blinkShape(ts - at), hash(k + 0.2, sd) < 0.05 ? blinkShape(ts - at - 0.33) : 0);                 // now and then a double blink
  }
  if (still) { yaw = pit = roll = emph = 0; }
  q.blink = blink; q.gx = clamp(gx, -1, 1); q.gy = clamp(gy, 0, 1); q.bu = clamp(bu, 0, 0.92); q.bd = clamp(bd, 0, 1);
  q.yaw = clamp(yaw, -1, 1); q.pit = clamp(pit, -0.9, 1); q.roll = roll; q.emph = Math.min(1, emph); q.still = !!still;
  return q;
}

/* ── a presenter: poses blended on the cut-out, then the head and brows moved by the mesh ── */
// Blends poses in the region's own small canvas. It starts from the photo; each pose is added with the opacity that
// leaves the exact weighted mix; the result is cut to the region's soft mask and laid back on the cut-out.
function region(a, x, mask, r, layers) {
  let acc = 1, any = false; for (const l of layers) if (l[1] >= 0.004) { acc -= l[1]; any = true; }
  if (!any) return; acc = Math.max(0, acc);
  x.globalCompositeOperation = 'copy'; x.globalAlpha = 1; x.drawImage(a.fg, -r.x, -r.y); x.globalCompositeOperation = 'source-over';
  for (const [im, w] of layers) { if (w < 0.004) continue; acc += w; x.globalAlpha = Math.min(1, w / acc); x.drawImage(im, 0, 0); }
  x.globalAlpha = 1; x.globalCompositeOperation = 'destination-in'; x.drawImage(mask, 0, 0);
  a.px.globalCompositeOperation = 'source-atop'; a.px.drawImage(x.canvas, r.x, r.y); a.px.globalCompositeOperation = 'source-over';
}
// Mouth poses form a grid: jaw opening along one axis (12 steps with neutral lips, 8 on the other rows), and across it
// lips fully rounded, half rounded, neutral, half spread, fully spread. A smile has a row of its own.
// "Neutral" is a relaxed mouth, made for speaking; the photograph's own closed-lip smile is the half-smile pose (g = 0.5).
const JAW = 46;                                                  // jaw units at an opening of 1; the widest pose is 60
function mouthLayers(a, o, s, g) {
  g *= 1 - 0.6 * Math.max(0, -s);                                // lips cannot round and smile at once: the smile gives way
  const M = a.m.mouth, out = [], j = Math.max(0, o) * JAW, shut = clamp(1 - j / 5, 0, 1);
  const gs = g * (1 - shut) + Math.max(0, 2 * g - 1) * shut, gh = shut * (g < 0.5 ? 2 * g : 2 - 2 * g), rest = Math.max(0, 1 - gs - gh);      // with the mouth shut a smile grows through a half smile
  const row = (imgs, arr, w, photo) => {
    if (w < 0.004) return; const v = Math.min(j, arr[arr.length - 1]); let i = 0; while (i < arr.length - 2 && v > arr[i + 1]) i++;
    const f = clamp((v - arr[i]) / (arr[i + 1] - arr[i]), 0, 1);
    if (!photo) out.push([imgs[i], w * (1 - f)], [imgs[i + 1], w * f]); else { if (i > 0) out.push([imgs[i - 1], w * (1 - f)]); out.push([imgs[i], w * f]); }     // step 0 of the neutral row is the photo itself
  };
  const as = Math.min(1, Math.abs(s)) * 2, wn = Math.max(0, 1 - as), w1 = as <= 1 ? as : 2 - as, w2 = Math.max(0, as - 1), press = o < 0 ? Math.min(1, -o / 0.12) : 0;
  if (press > 0) out.push([a.mP, press * wn * rest]);
  row(a.mN, M.jn, wn * rest, true); row(s >= 0 ? a.rows.e1 : a.rows.w1, M.js, w1 * rest); row(s >= 0 ? a.rows.e2 : a.rows.w2, M.js, w2 * rest);
  row(a.rows.sg, M.js, gs); if (gh > 0.004) out.push([a.mH, gh]);
  return out;
}
function eyeLayers(a, q) {
  const E = a.eye, b = q.blink, open = 1 - Math.min(1, 2 * b), w = [['gl', Math.max(0, -q.gx)], ['gr', Math.max(0, q.gx)], ['gd', q.gy], ['smile', 0.85 * clamp(2 * q.g - 1, 0, 1)]];      // the eyes join in only for a smile broader than the photograph's own
  let sum = 0; for (const l of w) sum += l[1]; const k = open / Math.max(1, sum);
  return w.map(l => [E[l[0]], l[1] * k]).concat([[E.half, b <= 0.5 ? 2 * b : 2 - 2 * b], [E.closed, Math.max(0, 2 * b - 1)]]);
}
function compose(a, q) {
  const x = a.px; x.globalCompositeOperation = 'copy'; x.globalAlpha = 1; x.drawImage(a.fg, 0, 0); x.globalCompositeOperation = 'source-over';
  region(a, a.mx, a.mMask, a.m.mouth, mouthLayers(a, q.o, q.s, q.g)); region(a, a.ex, a.eMask, a.m.eyes, eyeLayers(a, q));
}
/* The head and the body. A mesh lies over the picture; six measured displacement fields say where each point of the
   face goes when the head turns right or left, nods down or up, and when the brows rise or lower. The mesh is moved by
   a weighted sum of them (plus a tilt about the neck), so the nose travels further than the ears and the brows really move.
   Three maps of the picture (made from a face-parsing network's labels) say what else may move: how much a point
   belongs to the torso, how free the hair is there, and how exposed it is to wind. With them the same mesh lets the
   torso shift, tilt, lean, turn and breathe with the head riding on it, and lets loose hair hang back and swing.
   Where the picture meets the frame it is pinned: nothing moves up or down at the bottom edge, or sideways at the side
   edges, so the figure never lifts off the edge of the frame (it may slide along it, as a leaning body does).
   This is a second, small WebGL canvas; its picture is drawn back into the 2D frame. */
const warpGL = (() => {
  const cv = mkCanvas(FW, FH); let gl = null;
  try { gl = cv.getContext('webgl', { alpha: true, premultipliedAlpha: true, antialias: false, depth: false, stencil: false, preserveDrawingBuffer: true }); } catch (e) {}
  if (!gl) return null;
  const sh = (type, src) => { const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); return s; }, pr = gl.createProgram();
  // aM = (torso, free hair, wind). uBd = the torso's shift, tilt and lean, about the point uBc.xy; uBc.zw = the
  // torso's middle and 1 / half its width; uBr = (breath lift, breath widening, turn of the shoulders, how much of the
  // lift the head takes); uHr.xy = where free hair hangs relative to the head, uHr.zw = the shoulder line and 1 / the
  // distance below it over which a turn of the shoulders reaches its full size (the collar is near the axis of the
  // turn and hardly moves; the middle of the chest is well in front of it); uWd = (wind, flutter, time);
  // uPin = how far in from the side edges and up from the bottom edge the pinning reaches.
  gl.attachShader(pr, sh(gl.VERTEX_SHADER, `attribute vec2 aP; attribute vec4 aA, aB, aC; attribute vec3 aM; attribute float aK; uniform vec4 uW, uV, uT, uBd, uBc, uBr, uHr, uWd; uniform vec3 uZ; uniform vec2 uPin; varying vec2 vUV;
    void main() { vec2 d = aA.xy * uW.x + aA.zw * uW.y + aB.xy * uW.z + aB.zw * uW.w + aC.xy * uV.x + aC.zw * uV.y;
      d += aK * (uT.xy + uV.z * vec2(uT.w - aP.y, aP.x - uT.z));
      vec2 q = aP - uBc.xy; float u = (aP.x - uBc.z) * uBc.w; vec2 t = uBd.xy + uBd.z * vec2(-q.y, q.x) + uBd.w * q;
      t.y -= uBr.x * mix(uBr.w, 1.0, aM.x); t.x += aM.x * (uBr.y * (aP.x - uBc.z) + uBr.z * max(0.0, 1.0 - u * u) * mix(0.35, 1.0, smoothstep(0.0, 1.0, (aP.y - uHr.z) * uHr.w)));
      float ph = dot(aP, vec2(0.05, 0.035));
      t += aM.y * uHr.xy + aM.z * (uWd.xy * (0.75 + 0.25 * sin(ph * 0.7 - uWd.w * 3.1)) + uWd.z * vec2(sin(ph - uWd.w * 8.3), 0.5 * sin(ph * 1.31 - uWd.w * 6.1)));
      d += t * vec2(smoothstep(0.0, uPin.x, aP.x) * smoothstep(0.0, uPin.x, ${FW}.0 - aP.x), smoothstep(0.0, uPin.y, ${FH}.0 - aP.y));
      vec2 p = uZ.xy + (aP + d - uZ.xy) * uZ.z;
      gl_Position = vec4(p.x / ${FW / 2}.0 - 1.0, 1.0 - p.y / ${FH / 2}.0, 0.0, 1.0); vUV = aP / vec2(${FW}.0, ${FH}.0); }`));
  gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, `#ifdef GL_FRAGMENT_PRECISION_HIGH
    precision highp float;
    #else
    precision mediump float;
    #endif
    uniform sampler2D uS; varying vec2 vUV;
    #ifdef GL_FRAGMENT_PRECISION_HIGH
    // The picture is read between its pixels almost everywhere (the mesh moves it by fractions of a pixel), and reading
    // it as a plain average of the four nearest pixels blurred it: half the fine detail of eyes and hair was lost here.
    // This is the Catmull-Rom cubic over the sixteen nearest pixels, taken as nine averaged reads; it keeps edges.
    void main() { vec2 R = vec2(${FW}.0, ${FH}.0), s = vUV * R, c = floor(s - 0.5) + 0.5, f = s - c;
      vec2 w0 = f * (-0.5 + f * (1.0 - 0.5 * f)), w1 = 1.0 + f * f * (-2.5 + 1.5 * f), w2 = f * (0.5 + f * (2.0 - 1.5 * f)), w3 = f * f * (-0.5 + 0.5 * f), w12 = w1 + w2;
      vec2 a = (c - 1.0) / R, b = (c + w2 / w12) / R, e = (c + 2.0) / R;
      vec4 v = (texture2D(uS, vec2(a.x, a.y)) * w0.x + texture2D(uS, vec2(b.x, a.y)) * w12.x + texture2D(uS, vec2(e.x, a.y)) * w3.x) * w0.y
             + (texture2D(uS, vec2(a.x, b.y)) * w0.x + texture2D(uS, vec2(b.x, b.y)) * w12.x + texture2D(uS, vec2(e.x, b.y)) * w3.x) * w12.y
             + (texture2D(uS, vec2(a.x, e.y)) * w0.x + texture2D(uS, vec2(b.x, e.y)) * w12.x + texture2D(uS, vec2(e.x, e.y)) * w3.x) * w3.y;
      v.a = clamp(v.a, 0.0, 1.0); gl_FragColor = vec4(clamp(v.rgb, 0.0, v.a), v.a); }
    #else
    void main() { gl_FragColor = texture2D(uS, vUV); }
    #endif`));
  gl.linkProgram(pr); if (!gl.getProgramParameter(pr, gl.LINK_STATUS)) return null;
  gl.useProgram(pr); const loc = {}; for (const n of ['aP', 'aA', 'aB', 'aC', 'aK', 'aM']) { loc[n] = gl.getAttribLocation(pr, n); gl.enableVertexAttribArray(loc[n]); }
  const U = n => gl.getUniformLocation(pr, n), uW = U('uW'), uV = U('uV'), uT = U('uT'), uBd = U('uBd'), uBc = U('uBc'), uBr = U('uBr'), uHr = U('uHr'), uWd = U('uWd'), uPin = U('uPin'), uZ = U('uZ');
  gl.bindTexture(gl.TEXTURE_2D, gl.createTexture()); gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, true);
  for (const [k, v] of [[gl.TEXTURE_MIN_FILTER, gl.LINEAR], [gl.TEXTURE_MAG_FILTER, gl.LINEAR], [gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE], [gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE]]) gl.texParameteri(gl.TEXTURE_2D, k, v);
  gl.disable(gl.BLEND); gl.clearColor(0, 0, 0, 0); gl.viewport(0, 0, FW, FH);
  const w = { cv, ok: true };
  cv.addEventListener('webglcontextlost', e => { e.preventDefault(); w.ok = false; });           // fall back to the flat warp
  function mesh(a) {                                             // a grid over the whole frame, in step with the grid the fields were measured on
    const F = a.m.flow, f = a.m.face, st = F.step, i0 = Math.ceil(F.x / st), j0 = Math.ceil(F.y / st), nx = i0 + Math.ceil((FW - F.x) / st) + 1, ny = j0 + Math.ceil((FH - F.y) / st) + 1;
    const fl = F.f.map(([s, d]) => { const bin = atob(d), v = new Float32Array(bin.length); for (let i = 0; i < bin.length; i++) { const k = bin.charCodeAt(i); v[i] = (k > 127 ? k - 256 : k) / s; } return v; });
    const V = new Float32Array(nx * ny * 18), cx = f.cx, cy = f.cy - 0.1 * f.iod, R = 3.3 * f.iod, B = a.m.body; let p = 0;
    const map = k => { if (!B || !B[k]) return null; const bin = atob(B[k]), v = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) v[i] = bin.charCodeAt(i); return v; }, mb = map('b'), mh = map('h'), mw = map('w');
    const at = (m, x, y) => {                                      // a map's value at a point of the picture (the maps are on a coarse grid)
      if (!m) return 0; const gx = Math.min(x / B.step, B.cols - 1.001), gy = Math.min(y / B.step, B.rows - 1.001), i = Math.floor(gx), j = Math.floor(gy), fx = gx - i, fy = gy - j, k = j * B.cols + i;
      return ((m[k] * (1 - fx) + m[k + 1] * fx) * (1 - fy) + (m[k + B.cols] * (1 - fx) + m[k + B.cols + 1] * fx) * fy) / 255;
    };
    for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) {
      const x = clamp(F.x + (i - i0) * st, 0, FW), y = clamp(F.y + (j - j0) * st, 0, FH), gi = i - i0, gj = j - j0, ok = gi >= 0 && gi < F.cols && gj >= 0 && gj < F.rows, o = (gj * F.cols + gi) * 2;
      V[p++] = x; V[p++] = y; for (const v of fl) { V[p++] = ok ? v[o] : 0; V[p++] = ok ? v[o + 1] : 0; }
      const r2 = ((x - cx) * (x - cx) + (y - cy) * (y - cy)) / (R * R); V[p++] = r2 < 1 ? (1 - r2) * (1 - r2) : 0;                    // how much of a tilt this point takes: all at the face, none at the shoulders
      V[p++] = at(mb, x, y); V[p++] = at(mh, x, y); V[p++] = at(mw, x, y);
    }
    const I = new Uint16Array((nx - 1) * (ny - 1) * 6); p = 0;
    for (let j = 0; j < ny - 1; j++) for (let i = 0; i < nx - 1; i++) { const k = j * nx + i; I[p++] = k; I[p++] = k + 1; I[p++] = k + nx; I[p++] = k + 1; I[p++] = k + nx + 1; I[p++] = k + nx; }
    const vbo = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, vbo); gl.bufferData(gl.ARRAY_BUFFER, V, gl.STATIC_DRAW);
    const ibo = gl.createBuffer(); gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, ibo); gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, I, gl.STATIC_DRAW);
    return { vbo, ibo, n: I.length };
  }
  w.draw = (a, q, bd, ts, zf) => {
    const m = a.mesh || (a.mesh = mesh(a)), f = a.m.face, B = a.m.body;
    gl.bindBuffer(gl.ARRAY_BUFFER, m.vbo); gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, m.ibo);
    gl.vertexAttribPointer(loc.aP, 2, gl.FLOAT, false, 72, 0); gl.vertexAttribPointer(loc.aA, 4, gl.FLOAT, false, 72, 8); gl.vertexAttribPointer(loc.aB, 4, gl.FLOAT, false, 72, 24);
    gl.vertexAttribPointer(loc.aC, 4, gl.FLOAT, false, 72, 40); gl.vertexAttribPointer(loc.aK, 1, gl.FLOAT, false, 72, 56); gl.vertexAttribPointer(loc.aM, 3, gl.FLOAT, false, 72, 60);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, a.pf);
    gl.uniform4f(uW, Math.max(0, q.yaw), Math.max(0, -q.yaw), Math.max(0, q.pit), Math.max(0, -q.pit)); gl.uniform4f(uV, q.bu, q.bd, q.roll, 0); gl.uniform4f(uT, 0, 0, f.cx, f.cy + 1.6 * f.iod); gl.uniform2f(uPin, 0.45 * f.iod, 0.5 * f.iod); gl.uniform3f(uZ, f.cx, f.cy, zf || 1);
    if (bd && B) {
      // The torso tilts about a point at the waist (below the frame) and leans about the face, so a lean makes the head a
      // touch larger where it is; both are folded into one shift-plus-turn about the face.
      const wy = B.sy + 2.6 * f.iod;
      gl.uniform4f(uBd, bd.sx - bd.rot * (f.cy - wy), bd.sy + bd.rot * (f.cx - B.cx), bd.rot, bd.lean); gl.uniform4f(uBc, f.cx, f.cy, B.cx, 1 / B.r);
      gl.uniform4f(uBr, bd.lift, bd.wide, bd.tw, 0.25); gl.uniform4f(uHr, bd.hx, bd.hy, B.sy, 1 / (1.4 * f.iod)); gl.uniform4f(uWd, bd.wx, bd.wy, bd.wa, ts % 600);
    } else { gl.uniform4f(uBd, 0, 0, 0, 0); gl.uniform4f(uBc, f.cx, f.cy, f.cx, 0.002); gl.uniform4f(uBr, 0, 0, 0, 0); gl.uniform4f(uHr, 0, 0, 0, 0); gl.uniform4f(uWd, 0, 0, 0, 0); }
    gl.clear(gl.COLOR_BUFFER_BIT); gl.drawElements(gl.TRIANGLES, m.n, gl.UNSIGNED_SHORT, 0);
  };
  return w;
})();
// Without WebGL for the mesh: the head slides and tilts as a flat picture (no parallax, and the brows stay put).
function warpFlat(a, tx, ty, rot) {
  if (!a.wf) { a.wf = mkCanvas(FW, FH); a.wx = a.wf.getContext('2d'); }
  const w = a.wx, f = a.m.face, cx = f.cx, cy = f.cy - 0.1 * f.iod, R = 3.3 * f.iod, pv = f.cy + 1.6 * f.iod, M = 64, S = 16;
  w.clearRect(0, 0, FW, FH);
  for (let Y = 0; Y < FH; Y += M) for (let X = 0; X < FW; X += M) {
    const mx = X + M / 2 - cx, my = Y + M / 2 - cy;
    if (mx * mx + my * my > (R + 48) * (R + 48)) { w.drawImage(a.pf, X, Y, M, M, X, Y, M, M); continue; }
    for (let y = Y; y < Y + M; y += S) for (let x = X; x < X + M; x += S) {
      const px = x + S / 2 - cx, py = y + S / 2 - cy, r2 = (px * px + py * py) / (R * R), k = r2 < 1 ? (1 - r2) * (1 - r2) : 0;
      const sw = Math.min(S + 1, FW - x), sh = Math.min(S + 1, FH - y);
      w.drawImage(a.pf, x, y, sw, sh, x + k * (tx - rot * (y + S / 2 - pv)), y + k * (ty + rot * px), sw, sh);
    }
  }
  return a.wf;
}
/* The body at one moment. The torso drifts a little all the time, resettles with the phrases, dips into what is being
   stressed, turns part of the way with the head, and breathes: in before a phrase, out while it is spoken. Loose hair
   hangs on a spring behind the head: it follows late and swings past. Returns pixels and radians for the mesh. */
function bodyAt(id, q, ts) {
  const a = ACT[id], iod = a.m.face.iod, K = BODY[id] || BODY.cy, sd = a.m.seed, P = bodyPostureAt(POSE[id] || POSE0, ts), air = breathAt(id, ts), e = q.on ? 1 : 0.6;
  const d = a.dyn || (a.dyn = { t: -1e9 }), dt = ts - d.t, cut = dt < 0 || dt > 0.25;      // the clock jumped (a cut, a seek): start afresh
  d.yaw = cut ? q.yaw : d.yaw + (q.yaw - d.yaw) * (1 - Math.exp(-dt / 0.3));                // the shoulders follow a turn of the head slowly, and not its quick movements
  d.em = cut ? q.emph : d.em + (q.emph - d.em) * (1 - Math.exp(-dt / 0.12));                // and dip into a stressed word a moment after the head does
  const o = {
    sx: iod * (P[0] + 0.04 * K.sway * e * wob(ts * 0.31, sd + 11) + 0.03 * d.yaw),          // a shift of weight
    sy: iod * (0.02 * P[2] + 0.022 * d.em + 0.012 * K.sway * wob(ts * 0.23, sd + 17)),       // down a little into a stressed word
    rot: 0.004 * K.sway * e * wob(ts * 0.26, sd + 13) + 0.05 * P[0] - 0.15 * q.roll,         // the shoulder line tilts, a hair against the head
    lean: 0.004 * P[2] + 0.008 * d.em,                                                     // towards the camera
    tw: iod * 0.1 * (P[1] + 0.8 * d.yaw),                                                    // the shoulders turn: the middle of the chest moves, the outline hardly
    lift: iod * 0.11 * (air - 0.4), wide: 0.007 * (air - 0.4), hx: 0, hy: 0, wx: 0, wy: 0, wa: 0,
  };
  // where the head is on screen; the hair's spring follows that point
  const hx = o.sx + 0.11 * iod * q.yaw, hy = o.sy - 0.25 * o.lift + 0.08 * iod * q.pit;
  if (cut) { d.x = hx; d.y = hy; d.vx = d.vy = 0; }
  else if (dt > 0) {
    const n = Math.ceil(dt / 0.004), h = dt / n, w = 6.2832 * K.hz, k = w * w, cd = 2 * K.damp * w;
    for (let i = 1; i <= n; i++) { const tx = d.px + (hx - d.px) * i / n, ty = d.py + (hy - d.py) * i / n; d.vx += h * (k * (tx - d.x) - cd * d.vx); d.x += h * d.vx; d.vy += h * (k * (ty - d.y) - cd * d.vy); d.y += h * d.vy; }
  }
  d.t = ts; d.px = hx; d.py = hy;
  const lim = 0.14 * iod; o.hx = clamp(K.hair * (d.x - hx), -lim, lim); o.hy = clamp(0.6 * K.hair * (d.y - hy), -lim, lim);
  if (K.wind) { const g = 0.5 + 0.5 * wob(ts * 0.8, 21); o.wx = -iod * K.wind * (0.012 + 0.03 * g); o.wy = iod * K.wind * 0.006 * g; o.wa = iod * K.wind * 0.011 * (0.4 + 0.6 * g); }      // gusts, and a flutter that grows with them
  return o;
}
// Draws in frame coordinates (the caller sets the camera). o: { b, bt (the line on air), zb, zf, noBg, mid(), still, rigid }
// still: no head or body movement; rigid: the head moves but the body and hair stay as photographed.
function drawActor(id, ts, o) {
  const a = ACT[id], f = a.m.face, q = faceAt(id, o.b, o.bt, ts, o.still), bd = o.still || o.rigid ? null : bodyAt(id, q, ts), gl = warpGL && warpGL.ok;
  compose(a, q);
  let pic; if (gl) { warpGL.draw(a, q, bd, ts, o.zf); pic = warpGL.cv; }      // the mesh also does the presenter's zoom: one resampling of the picture, not two
  else pic = warpFlat(a, q.yaw * 0.11 * f.iod, q.pit * 0.08 * f.iod, q.roll);
  if (!o.noBg) { c.save(); c.translate(f.cx, f.cy); c.scale(o.zb, o.zb); c.translate(-f.cx, -f.cy); c.drawImage(a.bg, 0, 0); c.restore(); }
  if (o.mid) o.mid();
  c.save();
  if (!gl) { c.translate(f.cx, f.cy); c.scale(o.zf, o.zf); c.translate(-f.cx, -f.cy); }
  if (!gl && bd) {                 // without the mesh the whole figure leans from its bottom edge (which stays where it is) and rises a little with the breath
    c.transform(1, 0, -bd.sx / (FH - f.cy), 1, bd.sx * FH / (FH - f.cy), 0);
    c.translate(f.cx, FH); c.scale(1, 1 + bd.lean + 0.6 * bd.lift / (FH - f.cy)); c.translate(-f.cx, -FH);
  }
  c.drawImage(pic, 0, 0);
  c.restore();
}
function view(dx, dy, dw, dh, sx, sy, sw, sh, fn) {
  c.save(); c.beginPath(); c.rect(dx, dy, dw, dh); c.clip(); c.translate(dx, dy); c.scale(dw / sw, dh / sh); c.translate(-sx, -sy); fn(); c.restore();
}
function drawStill(key, p, dir) {
  const z = 1.07 + 0.07 * p; c.save(); c.translate(FW / 2 + (dir || 1) * (p - 0.5) * 34, FH / 2); c.scale(z, z); c.drawImage(STILL[key], -FW / 2, -FH / 2, FW, FH); c.restore();
}
function blurBack(key, dark) {
  softx.drawImage(STILL[key], 0, 0, 64, 36); c.drawImage(soft, 0, 0, 64, 36, -30, -20, FW + 60, FH + 40);
  c.fillStyle = `rgba(4,10,24,${dark})`; c.fillRect(0, 0, FW, FH);
}
function otsBox(b, left) {
  const x = left ? 50 : 668, y = 84, w = 306, h = 214;
  c.save(); c.shadowColor = 'rgba(0,0,0,.6)'; c.shadowBlur = 24; c.shadowOffsetY = 6; rr(x, y, w, h, 10); c.fillStyle = '#060d1c'; c.fill(); c.restore();
  c.save(); rr(x, y, w, h, 10); c.clip(); c.drawImage(STILL[b.ots[0]], 0, 30, FW, FH - 60, x, y, w, 160);
  const g = c.createLinearGradient(0, y + 110, 0, y + 160); g.addColorStop(0, 'rgba(6,13,28,0)'); g.addColorStop(1, 'rgba(6,13,28,.9)'); c.fillStyle = g; c.fillRect(x, y + 110, w, 50);
  c.fillStyle = '#060d1c'; c.fillRect(x, y + 160, w, 54); c.fillStyle = ACC; c.fillRect(x, y + 160, w, 3);
  c.fillStyle = '#fff'; c.font = `800 21px ${SANS}`; c.textAlign = 'left'; c.textBaseline = 'alphabetic'; c.fillText(b.ots[1], x + 16, y + 196);
  c.restore(); rr(x, y, w, h, 10); c.strokeStyle = 'rgba(255,255,255,.25)'; c.lineWidth = 1.5; c.stroke();
}
function paneCrop(a, w, h) {
  const f = a.m.face; let ch = Math.min(FH, 5.9 * f.iod), cw = ch * w / h; if (cw > FW) { cw = FW; ch = cw * h / w; }
  return [clamp(f.cx - cw / 2, 0, FW - cw), clamp(f.cy + 0.55 * f.iod - ch / 2, 0, FH - ch), cw, ch];
}
function pane(x, y, w, h, id, b, t, bt, remote) {
  const a = ACT[id], on = b.who === id, k = paneCrop(a, w, h);
  const lead = remote ? 0.02 : 0;      // a held picture is on average half its interval old: draw the caller that much ahead
  view(x, y, w, h, k[0], k[1], k[2], k[3], () => drawActor(id, b.start + bt + lead, { b, bt: bt + lead, zb: 1, zf: 1.012 }));
  if (remote) {                    // a video call: softer, and 25 pictures a second
    const tick = Math.floor(t * 25); if (tick !== lofiTick) { lofiTick = tick; lofix.drawImage(scr, x, y, w, h, 0, 0, 308, 227); }
    c.drawImage(lofi, 0, 0, 308, 227, x, y, w, h);
  }
  const g = c.createLinearGradient(0, y + h - 70, 0, y + h); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(0,0,0,.8)'); c.fillStyle = g; c.fillRect(x, y + h - 70, w, 70);
  c.fillStyle = ACC; c.fillRect(x + 14, y + h - 40, 4, 26);
  c.textAlign = 'left'; c.textBaseline = 'alphabetic'; c.fillStyle = '#fff'; c.font = `800 17px ${SANS}`; c.fillText(CAST[id].name, x + 26, y + h - 26);
  c.fillStyle = 'rgba(255,255,255,.8)'; c.font = `13px ${SANS}`; c.fillText(CAST[id].role, x + 26, y + h - 10);
  c.strokeStyle = on ? '#fff' : 'rgba(255,255,255,.28)'; c.lineWidth = on ? 3 : 1.5; c.strokeRect(x, y, w, h);
}
function weatherIcon(kind, x, y, t) {
  c.save(); c.shadowColor = 'rgba(0,0,0,.55)'; c.shadowBlur = 10; c.shadowOffsetY = 3; c.lineCap = 'round';
  if (kind === 'sun') {
    c.strokeStyle = '#ffd43b'; c.lineWidth = 4;
    for (let i = 0; i < 8; i++) { const a = i * Math.PI / 4 + t * 0.6; c.beginPath(); c.moveTo(x + Math.cos(a) * 24, y + Math.sin(a) * 24); c.lineTo(x + Math.cos(a) * 33, y + Math.sin(a) * 33); c.stroke(); }
    c.fillStyle = '#ffd43b'; ell(x, y, 18, 18); c.fill();
  } else {
    c.fillStyle = kind === 'rain' ? '#c3ccd9' : '#fff';
    c.beginPath(); c.arc(x - 16, y + 4, 14, 0, 7); c.arc(x + 2, y - 6, 19, 0, 7); c.arc(x + 20, y + 4, 13, 0, 7); c.rect(x - 16, y + 4, 36, 13); c.fill();
    if (kind === 'rain') { c.strokeStyle = '#8fd0ff'; c.lineWidth = 3; for (let i = 0; i < 4; i++) { const d = (t * 30 + i * 9) % 18; c.beginPath(); c.moveTo(x - 18 + i * 12, y + 22 + d); c.lineTo(x - 21 + i * 12, y + 30 + d); c.stroke(); } }
    else { c.strokeStyle = ACC; c.lineWidth = 4; c.beginPath(); c.arc(x + 2, y + 38, 9, t * 5, t * 5 + 4.2); c.stroke(); }
  }
  c.restore();
}

// Cutaways run from one word of a line to another; returns [start, end, still] while one is on screen.
function cutAt(b, bt) {
  if (b.cuts) for (const k of b.cuts) { const t0 = k[0] ? b.wt[k[0]] - 0.1 : 0, t1 = k[1] == null ? b.dur : b.wt[k[1]] - 0.1; if (bt >= t0 && bt < t1) return [t0, t1, k[2]]; }
  return null;
}
// Where the bulletin is at time t: the line being spoken and how far into it. The sound engine asks the same question.
function showAt(t) {
  if (pending > 0) return null;
  if (readyAt < 0) readyAt = t;
  const ts = Math.max(0, t - Math.max(readyAt, switchedAt + 0.32)) % SHOW_LEN;
  let bi = BEATS.length - 1; while (BEATS[bi].start > ts) bi--;
  return { b: BEATS[bi], bt: ts - BEATS[bi].start, ts };
}
function chNews(t) {
  c.textBaseline = 'alphabetic'; c.globalAlpha = 1;
  if (pending > 0) {              // still decoding the pictures
    c.fillStyle = '#050b1a'; c.fillRect(0, 0, SW, SH); opsLogo(SW / 2 - 40, 210, 80);
    c.fillStyle = '#fff'; c.textAlign = 'center'; c.font = `800 30px ${SANS}`; c.fillText('DEVOPS TONIGHT', SW / 2, 345); return;
  }
  const at = showAt(t), b = at.b, bt = at.bt, ts = at.ts, sp = clamp((ts - b.shot0) / b.shotLen, 0, 1);
  const cut = b.cuts ? cutAt(b, bt) : null;
  const showStrap = !!b.strap;

  if (b.intro || b.outro) {
    drawStill('studio', bt / b.dur, b.outro ? -1 : 1);
    const g = c.createLinearGradient(0, 0, 0, SH); g.addColorStop(0, 'rgba(3,8,22,.35)'); g.addColorStop(1, 'rgba(3,8,22,.82)'); c.fillStyle = g; c.fillRect(0, 0, SW, SH);
    if (b.intro) {
      c.lineWidth = 5; c.lineCap = 'butt';
      for (let i = 0; i < 5; i++) { c.strokeStyle = i % 2 ? 'rgba(46,230,166,.7)' : 'rgba(255,255,255,.3)'; c.beginPath(); const a = t * (0.8 + i * 0.3) * (i % 2 ? 1 : -1); c.arc(SW / 2, 214, 112 + i * 32, a, a + 1.6 + i * 0.5); c.stroke(); }
      const k = Math.min(1, bt / 0.8), s = 140 * (1 - Math.pow(1 - k, 3)); opsLogo(SW / 2 - s / 2, 214 - s / 2, s);
      const al = clamp((bt - 0.9) / 0.6, 0, 1); c.globalAlpha = al; c.textAlign = 'center'; c.fillStyle = '#fff';
      c.font = `800 62px ${SANS}`; c.fillText('DEVOPS TONIGHT', SW / 2, 428 + (1 - al) * 18);
      c.font = `22px ${SANS}`; c.fillStyle = ACC; c.fillText('with Paige Duty and Cy Dekar', SW / 2, 468); c.globalAlpha = 1;
    } else {
      opsLogo(SW / 2 - 45, 150, 90); c.textAlign = 'center'; c.fillStyle = '#fff'; c.font = `800 40px ${SANS}`; c.fillText('DEVOPS TONIGHT', SW / 2, 300);
      c.font = `20px ${SANS}`; c.fillStyle = 'rgba(255,255,255,.85)'; c.fillText('This bulletin was deployed on a Friday. No rollbacks so far.', SW / 2, 340);
      c.font = `15px ${SANS}`; c.fillStyle = ACC; c.fillText('Presenters and locations are AI-generated stills with synthetic voices, animated in plain JavaScript', SW / 2, 372);
    }
  } else if (cut) {
    drawStill(cut[2], clamp((bt - cut[0]) / (cut[1] - cut[0]), 0, 1), cut[2] === 'servers' ? -1 : 1);
  } else if (b.split) {
    blurBack('studio', 0.62);
    c.fillStyle = '#e23b2e'; c.fillRect(40, 26, 7, 28); c.fillStyle = '#fff'; c.font = `800 21px ${SANS}`; c.textAlign = 'left'; c.fillText(b.title, 58, 48);
    pane(40, 74, 462, 340, b.split[0], b, t, bt, false); pane(522, 74, 462, 340, b.split[1], b, t, bt, b.split[1] === 'mel');
  } else if (b.wx != null) {
    c.save(); c.translate(SW / 2 + 60 - sp * 50, SH / 2 - 6); c.scale(1.22, 1.22); c.drawImage(STILL.sat, -SW / 2, -SH / 2, SW, SH); c.restore();
    c.fillStyle = 'rgba(5,18,48,.38)'; c.fillRect(0, 0, SW, SH);
    const g = c.createLinearGradient(0, 0, 0, 90); g.addColorStop(0, 'rgba(3,8,22,.75)'); g.addColorStop(1, 'rgba(3,8,22,0)'); c.fillStyle = g; c.fillRect(0, 0, SW, 90);
    c.fillStyle = '#fff'; c.font = `800 22px ${SANS}`; c.textAlign = 'left'; c.fillText('CLUSTER MAP · TONIGHT', 470, 48);
    const spots = [['pending', 610, 150, 'Pending'], ['sun', 880, 230, '99.99%'], ['rain', 690, 330, '503']];
    const target = b.wx === 0 ? spots[0] : (bt < b.wt[10] ? spots[2] : spots[1]);
    for (const s of spots) {
      const hot = s === target; rr(s[1] - 62, s[2] - 40, 124, 128, 12); c.fillStyle = hot ? 'rgba(6,16,40,.72)' : 'rgba(6,16,40,.45)'; c.fill();
      if (hot) { c.strokeStyle = ACC; c.lineWidth = 2.5 + Math.sin(t * 6); c.stroke(); }
      weatherIcon(s[0], s[1], s[2], t);
      c.fillStyle = '#fff'; c.font = `800 20px ${SANS}`; c.textAlign = 'center'; c.fillText(s[3], s[1], s[2] + 74);
    }
    const a = ACT.sunny, f = a.m.face, z = a.m.wxScale || 1;
    c.save(); c.translate(250, 250); c.scale(z, z); c.translate(-f.cx, -f.cy);
    drawActor('sunny', ts, { b, bt, noBg: true, zb: 1, zf: 1 });
    c.restore();
  } else {
    // a single presenter on camera: slow push-in, parallax between person and set, hand-held when live
    const left = ACT[b.who].m.face.cx > 560, ox = b.ots ? (left ? 46 : -46) : 0;        // make room for the over-the-shoulder box
    const z = (b.ots ? 1.1 : 1.035) + 0.05 * ease(sp), sh = b.live ? 1 : 0.12;
    c.save(); c.translate(SW / 2 + ox + wob(t, 3) * 3.4 * sh, SH / 2 + wob(t, 9) * 2.6 * sh); c.rotate(wob(t * 0.8, 5) * 0.0035 * sh); c.scale(z, z); c.translate(-SW / 2, -SH / 2);
    drawActor(b.who, ts, { b, bt, zb: 1, zf: 1.012 + 0.022 * ease(sp), mid: b.ots ? () => otsBox(b, left) : null });
    c.restore();
  }

  // the camera's own texture: sensor grain and a little vignette, under the graphics
  c.save(); c.globalCompositeOperation = 'overlay'; c.globalAlpha = 0.11;
  const gx = Math.floor(Math.random() * 256), gy = Math.floor(Math.random() * 256);
  for (let y = -gy; y < SH; y += 256) for (let x = -gx; x < SW; x += 256) c.drawImage(grain, x, y);
  c.restore();
  const vg = c.createRadialGradient(SW / 2, SH / 2, SH * 0.55, SW / 2, SH / 2, SH * 1.05); vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(0,0,0,.34)'); c.fillStyle = vg; c.fillRect(0, 0, SW, SH);

  /* ── graphics ── */
  c.textAlign = 'left';
  if (!b.intro && !b.outro) {                                   // channel bug
    c.globalAlpha = 0.85; opsLogo(SW - 62, 22, 30); c.globalAlpha = 1;
    c.fillStyle = 'rgba(255,255,255,.85)'; c.font = `800 13px ${SANS}`; c.textAlign = 'right'; c.fillText('DEVOPS TONIGHT', SW - 72, 42); c.textAlign = 'left';
  }
  if (b.live && !b.split) {
    c.fillStyle = '#e23b2e'; rr(36, 26, 76, 30, 4); c.fill(); c.fillStyle = '#fff'; c.font = `800 16px ${SANS}`; c.fillText('LIVE', 62, 47);
    if (t % 1.2 < 0.8) { ell(50, 41, 5, 5); c.fill(); }
    c.fillStyle = 'rgba(0,0,0,.6)'; rr(116, 26, 112, 30, 4); c.fill(); c.fillStyle = '#fff'; c.font = `600 15px ${SANS}`; c.fillText(b.live, 128, 46);
  }
  if (b.text) {
    if (showStrap && !cut && bt < 3.8) {                        // name strap
      const k = ease(clamp(Math.min(bt / 0.35, (3.8 - bt) / 0.35), 0, 1)), p = CAST[b.who];
      c.save(); c.beginPath(); c.rect(40, 372, 440 * k, 64); c.clip();
      c.fillStyle = 'rgba(4,10,24,.86)'; c.fillRect(40, 372, 440, 64); c.fillStyle = ACC; c.fillRect(40, 372, 6, 64);
      c.fillStyle = '#fff'; c.font = `800 23px ${SANS}`; c.fillText(p.name, 60, 400); c.fillStyle = ACC; c.font = `600 15px ${SANS}`; c.fillText(p.role, 60, 424); c.restore();
    }
    // closed captions, revealed word by word as the line is spoken
    let n = 0, said = 0; while (said < b.wt.length && b.wt[said] <= bt) n += b.words[said++].length + 1;
    if (n > 0) {
      c.font = `600 21px ${SANS}`; const ls = lines(b.text, 860); let left = n, y = 452;
      for (const ln of ls) { if (left <= 0) break; const s = ln.slice(0, left), w = c.measureText(s).width;
        c.fillStyle = 'rgba(0,0,0,.78)'; c.fillRect(SW / 2 - c.measureText(ln).width / 2 - 10, y, w + 20, 27); c.fillStyle = '#fff'; c.fillText(s, SW / 2 - c.measureText(ln).width / 2, y + 20); left -= ln.length + 1; y += 27; }
    }
  }
  c.fillStyle = '#060d1c'; c.fillRect(0, 512, SW, 64); c.fillStyle = ACC; c.fillRect(0, 512, SW, 2);
  c.fillStyle = '#dfe9ff'; c.font = `19px ${SANS}`; c.textAlign = 'left';
  const tw = c.measureText(TICKER).width, off = (t * 100) % tw; c.fillText(TICKER, -off, 551); c.fillText(TICKER, -off + tw, 551);
  c.fillStyle = ACC; c.fillRect(0, 512, 118, 64);
  c.fillStyle = '#06281d'; c.font = `800 24px ${SANS}`; c.textAlign = 'center'; c.fillText(new Date().toTimeString().slice(0, 5), 59, 553);
}
