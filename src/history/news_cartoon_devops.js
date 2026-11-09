/* ── Vanilla JS News: a scripted bulletin with a cast, drawn shape by shape ── */
const ACC = '#2ee6a6';
const CAST = {
  ada:  { name: 'PAIGE DUTY', role: 'Anchor, currently on call', skin: '#e8b48c', hair: '#3a2218', style: 'long', suit: '#b3263a', blouse: true, seed: 1 },
  sam:  { name: 'CY DEKAR', role: 'Anchor', skin: '#8d5a3b', hair: '#17110e', style: 'short', suit: '#27324a', tie: ACC, seed: 2.7 },
  dom:  { name: 'DEE PLOY', role: 'Live at us-east-1', skin: '#f0c9a4', hair: '#b5651d', style: 'curly', suit: '#3f6b4f', tie: '#1d1d1d', seed: 4.1 },
  gale: { name: 'SUNNY UPTIME', role: 'Cloud forecast', skin: '#c98d62', hair: '#101018', style: 'bob', suit: '#2a8a8f', blouse: true, seed: 5.9 },
  semi: { name: 'Y. A. MEL', role: 'Staff YAML Engineer', skin: '#f2d2b6', hair: '#c9c9c9', style: 'bald', suit: '#5b5b66', tie: '#8a2be2', glasses: true, seed: 8.3 },
};
// [speaker, shot, line, over-the-shoulder graphic]
const SHOW = [
  { scene: 'intro', dur: 4.5 },
  { scene: 'desk', lines: [
    ['ada', 'two', "Good evening, this is DevOps Tonight. I'm Paige Duty, and yes, I am on call."],
    ['sam', 'two', "And I'm Cy Dekar. It is 2026, and production is, for the moment, up."],
    ['ada', 'solo', 'Our top story: an AI agent opened forty pull requests overnight. A second agent approved them. A human is now being paged.', 'AGENTS\nREVIEW\nAGENTS'],
    ['sam', 'solo', 'Meanwhile, a routine Friday deploy is under way in us-east-1. Dee Ploy is at the scene. Dee?', 'FRIDAY\nDEPLOY'],
  ] },
  { scene: 'field', lines: [
    ['dom', '', 'Thanks, Cy. The pipeline behind me has been green for nine minutes, and nobody here trusts it.'],
    ['dom', '', 'Engineers have checked the dashboards, the rollback plan, and DNS. Sources say it is always DNS.'],
    ['sam', 'split', 'Dee, did anyone suggest waiting until Monday?'],
    ['dom', 'split', 'One person did, Cy. They have been moved to the platform team. Back to you.'],
  ] },
  { scene: 'desk', lines: [['ada', 'solo', 'Brave work. Now the cloud forecast, with Sunny Uptime.', 'CLOUD\nFORECAST']] },
  { scene: 'weather', lines: [
    ['gale', '', 'Thanks, Paige. Pods are stuck Pending across the north while the autoscaler thinks about it.'],
    ['gale', '', 'In the south, scattered 503s with a chance of retries. Four nines along the coast, and a high of nine thousand dollars in egress.'],
  ] },
  { scene: 'interview', lines: [
    ['sam', '', 'Joining us is Y. A. Mel, Staff YAML Engineer. With agents writing the config now, is your job safe?'],
    ['semi', '', 'Cy, the agent writes four thousand lines of YAML a day. Someone still has to find the one wrong indent.'],
    ['sam', '', 'Chilling. Thank you for your time.'],
  ] },
  { scene: 'desk', end: true, lines: [
    ['ada', 'two', "That's all for tonight. Remember: you build it, you run it, and FinOps will ask what it cost."],
    ['sam', 'two', 'From all of us in the control plane, good night, and may your pager stay quiet.'],
  ] },
];
const BEATS = []; let SHOW_LEN = 0;
SHOW.forEach(seg => {
  const segStart = SHOW_LEN;
  if (!seg.lines) { BEATS.push({ start: SHOW_LEN, dur: seg.dur, scene: seg.scene, segStart }); SHOW_LEN += seg.dur; return; }
  seg.lines.forEach(([who, shot, text, gfx], li) => {
    const dur = text.length * 0.058 + 1.6;
    BEATS.push({ start: SHOW_LEN, dur, scene: seg.scene, who, shot, text, gfx, li, segStart, end: seg.end });
    SHOW_LEN += dur;
  });
});
const TICKER = '  ●  Kubernetes still the answer, question unclear  ●  platform team renames itself again  ●  terraform plan: 1 to add, 0 to change, 312 to destroy  ●  OpenTelemetry now observing the observers  ●  SBOM found to contain another SBOM  ●  cloud bill arrives, CFO joins incident channel  ●  change freeze begins, three hotfixes ship  ●  MTTR down, vibes mixed';

