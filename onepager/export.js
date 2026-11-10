// export.js : the one-pager as a single picture, for posting where a link will not do.
// Loads onepager/index.html at 1200 px wide and twice the pixel density, photographs it in slices (one very tall
// screenshot can exceed what the browser will draw), and writes them as slice_NN.png with the position of each
// section; stitch.py joins them.
// Run from the repository root:  node onepager/export.js && gen/venv6/bin/python onepager/stitch.py
const { chromium } = require('playwright'); const fs = require('fs');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1200, height: 1000 }, deviceScaleFactor: 2 });
  await p.goto('file://' + __dirname + '/index.html'); await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(800);
  const info = await p.evaluate(() => ({ h: document.documentElement.scrollHeight, tops: [...document.querySelectorAll('main > section')].map(e => Math.round(e.getBoundingClientRect().top + scrollY)), fonts: [...document.fonts].filter(f => f.status === 'loaded').map(f => f.family + ' ' + f.weight), wide: document.documentElement.scrollWidth - document.documentElement.clientWidth }));
  const H = 1600; fs.mkdirSync(__dirname + '/slices', { recursive: true }); let n = 0;
  for (let y = 0; y < info.h; y += H, n++) await p.screenshot({ path: `${__dirname}/slices/slice_${String(n).padStart(2, '0')}.png`, fullPage: true, clip: { x: 0, y, width: 1200, height: Math.min(H, info.h - y) } });
  fs.writeFileSync(__dirname + '/slices/sections.json', JSON.stringify({ height: info.h, tops: info.tops, scale: 2 }));
  console.log('page height', info.h, 'px, slices', n, '| sideways overflow', info.wide, '| fonts loaded:', [...new Set(info.fonts)].join(', ')); await b.close();
})();
