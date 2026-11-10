/* ───────────────────────── Sound ─────────────────────────
   Web Audio, no libraries. The voices are recordings: one MP3 per line, inlined next to its timing. Everything else is
   synthesised here: the title music, room tone, outdoor air, the video-call sound, static, clicks and the other channels.
   The set is a point in space and the listener sits at the camera: backing away quietens it and brings up the sound of
   the room, moving off to the side takes some level off, and going behind the panel muffles it. Nothing plays until the viewer turns sound on, because browsers require a click. */
const CALIB = /*CALIB*/'';            // a tiny MP3 with a tone burst at a known time, used to measure the decoder's delay
const snd = { ac: null, on: false, ready: false, vol: 0.7, bufs: [], sting: {}, lag: 0, cur: null, mus: null, osdAt: -9, sw: null, pw: null, hits: -1, tick: -1, keep: null };

function sndBytes(uri) { const bin = atob(uri.slice(uri.indexOf(',') + 1)), u = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i); return u.buffer; }
function sndDecode(uri) { return new Promise((ok, no) => snd.ac.decodeAudioData(sndBytes(uri), ok, no)); }        // callback form: older Safari has no promise
function sndNoise(ctx, sec, brown) {
  const n = Math.floor(sec * ctx.sampleRate), b = ctx.createBuffer(1, n, ctx.sampleRate), d = b.getChannelData(0); let last = 0;
  for (let i = 0; i < n; i++) { const w = Math.random() * 2 - 1; if (brown) { last = (last + 0.02 * w) / 1.02; d[i] = last * 3.5; } else d[i] = w; }
  return b;
}
function sndFilter(ctx, type, f, q, gain) { const n = ctx.createBiquadFilter(); n.type = type; n.frequency.value = f; if (q != null) n.Q.value = q; if (gain != null) n.gain.value = gain; return n; }
function sndGain(ctx, v) { const n = ctx.createGain(); n.gain.value = v; return n; }
function sndChain(nodes) { for (let i = 0; i < nodes.length - 1; i++) nodes[i].connect(nodes[i + 1]); return nodes[0]; }
function sndTo(node, v, tc) { if (node._v === v) return; node._v = v; node.gain.setTargetAtTime(v, snd.ac.currentTime, tc || 0.12); }

// A room as an impulse response: a few discrete early reflections (ms, gain) per ear, then a decaying, dulled noise tail whose
// overall gain is `tail`. Built to exact levels (the browser's own normalising is off), so it sounds the same everywhere.
function sndRoom(ac, sec, tail, tapsL, tapsR) {
  const n = Math.floor(ac.sampleRate * sec), buf = ac.createBuffer(2, n, ac.sampleRate), i0 = Math.floor(ac.sampleRate * 0.024);
  for (let ch = 0; ch < 2; ch++) {
    const d = buf.getChannelData(ch); let lp = 0, e = 0;
    for (let i = i0; i < n; i++) { lp += 0.32 * ((Math.random() * 2 - 1) - lp); d[i] = lp * Math.pow(1 - i / n, 2.6); e += d[i] * d[i]; }
    const k = tail / Math.sqrt(e); for (let i = i0; i < n; i++) d[i] *= k;
    for (const [ms, g] of ch ? tapsR : tapsL) d[Math.floor(ac.sampleRate * ms / 1000)] += g;
  }
  const cv = ac.createConvolver(); cv.normalize = false; cv.buffer = buf; return cv;
}