// channel ident: the DevOps infinity loop
function opsLogo(x, y, s) {
  if (s < 2) return;
  c.fillStyle = ACC; rr(x, y, s, s, s * 0.16); c.fill();
  c.strokeStyle = '#06281d'; c.lineWidth = s * 0.085; c.lineCap = 'round'; c.beginPath();
  for (let i = 0; i <= 48; i++) { const a = i / 48 * 6.2832, d = 1 + Math.sin(a) * Math.sin(a), px = x + s / 2 + s * 0.36 * Math.cos(a) / d, py = y + s / 2 + s * 0.36 * Math.sin(a) * Math.cos(a) / d; i ? c.lineTo(px, py) : c.moveTo(px, py); }
  c.stroke();
}

function rr(x, y, w, h, r) {
  c.beginPath(); c.moveTo(x + r, y); c.arcTo(x + w, y, x + w, y + h, r); c.arcTo(x + w, y + h, x, y + h, r);
  c.arcTo(x, y + h, x, y, r); c.arcTo(x, y, x + w, y, r); c.closePath();
}
function ell(x, y, rx, ry) { c.beginPath(); c.ellipse(x, y, rx, ry, 0, 0, 6.2832); }

// A presenter from the chest up. (x, y) is the base of the neck; s = 1 gives a head about 90px tall.
function person(id, x, y, s, talk, t, o) {
  o = o || {};
  const p = CAST[id], sd = p.seed;
  const open = talk ? (Math.sin(t * 13 + sd) * 0.5 + 0.5) * (0.3 + 0.7 * Math.abs(Math.sin(t * 4.7 + sd))) : 0;
  const tilt = Math.sin(t * 0.7 + sd) * 0.025 + (talk ? Math.sin(t * 2.9 + sd) * 0.04 : 0);
  const bob = talk ? Math.sin(t * 5.8 + sd) * 1.3 : 0;
  c.save(); c.translate(x, y); c.scale(s, s); c.lineCap = 'round'; c.lineJoin = 'round';
  if (p.style === 'long') { c.fillStyle = p.hair; ell(0, -30, 54, 78); c.fill(); }
  // jacket
  c.fillStyle = p.suit; c.beginPath(); c.moveTo(-104, 160); c.quadraticCurveTo(-104, 22, -38, 9); c.lineTo(38, 9);
  c.quadraticCurveTo(104, 22, 104, 160); c.closePath(); c.fill();
  if (p.blouse) {
    c.fillStyle = p.skin; c.beginPath(); c.moveTo(-22, 8); c.quadraticCurveTo(0, 56, 22, 8); c.closePath(); c.fill();
    c.strokeStyle = 'rgba(255,255,255,.7)'; c.lineWidth = 1.5; c.beginPath(); c.moveTo(-16, 14); c.quadraticCurveTo(0, 40, 16, 14); c.stroke();
  } else {
    c.fillStyle = '#f4f4f0'; c.beginPath(); c.moveTo(-24, 8); c.lineTo(24, 8); c.lineTo(0, 74); c.closePath(); c.fill();
    c.fillStyle = p.tie; c.beginPath(); c.moveTo(-6, 16); c.lineTo(6, 16); c.lineTo(9, 60); c.lineTo(0, 72); c.lineTo(-9, 60); c.closePath(); c.fill();
    c.strokeStyle = 'rgba(0,0,0,.35)'; c.lineWidth = 3; c.beginPath(); c.moveTo(-26, 9); c.lineTo(0, 76); c.lineTo(26, 9); c.stroke();
  }
  // pointing arm (weather) or microphone arm (field)
  if (o.point) {
    let dx = (o.point[0] - x) / s - 80, dy = (o.point[1] - y) / s - 46; const l = Math.hypot(dx, dy), k = Math.min(l, 112) / l;
    c.strokeStyle = p.suit; c.lineWidth = 26; c.beginPath(); c.moveTo(80, 46); c.lineTo(80 + dx * k, 46 + dy * k); c.stroke();
    c.strokeStyle = 'rgba(0,0,0,.18)'; c.lineWidth = 2; c.stroke();
    c.fillStyle = p.skin; ell(80 + dx * k * 1.08, 46 + dy * k * 1.08, 12, 12); c.fill();
  }
  // neck
  c.fillStyle = p.skin; c.fillRect(-13, -20, 26, 34); c.fillStyle = 'rgba(0,0,0,.14)'; c.fillRect(-13, -20, 26, 34);
  // head
  c.save(); c.translate(0, -55 + bob); c.rotate(tilt);
  c.fillStyle = p.hair;
  if (p.style === 'bob') { ell(0, -4, 49, 54); c.fill(); }
  if (p.style === 'long') { ell(0, -4, 48, 54); c.fill(); }
  c.fillStyle = p.skin; ell(-38, 0, 7, 9); c.fill(); ell(38, 0, 7, 9); c.fill(); ell(0, 0, 38, 46); c.fill();
  c.fillStyle = p.hair;
  if (p.style === 'curly') { for (let i = 0; i <= 8; i++) { const a = Math.PI + i * Math.PI / 8; ell(Math.cos(a) * 37, Math.sin(a) * 40 - 8, 14, 14); c.fill(); } }
  else if (p.style === 'bald') { ell(-37, -14, 8, 12); c.fill(); ell(37, -14, 8, 12); c.fill(); }
  else { c.beginPath(); c.moveTo(-39, -6); c.bezierCurveTo(-48, -64, 48, -64, 39, -6); c.quadraticCurveTo(34, -30, 8, -31); c.quadraticCurveTo(-22, -32, -39, -6); c.fill(); }
  const blink = ((t + sd * 1.3) % 3.7) < 0.13, look = (o.look || 0) * 2.6;
  for (const sx of [-1, 1]) {
    if (blink) { c.strokeStyle = '#3a2a22'; c.lineWidth = 2; c.beginPath(); c.moveTo(sx * 14 - 6, -6); c.lineTo(sx * 14 + 6, -6); c.stroke(); }
    else { c.fillStyle = '#fff'; ell(sx * 14, -6, 6.5, 4.6); c.fill(); c.fillStyle = '#20140f'; ell(sx * 14 + look, -6, 3, 3); c.fill(); }
    c.strokeStyle = p.style === 'bald' ? '#9a9a9a' : p.hair; c.lineWidth = 3;
    c.beginPath(); c.moveTo(sx * 21, -15 - open * 2); c.lineTo(sx * 8, -17 - open * 3); c.stroke();
    if (p.glasses) { c.strokeStyle = '#222'; c.lineWidth = 2; ell(sx * 14, -6, 10, 9); c.stroke(); }
  }
  if (p.glasses) { c.beginPath(); c.moveTo(-4, -6); c.lineTo(4, -6); c.stroke(); }
  c.strokeStyle = 'rgba(0,0,0,.28)'; c.lineWidth = 2; c.beginPath(); c.moveTo(0, -2); c.lineTo(-3, 9); c.lineTo(2, 10); c.stroke();
  if (open > 0.12) {
    const h = 1.5 + open * 7;
    c.fillStyle = '#4a1414'; ell(0, 24, 8.5, h); c.fill();
    c.fillStyle = '#fff'; c.fillRect(-5, 24 - h + 0.8, 10, Math.min(2.6, h));
  } else { c.strokeStyle = p.blouse ? '#a8323c' : '#7a2e2e'; c.lineWidth = 2.4; c.beginPath(); c.moveTo(-8, 23); c.quadraticCurveTo(0, 28, 8, 23); c.stroke(); }
  c.restore();
  if (o.mic) {
    c.strokeStyle = p.suit; c.lineWidth = 28; c.beginPath(); c.moveTo(84, 150); c.lineTo(40, 70); c.stroke();
    c.fillStyle = '#222'; c.fillRect(31, 14, 9, 46); c.fillStyle = '#8b8f97'; ell(35.5, 8, 10, 11); c.fill();
    c.fillStyle = ACC; c.fillRect(24, 22, 23, 17); c.fillStyle = '#111'; c.font = `bold 8px ${SANS}`; c.textAlign = 'center'; c.textBaseline = 'alphabetic'; c.fillText('OPS', 35.5, 34);
    c.fillStyle = p.skin; ell(37, 56, 13, 12); c.fill();
  }
  c.restore();
}

