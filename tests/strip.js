// strip.js <startShowTime> <step> <count> <out prefix> : renders consecutive frames of the TV picture
const { chromium } = require('playwright');
(async () => {
  const [t0, step, n, pre] = [parseFloat(process.argv[2]), parseFloat(process.argv[3]), parseInt(process.argv[4]), process.argv[5] || 'f'];
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 800, height: 500 } });
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto('file://' + __dirname + '/../lg-c4/index.html');
  await p.waitForFunction(() => typeof pending !== 'undefined' && pending === 0, null, { timeout: 30000 }); await p.waitForTimeout(400);
  for (let i = 0; i < n; i++) {
    const url = await p.evaluate(t => { readyAt = 0; switchedAt = -10; c.save(); chNews(t); c.restore(); return scr.toDataURL('image/jpeg', 0.9); }, t0 + i * step);
    require('fs').writeFileSync(`${pre}${i}.jpg`, Buffer.from(url.split(',')[1], 'base64'));
  }
  // every line's tracks at 60 samples a second: jaw, lip shape, head turn and nod, brows, blink, gaze, plus the events they were built from
  const curves = await p.evaluate(() => BEATS.filter(b => b.sp).map(b => { const k = { o: [], s: [], yaw: [], pit: [], roll: [], bu: [], bd: [], blink: [], gx: [], gy: [], g: [], f0: [] };
    for (let t = 0; t < b.dur; t += 1 / 60) { const q = faceAt(b.who, b, t, b.start + t, false); for (const n in k) if (n !== 'f0') k[n].push(+q[n].toFixed(4)); k.f0.push(+pitchAt(b, t).toFixed(2)); }
    return Object.assign(k, { who: b.who, ai: b.ai, start: +b.start.toFixed(3), dur: +b.dur.toFixed(3), lead: b.lead, t0: b.t0, t1: b.t1, wt: b.wt, words: b.words, nods: b.mo.nods, brows: b.mo.brows, frowns: b.mo.frowns, phr: b.mo.phr, blinks: b.mo.blinks }); }));
  require('fs').writeFileSync('curves.json', JSON.stringify(curves));
  console.log('errors:', errs); await b.close();
})();