/* Build the graph. Must be called from a click or key press. */
function sndCreate() {
  const AC = window.AudioContext || window.webkitAudioContext; if (!AC) return false;
  const ac = snd.ac = new AC(), G = v => sndGain(ac, v);
  snd.master = G(0); snd.occl = sndFilter(ac, 'lowpass', 18000, 0.5);
  snd.pan = ac.createPanner(); snd.pan.panningModel = 'equalpower'; snd.pan.distanceModel = 'inverse'; snd.pan.refDistance = 2.55; snd.pan.rolloffFactor = 0.9;
  snd.pan.coneInnerAngle = 140; snd.pan.coneOuterAngle = 320; snd.pan.coneOuterGain = 0.4;       // the speakers face the room
  sndChain([snd.master, snd.occl, snd.pan, ac.destination]);
  // The viewer's room. Besides the direct sound, the set is heard off the walls: a few early reflections and a short,
  // dull tail, different in each ear. It does not pass through the cone above, and it grows as the listener backs away.
  const room = sndRoom(ac, 0.42, 0.45, [[6, 0.35], [13, 0.28], [19, -0.22], [28, 0.18]], [[8, 0.33], [15, -0.27], [22, 0.22], [31, 0.17]]);
  snd.roomSend = G(0); sndChain([snd.occl, snd.roomSend, room, ac.destination]);
  snd.voice = G(1); snd.bed = G(1); snd.music = G(0.8); snd.ui = G(1);
  for (const n of [snd.voice, snd.bed, snd.music, snd.ui]) n.connect(snd.master);
  // a little of the studio around the anchors' microphones: a treated room, so only a trace
  const rev = sndRoom(ac, 0.3, 0.3, [[11, 0.2], [17, 0.15]], [[9, 0.2], [21, -0.15]]); sndChain([rev, G(0.16), snd.voice]);
  // one microphone chain per kind of voice
  const studio = G(1); sndChain([studio, sndFilter(ac, 'highpass', 70, 0.7), snd.voice]); studio.connect(rev);
  const field = G(1), fmic = sndFilter(ac, 'highpass', 170, 0.7); sndChain([field, fmic, sndFilter(ac, 'peaking', 2600, 0.9, 3), sndFilter(ac, 'lowpass', 7500, 0.7), snd.voice]);
  const slap = ac.createDelay(0.2); slap.delayTime.value = 0.058; sndChain([field, slap, sndFilter(ac, 'lowpass', 2400, 0.5), G(0.09), fmic]);          // the reporter's voice comes back faintly off the building
  const shaper = ac.createWaveShaper(), curve = new Float32Array(257); for (let i = 0; i < 257; i++) { const x = i / 128 - 1; curve[i] = Math.tanh(1.1 * x) / Math.tanh(1.1); } shaper.curve = curve;
  // The guest is on a video call: a laptop microphone in a small bare room. Today's calls carry nearly the whole voice, so this is
  // a little boxy and a little close, not a telephone. (The first version cut everything above 3.6 kHz and overdrove it, which
  // made the one voice that passes through it the worst-sounding in the bulletin.)
  const call = G(1), cmic = sndFilter(ac, 'highpass', 120, 0.7); sndChain([call, cmic, sndFilter(ac, 'lowpass', 6800, 0.7), sndFilter(ac, 'peaking', 450, 1.0, 2.5), shaper, G(0.68), snd.voice]);
  const box = ac.createDelay(0.2), fb = G(0.28); box.delayTime.value = 0.027; sndChain([call, box, sndFilter(ac, 'lowpass', 3000, 0.5), G(0.2), cmic]); sndChain([box, fb, box]);
  snd.chain = { studio, field, call };
  // looping beds, silent until a scene asks for them
  const white = sndNoise(ac, 2, false), brown = sndNoise(ac, 4, true); snd.white = white;
  const loop = buf => { const s = ac.createBufferSource(); s.buffer = buf; s.loop = true; s.start(); return s; };
  const osc = (type, f) => { const o = ac.createOscillator(); o.type = type; o.frequency.value = f; o.start(); return o; };
  const bed = () => { const g = G(0); g.connect(snd.bed); return g; };
  snd.room = bed(); sndChain([loop(brown), sndFilter(ac, 'lowpass', 500, 0.5), G(0.03), snd.room]);
  snd.air = bed(); const gust = G(1); gust.connect(snd.air); sndChain([osc('sine', 0.11), G(0.35), gust.gain]);       // slow gusts
  sndChain([loop(brown), sndFilter(ac, 'lowpass', 1100, 0.5), G(0.22), gust]); sndChain([loop(white), sndFilter(ac, 'bandpass', 2600, 0.4), G(0.012), gust]);
  sndChain([loop(brown), sndFilter(ac, 'bandpass', 118, 2.2), G(0.1), snd.air]); sndChain([osc('triangle', 97.5), G(0.003), snd.air]); sndChain([osc('triangle', 146.2), G(0.0015), snd.air]);       // cooling plant on the roof
  const pass = G(0.05); pass.connect(snd.air); sndChain([osc('sine', 0.045), G(0.04), pass.gain]); sndChain([loop(brown), sndFilter(ac, 'bandpass', 420, 0.6), pass]);                // traffic, far off, coming and going
  snd.line = bed(); sndChain([loop(white), sndFilter(ac, 'bandpass', 1500, 0.5), G(0.006), snd.line]);                                                  // the open line of a video call
  snd.hum = bed(); sndChain([loop(brown), sndFilter(ac, 'lowpass', 260, 0.5), G(0.3), snd.hum]); sndChain([osc('sine', 100), G(0.02), snd.hum]); sndChain([loop(white), sndFilter(ac, 'bandpass', 5200, 0.6), G(0.006), snd.hum]);
  snd.pad = bed(); const pf = sndFilter(ac, 'lowpass', 700, 0.7); sndChain([pf, G(0.09), snd.pad]); for (const f of [110, 164.81, 220.4]) osc('triangle', f).connect(pf);
  snd.tone = bed(); sndChain([osc('sine', 1000), G(0.03), snd.tone]);
  snd.log = bed(); sndChain([loop(brown), sndFilter(ac, 'lowpass', 180, 0.5), G(0.25), snd.log]);
  return true;
}