function studio(t, big) {
  const g = c.createLinearGradient(0, 0, 0, SH); g.addColorStop(0, '#0a1a38'); g.addColorStop(1, '#173a6b');
  c.fillStyle = g; c.fillRect(0, 0, SW, SH);
  // video wall: a night skyline with windows that flicker on and off
  for (let i = 0; i < 5; i++) {
    const x = i * 212 - 18, w = 196, y = 34, h = big ? 300 : 250;
    rr(x, y, w, h, 10); c.fillStyle = 'rgba(70,130,235,.16)'; c.fill(); c.strokeStyle = 'rgba(150,200,255,.25)'; c.lineWidth = 2; c.stroke();
    for (let j = 0; j < 6; j++) {
      const bh = 50 + ((i * 53 + j * 97) % 110), bx = x + 8 + j * 30;
      c.fillStyle = 'rgba(6,14,34,.75)'; c.fillRect(bx, y + h - bh - 4, 26, bh);
      c.fillStyle = 'rgba(255,214,120,.55)';
      for (let k = 0; k < bh / 16 - 1; k++) if (Math.sin(i * 7 + j * 13 + k * 5 + Math.floor(t / 3 + k)) > 0) c.fillRect(bx + 5 + (k % 2) * 10, y + h - bh + 4 + k * 14, 5, 6);
    }
  }
  c.fillStyle = 'rgba(46,230,166,.85)'; c.fillRect(0, 22, SW, 4);
}
function desk(y) {
  const g = c.createLinearGradient(0, y, 0, SH); g.addColorStop(0, '#22407a'); g.addColorStop(1, '#0a1630');
  c.fillStyle = g; c.fillRect(0, y, SW, SH - y);
  c.fillStyle = ACC; c.fillRect(0, y, SW, 5); c.fillStyle = 'rgba(255,255,255,.1)'; c.fillRect(0, y + 5, SW, 12);
}
function lines(text, maxW) {
  const out = []; let line = '';
  for (const w of text.split(' ')) {
    if (line && c.measureText(line + ' ' + w).width > maxW) { out.push(line); line = w; } else line = line ? line + ' ' + w : w;
  }
  out.push(line); return out;
}
function pane(x, y, w, h, kind, who, talk, t) {
  c.save(); rr(x, y, w, h, 8); c.clip();
  if (kind === 'field') {
    c.fillStyle = '#8fd0f2'; c.fillRect(x, y, w, h); c.fillStyle = '#c9b27a'; c.fillRect(x, y + h * 0.7, w, h);
    c.fillStyle = '#69727f'; c.fillRect(x + w - 160, y + 96, 150, 142); c.fillStyle = '#2ee66a'; for (let i = 0; i < 24; i++) c.fillRect(x + w - 148 + (i % 8) * 17, y + 112 + Math.floor(i / 8) * 22, 8, 5);
  } else if (kind === 'office') {
    c.fillStyle = '#3b2f4a'; c.fillRect(x, y, w, h);
    for (let r = 0; r < 3; r++) { c.fillStyle = '#241b30'; c.fillRect(x, y + 70 + r * 80, w, 6);
      for (let b = 0; b < 16; b++) { c.fillStyle = ['#c55', '#5a8', '#f7df1e', '#58c', '#b7a'][(b * 3 + r) % 5]; const bh = 40 + (b * 17 + r * 7) % 22; c.fillRect(x + 10 + b * 29, y + 70 + r * 80 - bh, 20, bh); } }
    c.fillStyle = 'rgba(20,10,30,.45)'; c.fillRect(x, y, w, h);
  } else {
    const g = c.createLinearGradient(0, y, 0, y + h); g.addColorStop(0, '#0d2147'); g.addColorStop(1, '#1d4a85'); c.fillStyle = g; c.fillRect(x, y, w, h);
    c.globalAlpha = 0.25; opsLogo(x + w - 120, y + 30, 90); c.globalAlpha = 1;
  }
  person(who, x + w / 2, y + h * 0.6, 1.5, talk, t);
  const p = CAST[who];
  c.fillStyle = ACC; c.fillRect(x, y + h - 38, w, 38);
  c.fillStyle = '#111'; c.textAlign = 'left'; c.textBaseline = 'alphabetic'; c.font = `bold 17px ${SANS}`; c.fillText(p.name, x + 14, y + h - 14);
  c.font = `14px ${SANS}`; c.textAlign = 'right'; c.fillText(p.role, x + w - 14, y + h - 14);
  c.restore();
  rr(x, y, w, h, 8); c.strokeStyle = talk ? '#fff' : 'rgba(255,255,255,.3)'; c.lineWidth = talk ? 4 : 2; c.stroke();
}
function splitBg(title) {
  const g = c.createLinearGradient(0, 0, SW, SH); g.addColorStop(0, '#081530'); g.addColorStop(1, '#122c55'); c.fillStyle = g; c.fillRect(0, 0, SW, SH);
  c.fillStyle = '#e23b2e'; c.fillRect(40, 24, 8, 30); c.fillStyle = '#fff'; c.font = `bold 22px ${SANS}`; c.textAlign = 'left'; c.textBaseline = 'alphabetic'; c.fillText(title, 60, 47);
}
function weatherIcon(kind, x, y, t) {
  c.lineCap = 'round';
  if (kind === 'sun') {
    c.strokeStyle = '#ffd43b'; c.lineWidth = 4;
    for (let i = 0; i < 8; i++) { const a = i * Math.PI / 4 + t * 0.6; c.beginPath(); c.moveTo(x + Math.cos(a) * 24, y + Math.sin(a) * 24); c.lineTo(x + Math.cos(a) * 33, y + Math.sin(a) * 33); c.stroke(); }
    c.fillStyle = '#ffd43b'; ell(x, y, 18, 18); c.fill();
  } else {
    c.fillStyle = kind === 'rain' ? '#aeb8c8' : '#fff';
    ell(x - 16, y + 4, 15, 13); c.fill(); ell(x + 2, y - 6, 19, 18); c.fill(); ell(x + 20, y + 4, 14, 12); c.fill(); c.fillRect(x - 16, y + 4, 36, 13);
    if (kind === 'rain') { c.strokeStyle = '#8fd0ff'; c.lineWidth = 3; for (let i = 0; i < 4; i++) { const d = (t * 30 + i * 9) % 18; c.beginPath(); c.moveTo(x - 18 + i * 12, y + 22 + d); c.lineTo(x - 21 + i * 12, y + 30 + d); c.stroke(); } }
    else { c.strokeStyle = ACC; c.lineWidth = 4; c.beginPath(); c.arc(x + 2, y + 36, 9, t * 5, t * 5 + 4.2); c.stroke(); }
  }
}

