// rec_show.js <out dir> [fps] : render every frame of the bulletin's picture (the 1024x576 canvas the TV shows), for encoding.
// Also writes timing.json with each line's start, so a sound track can be laid under the frames.
const { chromium } = require('playwright'); const fs = require('fs');
(async () => {
  const dir = process.argv[2] || 'rec_show', fps = parseFloat(process.argv[3] || '30'); fs.mkdirSync(dir, { recursive: true });
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 800, height: 500 } }); const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto('file://' + __dirname + '/../lg-c4/index.html');
  await p.waitForFunction(() => typeof pending !== 'undefined' && pending === 0, null, { timeout: 30000 }); await p.waitForTimeout(400);
  const info = await p.evaluate(() => ({ len: SHOW_LEN, beats: BEATS.map(b => ({ ai: b.ai == null ? -1 : b.ai, start: b.start, dur: b.dur, kind: b.kind, lead: b.lead || 0 })) }));
  fs.writeFileSync(`${dir}/timing.json`, JSON.stringify(info)); const n = Math.floor(info.len * fps);
  for (let i = 0; i < n; i++) {
    const url = await p.evaluate(t => { readyAt = 0; switchedAt = -10; c.save(); chNews(t); c.restore(); return scr.toDataURL('image/jpeg', 0.92); }, i / fps);
    fs.writeFileSync(`${dir}/f${String(i).padStart(5, '0')}.jpg`, Buffer.from(url.split(',')[1], 'base64'));
  }
  console.log('frames', n, 'seconds', info.len.toFixed(2), 'errors:', errs); await b.close();
})();
