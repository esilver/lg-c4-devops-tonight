const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 1200, height: 750 }, deviceScaleFactor: 2 });
  const errs = []; p.on('pageerror', e => errs.push(e.message)); p.on('console', m => m.type() === 'error' && errs.push(m.text()));
  await p.goto('file://' + __dirname + '/../lg-c4/index.html');
  await p.waitForFunction(() => pending === 0);
  await p.waitForTimeout(9000); await p.screenshot({ path: 'tv1.png' });
  await p.evaluate(() => { cam.auto = false; cam.yaw = -0.18; cam.pitch = 0.05; cam.dist = 1.75; });
  await p.waitForTimeout(6000); await p.screenshot({ path: 'tv2.png' });
  await p.keyboard.press('ArrowRight'); await p.waitForTimeout(700); await p.keyboard.press('ArrowLeft'); await p.waitForTimeout(1500);
  await p.screenshot({ path: 'tv3.png' });
  const gl2 = await p.evaluate(() => GL2);
  await p.setViewportSize({ width: 400, height: 800 }); await p.waitForTimeout(2500); await p.screenshot({ path: 'tv4.png' });
  console.log('GL2', gl2, 'errors:', errs); await b.close();
})();
