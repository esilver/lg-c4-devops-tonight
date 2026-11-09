/* ── DevOps Tonight: photographic stills, brought to life in plain JavaScript ──
   Every frame is composited here: a background plate, a cut-out presenter with mouth and
   eyelid sprites, a small head warp, camera moves, sensor grain and the broadcast graphics. */
const ACC = '#2ee6a6';
const ASSETS = /*ASSETS*/{ img: {}, cast: {} };
const FW = 1024, FH = 576;
const CAST = {
  paige: { name: 'PAIGE DUTY', role: 'Anchor · on call tonight' },
  cy:    { name: 'CY DEKAR', role: 'Anchor' },
  dee:   { name: 'DEE PLOY', role: 'Reporting live from us-east-1' },
  sunny: { name: 'SUNNY UPTIME', role: 'Cloud forecast' },
  mel:   { name: 'Y. A. MEL', role: 'Staff YAML Engineer' },
};
const SHOW = [
  { intro: 5 },
  { who: 'paige', text: "Good evening, this is DevOps Tonight. I'm Paige Duty, and yes, I am on call." },
  { who: 'cy', text: "And I'm Cy Dekar. It is 2026, and production is, for the moment, up." },
  { who: 'paige', ots: ['office', 'AGENTS REVIEW AGENTS'], cuts: [[0.735, 1, 'paged']], text: 'Our top story: an AI agent opened forty pull requests overnight. A second agent approved them. A human is now being paged.' },
  { who: 'cy', ots: ['dcext', 'FRIDAY DEPLOY'], text: 'Meanwhile, a routine Friday deploy is under way in us-east-1. Dee Ploy is at the scene. Dee?' },
  { who: 'dee', live: 'us-east-1', cuts: [[0, 0.2, 'dcext']], text: 'Thanks, Cy. The pipeline behind me has been green for nine minutes, and nobody here trusts it.' },
  { who: 'dee', live: 'us-east-1', cuts: [[0.04, 0.6, 'servers']], text: 'Engineers have checked the dashboards, the rollback plan, and DNS. Sources say it is always DNS.' },
  { who: 'cy', split: ['cy', 'dee'], title: 'LIVE · us-east-1', text: 'Dee, did anyone suggest waiting until Monday?' },
  { who: 'dee', split: ['cy', 'dee'], title: 'LIVE · us-east-1', text: 'One person did, Cy. They have been moved to the platform team. Back to you.' },
  { who: 'paige', ots: ['sat', 'CLOUD FORECAST'], text: 'Brave work. Now the cloud forecast, with Sunny Uptime.' },
  { who: 'sunny', wx: 0, text: 'Thanks, Paige. Pods are stuck Pending across the north while the autoscaler thinks about it.' },
  { who: 'sunny', wx: 1, text: 'In the south, scattered 503s with a chance of retries. Four nines along the coast, and a high of nine thousand dollars in egress.' },
  { who: 'cy', split: ['cy', 'mel'], title: 'THE BIG INTERVIEW', text: 'Joining us is Y. A. Mel, Staff YAML Engineer. With agents writing the config now, is your job safe?' },
  { who: 'mel', split: ['cy', 'mel'], title: 'THE BIG INTERVIEW', text: 'Cy, the agent writes four thousand lines of YAML a day. Someone still has to find the one wrong indent.' },
  { who: 'cy', split: ['cy', 'mel'], title: 'THE BIG INTERVIEW', text: 'Chilling. Thank you for your time.' },
  { who: 'paige', text: "That's all for tonight. Remember: you build it, you run it, and FinOps will ask what it cost." },
  { who: 'cy', text: 'From all of us in the control plane, good night, and may your pager stay quiet.' },
  { outro: 4.5 },
];
// Timing: every character gets a moment on the clock, punctuation gets a pause, and each
// letter maps to a mouth shape (0 at rest, 1 slightly open, 2 open, 3 teeth, 4 round, 5 lips pressed, -1 hold).
const BEATS = []; let SHOW_LEN = 0; const seen = {};
SHOW.forEach(L => {
  const b = Object.assign({ start: SHOW_LEN }, L);
  if (L.text && !L.split) { b.strap = !seen[L.who]; seen[L.who] = true; }      // name strap the first time someone is on camera
  if (L.text) {
    b.T = []; let t = 0.3;
    for (const ch of L.text) { b.T.push(t); t += /[.?!:]/.test(ch) ? 0.34 : ch === ',' ? 0.2 : 0.062; }
    b.dur = t + 0.35;
    b.vis = [...L.text.toLowerCase()].map(ch => ch === 'a' ? 2 : 'ei'.includes(ch) ? 3 : 'ouw'.includes(ch) ? 4 : 'mbp'.includes(ch) ? 5 : /[a-z0-9]/.test(ch) ? 1 : (ch === ' ' || ch === "'") ? -1 : 0);
    b.kind = L.split ? 'split' + L.split.join() : L.wx != null ? 'wx' : 'solo' + L.who;
  } else { b.dur = L.intro || L.outro; b.kind = L.intro ? 'intro' : 'outro'; }
  const p = BEATS[BEATS.length - 1];
  b.shot0 = p && p.kind === b.kind ? p.shot0 : b.start;      // lines that share a camera set-up form one shot
  BEATS.push(b); SHOW_LEN += b.dur;
});
BEATS.forEach(b => { let e = b.start + b.dur; for (const o of BEATS) if (o.shot0 === b.shot0) e = Math.max(e, o.start + o.dur); b.shotLen = e - b.shot0; });
const TICKER = '  ●  Kubernetes still the answer, question unclear  ●  platform team renames itself again  ●  terraform plan: 1 to add, 0 to change, 312 to destroy  ●  OpenTelemetry now observing the observers  ●  SBOM found to contain another SBOM  ●  cloud bill arrives, CFO joins incident channel  ●  change freeze begins, three hotfixes ship  ●  MTTR down, vibes mixed';

