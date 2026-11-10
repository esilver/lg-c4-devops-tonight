// demo_check.js : the single-presenter demo page. Loads it at a desktop and a phone width, pauses on a chosen moment,
// switches presenter, switches between the two sets of voices and back, turns on the close-up, and saves screenshots.
// Reports script errors and whether the layout overflows sideways. Run from tests/output:  node ../demo_check.js
const { chromium, devices } = require('playwright');
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--autoplay-policy=no-user-gesture-required'] });
  for (const [name, opt] of [['desktop', { viewport: { width: 1360, height: 1200 } }], ['phone', devices['iPhone 13']]]) {
    const ctx = await b.newContext(opt), p = await ctx.newPage(); const errs = [];
    p.on('pageerror', e => errs.push(e.message)); p.on('console', m => m.type() === 'error' && errs.push(m.text()));
    await p.goto('file://' + __dirname + '/../demo/index.html');
    await p.waitForFunction(() => typeof pending !== 'undefined' && pending === 0, null, { timeout: 60000 }); await p.waitForTimeout(600);
    await p.evaluate(() => { setPlaying(false); st.vt = 1.9; }); await p.waitForTimeout(300);
    const wide = await p.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    await p.screenshot({ path: `demo_${name}.png`, fullPage: true });
    const lenNew = await p.evaluate(() => total);
    await p.click('[data-voices=first]'); await p.waitForTimeout(300);
    const lenFirst = await p.evaluate(() => total); await p.evaluate(() => { st.vt = 2.4; }); await p.waitForTimeout(200);
    if (name === 'desktop') await p.screenshot({ path: 'demo_first_voices.png', fullPage: false });
    await p.click('[data-voices=second]'); await p.waitForTimeout(200); const lenSecond = await p.evaluate(() => total);
    await p.click('[data-voices=new]'); await p.keyboard.press('3'); await p.waitForTimeout(200);
    await p.evaluate(() => { document.getElementById('o-closeup').click(); st.vt = 3.1; }); await p.waitForTimeout(300);
    if (name === 'desktop') await p.screenshot({ path: 'demo_closeup.png', fullPage: false });
    console.log(name, '| sideways overflow px:', wide, '| playlist seconds: Phonon', lenNew.toFixed(2), 'Chatterbox', lenSecond.toFixed(2), 'Kokoro', lenFirst.toFixed(2), '| errors:', errs.length ? errs.slice(0, 4) : 'none');
    await ctx.close();
  }
  await b.close();
})();
