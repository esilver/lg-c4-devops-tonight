// capture.js : the picture for the one-pager that has to come from a running page.
//   src/chart.png    the demo page's chart of what drives the face during one line
// Run from the repository root:  node onepager/capture.js      (the pose sheet and the mouth strip come from tests/poses.js
// and tests/phoneme_strip.js; make_images.py says how)
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
  const errs = []; let p;
  p = await b.newPage({ viewport: { width: 1360, height: 1500 }, deviceScaleFactor: 2 }); p.on('pageerror', e => errs.push(e.message));
  await p.goto('file://' + __dirname + '/../demo/index.html');
  await p.waitForFunction(() => typeof pending !== 'undefined' && pending === 0, null, { timeout: 60000 }); await p.waitForTimeout(1200);
  await p.evaluate(() => { setPlaying(false); st.vt = 3.05; }); await p.waitForTimeout(500);
  const card = await p.evaluateHandle(() => document.getElementById('chart').closest('.card'));
  await card.asElement().screenshot({ path: __dirname + '/src/chart.png' });
  console.log('captured; errors:', errs); await b.close();
})();
