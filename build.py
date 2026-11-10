"""build.py : assemble the two single-file pages.
   lg-c4/index.html  = src/page.html (the WebGL TV)        + src/news.js with assets.json and src/speech.json inlined
   demo/index.html   = src/demo.html (one presenter, large) + the same news.js, plus the two earlier sets of voices for its switch
   Both also get src/sound.js, with the decoder-calibration clip from src/calib.txt.
   python3 build.py          the current voices (src/speech.json)
   python3 build.py first    the first voices (src/speech_first.json), same picture engine, for comparison
   python3 build.py second   the second voices (src/speech_second.json)"""
import os, sys
# "python3 build.py first" or "second": an earlier set of voices instead of the current one
SPEECH = 'src/speech_first.json' if 'first' in sys.argv[1:] else 'src/speech_second.json' if 'second' in sys.argv[1:] else 'src/speech.json'
news = open('src/news.js').read()
assets = open('assets.json').read() if os.path.exists('assets.json') else '{ "img": {}, "cast": {} }'
news = news.replace('/*ASSETS*/{ img: {}, cast: {} }', assets).replace('/*SPEECH*/[]', open(SPEECH).read())
sound = open('src/sound.js').read().replace("/*CALIB*/''", repr(open('src/calib.txt').read().strip()) if os.path.exists('src/calib.txt') else "''")
for src, out in (('src/page.html', 'lg-c4/index.html'), ('src/demo.html', 'demo/index.html')):
    html = open(src).read().replace('/*NEWS*/\n', news + '\n').replace('/*SOUND*/\n', sound + '\n')
    if SPEECH == 'src/speech.json':                                  # the demo page carries all three sets of voices, with a switch
        for tag, f in (('/*SPEECH_FIRST*/null', 'src/speech_first.json'), ('/*SPEECH_SECOND*/null', 'src/speech_second.json')):
            if os.path.exists(f): html = html.replace(tag, open(f).read())
    os.makedirs(os.path.dirname(out), exist_ok=True); open(out, 'w').write(html); print('built', out, round(len(html) / 1e6, 2), 'MB')
