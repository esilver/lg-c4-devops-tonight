// poses.js <presenter> <out.jpg> [name;name;...] : one sheet of the face in every kind of pose the page can make, each forced directly
// (or only the named ones, drawn twice as large):
// head turned and nodded, brows, lids, gaze, smiles, and the mouth grid. A check that every pose path draws what its name says.
const { chromium } = require('playwright');
(async () => {
  const who = process.argv[2] || 'paige', out = process.argv[3] || `poses_${who}.jpg`, only = process.argv[4] ? process.argv[4].split(';') : null;
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 800, height: 500 } }); const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto('file://' + __dirname + '/../lg-c4/index.html');
  await p.waitForFunction(() => typeof pending !== 'undefined' && pending === 0, null, { timeout: 30000 }); await p.waitForTimeout(400);
  const url = await p.evaluate(([who, only]) => {
    const a = ACT[who], f = a.m.face, ALL = [
      ['neutral', {}], ['turned right', { yaw: 1 }], ['turned left', { yaw: -1 }], ['nodded down', { pit: 1 }], ['chin up', { pit: -0.9 }], ['tilt', { roll: 0.05 }], ['brows up', { bu: 1 }], ['brows down', { bd: 1 }],
      ['half blink', { blink: 0.5 }], ['eyes shut', { blink: 1 }], ['eyes left', { gx: -1 }], ['eyes right', { gx: 1 }], ['eyes down', { gy: 1 }], ['half smile', { g: 0.5 }], ['smile', { g: 1 }], ['smile, talking', { g: 1, o: 0.55 }],
      ['pressed (m)', { o: -0.12 }], ['jaw 0.15', { o: 0.15 }], ['jaw 0.3', { o: 0.3 }], ['jaw 0.5', { o: 0.5 }], ['jaw 0.75', { o: 0.75 }], ['jaw 1', { o: 1 }], ['jaw 1.3 (max)', { o: 1.3 }], ['f / v', { o: 0.08, s: 0.2 }],
      ['ee, half', { o: 0.25, s: 0.5 }], ['ee', { o: 0.25, s: 1 }], ['ee, open', { o: 0.6, s: 1 }], ['oo, half', { o: 0.2, s: -0.5 }], ['oo', { o: 0.2, s: -1 }], ['oh, open', { o: 0.6, s: -1 }], ['nod + brows + turn', { pit: 0.6, bu: 0.8, yaw: 0.5, o: 0.5 }], ['between poses', { o: 0.41, s: 0.33, yaw: -0.4, pit: -0.3, bd: 0.4, gx: 0.5 }]];
    const P = only ? ALL.filter(q => only.includes(q[0])) : ALL, cw = only ? 460 : 230, ch = only ? 524 : 262, cols = only ? 4 : 8, K = document.createElement('canvas'); K.width = cols * cw; K.height = Math.ceil(P.length / cols) * ch; const k = K.getContext('2d');
    P.forEach(([name, q], i) => {
      const z = Object.assign({ o: 0, s: 0, g: 0, blink: 0, gx: 0, gy: 0, bu: 0, bd: 0, yaw: 0, pit: 0, roll: 0 }, q);
      compose(a, z); warpGL.draw(a, z); c.setTransform(1, 0, 0, 1, 0, 0); c.globalAlpha = 1; c.drawImage(a.bg, 0, 0); c.drawImage(warpGL.cv, 0, 0);
      const x = (i % cols) * cw, y = Math.floor(i / cols) * ch, sw = 3.3 * f.iod, sh = sw * ch / cw;
      k.drawImage(scr, f.cx - sw / 2, f.cy - 0.35 * f.iod - sh / 2, sw, sh, x, y, cw, ch);
      k.fillStyle = 'rgba(0,0,0,.6)'; k.fillRect(x, y + ch - 20, cw, 20); k.fillStyle = '#fff'; k.font = '13px sans-serif'; k.fillText(name, x + 6, y + ch - 6);
    });
    return K.toDataURL('image/jpeg', 0.9);
  }, [who, only]);
  require('fs').writeFileSync(out, Buffer.from(url.split(',')[1], 'base64')); console.log('wrote', out, 'errors:', errs); await b.close();
})();
