// ios_sound_check.js : the iPhone-only part of the sound engine, exercised in Chromium pretending to be an iPhone.
// It taps the Sound button on both pages and reports: the button's label, whether the silent keep-alive element exists
// and is playing, the audio session type (a stand-in object is planted, since Chromium has none), the audio context's
// state and how many lines decoded; then taps again and checks everything stops. This shows the code path runs without
// error. It cannot show that a real ringer switch is overridden: only a real device can.   node ../ios_sound_check.js
const { chromium, devices } = require('playwright');
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--autoplay-policy=no-user-gesture-required'] });
  for (const page of ['lg-c4/index.html', 'demo/index.html']) {
    const ctx = await b.newContext(devices['iPhone 13']), p = await ctx.newPage(); const errs = [];
    p.on('pageerror', e => errs.push(e.message)); p.on('console', m => m.type() === 'error' && errs.push(m.text()));
    await p.addInitScript(() => { navigator.audioSession = { type: 'auto' }; });
    await p.goto('file://' + __dirname + '/../' + page);
    await p.waitForFunction(() => typeof pending !== 'undefined' && pending === 0, null, { timeout: 60000 });
    const btn = page.startsWith('demo') ? '#snd' : '#sound';
    await p.tap(btn); await p.waitForTimeout(2500);
    const on = await p.evaluate(() => ({ status: sndStatus(), label: document.querySelector('#snd, #sound').textContent, keepAlive: !!snd.keep, keepAlivePlaying: snd.keep ? !snd.keep.paused : null, session: navigator.audioSession && navigator.audioSession.type, context: snd.ac.state, lines: snd.bufs.filter(Boolean).length }));
    await p.tap(btn); await p.waitForTimeout(400);
    const off = await p.evaluate(() => ({ status: sndStatus(), label: document.querySelector('#snd, #sound').textContent, keepAlivePlaying: snd.keep ? !snd.keep.paused : null }));
    console.log(page, '\n  on: ', JSON.stringify(on), '\n  off:', JSON.stringify(off), '\n  errors:', errs.length ? errs : 'none'); await ctx.close();
  }
  await b.close();
})();
