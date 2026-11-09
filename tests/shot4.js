const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 1200, height: 750 } });
  const errs = []; p.on('pageerror', e => errs.push(e.message)); p.on('console', m => m.type() === 'error' && errs.push(m.text()));
  await p.goto('file://' + __dirname + '/../lg-c4/index.html');
  await p.waitForFunction(() => typeof pending !== 'undefined' && pending === 0, null, { timeout: 30000 });
  await p.waitForTimeout(500);
  const info = await p.evaluate(() => ({ len: SHOW_LEN, beats: BEATS.map(b => [Math.round(b.start * 10) / 10, b.kind, b.who || '']) }));
  if (process.argv[2] === 'info') console.log(JSON.stringify(info));
  const times = process.argv.slice(3).map(Number), t0 = Date.now();
  for (const [i, t] of times.entries()) {
    const url = await p.evaluate(t => { readyAt = 0; switchedAt = -10; c.save(); chNews(t); c.restore(); return scr.toDataURL('image/jpeg', 0.85); }, t);
    require('fs').writeFileSync(`n${i}.jpg`, Buffer.from(url.split(',')[1], 'base64'));
  }
  const ms = await p.evaluate(() => { const t0 = performance.now(); for (let i = 0; i < 60; i++) { c.save(); chNews(20 + i / 60); c.restore(); } return (performance.now() - t0) / 60; });
  console.log('ms/frame', ms.toFixed(2), 'errors:', errs); await b.close();
})();
