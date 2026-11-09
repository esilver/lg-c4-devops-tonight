const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 1200, height: 750 } });
  const errs = []; p.on('pageerror', e => errs.push(e.message)); p.on('console', m => m.type()==='error' && errs.push(m.text()));
  await p.goto('file://' + __dirname + '/../lg-c4/index.html');
  await p.waitForTimeout(800);
  const info = await p.evaluate(() => ({ len: SHOW_LEN, beats: BEATS.map(b => [Math.round(b.start*10)/10, b.scene, b.shot, b.who]) }));
  console.log(JSON.stringify(info));
  const times = process.argv.slice(2).map(Number);
  for (const [i, t] of times.entries()) {
    const url = await p.evaluate(t => { switchedAt = -10; c.save(); chNews(t); c.restore(); return scr.toDataURL('image/jpeg', 0.85); }, t);
    require('fs').writeFileSync(`n${i}.jpg`, Buffer.from(url.split(',')[1], 'base64'));
  }
  await p.waitForTimeout(9000); await p.screenshot({ path: 'tv.png' });
  console.log('errors:', errs); await b.close();
})();