/* ── assets ── */
function mkCanvas(w, h) { const k = document.createElement('canvas'); k.width = w; k.height = h; return k; }
let pending = 0, readyAt = -1;
function loadImg(src) { const im = new Image(); pending++; im.onload = im.onerror = () => { pending--; }; im.src = src; return im; }
const STILL = {}; for (const k in ASSETS.img) STILL[k] = loadImg(ASSETS.img[k]);
const ACT = {};
for (const k in ASSETS.cast) {
  const m = ASSETS.cast[k], pf = mkCanvas(FW, FH), wf = mkCanvas(FW, FH);
  ACT[k] = { m, bg: loadImg(m.bg), fg: loadImg(m.fg), mouths: m.mouth.frames.map(loadImg), blink: loadImg(m.blink.src), pf, px: pf.getContext('2d'), wf, wx: wf.getContext('2d') };
}
const grain = mkCanvas(256, 256);
{ const g = grain.getContext('2d'), d = g.createImageData(256, 256); for (let i = 0; i < d.data.length; i += 4) { const v = 128 + (Math.random() - 0.5) * 150; d.data[i] = d.data[i + 1] = d.data[i + 2] = v; d.data[i + 3] = 255; } g.putImageData(d, 0, 0); }
const soft = mkCanvas(64, 36), softx = soft.getContext('2d');          // tiny copy = cheap blur
const lofi = mkCanvas(231, 170), lofix = lofi.getContext('2d'); let lofiTick = -1;

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
const ease = p => p * p * (3 - 2 * p), clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const wob = (t, s) => Math.sin(t * 1.3 + s) * 0.6 + Math.sin(t * 2.9 + s * 1.7) * 0.3 + Math.sin(t * 5.1 + s * 0.3) * 0.1;

