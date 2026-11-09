"""build.py : assemble the two single-file pages.
   lg-c4/index.html  = src/page.html (the WebGL TV)        + src/news.js with assets.json and src/phon.json inlined
   demo/index.html   = src/demo.html (one presenter, large) + the same news.js"""
import os
news = open('src/news.js').read()
assets = open('assets.json').read() if os.path.exists('assets.json') else '{ "img": {}, "cast": {} }'
news = news.replace('/*ASSETS*/{ img: {}, cast: {} }', assets).replace('/*PHON*/[]', open('src/phon.json').read())
for src, out in (('src/page.html', 'lg-c4/index.html'), ('src/demo.html', 'demo/index.html')):
    html = open(src).read().replace('/*NEWS*/\n', news + '\n')
    os.makedirs(os.path.dirname(out), exist_ok=True); open(out, 'w').write(html); print('built', out, round(len(html) / 1e6, 2), 'MB')
