"""build.py : assemble the two single-file pages.
   lg-c4/index.html  = src/page.html (the WebGL TV)        + src/news.js with assets.json and src/speech.json inlined
   demo/index.html   = src/demo.html (one presenter, large) + the same news.js, plus the first voices (src/speech_first.json) for its switch
   Both also get src/sound.js, with the decoder-calibration clip from src/calib.txt.
   python3 build.py          the current voices (src/speech.json)
   python3 build.py first    the first voices (src/speech_first.json), same picture engine, for comparison"""
import os, sys
SPEECH = 'src/speech_first.json' if 'first' in sys.argv[1:] else 'src/speech.json'      # "python3 build.py first": the first voices instead of the second
news = open('src/news.js').read()
assets = open('assets.json').read() if os.path.exists('assets.json') else '{ "img": {}, "cast": {} }'
news = news.replace('/*ASSETS*/{ img: {}, cast: {} }', assets).replace('/*SPEECH*/[]', open(SPEECH).read())
sound = open('src/sound.js').read().replace("/*CALIB*/''", repr(open('src/calib.txt').read().strip()) if os.path.exists('src/calib.txt') else "''")
for src, out in (('src/page.html', 'lg-c4/index.html'), ('src/demo.html', 'demo/index.html')):
    html = open(src).read().replace('/*NEWS*/\n', news + '\n').replace('/*SOUND*/\n', sound + '\n')
    if os.path.exists('src/speech_first.json') and SPEECH != 'src/speech_first.json':        # the demo page carries both sets of voices, with a switch
        html = html.replace('/*SPEECH_FIRST*/null', open('src/speech_first.json').read())
    os.makedirs(os.path.dirname(out), exist_ok=True); open(out, 'w').write(html); print('built', out, round(len(html) / 1e6, 2), 'MB')
