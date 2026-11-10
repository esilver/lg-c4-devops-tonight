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
  const curves = await p.evaluate(() => BEATS.filter(b => b.sp).map(b => { const o = [], s = []; for (let t = 0; t < b.dur; t += 1 / 60) { const q = speechAt(b, t, b.who); o.push(+q.o.toFixed(3)); s.push(+q.s.toFixed(3)); } return { who: b.who, dur: +b.dur.toFixed(2), syl: b.stress.length, o, s, wt: b.wt, words: b.words, stress: b.stress }; }));
  require('fs').writeFileSync('curves.json', JSON.stringify(curves));
  console.log('errors:', errs); await b.close();
})();
