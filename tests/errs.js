// errs.js [page] : load a built page and print any script errors (default: the TV page)
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--autoplay-policy=no-user-gesture-required'] });
  const p = await b.newPage(); const errs = [];
  p.on('pageerror', e => errs.push(e.message + ' @ ' + ((e.stack || '').split('\n')[1] || '').trim())); p.on('console', m => m.type() === 'error' && errs.push(m.text()));
  await p.goto('file://' + __dirname + '/../' + (process.argv[2] || 'lg-c4/index.html')); await p.waitForTimeout(3000);
  console.log(errs.length ? errs.slice(0, 6) : 'no errors'); await b.close();
})();