/* ── speech ── */
function charAt(b, bt) { const T = b.T; let lo = 0, hi = T.length - 1; if (bt < T[0]) return -1; while (lo < hi) { const m = (lo + hi + 1) >> 1; if (T[m] <= bt) lo = m; else hi = m - 1; } return lo; }
function visAt(b, tt) { let i = charAt(b, tt); if (i < 0 || tt > b.T[b.T.length - 1] + 0.12) return 0; while (i > 0 && b.vis[i] < 0) i--; return Math.max(0, b.vis[i]); }
function mouthAt(b, bt) { const q = 0.09, tq = Math.floor(bt / q) * q; return { cur: visAt(b, tq), prev: visAt(b, tq - q), mix: Math.min(1, (bt - tq) / 0.055) }; }
function speaking(b, bt) { return bt > b.T[0] - 0.1 && bt < b.T[b.T.length - 1] + 0.2; }

/* ── a presenter: sprites onto the cut-out, then a gentle warp around the head ── */
function compose(a, t, mo) {
  const x = a.px, m = a.m; x.globalAlpha = 1;
  x.clearRect(0, 0, FW, FH); x.drawImage(a.fg, 0, 0);
  if (mo) {
    const pi = m.mouth.map[mo.prev], ci = m.mouth.map[mo.cur];
    if (ci >= 0) { if (pi >= 0 && mo.mix < 1) x.drawImage(a.mouths[pi], m.mouth.x, m.mouth.y); x.globalAlpha = mo.mix; x.drawImage(a.mouths[ci], m.mouth.x, m.mouth.y); }
    else if (pi >= 0 && mo.mix < 1) { x.globalAlpha = 1 - mo.mix; x.drawImage(a.mouths[pi], m.mouth.x, m.mouth.y); }
    x.globalAlpha = 1;
  }
  const P = 3.3 + (m.seed % 1.9), ph = (t + m.seed * 2.7) % P, bl = ph < 0.05 ? ph / 0.05 : ph < 0.11 ? 1 : ph < 0.18 ? (0.18 - ph) / 0.07 : 0;
  if (bl > 0) { x.globalAlpha = bl; x.drawImage(a.blink, m.blink.x, m.blink.y); x.globalAlpha = 1; }
}
function warp(a, tx, ty, rot) {
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
}
// Draws in frame coordinates (the caller sets the camera). o: { mo, e (energy 0..1), zb, zf, noBg, mid() }
function drawActor(id, t, o) {
  const a = ACT[id], f = a.m.face, s = a.m.seed, e = o.e;
  compose(a, t, o.mo);
  warp(a, e * (1.5 * Math.sin(t * 2.3 + s) + 0.9 * Math.sin(t * 4.1 + s * 2)),
          e * (1.7 * Math.sin(t * 3.1 + s * 1.3) + 1.1 * Math.sin(t * 5.7 + s)),
          e * 0.011 * Math.sin(t * 1.7 + s * 0.7));
  if (!o.noBg) { c.save(); c.translate(f.cx, f.cy); c.scale(o.zb, o.zb); c.translate(-f.cx, -f.cy); c.drawImage(a.bg, 0, 0); c.restore(); }
  if (o.mid) o.mid();
  c.save();
  c.translate(f.cx, FH + 260); c.rotate((0.0032 * Math.sin(t * 0.53 + s) + 0.0018 * Math.sin(t * 1.31 + s * 2)) * (0.6 + 0.4 * e)); c.translate(-f.cx, -(FH + 260));
  c.translate(f.cx, f.cy); c.scale(o.zf, o.zf); c.translate(-f.cx, -f.cy);
  c.drawImage(a.wf, 0, 0);
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
  view(x, y, w, h, k[0], k[1], k[2], k[3], () => drawActor(id, t, { mo: on ? mouthAt(b, bt) : null, e: on && speaking(b, bt) ? 1 : 0.3, zb: 1, zf: 1.012 }));
  if (remote) {                    // a video call: low resolution, low frame rate
    const tick = Math.floor(t * 15); if (tick !== lofiTick) { lofiTick = tick; lofix.drawImage(scr, x, y, w, h, 0, 0, 231, 170); }
    c.drawImage(lofi, 0, 0, 231, 170, x, y, w, h);
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

function chNews(t) {
  c.textBaseline = 'alphabetic'; c.globalAlpha = 1;
  if (pending > 0) {              // still decoding the pictures
    c.fillStyle = '#050b1a'; c.fillRect(0, 0, SW, SH); opsLogo(SW / 2 - 40, 210, 80);
    c.fillStyle = '#fff'; c.textAlign = 'center'; c.font = `800 30px ${SANS}`; c.fillText('DEVOPS TONIGHT', SW / 2, 345); return;
  }
  if (readyAt < 0) readyAt = t;
  const ts = Math.max(0, t - Math.max(readyAt, switchedAt + 0.32)) % SHOW_LEN;
  let bi = BEATS.length - 1; while (BEATS[bi].start > ts) bi--;
  const b = BEATS[bi], bt = ts - b.start, sp = clamp((ts - b.shot0) / b.shotLen, 0, 1);
  let cut = null; if (b.cuts) for (const k of b.cuts) if (bt >= k[0] * b.dur && bt < k[1] * b.dur) cut = k;
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
      c.font = `15px ${SANS}`; c.fillStyle = ACC; c.fillText('Presenters and locations are AI-generated stills, animated in plain JavaScript', SW / 2, 372);
    }
  } else if (cut) {
    drawStill(cut[2], clamp((bt - cut[0] * b.dur) / ((cut[1] - cut[0]) * b.dur), 0, 1), cut[2] === 'servers' ? -1 : 1);
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
    const target = b.wx === 0 ? spots[0] : (bt < b.dur * 0.5 ? spots[2] : spots[1]);
    for (const s of spots) {
      const hot = s === target; rr(s[1] - 62, s[2] - 40, 124, 128, 12); c.fillStyle = hot ? 'rgba(6,16,40,.72)' : 'rgba(6,16,40,.45)'; c.fill();
      if (hot) { c.strokeStyle = ACC; c.lineWidth = 2.5 + Math.sin(t * 6); c.stroke(); }
      weatherIcon(s[0], s[1], s[2], t);
      c.fillStyle = '#fff'; c.font = `800 20px ${SANS}`; c.textAlign = 'center'; c.fillText(s[3], s[1], s[2] + 74);
    }
    const a = ACT.sunny, f = a.m.face, z = a.m.wxScale || 1;
    c.save(); c.translate(250, 250); c.scale(z, z); c.translate(-f.cx, -f.cy);
    drawActor('sunny', t, { mo: mouthAt(b, bt), e: speaking(b, bt) ? 1 : 0.3, noBg: true, zb: 1, zf: 1 });
    c.restore();
  } else {
    // a single presenter on camera: slow push-in, parallax between person and set, hand-held when live
    const left = ACT[b.who].m.face.cx > 560, ox = b.ots ? (left ? 46 : -46) : 0;        // make room for the over-the-shoulder box
    const z = (b.ots ? 1.1 : 1.035) + 0.05 * ease(sp), sh = b.live ? 1 : 0.12;
    c.save(); c.translate(SW / 2 + ox + wob(t, 3) * 3.4 * sh, SH / 2 + wob(t, 9) * 2.6 * sh); c.rotate(wob(t * 0.8, 5) * 0.0035 * sh); c.scale(z, z); c.translate(-SW / 2, -SH / 2);
    drawActor(b.who, t, { mo: mouthAt(b, bt), e: speaking(b, bt) ? 1 : 0.3, zb: 1, zf: 1.012 + 0.022 * ease(sp), mid: b.ots ? () => otsBox(b, left) : null });
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
    let n = charAt(b, bt) + 1; while (n > 0 && n < b.text.length && b.text[n] !== ' ') n++;
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
