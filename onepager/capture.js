// capture.js : the pictures for the one-pager that have to come from the running pages.
//   src/hero.png     the television page, camera moved in, a presenter speaking
//   src/chart.png    the demo page's chart of what drives the face during one line
// Run from the repository root:  node onepager/capture.js      (the pose sheet and the mouth strip come from tests/poses.js
// and tests/phoneme_strip.js; make_images.py says how)
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
  let p = await b.newPage({ viewport: { width: 1280, height: 760 }, deviceScaleFactor: 2 }); const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto('file://' + __dirname + '/../lg-c4/index.html');
  await p.waitForFunction(() => typeof pending !== 'undefined' && pending === 0, null, { timeout: 60000 });
  // The camera is moved in, and the bulletin is held at one moment (6.6 s: the anchor is a few words into her first
  // line, with her name strap up), so the picture does not depend on how fast this machine draws.
  await p.evaluate(T => { cam.auto = false; cam.yaw = -0.22; cam.pitch = 0.07; cam.dist = 2.0; (function hold() { readyAt = performance.now() / 1000 - T; requestAnimationFrame(hold); })(); }, 6.6);
  await p.waitForTimeout(2500);
  await p.screenshot({ path: __dirname + '/src/hero.png' });
  await p.close();
  p = await b.newPage({ viewport: { width: 1360, height: 1500 }, deviceScaleFactor: 2 }); p.on('pageerror', e => errs.push(e.message));
  await p.goto('file://' + __dirname + '/../demo/index.html');
  await p.waitForFunction(() => typeof pending !== 'undefined' && pending === 0, null, { timeout: 60000 }); await p.waitForTimeout(1200);
  await p.evaluate(() => { setPlaying(false); st.vt = 3.05; }); await p.waitForTimeout(500);
  const card = await p.evaluateHandle(() => document.getElementById('chart').closest('.card'));
  await card.asElement().screenshot({ path: __dirname + '/src/chart.png' });
  console.log('captured; errors:', errs); await b.close();
})();
