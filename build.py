"""build.py : assemble the two single-file pages.
   lg-c4/index.html  = src/page.html (the WebGL TV)        + src/news.js with assets.json and src/speech.json inlined
   demo/index.html   = src/demo.html (one presenter, large) + the same news.js
   Both also get src/sound.js, with the decoder-calibration clip from src/calib.txt."""
import os
news = open('src/news.js').read()
assets = open('assets.json').read() if os.path.exists('assets.json') else '{ "img": {}, "cast": {} }'
news = news.replace('/*ASSETS*/{ img: {}, cast: {} }', assets).replace('/*SPEECH*/[]', open('src/speech.json').read())
sound = open('src/sound.js').read().replace("/*CALIB*/''", repr(open('src/calib.txt').read().strip()) if os.path.exists('src/calib.txt') else "''")
for src, out in (('src/page.html', 'lg-c4/index.html'), ('src/demo.html', 'demo/index.html')):
    html = open(src).read().replace('/*NEWS*/\n', news + '\n').replace('/*SOUND*/\n', sound + '\n')
    os.makedirs(os.path.dirname(out), exist_ok=True); open(out, 'w').write(html); print('built', out, round(len(html) / 1e6, 2), 'MB')