/* Decode the lines, measure the decoder's delay, and render the two pieces of music. */
function sndLoad(set) {
  snd.ready = false; snd.bufs = [];
  const jobs = (set || SPEECH).map((L, i) => sndDecode(L.audio).then(b => { snd.bufs[i] = b; }));
  if (CALIB) jobs.push(sndDecode(CALIB).then(b => {                 // the burst was encoded at 0.100 s; wherever it turns up, the difference is delay
    const d = b.getChannelData(0); let i = 0; while (i < d.length && Math.abs(d[i]) < 0.2) i++; snd.lag = clamp(i / b.sampleRate - 0.1, -0.02, 0.12);
  }));
  for (const k of ['intro', 'outro']) jobs.push(sndSting(k).then(b => { snd.sting[k] = b; }).catch(() => {}));
  return Promise.all(jobs).then(() => { snd.ready = true; }).catch(() => { snd.ready = snd.bufs.length > 0; });
}

/* The news theme, rendered once into a buffer. Key of D at 132 beats a minute: a driving pulse, a rising brass figure,
   drum hits and a cymbal swell into a held chord. The closing version is the chord with a falling figure. */
function sndSting(kind) {
  const OC = window.OfflineAudioContext || window.webkitOfflineAudioContext; if (!OC) return Promise.reject();
  const sr = 44100, len = kind === 'intro' ? 5.6 : 5.2, oc = new OC(2, Math.floor(sr * len), sr), out = sndGain(oc, 0.8), q = 60 / 132, s = q / 4;
  const comp = oc.createDynamicsCompressor(); comp.threshold.value = -14; comp.ratio.value = 4; sndChain([out, comp, oc.destination]);
  const noise = sndNoise(oc, 2, false);
  const env = (p, pts) => { p.setValueAtTime(pts[0][1], pts[0][0]); for (let i = 1; i < pts.length; i++) p.linearRampToValueAtTime(pts[i][1], pts[i][0]); };
  const brass = (f, t0, dur, peak, cut) => {                        // three slightly detuned saws through a filter that opens on the attack
    const lp = sndFilter(oc, 'lowpass', 500, 0.8), g = sndGain(oc, 0); sndChain([lp, g, out]);
    env(lp.frequency, [[t0, 500], [t0 + 0.06, cut], [t0 + dur, cut * 0.6]]); env(g.gain, [[t0, 0], [t0 + 0.03, peak], [t0 + dur - 0.05, peak * 0.8], [t0 + dur + 0.12, 0]]);
    for (const c of [-7, 0, 7]) { const o = oc.createOscillator(); o.type = 'sawtooth'; o.frequency.value = f; o.detune.value = c; o.connect(lp); o.start(t0); o.stop(t0 + dur + 0.2); }
  };
  const pluck = (f, t0, peak) => {                                  // the pulse: a short filtered saw
    const o = oc.createOscillator(), lp = sndFilter(oc, 'lowpass', 1300, 1), g = sndGain(oc, 0); o.type = 'sawtooth'; o.frequency.value = f; sndChain([o, lp, g, out]);
    env(g.gain, [[t0, 0], [t0 + 0.005, peak], [t0 + 0.09, 0]]); o.start(t0); o.stop(t0 + 0.12);
  };
  const drum = (t0, peak) => {                                      // a pitched thump with a short noise attack
    const o = oc.createOscillator(), g = sndGain(oc, 0); o.type = 'sine'; sndChain([o, g, out]);
    env(o.frequency, [[t0, 130], [t0 + 0.06, 73.42]]); env(g.gain, [[t0, 0], [t0 + 0.004, peak], [t0 + 0.9, 0]]); o.start(t0); o.stop(t0 + 1);
    const n = oc.createBufferSource(), ng = sndGain(oc, 0); n.buffer = noise; sndChain([n, sndFilter(oc, 'lowpass', 900, 0.7), ng, out]); env(ng.gain, [[t0, peak * 0.5], [t0 + 0.07, 0]]); n.start(t0); n.stop(t0 + 0.1);
  };
  const swell = (t0, t1, peak) => {                                 // cymbal: rising hiss, then a crash that rings out
    const n = oc.createBufferSource(), g = sndGain(oc, 0); n.buffer = noise; n.loop = true; sndChain([n, sndFilter(oc, 'highpass', 5200, 0.7), g, out]);
    env(g.gain, [[t0, 0], [t1 - 0.02, peak * 0.5], [t1, peak], [t1 + 0.5, peak * 0.3], [t1 + 1.7, 0]]); n.start(t0); n.stop(t1 + 1.8);
  };
  const D2 = 73.42, D3 = 146.83, D4 = 293.66, Fs4 = 369.99, A4 = 440, B4 = 493.88, D5 = 587.33, A3 = 220;
  if (kind === 'intro') {
    const n = oc.createBufferSource(), bp = sndFilter(oc, 'bandpass', 400, 1.2), g = sndGain(oc, 0); n.buffer = noise; sndChain([n, bp, g, out]);      // opening whoosh
    env(bp.frequency, [[0, 400], [0.5, 4200]]); env(g.gain, [[0, 0], [0.25, 0.22], [0.55, 0]]); n.start(0); n.stop(0.6);
    for (let i = 0; i < 28; i++) { pluck(D3, i * s, i % 4 ? 0.07 : 0.13); if (i % 4 === 0) pluck(D2, i * s, 0.16); }
    brass(D4, q, q * 0.9, 0.075, 2200); brass(A4, q * 2, q * 0.9, 0.075, 2300); brass(D5, q * 3, q * 1.9, 0.08, 2500);
    brass(B4, q * 5, q * 0.9, 0.07, 2300); brass(A4, q * 6, q * 0.9, 0.07, 2300);
    for (const [f, p] of [[D3, 0.07], [A3, 0.06], [D4, 0.06], [Fs4, 0.055], [A4, 0.055], [D5, 0.06]]) brass(f, q * 7, 1.7, p, 2400);                 // the held chord
    drum(0, 0.4); drum(q * 3, 0.32); drum(q * 7, 0.5); swell(q * 5, q * 7, 0.11);
  } else {
    for (const [f, p] of [[D3, 0.06], [A3, 0.05], [D4, 0.05], [Fs4, 0.045], [A4, 0.045]]) brass(f, 0.05, 3.6, p, 1800);
    brass(D5, 0.25, 0.42, 0.075, 2400); brass(A4, 0.7, 0.42, 0.075, 2300); brass(Fs4, 1.15, 0.42, 0.075, 2200); brass(D4, 1.6, 2.2, 0.08, 2200);
    drum(0.25, 0.36); drum(1.6, 0.46); swell(0.9, 1.6, 0.09);
  }
  return new Promise((ok, no) => { oc.oncomplete = e => ok(e.renderedBuffer); const p = oc.startRendering(); if (p && p.catch) p.catch(no); });
}