function chNews(t) {
  const base = switchedAt < 0 ? 0 : switchedAt + 0.32;
  const ts = Math.max(0, t - base) % SHOW_LEN;
  let bi = BEATS.length - 1; while (BEATS[bi].start > ts) bi--;
  const b = BEATS[bi], bt = ts - b.start, prev = BEATS[bi - 1];
  c.textBaseline = 'alphabetic';

  if (b.scene === 'intro') {
    const g = c.createRadialGradient(SW / 2, 250, 20, SW / 2, 250, 620); g.addColorStop(0, '#1d4a85'); g.addColorStop(1, '#050b1a');
    c.fillStyle = g; c.fillRect(0, 0, SW, SH);
    c.lineWidth = 6; c.lineCap = 'butt';
    for (let i = 0; i < 5; i++) { c.strokeStyle = i % 2 ? 'rgba(46,230,166,.75)' : 'rgba(255,255,255,.35)'; c.beginPath(); const a = t * (0.8 + i * 0.3) * (i % 2 ? 1 : -1); c.arc(SW / 2, 220, 120 + i * 34, a, a + 1.6 + i * 0.5); c.stroke(); }
    const k = Math.min(1, bt / 0.8), e = 1 - Math.pow(1 - k, 3), s = 150 * e;
    opsLogo(SW / 2 - s / 2, 220 - s / 2, s);
    c.textAlign = 'center'; c.fillStyle = '#fff'; c.globalAlpha = Math.max(0, Math.min(1, (bt - 0.9) / 0.6));
    c.font = `800 62px ${SANS}`; c.fillText('DEVOPS TONIGHT', SW / 2, 432 + (1 - c.globalAlpha) * 20);
    c.font = `22px ${MONO}`; c.fillStyle = ACC; c.fillText('with Paige Duty and Cy Dekar', SW / 2, 472);
    c.globalAlpha = 1;
  } else if (b.scene === 'desk') {
    if (b.shot === 'two') {
      studio(t, false);
      c.globalAlpha = 0.9; opsLogo(SW / 2 - 60, 90, 120); c.globalAlpha = 1;
      person('ada', 300, 292, 1.3, b.who === 'ada', t, { look: b.who === 'sam' ? 1 : 0 });
      person('sam', 724, 292, 1.3, b.who === 'sam', t, { look: b.who === 'ada' ? -1 : 0 });
      desk(398);
      for (const mx of [452, 560]) { c.fillStyle = '#f4f4f0'; rr(mx, 372, 26, 30, 4); c.fill(); c.fillStyle = ACC; c.fillRect(mx + 6, 382, 14, 12); }
      if (b.end && b.who === 'sam') {
        c.fillStyle = 'rgba(0,0,0,.55)'; c.fillRect(0, 60, SW, 64); c.fillStyle = '#fff'; c.textAlign = 'center'; c.font = `22px ${MONO}`;
        c.fillText('This bulletin was deployed on a Friday. No rollbacks so far.', SW / 2, 100);
      }
    } else {
      studio(t, true);
      person(b.who, 360, 268, 1.9, true, t);
      desk(424);
      rr(628, 64, 340, 250, 12); c.fillStyle = 'rgba(5,12,30,.9)'; c.fill(); c.strokeStyle = ACC; c.lineWidth = 4; c.stroke();
      opsLogo(646, 82, 44);
      c.fillStyle = '#fff'; c.textAlign = 'center'; const gl_ = (b.gfx || '').split('\n');
      gl_.forEach((ln, i) => { c.font = `bold 32px ${SANS}`; c.fillText(ln, 798, 205 - gl_.length * 20 + i * 44 + 16); });
    }
  } else if (b.scene === 'field') {
    if (b.shot === 'split') {
      splitBg('LIVE · us-east-1');
      pane(40, 74, 462, 340, 'studio', 'sam', b.who === 'sam', t); pane(522, 74, 462, 340, 'field', 'dom', b.who === 'dom', t);
    } else {
      const g = c.createLinearGradient(0, 0, 0, 380); g.addColorStop(0, '#6bbcec'); g.addColorStop(1, '#dff3ff'); c.fillStyle = g; c.fillRect(0, 0, SW, SH);
      c.fillStyle = '#fff2b0'; ell(140, 90, 40, 40); c.fill();
      c.fillStyle = '#a9c79a'; c.beginPath(); c.moveTo(0, 372); c.quadraticCurveTo(260, 290, 520, 372); c.quadraticCurveTo(800, 300, SW, 372); c.fill();
      c.fillStyle = '#c9b27a'; c.fillRect(0, 368, SW, SH);
      // the data centre: racks of status lights and a pipeline readout
      c.fillStyle = '#59626f'; c.fillRect(596, 150, 392, 232); c.fillStyle = '#454d59'; c.fillRect(586, 138, 412, 16);
      c.fillStyle = '#0c1118'; rr(616, 172, 352, 62, 6); c.fill();
      c.fillStyle = '#fff'; c.textAlign = 'left'; c.font = `bold 26px ${MONO}`; c.fillText('us-east-1', 632, 200);
      c.fillStyle = '#2ee66a'; c.font = `17px ${MONO}`; c.fillText('deploy #4127 ● passing (9m)', 632, 224);
      for (let i = 0; i < 6; i++) { c.fillStyle = '#2b323c'; c.fillRect(616 + i * 60, 248, 50, 122);
        for (let k = 0; k < 7; k++) { const v = Math.sin(i * 9.1 + k * 4.7 + Math.floor(t * 3 + i + k)); c.fillStyle = v > 0.93 ? '#ffb020' : v > -0.3 ? '#2ee66a' : '#1c4a2c'; c.fillRect(624 + i * 60, 258 + k * 16, 34, 6); } }
      for (let i = 0; i < 3; i++) { const cx = (t * (14 + i * 6) + i * 380) % (SW + 200) - 100; c.fillStyle = 'rgba(255,255,255,.85)'; ell(cx, 70 + i * 34, 44, 16); c.fill(); ell(cx + 26, 60 + i * 34, 30, 16); c.fill(); }
      person('dom', 300, 296, 1.75, true, t, { mic: true });
      c.fillStyle = '#e23b2e'; c.fillRect(40, 30, 150, 34); c.fillStyle = '#fff'; c.font = `bold 18px ${SANS}`; c.textAlign = 'left'; c.fillText('● LIVE', 54, 54); c.font = `16px ${MONO}`; c.fillText('prod', 126, 54);
    }
  } else if (b.scene === 'weather') {
    const g = c.createLinearGradient(0, 0, 0, SH); g.addColorStop(0, '#1b5fa8'); g.addColorStop(1, '#0d3a72'); c.fillStyle = g; c.fillRect(0, 0, SW, SH);
    c.strokeStyle = 'rgba(255,255,255,.08)'; c.lineWidth = 1; c.beginPath(); for (let i = 0; i < 12; i++) { const y = 30 + i * 40 + Math.sin(t + i) * 3; c.moveTo(380, y); c.bezierCurveTo(560, y - 12, 800, y + 12, SW, y); } c.stroke();
    c.beginPath(); c.moveTo(560, 96); c.bezierCurveTo(640, 46, 800, 56, 868, 122); c.bezierCurveTo(940, 196, 884, 256, 904, 320); c.bezierCurveTo(914, 410, 780, 432, 704, 404); c.bezierCurveTo(620, 440, 520, 400, 540, 320); c.bezierCurveTo(476, 250, 500, 146, 560, 96);
    c.fillStyle = '#3f9b5a'; c.fill(); c.strokeStyle = '#bfe8c4'; c.lineWidth = 3; c.stroke();
    c.fillStyle = 'rgba(255,255,255,.85)'; c.font = `bold 20px ${SANS}`; c.textAlign = 'left'; c.fillText('CLUSTER MAP · TONIGHT', 420, 50);
    const spots = [['pending', 650, 150, 'Pending'], ['sun', 826, 236, '99.99%'], ['rain', 660, 326, '503']];
    const target = b.li === 0 ? spots[0] : (bt < b.dur * 0.55 ? spots[2] : spots[1]);
    for (const sp of spots) {
      if (sp === target) { c.strokeStyle = ACC; c.lineWidth = 3; ell(sp[1], sp[2] + 8, 52 + Math.sin(t * 6) * 4, 52 + Math.sin(t * 6) * 4); c.stroke(); }
      weatherIcon(sp[0], sp[1], sp[2], t);
      c.fillStyle = '#fff'; c.font = `bold 20px ${MONO}`; c.textAlign = 'center'; c.fillText(sp[3], sp[1], sp[2] + 74);
    }
    person('gale', 210, 300, 1.7, true, t, { point: [target[1] - 60, target[2]], look: 0.6 });
  } else if (b.scene === 'interview') {
    splitBg('THE BIG INTERVIEW');
    pane(40, 74, 462, 340, 'studio', 'sam', b.who === 'sam', t); pane(522, 74, 462, 340, 'office', 'semi', b.who === 'semi', t);
  }

  // scene-change wipe
  const sw = ts - b.segStart;
  if (b.scene !== 'intro' && sw < 0.35) { const k = sw / 0.35; c.fillStyle = ACC; c.fillRect(k * (SW + 300) - 300, 0, 300, SH); c.fillStyle = '#fff'; c.fillRect(k * (SW + 300) - 340, 0, 30, SH); }

  if (b.who) {
    // name strap when a new person starts speaking on a full-frame shot
    const p = CAST[b.who], full = b.shot !== 'split' && b.scene !== 'interview';
    if (full && (!prev || prev.who !== b.who || b.li === 0) && bt < 3.6) {
      const k = Math.min(1, bt / 0.3, (3.6 - bt) / 0.3), sx = b.shot === 'two' && b.who === 'sam' ? 560 : 48;
      c.save(); c.beginPath(); c.rect(sx, 386, 420 * k, 60); c.clip();
      c.fillStyle = ACC; c.fillRect(sx, 386, 300, 34); c.fillStyle = 'rgba(255,255,255,.95)'; c.fillRect(sx, 420, 300, 26);
      c.textAlign = 'left'; c.fillStyle = '#111'; c.font = `bold 20px ${SANS}`; c.fillText(p.name, sx + 14, 411);
      c.fillStyle = '#10213d'; c.font = `15px ${SANS}`; c.fillText(p.role, sx + 14, 439); c.restore();
    }
    // subtitles, typed out as the line is spoken
    c.font = `600 21px ${SANS}`; const ls = lines(b.text, 890); let left = Math.floor(bt * 30);
    c.fillStyle = 'rgba(0,0,0,.72)'; c.fillRect(48, 452, 928, ls.length > 1 ? 56 : 34);
    c.textAlign = 'left'; c.fillStyle = '#fff';
    ls.forEach((ln, i) => { if (left > 0) c.fillText(ln.slice(0, left), 62, 476 + i * 24); left -= ln.length + 1; });
  }

  // ticker, clock, live bug
  c.fillStyle = '#060d1c'; c.fillRect(0, 512, SW, 64);
  c.fillStyle = '#dfe9ff'; c.font = `20px ${MONO}`; c.textAlign = 'left';
  const tw = c.measureText(TICKER).width, off = (t * 110) % tw;
  c.fillText(TICKER, -off, 551); c.fillText(TICKER, -off + tw, 551);
  c.fillStyle = ACC; c.fillRect(0, 512, 118, 64);
  c.fillStyle = '#111'; c.font = `bold 24px ${MONO}`; c.textAlign = 'center'; c.fillText(new Date().toTimeString().slice(0, 5), 59, 553);
  if (b.scene === 'desk') {
    c.textAlign = 'right'; c.fillStyle = '#fff'; c.font = `bold 18px ${SANS}`; c.fillText('LIVE', 976, 56);
    if (t % 1.2 < 0.8) { c.fillStyle = '#ff3b30'; ell(915, 49, 7, 7); c.fill(); }
  }
}
