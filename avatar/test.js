// test.js : the live page in a headless browser, with stand-ins for what the artifact viewer provides.
//   sample  answers after 300 ms with a fixed reply of three sentences
//   tts     "speaks" each line at 11 letters a second (slower than the page assumes, to exercise its clock),
//           reporting the start of each line and the position within it five times a second, as the real one does
// It sends one message, records the mouth opening and the state every 50 ms, saves three frames, and reports whether the
// lips moved while "speaking", shut afterwards, and how far the page's estimate of the voice's pace moved.
// Then it loads the page again with no stand-ins at all (as opened from disk) and sends a message, to check the fallbacks.
// Run from the repository root:  node avatar/test.js
const { chromium } = require('playwright'); const fs = require('fs');
const mocks = () => {
  const cbs = { line: [], pos: [], state: [] }; let stop = false;
  const tts = { onLine: f => cbs.line.push(f), onPosition: f => cbs.pos.push(f), onState: f => cbs.state.push(f), stop: () => { stop = true; },
    speak: async lines => { stop = false; cbs.state.forEach(f => f({ state: 'speaking' }));
      for (let i = 0; i < lines.length && !stop; i++) { cbs.line.forEach(f => f({ line: i, id: lines[i].id })); const dur = lines[i].text.replace(/[^a-z]/gi, '').length / 11 * 1000, t0 = performance.now();
        while (performance.now() - t0 < dur && !stop) { await new Promise(r => setTimeout(r, 200)); cbs.pos.forEach(f => f({ ms: Math.min(dur, performance.now() - t0), line: i })); }
        await new Promise(r => setTimeout(r, 250)); }
      cbs.state.forEach(f => f({ state: 'idle', reason: stop ? 'viewer_stopped' : 'completed' })); } };
  const sample = async () => { await new Promise(r => setTimeout(r, 300)); return { text: 'Hello there, it is good to meet you. I am an avatar made from one photograph, and my mouth is following these words. What would you like to talk about?' }; };
  window.claude = { use: async n => ({ sample, tts })[n] || null };
};
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
  for (const [name, init] of [['with stand-ins', mocks], ['bare page', null]]) {
    const p = await b.newPage({ viewport: { width: 900, height: 1100 } }); const errs = []; p.on('pageerror', e => errs.push(e.message)); p.on('console', m => m.type() === 'error' && errs.push(m.text()));
    if (init) await p.addInitScript(init);
    await p.goto('file://' + __dirname + '/index.html');
    await p.waitForFunction(() => typeof pending !== 'undefined' && pending === 0 && live.state === 'idle', null, { timeout: 30000 }); await p.waitForTimeout(600);
    await p.fill('#say', 'Hi, who are you?'); await p.click('#send');
    const rows = []; let shots = 0;
    for (let i = 0; i < 520; i++) {
      const r = await p.evaluate(() => { const b = live.beat, bt = b ? PRE + planned() : 0; return { s: live.state, o: b ? speechAt(b, bt, WHO).o : 0, cur: live.cur, k: live.stretch, cap: document.getElementById('cap').textContent, voice: io.voice }; }); rows.push(r);
      if (init && r.s === 'speaking' && r.o > 0.45 && shots < 3 && (i % 12 === 0)) await p.screenshot({ path: `${__dirname}/test_${shots++}.png` });
      if (i > 40 && r.s === 'idle') break; await p.waitForTimeout(50);
    }
    const sp = rows.filter(r => r.s === 'speaking'), open = sp.filter(r => r.o > 0.2).length, last = rows[rows.length - 1];
    console.log(`${name}: states ${[...new Set(rows.map(r => r.s))].join(' > ')} | voice ${last.voice} | speaking for ${(sp.length * 0.05).toFixed(1)} s, mouth open (>0.2) in ${Math.round(100 * open / Math.max(1, sp.length))}% of it, widest ${Math.max(...sp.map(r => r.o)).toFixed(2)}, lines reached ${Math.max(...rows.map(r => r.cur)) + 1} | mouth at the end ${last.o.toFixed(2)} | pace estimate ${rows[0].k.toFixed(2)} -> ${last.k.toFixed(2)} | caption "${last.cap.slice(0, 50)}" | log ${await p.evaluate(() => document.getElementById('log').children.length)} entries | errors: ${errs.length ? errs.slice(0, 3) : 'none'}`);
    await p.close();
  }
  await b.close();
})();