/* One-shots through the set's speaker. */
function sndShot(build) { const ac = snd.ac; if (!ac || !snd.on) return; build(ac, ac.currentTime + 0.01, snd.ui); }
function sndStatic() { sndShot((ac, t, out) => { const n = ac.createBufferSource(), g = sndGain(ac, 0); n.buffer = snd.white; sndChain([n, sndFilter(ac, 'bandpass', 1800, 0.4), g, out]);
  g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(0.2, t + 0.01); g.gain.setValueAtTime(0.2, t + 0.27); g.gain.linearRampToValueAtTime(0, t + 0.32); n.start(t); n.stop(t + 0.34); }); }
function sndBlip(f, at) { sndShot((ac, t, out) => { const o = ac.createOscillator(), g = sndGain(ac, 0); o.frequency.value = f; sndChain([o, g, out]); const t0 = t + (at || 0);
  g.gain.setValueAtTime(0, t0); g.gain.linearRampToValueAtTime(0.07, t0 + 0.005); g.gain.exponentialRampToValueAtTime(0.0005, t0 + 0.09); o.start(t0); o.stop(t0 + 0.1); }); }
function sndTick() { sndShot((ac, t, out) => { const n = ac.createBufferSource(), g = sndGain(ac, 0.05); n.buffer = snd.white; sndChain([n, sndFilter(ac, 'highpass', 3000, 0.7), g, out]); n.start(t, Math.random(), 0.006); }); }
function sndPower(on) { sndShot((ac, t, out) => { const o = ac.createOscillator(), g = sndGain(ac, 0); sndChain([o, g, out]);
  if (on) { o.frequency.setValueAtTime(90, t); o.frequency.exponentialRampToValueAtTime(48, t + 0.22); g.gain.setValueAtTime(0.25, t); g.gain.exponentialRampToValueAtTime(0.001, t + 0.28); }
  else { o.frequency.setValueAtTime(420, t); o.frequency.exponentialRampToValueAtTime(70, t + 0.12); g.gain.setValueAtTime(0.1, t); g.gain.exponentialRampToValueAtTime(0.001, t + 0.14); }
  o.start(t); o.stop(t + 0.3); }); }

