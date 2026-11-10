// check.js [face] : looks at avatar/faces/preview_<face>.html in a headless browser and writes pictures to avatar/faces/check/.
// Every pose is forced directly, as tests/poses.js does for the bulletin, so each tile shows what its label says.
//   <face>_page_idle.png            the page as it loads (the photograph's own expression, the listening pose)
//   <face>_three.jpg                the whole picture three times: relaxed (speaking) mouth, the photograph's expression, broad smile
//   <face>_mouths.jpg               the mouth, large: shut, pressed, eleven openings, spread, rounded, smiling while talking
//   <face>_eyes.jpg                 the eyes, large: lids, gaze, smiling eyes, brows
//   <face>_head.jpg                 the head turned, nodded, tilted, and combinations; with the still picture beside each
//   <face>_body.jpg                 the body at the ends of its range: breath, shift, lean, turn of the shoulders, hair
//   <face>_speak_sounds.jpg         the mouth 12.5 times a second through a line, each frame labelled with the sound, the word and the opening
//   <face>_speak_frames.jpg         the page's own picture four times a second through the same line
//   <face>_page_thinking.png, <face>_page_speaking_N.png     the page itself, with stand-ins for the reply and the voice (as avatar/test.js)
// and prints how the mouth moved. Run from the repository root:  node avatar/faces/check.js me
// To try another opening gain without rebuilding (the cast entry's `gain`), and keep the pictures apart:
//   CHECK_GAIN=1.3 CHECK_OUT=/some/folder node avatar/faces/check.js me
const { chromium } = require('playwright'); const fs = require('fs');
const who = process.argv[2] || 'me', out = process.env.CHECK_OUT || `${__dirname}/check`, GAIN = +process.env.CHECK_GAIN || 0, LINE = process.argv[3] || 'Hello, my name is Bob. People watch my mouth move when we speak, so above all it should look calm and free.';
const save = (name, url) => { fs.writeFileSync(`${out}/${who}_${name}`, Buffer.from(url.split(',')[1], 'base64')); console.log('wrote', `check/${who}_${name}`); };
const mocks = () => {       // the reply and the voice the artifact viewer would provide (the same stand-ins as avatar/test.js)
  const cbs = { line: [], pos: [], state: [] }; let stop = false;
  const tts = { onLine: f => cbs.line.push(f), onPosition: f => cbs.pos.push(f), onState: f => cbs.state.push(f), stop: () => { stop = true; },
    speak: async lines => { stop = false; cbs.state.forEach(f => f({ state: 'speaking' }));
      for (let i = 0; i < lines.length && !stop; i++) { cbs.line.forEach(f => f({ line: i, id: lines[i].id })); const dur = lines[i].text.replace(/[^a-z]/gi, '').length / 11 * 1000, t0 = performance.now();
        while (performance.now() - t0 < dur && !stop) { await new Promise(r => setTimeout(r, 200)); cbs.pos.forEach(f => f({ ms: Math.min(dur, performance.now() - t0), line: i })); }
        await new Promise(r => setTimeout(r, 250)); }
      cbs.state.forEach(f => f({ state: 'idle', reason: stop ? 'viewer_stopped' : 'completed' })); } };
  const sample = async () => { await new Promise(r => setTimeout(r, 1500)); return { text: 'Hello there, it is good to meet you. I am an avatar made from one photograph, and my mouth is following these words. What would you like to talk about?' }; };
  window.claude = { use: async n => ({ sample, tts })[n] || null };
};
(async () => {
  fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
  const open = async init => {
    const p = await b.newPage({ viewport: { width: 900, height: 1100 }, deviceScaleFactor: 1 }); p.errs = []; p.on('pageerror', e => p.errs.push(e.message)); p.on('console', m => m.type() === 'error' && !/ERR_FAILED/.test(m.text()) && p.errs.push(m.text()));
    await p.route(/^https?:/, r => r.abort());                                 // nothing leaves this machine: the page's web fonts are not fetched
    if (init) await p.addInitScript(init);
    await p.goto(`file://${__dirname}/preview_${who}.html`);
    await p.waitForFunction(() => typeof pending !== 'undefined' && pending === 0 && live.state === 'idle', null, { timeout: 30000 }); await p.waitForTimeout(700);
    if (GAIN) await p.evaluate(g => { ACT[WHO].m.gain = g; }, GAIN);
    return p;
  };
  // ── 1. poses, forced ──
  let p = await open(null);
  await p.screenshot({ path: `${out}/${who}_page_idle.png` }); console.log('wrote', `check/${who}_page_idle.png`);
  const sheets = await p.evaluate(line => {
    const a = ACT[WHO], f = a.m.face, I = f.iod, T = document.createElement('canvas'); T.width = FW; T.height = FH; const tx = T.getContext('2d');
    const base = { o: 0, s: 0, g: 0, blink: 0, gx: 0, gy: 0, bu: 0, bd: 0, yaw: 0, pit: 0, roll: 0 }, nob = { sx: 0, sy: 0, rot: 0, lean: 0, tw: 0, lift: 0, wide: 0, hx: 0, hy: 0, wx: 0, wy: 0, wa: 0 };
    const draw = (q, bd) => { const z = Object.assign({}, base, q); compose(a, z); if (warpGL && warpGL.ok) warpGL.draw(a, z, bd ? Object.assign({}, nob, bd) : null, 0); tx.globalAlpha = 1; tx.drawImage(a.bg, 0, 0); tx.drawImage(warpGL && warpGL.ok ? warpGL.cv : a.pf, 0, 0); };
    // a sheet of tiles: list of [label, pose, body]; the same window of the picture (sx, sy, sw, sh) in every tile
    const sheet = (list, cols, cw, ch, win, q = 0.9) => {
      const K = document.createElement('canvas'); K.width = cols * cw; K.height = Math.ceil(list.length / cols) * (ch + 20); const k = K.getContext('2d'); k.fillStyle = '#111'; k.fillRect(0, 0, K.width, K.height);
      list.forEach(([name, pose, bd], i) => { draw(pose, bd); const x = (i % cols) * cw, y = Math.floor(i / cols) * (ch + 20); k.drawImage(T, win[0], win[1], win[2], win[3], x, y, cw, ch); k.fillStyle = '#fff'; k.font = '13px sans-serif'; k.fillText(name, x + 6, y + ch + 15); });
      return K.toDataURL('image/jpeg', q);
    };
    const R = {}, mw = 1.7 * I, mouth = [f.cx - mw / 2, f.cy + 0.62 * I - mw * 0.36, mw, mw * 0.72], ew = 2.5 * I, eyes = [f.cx - ew / 2, f.cy - 0.45 * I - ew * 0.24, ew, ew * 0.48], hw = 3.6 * I, head = [f.cx - hw / 2, Math.max(0, f.cy - 0.4 * I - hw * 0.58), hw, hw * 1.16];
    R['three.jpg'] = sheet([['relaxed mouth, as while speaking (smile 0)', {}], ["the photograph's own expression, as while listening (smile 0.5)", { g: 0.5 }], ['broad smile (smile 1)', { g: 1 }]], 1, FW, FH, [0, 0, FW, FH], 0.93);
    R['mouths.jpg'] = sheet([['relaxed, shut (jaw 0)', {}], ["photograph's expression", { g: 0.5 }], ['broad smile', { g: 1 }], ['pressed (m, b, p)', { o: -0.12 }], ['f / v', { o: 0.08, s: 0.2 }],
      ['jaw 0.1', { o: 0.1 }], ['jaw 0.2', { o: 0.2 }], ['jaw 0.3', { o: 0.3 }], ['jaw 0.4', { o: 0.4 }], ['jaw 0.5', { o: 0.5 }], ['jaw 0.65', { o: 0.65 }], ['jaw 0.8', { o: 0.8 }], ['jaw 1', { o: 1 }], ['jaw 1.15', { o: 1.15 }], ['jaw 1.3 (the most)', { o: 1.3 }],
      ['ee, half, jaw 0.25', { o: 0.25, s: 0.5 }], ['ee, jaw 0.1', { o: 0.1, s: 1 }], ['ee, jaw 0.25', { o: 0.25, s: 1 }], ['ee, jaw 0.6', { o: 0.6, s: 1 }], ['ee, jaw 1', { o: 1, s: 1 }],
      ['oo, half, jaw 0.2', { o: 0.2, s: -0.5 }], ['oo, jaw 0.1', { o: 0.1, s: -1 }], ['oo, jaw 0.2', { o: 0.2, s: -1 }], ['oh, jaw 0.6', { o: 0.6, s: -1 }], ['oh, jaw 1', { o: 1, s: -1 }],
      ['smiling, jaw 0.2', { o: 0.2, g: 1 }], ['smiling, jaw 0.55', { o: 0.55, g: 1 }], ['smiling, jaw 1', { o: 1, g: 1 }], ['between poses', { o: 0.41, s: 0.33 }], ['between poses, round', { o: 0.33, s: -0.7, g: 0.3 }]], 5, 300, 216, mouth);
    R['eyes.jpg'] = sheet([['open (relaxed)', {}], ["photograph's expression", { g: 0.5 }], ['half blink', { blink: 0.5 }], ['shut', { blink: 1 }], ['quarter blink', { blink: 0.25 }], ['eyes left', { gx: -1 }], ['eyes right', { gx: 1 }], ['eyes down', { gy: 1 }],
      ['half left', { gx: -0.5 }], ['half right, a little down', { gx: 0.5, gy: 0.3 }], ['smiling eyes (smile 1)', { g: 1 }], ['brows up', { bu: 1 }], ['brows up, half', { bu: 0.5 }], ['brows down', { bd: 1 }], ['thinking: aside, brows a little up', { gx: 0.6, gy: 0.22, bu: 0.14, yaw: 0.16 }], ['brows up + eyes shut', { bu: 0.9, blink: 1 }]], 4, 375, 180, eyes);
    R['head.jpg'] = sheet([['as photographed', { g: 0.5 }], ['turned right (yaw 1)', { yaw: 1, g: 0.5 }], ['turned left (yaw -1)', { yaw: -1, g: 0.5 }], ['nodded down (pit 1)', { pit: 1, g: 0.5 }], ['chin up (pit -0.9)', { pit: -0.9, g: 0.5 }], ['tilt (roll 0.05)', { roll: 0.05, g: 0.5 }], ['tilt (roll -0.05)', { roll: -0.05, g: 0.5 }],
      ['half right, half down', { yaw: 0.5, pit: 0.5, g: 0.5 }], ['nod + brows + turn, talking', { pit: 0.6, bu: 0.8, yaw: 0.5, o: 0.5 }], ['left, up, frown, eyes right, talking', { o: 0.41, s: 0.33, yaw: -0.4, pit: -0.3, bd: 0.4, gx: 0.5 }]], 5, 300, 348, head);
    const hair = (BODY[WHO] || BODY.cy).hair;
    R['body.jpg'] = sheet([['still', { g: 0.5 }, {}], ['breath in (full)', { g: 0.5 }, { lift: 0.066 * I, wide: 0.0042 }], ['breath out (empty)', { g: 0.5 }, { lift: -0.044 * I, wide: -0.0028 }], ['weight right', { g: 0.5 }, { sx: 0.12 * I, rot: 0.012 }], ['weight left', { g: 0.5 }, { sx: -0.12 * I, rot: -0.012 }],
      ['lean in + dip', { g: 0.5 }, { lean: 0.012, sy: 0.03 * I }], ['shoulders turned right', { g: 0.5, yaw: 0.6 }, { tw: 0.09 * I }], ['shoulders turned left', { g: 0.5, yaw: -0.6 }, { tw: -0.09 * I }],
      [`hair swung right as far as it goes (x ${hair})`, { g: 0.5 }, { hx: 0.14 * I * Math.min(1, hair), hy: 0 }], [`hair swung left and down (x ${hair})`, { g: 0.5 }, { hx: -0.14 * I * Math.min(1, hair), hy: 0.14 * I * Math.min(1, hair) }],
      ['all at once, right', { g: 0.5, yaw: 0.8, pit: 0.4 }, { sx: 0.1 * I, rot: 0.01, lean: 0.01, tw: 0.08 * I, lift: 0.066 * I, wide: 0.0042 }], ['all at once, left', { g: 0.5, yaw: -0.8, pit: -0.4 }, { sx: -0.1 * I, rot: -0.01, lean: 0, tw: -0.08 * I, lift: -0.044 * I, wide: -0.0028 }]], 4, 512, 288, [0, 0, FW, FH]);
    // ── a line, spoken: the page's own plan, engine and picture, stepped through by hand ──
    begin({ text: line, first: true }, clock()); const bb = live.beat, n = Math.ceil((bb.t1 + 0.35) * 12.5), cols = 10, cw = 180, ch = 150;
    const K = document.createElement('canvas'); K.width = cols * cw; K.height = Math.ceil(n / cols) * ch; const k = K.getContext('2d'), tr = -clamp(f.cx - 384, 0, FW - 768), os = [];
    const step = bt => { c.setTransform(1, 0, 0, 1, tr, 0); c.globalAlpha = 1; c.globalCompositeOperation = 'source-over'; drawActor(WHO, bb.start + bt, { b: bb, bt, zb: 1, zf: 1.02 }); c.setTransform(1, 0, 0, 1, 0, 0); };
    for (let t = -0.6; t < 0; t += 1 / 30) step(t);                                             // run the eased smile and the hair's spring in
    for (let i = 0; i < n; i++) {
      const bt = i / 12.5; step(bt); const x = (i % cols) * cw, y = Math.floor(i / cols) * ch, sw = 1.9 * I, sh = sw * (ch - 18) / cw;
      k.drawImage(scr, f.cx + tr - sw / 2, f.cy + 0.62 * I - sh / 2, sw, sh, x, y, cw, ch - 18);
      const ta = bt - bb.lead; let lab = '·'; for (const q of bb.sp.seg) if (q[2] > 0 && ta >= q[1] && ta < q[1] + q[2]) lab = ' ,.:?!'.includes(q[0]) ? 'pause' : q[0];
      let word = ''; bb.wt.forEach((w, j) => { if (bt >= w) word = bb.words[j]; }); const o = speechAt(bb, bt, WHO).o; os.push(o);
      k.fillStyle = '#111'; k.fillRect(x, y + ch - 18, cw, 18); k.fillStyle = '#fff'; k.font = '12px sans-serif'; k.fillText(`${lab}   ${word.slice(0, 11)}   ${o.toFixed(2)}`, x + 4, y + ch - 5);
    }
    R['speak_sounds.jpg'] = K.toDataURL('image/jpeg', 0.9);
    const n2 = Math.ceil((bb.t1 + 0.6) * 4), K2 = document.createElement('canvas'); K2.width = 4 * 384; K2.height = Math.ceil(n2 / 4) * 288; const k2 = K2.getContext('2d');
    for (let t = -0.6; t < 0; t += 1 / 30) step(t);
    for (let i = 0, last = 0; i < n2; i++) { const bt = i / 4; for (let t = last + 1 / 30; t < bt; t += 1 / 30) step(t); step(bt); last = bt; k2.drawImage(scr, 0, 0, 768, 576, (i % 4) * 384, Math.floor(i / 4) * 288, 384, 288); k2.fillStyle = '#fff'; k2.font = '13px sans-serif'; k2.fillText(`${bt.toFixed(2)} s`, (i % 4) * 384 + 8, Math.floor(i / 4) * 288 + 18); }
    R['speak_frames.jpg'] = K2.toDataURL('image/jpeg', 0.9);
    const sp = []; for (let bt = bb.t0; bt < bb.t1; bt += 0.01) sp.push(speechAt(bb, bt, WHO).o); sp.sort((x, y) => x - y);
    R.stats = { gl: !!(warpGL && warpGL.ok), gain: a.m.gain, style: STYLE[WHO], body: BODY[WHO], seconds: bb.t1 - bb.t0, median: sp[sp.length >> 1], p90: sp[Math.floor(sp.length * 0.9)], max: sp[sp.length - 1], open: sp.filter(v => v > 0.2).length / sp.length, pressed: sp.filter(v => v < -0.02).length / sp.length };
    finish(); rest(clock()); return R;
  }, LINE);
  for (const k in sheets) if (k !== 'stats') save(k, sheets[k]);
  const s = sheets.stats; console.log(`forced line (${s.seconds.toFixed(1)} s): mesh ${s.gl ? 'WebGL' : 'flat fallback'}, gain ${s.gain}, style ${s.style}, body ${JSON.stringify(s.body)} | opening: median ${s.median.toFixed(2)}, loud end (90th percentile) ${s.p90.toFixed(2)}, widest ${s.max.toFixed(2)}, above 0.2 for ${Math.round(100 * s.open)}% of the line, lips pressed for ${Math.round(100 * s.pressed)}% | errors: ${p.errs.length ? p.errs.slice(0, 3) : 'none'}`);
  await p.close();
  // ── 2. the page itself, with stand-ins for the reply and the voice ──
  p = await open(mocks);
  await p.fill('#say', 'Hi, who are you?'); await p.click('#send'); await p.waitForTimeout(900);
  await p.screenshot({ path: `${out}/${who}_page_thinking.png` }); console.log('wrote', `check/${who}_page_thinking.png`);
  const rows = []; let shots = 0, lastShot = -99;
  for (let i = 0; i < 700; i++) {
    const r = await p.evaluate(() => { const b = live.beat, bt = b ? PRE + planned() : 0; return { s: live.state, o: b ? speechAt(b, bt, WHO).o : 0, cur: live.cur, k: live.stretch }; }); rows.push(r);
    if (r.s === 'speaking' && shots < 4 && i - lastShot > 25 && (r.o > 0.4 || (shots === 2 && r.o < -0.02))) { await p.screenshot({ path: `${out}/${who}_page_speaking_${shots++}.png` }); lastShot = i; }
    if (i > 60 && r.s === 'idle') break; await p.waitForTimeout(40);
  }
  const sp = rows.filter(r => r.s === 'speaking'), last = rows[rows.length - 1];
  console.log(`page with stand-ins: states ${[...new Set(rows.map(r => r.s))].join(' > ')} | ${shots} screenshots while speaking | mouth open (>0.2) in ${Math.round(100 * sp.filter(r => r.o > 0.2).length / Math.max(1, sp.length))}% of the speaking time, widest ${Math.max(...sp.map(r => r.o)).toFixed(2)}, lines reached ${Math.max(...rows.map(r => r.cur)) + 1} | mouth at the end ${last.o.toFixed(2)} | pace estimate ${last.k.toFixed(2)} | errors: ${p.errs.length ? p.errs.slice(0, 3) : 'none'}`);
  await p.close(); await b.close();
})();
