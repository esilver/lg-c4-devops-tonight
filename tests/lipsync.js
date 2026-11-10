// lipsync.js <page.html> <out.json> : dump every line's mouth-opening curve from a built page, 100 samples a second, on
// the recording's own clock (0 = first sample of the line's audio). Works on this build and on earlier ones.
const { chromium } = require('playwright'); const path = require('path');
(async () => {
  const page = path.resolve(process.argv[2]), out = process.argv[3] || 'lipsync.json';
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 800, height: 500 } }); const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto('file://' + page);
  await p.waitForFunction(() => typeof pending !== 'undefined' && pending === 0, null, { timeout: 30000 }); await p.waitForTimeout(300);
  const d = await p.evaluate(() => BEATS.filter(b => b.sp).map(b => { const lead = b.lead == null ? LEAD : b.lead, o = [];
    for (let t = 0; t < b.sp.len; t += 0.01) o.push(+speechAt(b, t + lead, b.who).o.toFixed(3)); return { ai: b.ai, who: b.who, len: b.sp.len, o }; }));
  require('fs').writeFileSync(out, JSON.stringify(d)); console.log('wrote', out, d.length, 'lines; errors:', errs); await b.close();
})();