/* Keep a recording locked to the picture: `want` is where in the buffer we should be right now. */
function sndPlay(slot, key, buf, dest, want, rate) {
  const ac = snd.ac, cur = snd[slot], r = rate || 1;
  if (cur && cur.key === key && cur.r === r && Math.abs((ac.currentTime - cur.t0) * r - want) < 0.08) return;
  sndStop(slot); if (!buf || want > buf.duration - 0.03) { snd[slot] = { key, r, t0: ac.currentTime - want / r, src: null }; return; }
  const src = ac.createBufferSource(), g = sndGain(ac, 1); src.buffer = buf; src.playbackRate.value = r; sndChain([src, g, dest]);
  if (want >= 0) src.start(0, want); else src.start(ac.currentTime - want / r);
  snd[slot] = { key, r, src, g, t0: ac.currentTime - want / r };
}
function sndStop(slot) {
  const cur = snd[slot]; snd[slot] = null; if (!cur || !cur.src) return;
  try { cur.g.gain.setTargetAtTime(0, snd.ac.currentTime, 0.012); cur.src.stop(snd.ac.currentTime + 0.06); } catch (e) {}
}
// The ear hears late by whatever the output path adds, and the eye sees late by about a frame of display delay.
// The recording is started ahead by the first and held back by the second.
function sndLatency() { const ac = snd.ac; return snd.lag + (ac.outputLatency || ac.baseLatency || 0) - 0.02; }
function sndVoiceKind(b) { return b.who === 'mel' ? 'call' : b.who === 'dee' ? 'field' : 'studio'; }

