// phoneme_strip.js <presenter> <line of theirs, from 0> <start s> <frames> <fps> <out.jpg> : the mouth, frame by frame, each
// frame labelled with the sound being made at that moment (from the recording's timing) and the jaw opening the page drew.
// For checking that the lips make sense for what is being said: shut on m, b, p; round on w and oo; open on ah.
const { chromium } = require('playwright');
(async () => {
  const [who, li, t0, n, fps, out] = [process.argv[2] || 'paige', +(process.argv[3] || 0), +(process.argv[4] || 0), +(process.argv[5] || 40), +(process.argv[6] || 25), process.argv[7] || 'phonemes.jpg'];
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 1360, height: 900 } }); const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto('file://' + __dirname + '/../demo/index.html');
  await p.waitForFunction(() => typeof pending !== 'undefined' && pending === 0, null, { timeout: 60000 }); await p.waitForTimeout(400);
  const url = await p.evaluate(([who, li, t0, n, fps]) => {
    choose(who); setPlaying(false); st.captions = false; st.grain = false; st.camera = false;
    const cols = 10, cw = 150, ch = 118, K = document.createElement('canvas'); K.width = cols * cw; K.height = Math.ceil(n / cols) * ch; const k = K.getContext('2d'), bt0 = starts[li] + t0;
    for (let i = 0; i < n; i++) {
      st.vt = bt0 + i / fps; render(); const [bb, bt] = where(st.vt), f = ACT[who].m.face, x = (i % cols) * cw, y = Math.floor(i / cols) * ch, sw = 1.9 * f.iod, sh = sw * (ch - 18) / cw;
      k.drawImage(scr, f.cx - sw / 2, f.cy + 0.62 * f.iod - sh / 2, sw, sh, x, y, cw, ch - 18);
      const ta = bt - bb.lead; let lab = '·'; for (const q of bb.sp.seg) if (q[2] > 0 && ta >= q[1] && ta < q[1] + q[2]) lab = ' ,.:?'.includes(q[0]) ? 'pause' : q[0];
      let word = ''; bb.wt.forEach((w, j) => { if (bt >= w) word = bb.words[j]; });
      k.fillStyle = '#111'; k.fillRect(x, y + ch - 18, cw, 18); k.fillStyle = '#fff'; k.font = '12px sans-serif'; k.fillText(`${lab}   ${word.slice(0, 9)}   ${speechAt(bb, bt, who).o.toFixed(2)}`, x + 4, y + ch - 5);
    }
    return K.toDataURL('image/jpeg', 0.9);
  }, [who, li, t0, n, fps]);
  require('fs').writeFileSync(out, Buffer.from(url.split(',')[1], 'base64')); console.log('wrote', out, 'errors:', errs); await b.close();
})();
