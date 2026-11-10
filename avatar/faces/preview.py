"""preview.py [face] [--news path] [--page path] : the live avatar page with a face from avatar/faces/<face>.json.

What avatar/build.py does (the engine, src/news.js, inlined into the page with one presenter's pictures), with two
differences: the pictures come from avatar/faces/<face>.json instead of assets.json, and the page is the copy taken
when the face was made (avatar/faces/page_snapshot.html), because avatar/page.html was being rewritten at the time.

<face>.json holds {"cast": the presenter's entry, as in assets.json["cast"][name], "style": how much this presenter
moves (STYLE in src/news.js), "body": {"sway", "hz", "damp", "hair"} (BODY in src/news.js)}. The engine has no entry
for a new name in those two tables and would fall back to 1 and to the co-anchor's body; here the face's own values
are written into this copy of the engine, by adding one entry to each table. Nothing in src/ is changed.

Run from the repository root:  python3 avatar/faces/preview.py me        -> avatar/faces/preview_me.html"""
import json, os, sys
a = sys.argv[1:]; opt = {}
for k in ("--news", "--page"):
    if k in a: i = a.index(k); opt[k] = a[i + 1]; del a[i:i + 2]
who = a[0] if a else "me"; d = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(os.path.dirname(d))
F = json.load(open(f"{d}/{who}.json")); assets = json.dumps({"img": {}, "cast": {who: F["cast"]}})
news = open(opt.get("--news", f"{root}/src/news.js"), encoding="utf-8").read()
body = "{ " + ", ".join(f"{k}: {json.dumps(v)}" for k, v in F["body"].items()) + " }"
for old, new in (("/*ASSETS*/{ img: {}, cast: {} }", assets), ("buildShow(SPEECH);\n", ""),
                 ("const STYLE = { ", f"const STYLE = {{ {who}: {json.dumps(F['style'])}, "), ("const BODY = {\n", f"const BODY = {{\n  {who}: {body},\n")):
    assert news.count(old) == 1, old; news = news.replace(old, new)
html = open(opt.get("--page", f"{d}/page_snapshot.html"), encoding="utf-8").read(); assert html.count("/*NEWS*/\n") == 1
out = f"{d}/preview_{who}.html"; open(out, "w", encoding="utf-8").write(html.replace("/*NEWS*/\n", news + "\n"))
print(f"built {os.path.relpath(out, root)} with {who}: {os.path.getsize(out) / 1e6:.2f} MB; style {F['style']}, body {body}")