/* Called once per frame by the television. Audio is scheduled against the clock as it is now, not the frame's
   timestamp, so a frame that arrives late does not drag the voice back. */
function soundFrame(frameT, eye) {
  const ac = snd.ac; if (!ac || !snd.on) return;
  const t = performance.now() / 1000;
  // the listener is the camera, facing the set; the set's speaker sits at the panel
  const L = ac.listener, tv = [0, PY, 0], dx = tv[0] - eye[0], dy = tv[1] - eye[1], dz = tv[2] - eye[2], dist = Math.hypot(dx, dy, dz) || 1;
  if (L.positionX) { L.positionX.value = eye[0]; L.positionY.value = eye[1]; L.positionZ.value = eye[2]; L.forwardX.value = dx / dist; L.forwardY.value = dy / dist; L.forwardZ.value = dz / dist; L.upX.value = 0; L.upY.value = 1; L.upZ.value = 0; }
  else { L.setPosition(eye[0], eye[1], eye[2]); L.setOrientation(dx / dist, dy / dist, dz / dist, 0, 1, 0); }
  if (snd.pan.positionX) { snd.pan.positionX.value = 0; snd.pan.positionY.value = PY; snd.pan.positionZ.value = 0; snd.pan.orientationX.value = 0; snd.pan.orientationY.value = 0; snd.pan.orientationZ.value = 1; }
  else { snd.pan.setPosition(0, PY, 0); snd.pan.setOrientation(0, 0, 1); }
  const front = eye[2] / dist, cut = front > 0.15 ? 18000 : 18000 * Math.pow(0.07, Math.min(1, (0.15 - front) / 1.15));      // behind the panel the sound is muffled
  if (snd.occl._f !== cut) { snd.occl._f = cut; snd.occl.frequency.setTargetAtTime(cut, ac.currentTime, 0.08); }
  sndTo(snd.master, Math.pow(snd.vol, 1.6), 0.05);
  // remote events
  if (snd.pw !== powered) { if (snd.pw !== null) sndPower(powered); snd.pw = powered; }
  if (snd.sw !== switchedAt) { if (snd.sw !== null && powered && switchedAt <= t + 0.01) sndStatic(); snd.sw = switchedAt; }
  const live = powered && t - switchedAt >= 0.32, at = live && channel === 0 ? showAt(t) : null, b = at && at.b;
  // channel 1: the bulletin
  let air = 0, room = 0, hum = 0, line = 0;
  if (b && snd.ready) {
    if (b.sp) { sndPlay('cur', b.ai, snd.bufs[b.ai], snd.chain[sndVoiceKind(b)], at.bt - b.lead + sndLatency()); sndStop('mus'); }
    else { sndStop('cur'); const k = b.intro ? 'intro' : 'outro'; sndPlay('mus', k, snd.sting[k], snd.music, at.bt + sndLatency()); }
    const dee = b.who === 'dee' || (b.split && b.split.includes('dee')), cut = b.sp ? cutAt(b, at.bt) : null;
    air = dee ? (b.split ? (b.who === 'dee' ? 0.4 : 0.22) : 0.5) : 0; hum = cut && cut[2] === 'servers' ? 0.8 : 0; room = b.sp && !dee ? 1 : 0;
    line = b.split && b.split.includes('mel') ? (b.who === 'mel' && at.bt > b.t0 - 0.25 && at.bt < b.t1 + 0.3 ? 1 : 0.25) : 0;       // the caller's side opens up when he speaks
  } else { sndStop('cur'); sndStop('mus'); }
  sndTo(snd.air, air, 0.15); sndTo(snd.room, room, 0.3); sndTo(snd.hum, hum, 0.2); sndTo(snd.line, line, 0.06);
  sndTo(snd.roomSend, clamp(0.12 + 0.07 * (dist - 1.1), 0.12, 0.5), 0.2);            // about 16 dB under the direct sound from the usual seat, 9 dB from the back of the room
  // the other channels
  sndTo(snd.pad, live && channel === 1 ? 1 : 0, 0.3); sndTo(snd.log, live && channel === 3 ? 1 : 0, 0.3); sndTo(snd.tone, live && channel === 4 ? 1 : 0, 0.05);
  if (live && channel === 2) { if (snd.hits >= 0 && dvd.hits !== snd.hits) { if (dvd.corners !== snd.corners) { sndBlip(740); sndBlip(932, 0.09); sndBlip(1109, 0.18); } else sndBlip(620 + (dvd.hits % 5) * 70); } snd.hits = dvd.hits; snd.corners = dvd.corners; } else snd.hits = -1;
  if (live && channel === 3) { const k = Math.floor(t * 45 / 40); if (snd.tick >= 0 && k !== snd.tick) sndTick(); snd.tick = k; } else snd.tick = -1;
}
/* iPhones and iPads. Web Audio there follows the ringer switch: with the phone on silent, a page's sound is muted even
   though videos play. Two things lift that, and both must happen inside the tap: asking for a "playback" audio session
   (iOS 17 and later), and, for older systems, keeping a silent <audio> element playing, which puts the page in the
   same class as a video. Neither does anything on other devices. */
