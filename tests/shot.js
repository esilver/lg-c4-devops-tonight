const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 1200, height: 750 } });
  const errs = []; p.on('pageerror', e => errs.push(e.message)); p.on('console', m => m.type()==='error' && errs.push(m.text()));
  await p.goto('file://' + __dirname + '/../lg-c4/index.html');
  await p.waitForTimeout(1500); await p.screenshot({ path: 's1.png' });
  await p.keyboard.press('ArrowRight'); await p.waitForTimeout(1200); await p.screenshot({ path: 's2.png' });
  await p.mouse.move(600, 300); await p.mouse.down(); await p.mouse.move(100, 250, { steps: 5 }); await p.mouse.up();
  await p.keyboard.press('p'); await p.waitForTimeout(600); await p.screenshot({ path: 's3.png' });
  await p.keyboard.press('p'); await p.keyboard.press('3');
  await p.mouse.move(600, 300); await p.mouse.down(); await p.mouse.move(1000, 330, { steps: 5 }); await p.mouse.up();
  await p.setViewportSize({ width: 400, height: 800 }); await p.waitForTimeout(1500); await p.screenshot({ path: 's4.png' });
  console.log('errors:', errs); await b.close();
})();
