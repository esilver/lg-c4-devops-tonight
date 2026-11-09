const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 1200, height: 750 } });
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto('file://' + __dirname + '/../lg-c4/index.html');
  for (let i = 2; i <= 5; i++) { await p.keyboard.press(String(i)); await p.waitForTimeout(1500);
    const url = await p.evaluate(() => scr.toDataURL('image/jpeg', 0.6)); require('fs').writeFileSync(`c${i}.jpg`, Buffer.from(url.split(',')[1], 'base64')); }
  console.log('errors:', errs); await b.close();
})();