function sndSession() { try { if (navigator.audioSession) navigator.audioSession.type = 'playback'; } catch (e) {} }
function sndUnlock() {
  const ios = /iP(hone|ad|od)/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  if (ios && !snd.keep) {
    try {                                                        // half a second of silence as a plain 16-bit WAV, looped
      const n = 22050, b = new Uint8Array(44 + n), v = new DataView(b.buffer), put = (o, t) => { for (let i = 0; i < t.length; i++) b[o + i] = t.charCodeAt(i); };
      put(0, 'RIFF'); v.setUint32(4, 36 + n, true); put(8, 'WAVEfmt '); v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true);
      v.setUint32(24, 22050, true); v.setUint32(28, 44100, true); v.setUint16(32, 2, true); v.setUint16(34, 16, true); put(36, 'data'); v.setUint32(40, n, true);
      const el = snd.keep = document.createElement('audio'); el.src = URL.createObjectURL(new Blob([b], { type: 'audio/wav' }));
      el.loop = true; el.preload = 'auto'; el.setAttribute('playsinline', ''); el.setAttribute('x-webkit-airplay', 'deny');
    } catch (e) { snd.keep = null; }
  }
  if (snd.keep) { if (snd.on) { const p = snd.keep.play(); if (p && p.catch) p.catch(() => {}); } else snd.keep.pause(); }
  // start something inside the tap as well: older systems only unlock the context when a source starts in the gesture
  try { const src = snd.ac.createBufferSource(); src.buffer = snd.ac.createBuffer(1, 1, snd.ac.sampleRate); src.connect(snd.ac.destination); src.start(0); } catch (e) {}
}
// 'off', 'on', 'loading' (recordings still decoding) or 'blocked' (the device has not let the sound start: tap again)
function sndStatus() { return !snd.ac || !snd.on ? 'off' : snd.ac.state !== 'running' ? 'blocked' : snd.ready ? 'on' : 'loading'; }
const SND_LABEL = { off: 'Sound: off', on: 'Sound: on', loading: 'Sound: loading', blocked: 'Sound: tap again' };
function soundToggle() {
  sndSession();                                                  // before the audio context exists, so it starts life in the right class
  if (!snd.ac) { if (!sndCreate()) return false; sndLoad(); }
  const stuck = snd.on && snd.ac.state !== 'running';             // a tap while blocked is another try, not "off"
  if (!stuck) snd.on = !snd.on;
  sndUnlock();
  if (snd.on) { const p = snd.ac.resume(); if (p && p.catch) p.catch(() => {}); }
  else { sndStop('cur'); sndStop('mus'); const p = snd.ac.suspend(); if (p && p.catch) p.catch(() => {}); }
  return true;
}
// Coming back to the page (after a call, or from another app) the system may have paused the sound: pick it up again.
document.addEventListener('visibilitychange', () => {
  if (document.hidden || !snd.ac || !snd.on) return;
  const p = snd.ac.resume(); if (p && p.catch) p.catch(() => {}); if (snd.keep) { const q = snd.keep.play(); if (q && q.catch) q.catch(() => {}); }
});
