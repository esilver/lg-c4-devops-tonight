// sound_check.js : turn sound on in a headless browser and check the engine end to end.
//  1. every line decodes, the decoder delay is measured, both pieces of music render
//  2. while the show plays, the voice stays locked to the picture (scheduled position vs wanted position, restarts counted)
//  3. the set's output is recorded for a stretch (rec.webm) and the two music buffers are dumped (sting_*.f32) for analysis
// Run from tests/output:  node ../sound_check.js [seconds to record]
const { chromium } = require('playwright'); const fs = require('fs');
(async () => {
  const secs = parseFloat(process.argv[2] || '24');
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--autoplay-policy=no-user-gesture-required'] });
  const p = await b.newPage({ viewport: { width: 1000, height: 640 } });
  const errs = []; p.on('pageerror', e => errs.push(e.message)); p.on('console', m => m.type() === 'error' && errs.push(m.text()));
  await p.goto('file://' + __dirname + '/../lg-c4/index.html');
  await p.waitForFunction(() => typeof pending !== 'undefined' && pending === 0, null, { timeout: 30000 });
  await p.click('#sound');
  await p.waitForFunction(() => snd.ready, null, { timeout: 60000 });
  const info = await p.evaluate(() => ({ state: snd.ac.state, sr: snd.ac.sampleRate, lagMs: Math.round(snd.lag * 1000), latencyMs: Math.round((snd.ac.outputLatency || snd.ac.baseLatency || 0) * 1000),
    lines: snd.bufs.filter(Boolean).length, durs: snd.bufs.map((x, i) => +(x.duration - SPEECH[i].len).toFixed(3)), sting: Object.fromEntries(Object.entries(snd.sting).map(([k, v]) => [k, v ? +v.duration.toFixed(2) : null])) }));
  console.log(JSON.stringify(info));
  for (const k of ['intro', 'outro']) {
    const arr = await p.evaluate(k => { const bf = snd.sting[k]; if (!bf) return null; const d = bf.getChannelData(0), e = bf.getChannelData(1), o = new Float32Array(d.length); for (let i = 0; i < d.length; i++) o[i] = (d[i] + e[i]) / 2; return Array.from(new Uint8Array(o.buffer)); }, k);
    if (arr) fs.writeFileSync(`sting_${k}.f32`, Buffer.from(arr));
  }
  // restart the bulletin from its titles and record the set's output while logging sync every 50 ms
  await p.evaluate(() => {
    window.__log = []; window.__chunks = [];
    const dest = snd.ac.createMediaStreamDestination(); snd.master.connect(dest);
    const rec = new MediaRecorder(dest.stream, { mimeType: 'audio/webm;codecs=opus', audioBitsPerSecond: 128000 }); window.__rec = rec;
    rec.ondataavailable = e => window.__chunks.push(e.data);
    channel = 0; switchedAt = nowT - 0.32; readyAt = 0; window.__t0 = nowT; rec.start(); window.__recAt = performance.now() / 1000;
    window.__iv = setInterval(() => { const now = performance.now() / 1000, at = showAt(now), c = snd.cur; if (at && at.b.sp && c && c.src && c.key === at.b.ai) __log.push([+(now - __t0).toFixed(3), at.b.ai, +((snd.ac.currentTime - c.t0) - (at.bt - at.b.lead + sndLatency())).toFixed(4)]); }, 50);
  });
  await p.waitForTimeout(secs * 1000);
  const out = await p.evaluate(() => new Promise(res => { clearInterval(__iv); __rec.onstop = async () => { const buf = await new Blob(__chunks).arrayBuffer(); res({ log: __log, t0: __t0, recAt: __recAt, lat: sndLatency(), lag: snd.lag, webm: Array.from(new Uint8Array(buf)) }); }; __rec.stop(); }));
  fs.writeFileSync('rec.webm', Buffer.from(out.webm));
  const errsMs = out.log.map(r => Math.abs(r[2]) * 1000), lines = [...new Set(out.log.map(r => r[1]))];
  const info2 = await p.evaluate(() => ({ starts: BEATS.map(b => [b.ai == null ? -1 : b.ai, +b.start.toFixed(3), b.lead || 0]) }));
  console.log('sync samples', out.log.length, 'lines heard', lines.join(','), 'max |scheduled - wanted| ms', Math.max(...errsMs).toFixed(1), 'mean', (errsMs.reduce((a, c) => a + c, 0) / errsMs.length).toFixed(2));
  fs.writeFileSync('sound_check.json', JSON.stringify({ info, t0: out.t0, recAt: out.recAt, lat: out.lat, lag: out.lag, log: out.log, beats: info2.starts }));
  console.log('errors:', errs); await b.close();
})();
