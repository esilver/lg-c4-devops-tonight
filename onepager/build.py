"""build.py : onepager/page.html with its pictures inlined -> onepager/index.html, one self-contained file.
page.html itself opens from disk as it is (it loads img/ by relative path). Run from the repository root:  python3 onepager/build.py"""
import re, base64, os
d = os.path.dirname(os.path.abspath(__file__)); s = open(f"{d}/page.html", encoding="utf-8").read()
def inline(m):
    f = m.group(1); mime = "image/png" if f.endswith(".png") else "image/jpeg"
    return f'src="data:{mime};base64,{base64.b64encode(open(f"{d}/img/{f}", "rb").read()).decode()}"'
out, n = re.subn(r'src="img/([^"]+)"', inline, s); open(f"{d}/index.html", "w", encoding="utf-8").write(out)
print(f"built onepager/index.html: {n} pictures inlined, {len(out) / 1e6:.2f} MB")
