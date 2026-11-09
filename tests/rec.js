// rec.js <presenter> <out dir> : renders the demo frame by frame (full frame + mouth close-up side by side) for encoding
const { chromium } = require('playwright'); const fs = require('fs');
(async () => {
  const who = process.argv[2] || 'paige', dir = process.argv[3] || 'rec'; fs.mkdirSync(dir, { recursive: true });
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 1360, height: 900 } });
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto('file://' + __dirname + '/../demo/index.html');
  await p.waitForFunction(() => typeof pending !== 'undefined' && pending === 0, null, { timeout: 30000 }); await p.waitForTimeout(500);
  const total = await p.evaluate(who => { choose(who); setPlaying(false); window.__combo = document.createElement('canvas'); __combo.width = 2048; __combo.height = 576; return total; }, who);
  const n = Math.floor(total * 30);
  for (let i = 0; i < n; i++) {
    const url = await p.evaluate(t => { const x = __combo.getContext('2d'); st.vt = t; st.closeup = false; render(); x.drawImage(scr, 0, 0); st.closeup = true; st.captions = false; render(); x.drawImage(scr, 1024, 0); st.captions = true; st.closeup = false; return __combo.toDataURL('image/jpeg', 0.93); }, i / 30);
    fs.writeFileSync(`${dir}/f${String(i).padStart(4, '0')}.jpg`, Buffer.from(url.split(',')[1], 'base64'));
  }
  console.log('frames', n, 'seconds', total.toFixed(2), 'errors:', errs); await b.close();
})();
