// body_check.js <presenter> <out dir> [seconds] [fps] : plays one presenter in the demo page with the camera, grain and
// captions off (so only the presenter moves) three times over: as shown (f0000.jpg …), with the hair's spring and the wind
// switched off (h0000.jpg …), and with body and hair both switched off (r0000.jpg …). With the frames it writes what the
// engine asked the body to do at every moment (breath, shift, turn, hair) and a few points worth watching (shoulders,
// chest, the freest hair) -> <out dir>/body.json. body_check.py then measures how far those points really moved.
const { chromium } = require('playwright'); const fs = require('fs');
(async () => {
  const who = process.argv[2] || 'paige', dir = process.argv[3] || 'body', secs = parseFloat(process.argv[4] || '0'), fps = parseFloat(process.argv[5] || '30'); fs.mkdirSync(dir, { recursive: true });
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 1360, height: 900 } }); const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto('file://' + __dirname + '/../demo/index.html');
  await p.waitForFunction(() => typeof pending !== 'undefined' && pending === 0, null, { timeout: 30000 }); await p.waitForTimeout(500);
  const info = await p.evaluate(who => {
    choose(who); setPlaying(false); st.camera = false; st.grain = false; st.captions = false;
    const inner = bodyAt; window.__bd = null; bodyAt = (id, q, ts) => { const o = inner(id, q, ts); window.__bd = Object.assign({ ts: ts % 600, yaw: q.yaw, pit: q.pit, roll: q.roll, o: q.o, on: q.on ? 1 : 0, g: q.g, air: breathAt(id, ts) }, o); return o; };
    const a = ACT[who], m = a.m, B = m.body, f = m.face, dec = k => B[k] ? Uint8Array.from(atob(B[k]), ch => ch.charCodeAt(0)) : null, mb = dec('b'), mh = dec('h'), mw = dec('w');
    const at = (mp, x, y) => mp ? mp[Math.round(y / B.step) * B.cols + Math.round(x / B.step)] / 255 : 0;
    // the freest hair that is clear of the pinned bottom edge, and the most wind-blown
    let tip = null, gust = null;
    for (let j = 0; j < B.rows; j++) for (let i = 0; i < B.cols; i++) { const x = i * B.step, y = j * B.step, k = j * B.cols + i; if (y > FH - 0.6 * f.iod) continue;
      if (mh && (!tip || mh[k] > tip.v * 255)) tip = { x, y, v: mh[k] / 255 }; if (mw && (!gust || mw[k] > gust.v * 255)) gust = { x, y, v: mw[k] / 255 }; }
    const pts = { head: { x: f.cx, y: f.cy - 0.45 * f.iod }, chest: { x: B.cx, y: Math.min(B.sy + 0.9 * f.iod, FH - 0.65 * f.iod) }, shoulderL: { x: B.cx - 0.6 * B.r, y: B.sy + 0.45 * f.iod }, shoulderR: { x: B.cx + 0.6 * B.r, y: B.sy + 0.45 * f.iod }, tip, gust };
    if (tip && tip.v < 0.3) tip = pts.tip = null;                 // no loose hair to watch
    for (const k in pts) if (pts[k]) Object.assign(pts[k], { body: at(mb, pts[k].x, pts[k].y), hair: at(mh, pts[k].x, pts[k].y), wind: at(mw, pts[k].x, pts[k].y) });
    // how much of the picture's bottom row is covered by the figure: if the figure were ever lifted off the bottom edge, this would drop
    const row = document.createElement('canvas'); row.width = FW; row.height = 1; const rx = row.getContext('2d', { willReadFrequently: true });
    window.__bottom = () => { rx.clearRect(0, 0, FW, 1); rx.drawImage(warpGL.cv, 0, FH - 1, FW, 1, 0, 0, FW, 1); const d = rx.getImageData(0, 0, FW, 1).data; let n = 0; for (let i = 3; i < d.length; i += 4) if (d[i] > 128) n++; return n; };
    return { total, gl: !!(warpGL && warpGL.ok), face: f, body: { cx: B.cx, sy: B.sy, r: B.r, chin: B.chin }, style: BODY[who], pts, lines: L.map((b, i) => ({ start: starts[i], dur: b.dur, t0: b.t0, t1: b.t1, phr: b.mo.phr, text: b.text })) };
  }, who);
  const n = Math.floor((secs || info.total) * fps), rows = [], bottom = { f: [], h: [], r: [] };
  for (const [pre, setup] of [['f', () => { st.body = true; }], ['h', who => { st.body = true; window.__keep = Object.assign({}, BODY[who]); BODY[who].hair = 0; BODY[who].wind = 0; }], ['r', who => { Object.assign(BODY[who], window.__keep); st.body = false; }]]) {
    await p.evaluate(setup, who);
    for (let i = 0; i < n; i++) {
      const r = await p.evaluate(t => { st.vt = t; render(); return { bd: window.__bd, bottom: window.__bottom(), url: scr.toDataURL('image/jpeg', 0.93) }; }, i / fps);
      fs.writeFileSync(`${dir}/${pre}${String(i).padStart(4, '0')}.jpg`, Buffer.from(r.url.split(',')[1], 'base64')); if (pre === 'f') rows.push(Object.assign({ t: i / fps }, r.bd)); bottom[pre].push(r.bottom);
    }
  }
  fs.writeFileSync(`${dir}/body.json`, JSON.stringify(Object.assign(info, { who, fps, rows, bottom })));
  console.log(who, 'frames', n, 'x 3, mesh:', info.gl, 'errors:', errs); await b.close();
})();
