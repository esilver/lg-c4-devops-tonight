"""build.py [presenter] : the live avatar page -> avatar/index.html, one self-contained file.

avatar/page.html (the conversation, the voice and the clock) gets the bulletin's own engine, src/news.js, with one
presenter's pictures from assets.json. The engine is used as it is, with two things left out: the bulletin's script is
not laid out (there are no recordings here; lines are made as they are spoken), and the other presenters and the
location stills are not bundled.     Run from the repository root:  python3 avatar/build.py        (default: paige)"""
import json, os, sys
who = sys.argv[1] if len(sys.argv) > 1 else "paige"; d = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(d)
A = json.load(open(f"{root}/assets.json")); assets = json.dumps({"img": {}, "cast": {who: A["cast"][who]}})
news = open(f"{root}/src/news.js", encoding="utf-8").read()
for old, new in (("/*ASSETS*/{ img: {}, cast: {} }", assets), ("buildShow(SPEECH);\n", "")):
    assert news.count(old) == 1, old; news = news.replace(old, new)
html = open(f"{d}/page.html", encoding="utf-8").read(); assert html.count("/*NEWS*/\n") == 1
open(f"{d}/index.html", "w", encoding="utf-8").write(html.replace("/*NEWS*/\n", news + "\n")); print(f"built avatar/index.html with {who}: {os.path.getsize(f'{d}/index.html') / 1e6:.2f} MB")
