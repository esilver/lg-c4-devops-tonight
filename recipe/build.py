"""build.py : recipe/SKILL.md -> recipe/index.html, one self-contained page.

The recipe is written once, as Markdown, in SKILL.md. This script puts that file on the page twice: verbatim in a code
block with a Copy button (it can be pasted into a skill folder as it is), and rendered for reading, section by section,
with pictures from recipe/img/ added where figures.json says. Because both come from the same file, the block and the
page cannot say different things. The only page-only words are the picture captions, the six number tiles (each
checked below against a sentence of SKILL.md) and a few labels.

Standard library only, plus Pillow to read picture sizes. Run from the repository root:  python3 recipe/build.py"""
import re, html, json, base64, os, sys
from PIL import Image

D = os.path.dirname(os.path.abspath(__file__))
SRC = open(f"{D}/SKILL.md", encoding="utf-8").read()
CFG = json.load(open(f"{D}/figures.json", encoding="utf-8"))
esc = lambda s: html.escape(s, quote=False)

# ── front matter ─────────────────────────────────────────────────────────────────────────────────────────────────
m = re.match(r"---\n(.*?)\n---\n", SRC, re.S); assert m, "SKILL.md must start with YAML front matter"
FM = dict(ln.split(": ", 1) for ln in m.group(1).split("\n")); BODY = SRC[m.end():]
assert set(FM) == {"name", "description"} and re.fullmatch(r"[a-z0-9-]{1,64}", FM["name"]) and 0 < len(FM["description"]) <= 1024
assert ": " not in FM["description"] and " #" not in FM["description"], "the description is a plain YAML scalar: no ': ' or ' #' in it"

# ── Markdown, the small subset SKILL.md uses ─────────────────────────────────────────────────────────────────────
INLINE = re.compile(r"(`[^`]+`)|\[((?:[^\]`]|`[^`]*`)+)\]\(([^)\s]+)\)|\*\*(.+?)\*\*")
def inline(s):
    out, i = [], 0
    for q in INLINE.finditer(s):
        out.append(esc(s[i:q.start()])); i = q.end()
        if q.group(1): out.append("<code>" + esc(q.group(1)[1:-1]) + "</code>")
        elif q.group(2): out.append(f'<a href="{html.escape(q.group(3))}">{inline(q.group(2))}</a>')
        else: out.append("<b>" + inline(q.group(4)) + "</b>")
    out.append(esc(s[i:])); r = "".join(out)
    assert "**" not in r and "](" not in r, "inline Markdown this script does not know: " + s[:90]
    return r
LIST = re.compile(r"( *)(-|\d+\.) +(.*)")
def starts_block(ln): return bool(re.match(r"#{1,4} |```|\||(-|\d+\.) ", ln))
def blocks(lines):
    """-> a list of ('h', level, text) | ('p', text) | ('code', text) | ('table', head, rows) | ('list', ordered, start, items)"""
    out, i = [], 0
    while i < len(lines):
        ln = lines[i]
        if not ln.strip(): i += 1; continue
        if ln.startswith("```"):
            j = i + 1
            while not lines[j].startswith("```"): j += 1
            out.append(("code", "\n".join(lines[i + 1:j]))); i = j + 1; continue
        h = re.match(r"(#{1,4}) (.*)", ln)
        if h: out.append(("h", len(h.group(1)), h.group(2).strip())); i += 1; continue
        if ln.startswith("|"):
            assert re.match(r"\|(\s*:?-{3,}:?\s*\|)+\s*$", lines[i + 1]), "a table needs a separator row: " + ln[:60]
            cells = lambda r: [c.strip() for c in r.strip().strip("|").split("|")]
            j = i + 2
            while j < len(lines) and lines[j].startswith("|"): j += 1
            head, rows = cells(ln), [cells(r) for r in lines[i + 2:j]]
            assert all(len(r) == len(head) for r in rows), "ragged table under: " + ln[:60]
            out.append(("table", head, rows)); i = j; continue
        if LIST.match(ln) and not ln.startswith(" "):
            j = i
            while j < len(lines) and lines[j].strip(): j += 1          # a list ends at the first blank line
            base, items = LIST.match(ln), []
            for l2 in lines[i:j]:
                q = LIST.match(l2)
                if q and len(q.group(1)) == 0: items.append([q.group(2), [q.group(3)]])
                else: items[-1][1].append(l2)
            ordered = base.group(2) != "-"; start = int(base.group(2)[:-1]) if ordered else 1
            for k, (mark, _) in enumerate(items):
                assert (mark != "-") == ordered and (not ordered or int(mark[:-1]) == start + k), "list numbering broken at: " + ln[:60]
            body = []
            for _, ls in items:
                rest = ls[1:]; ind = min((len(x) - len(x.lstrip()) for x in rest if x.strip()), default=0)
                body.append(blocks([ls[0]] + [x[ind:] for x in rest]))
            out.append(("list", ordered, start, body)); i = j; continue
        j = i
        while j < len(lines) and lines[j].strip() and (j == i or not starts_block(lines[j])): j += 1
        out.append(("p", " ".join(x.strip() for x in lines[i:j]))); i = j
    return out
def table(head, rows):
    n = len(head); cls = "c2" if n <= 2 else f"c{min(n, 5)}"
    th = "".join(f"<th>{inline(c)}</th>" for c in head)
    tr = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rows)
    return f'<div class="tablewrap" tabindex="0" role="region" aria-label="Table: {html.escape(re.sub(r"[`*]", "", head[0]))}"><table class="{cls}"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>'
def render(bl, top=True):
    out = []
    for b in bl:
        if b[0] == "p":
            w = re.match(r"\*\*With:\*\* (.*)", b[1])
            if w and top: out.append('<div class="with">With ' + " ".join(f"<i>{inline(x.strip())}</i>" for x in w.group(1).split(";")) + "</div>")
            else: out.append(f"<p>{inline(b[1])}</p>" if top else inline(b[1]))
        elif b[0] == "code": out.append(f"<pre><code>{esc(b[1])}</code></pre>")
        elif b[0] == "table": out.append(table(b[1], b[2]))
        elif b[0] == "list":
            tag = "ol" if b[1] else "ul"; st = f' start="{b[2]}"' if b[1] and b[2] != 1 else ""
            out.append(f"<{tag}{st}>" + "".join("<li>" + render(it, False) + "</li>" for it in b[3]) + f"</{tag}>")
        else: raise AssertionError(("a heading inside a list or below level 3", b))
    return "".join(out)

# ── pictures ─────────────────────────────────────────────────────────────────────────────────────────────────────
used = set()
def img(it):
    f = it["file"]; used.add(f); w, h = Image.open(f"{D}/img/{f}").size
    mime = "image/png" if f.endswith(".png") else "image/jpeg"; data = base64.b64encode(open(f"{D}/img/{f}", "rb").read()).decode()
    return f'<img src="data:{mime};base64,{data}" width="{w}" height="{h}" alt="{html.escape(it["alt"])}" loading="lazy">'
def figure(fg):
    cap = f'<figcaption>{esc(fg["caption"])}</figcaption>' if fg.get("caption") else ""
    if len(fg["items"]) == 1: return f'<figure>{img(fg["items"][0])}{cap}</figure>'
    tiles = "".join(f'<figure>{img(it)}<figcaption>{esc(it["label"])}</figcaption></figure>' for it in fg["items"])
    return f'<figure><div class="{fg["class"]}">{tiles}</div>{cap}</figure>'

# ── the page ─────────────────────────────────────────────────────────────────────────────────────────────────────
slug = lambda s: re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
B = blocks(BODY.split("\n"))
assert B[0][0] == "h" and B[0][1] == 1 and B[1][0] == "p" and B[2][0] == "p" and B[2][1].startswith("**This is a recipe, not the working code.**")
h1a, h1b = B[0][2].split(", ", 1); lead, notice = B[1][1], B[2][1]
sections, cur = [], None
for b in B[3:]:
    if b[0] == "h" and b[1] == 2:
        st = re.match(r"Step (\d+)\. (.*)", b[2])
        cur = dict(id=f"step-{st.group(1)}" if st else slug(b[2]), no=f"{int(st.group(1)):02d}" if st else CFG["tags"][b[2]], title=st.group(2) if st else b[2], parts=[["top", []]])
        sections.append(cur)
    elif b[0] == "h":
        assert b[1] == 3, b; cur["parts"].append([b[2], []])
    else: cur["parts"][-1][1].append(b)
figs = {}
for fg in CFG["figures"]: figs.setdefault((fg["section"], fg["after"]), []).append(fg)
body = []
for s in sections:
    o = [f'<section id="{s["id"]}"><div class="strap"><span class="no">{esc(s["no"])}</span><h2>{inline(s["title"])}</h2></div>']
    for name, bl in s["parts"]:
        if name == "top":                                           # the "With" line stays under the strap; a picture for the top comes before the words
            w = [x for x in bl if x[0] == "p" and x[1].startswith("**With:**")]; rest = [x for x in bl if x not in w]
            o.append(render(w) + "".join(figure(f) for f in figs.pop((s["id"], "top"), [])) + ('<div class="prose">' + render(rest) + "</div>" if rest else ""))
        else:
            o.append(f'<div class="prose"><h3>{inline(name)}</h3>{render(bl)}</div>' + "".join(figure(f) for f in figs.pop((s["id"], name), [])))
    body.append("".join(o) + "</section>")
assert not figs, ("pictures with nowhere to go", list(figs))
steps = [s for s in sections if s["id"].startswith("step-")]
toc = "".join(f'<li><a href="#{s["id"]}"><span>{esc(s["no"])}</span>{inline(s["title"])}</a></li>' for s in sections)

# the number tiles are the only figures not taken from SKILL.md by the renderer, so each names the sentence it rests on
for f in CFG["facts"]: assert f["source"] in SRC, ("a number tile with no sentence behind it", f)
assert len(steps) == 8 and [s["no"] for s in steps] == [f"{i:02d}" for i in range(1, 9)]
models = next(b for b in B if b[0] == "table" and b[1][0] == "Model" and len(b[1]) == 5); assert len(models[2]) == 12
for s in steps: assert [p[0] for p in s["parts"]] == ["top", "In", "Do", "Out", "Check", "Settings that worked"], s["id"]
facts = "".join(f'<li><b>{esc(f["n"])}</b><span>{esc(f["label"])}</span></li>' for f in CFG["facts"])
kb = len(SRC.encode()) / 1024; footer = "".join("<span>" + esc(x) + "</span>" for x in CFG["footer"]); sections_html = "".join(body)

CSS = """
  /* The bulletin's own broadcast graphics, as on the first one-pager: its navy, its mint, a channel band across the top
     and a name strap for each step. This page is the longer companion: the same recipe twice, once to copy, once to read. */
  :root {
    color-scheme: dark;
    --bg: #070d1b; --panel: #0e1730; --line: #25345a; --ink: #eef2fb; --muted: #a3b2d0;
    --accent: #2ee6a6; --live: #e23b2e; --code: #121d3b;
    --display: "Barlow Condensed", "Arial Narrow", "Roboto Condensed", sans-serif;
    --body: "IBM Plex Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
    --mono: "IBM Plex Mono", ui-monospace, Menlo, Consolas, monospace;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; background: var(--bg); color: var(--ink); font: 17px/1.55 var(--body); }
  html { scroll-behavior: smooth; }
  img { display: block; max-width: 100%; height: auto; }
  a { color: var(--accent); text-underline-offset: 2px; }
  a:focus-visible, button:focus-visible, [tabindex]:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; }
  main { max-width: 1152px; margin: 0 auto; padding: 0 16px 56px; display: grid; gap: 44px; grid-template-columns: minmax(0, 1fr); }

  .band { background: var(--panel); border-bottom: 2px solid var(--accent); }
  .band div { max-width: 1152px; margin: 0 auto; padding: 10px 16px; display: flex; flex-wrap: wrap; gap: 8px 18px; align-items: center; font: 500 13px var(--mono); letter-spacing: .06em; text-transform: uppercase; color: var(--muted); }
  .bug { display: inline-flex; align-items: center; gap: 9px; color: var(--ink); font: 700 19px var(--display); letter-spacing: .05em; }
  .bug svg { width: 26px; height: 26px; }
  .tally { display: inline-flex; align-items: center; gap: 7px; color: var(--ink); }
  .tally::before { content: ""; width: 9px; height: 9px; border-radius: 50%; background: var(--live); }

  header { display: grid; gap: 18px; padding-top: 34px; }
  h1 { margin: 0; font: 700 clamp(44px, 7.4vw, 86px)/0.95 var(--display); letter-spacing: .005em; text-transform: uppercase; text-wrap: balance; }
  h1 em { font-style: normal; color: var(--accent); }
  .deck { margin: 0; max-width: 70ch; font-size: 19px; }
  .notice { margin: 0; max-width: 78ch; padding: 14px 16px; background: var(--panel); border: 1px solid var(--line); border-left: 6px solid var(--live); font-size: 18px; }
  .facts { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1px; background: var(--line); border: 1px solid var(--line); }
  .facts li { background: var(--panel); padding: 13px 14px 12px; display: grid; gap: 2px; }
  .facts b { font: 700 38px/1 var(--display); color: var(--ink); font-variant-numeric: tabular-nums; }
  .facts span { font-size: 13.5px; line-height: 1.35; color: var(--muted); }

  figure { margin: 0; display: grid; gap: 8px; }
  figure img { border: 1px solid var(--line); }
  figcaption { font-size: 14px; line-height: 1.45; color: var(--muted); max-width: 86ch; }
  .tiles { display: grid; gap: 8px; }
  .tiles.two { grid-template-columns: repeat(2, minmax(0, 1fr)); max-width: 860px; }
  .tiles.four { grid-template-columns: repeat(4, minmax(0, 1fr)); }
  .tiles figcaption { font: 500 12.5px var(--mono); color: var(--ink); }

  section { display: grid; gap: 18px; grid-template-columns: minmax(0, 1fr); scroll-margin-top: 12px; }
  .strap { display: flex; align-items: stretch; background: var(--panel); border-left: 6px solid var(--accent); }
  .strap .no { display: grid; place-items: center; min-width: 52px; padding: 0 14px; font: 500 15px var(--mono); color: var(--accent); border-right: 1px solid var(--line); }
  .strap h2 { margin: 0; padding: 9px 16px 8px; font: 700 31px/1.05 var(--display); letter-spacing: .02em; text-transform: uppercase; text-wrap: balance; }
  .with { display: flex; flex-wrap: wrap; gap: 6px 8px; align-items: baseline; font: 500 12.5px var(--mono); color: var(--muted); }
  .with i { font-style: normal; color: var(--ink); border: 1px solid var(--line); background: var(--panel); border-radius: 4px; padding: 2px 8px; }

  /* the recipe as prose: denser than the first page, still one column */
  .prose { display: grid; gap: 12px; grid-template-columns: minmax(0, 1fr); }
  .prose > p, .prose > ul, .prose > ol { margin: 0; max-width: 84ch; }
  .prose ul, .prose ol { padding-left: 1.5em; display: grid; gap: 7px; }
  .prose li > ul, .prose li > ol { margin: 7px 0 0; }
  .prose li::marker { color: var(--muted); font-family: var(--mono); font-size: .88em; }
  .prose b { font-weight: 600; }
  h3 { margin: 0; padding-top: 14px; border-top: 1px solid var(--line); font: 500 13px var(--mono); letter-spacing: .08em; text-transform: uppercase; color: var(--accent); }
  code { font: .88em var(--mono); background: var(--code); border: 1px solid var(--line); border-radius: 3px; padding: 0 4px; overflow-wrap: anywhere; }
  a code { color: inherit; }
  pre { margin: 0; padding: 14px 16px; background: var(--code); border: 1px solid var(--line); overflow: auto; font: 13.5px/1.5 var(--mono); tab-size: 2; }
  pre code { font: inherit; background: none; border: 0; padding: 0; overflow-wrap: normal; white-space: pre; }

  .tablewrap { overflow-x: auto; border: 1px solid var(--line); }
  table { border-collapse: collapse; width: 100%; font-size: 14.5px; line-height: 1.45; }
  table.c3 { min-width: 580px; } table.c4 { min-width: 780px; } table.c5 { min-width: 1060px; }
  table.c5 th:nth-child(2) { width: 32%; } table.c5 th:nth-child(1) { width: 14%; }
  th, td { text-align: left; vertical-align: top; padding: 8px 12px; border-bottom: 1px solid var(--line); }
  tbody tr:last-child td { border-bottom: 0; }
  th { font: 500 12px var(--mono); letter-spacing: .06em; text-transform: uppercase; color: var(--muted); background: var(--panel); white-space: nowrap; }
  td:first-child { font-weight: 600; }
  td code { overflow-wrap: anywhere; }

  /* the block to copy */
  .skillbar { display: flex; flex-wrap: wrap; gap: 10px 16px; align-items: center; padding: 10px 12px; background: var(--panel); border: 1px solid var(--line); border-bottom: 0; font: 500 12.5px var(--mono); color: var(--muted); }
  .skillbar b { color: var(--ink); font-weight: 500; }
  .skillbar button { font: 500 14px var(--mono); letter-spacing: .04em; color: #06281d; background: var(--accent); border: 0; border-radius: 4px; padding: 7px 18px; cursor: pointer; }
  .skillbar button:hover { background: #5cf0bd; }
  .skillbar [role=status] { flex: 1 1 8ch; text-align: right; color: var(--ink); }
  #skillmd { max-height: 30rem; font-size: 12.5px; }
  .skill { gap: 0; }
  .skill > .strap, .skill > .prose { margin-bottom: 18px; }

  .toc { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); background: var(--panel); border: 1px solid var(--line); border-width: 1px 0 0 1px; }
  .toc li { border: 1px solid var(--line); border-width: 0 1px 1px 0; }
  .toc a { display: flex; gap: 10px; align-items: baseline; height: 100%; padding: 8px 12px; color: var(--ink); text-decoration: none; font-size: 15px; }
  .toc a:hover { background: #142044; }
  .toc span { min-width: 2.2em; font: 500 12.5px var(--mono); color: var(--accent); }

  footer { border-top: 2px solid var(--accent); padding-top: 14px; font: 500 13px var(--mono); color: var(--muted); display: flex; flex-wrap: wrap; gap: 6px 22px; }
  @media (max-width: 760px) {
    html, body { font-size: 16px; }
    main { gap: 36px; }
    .tiles.four { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .strap h2 { font-size: 25px; }
    .strap .no { min-width: 44px; padding: 0 10px; }
    .deck { font-size: 17.5px; } .notice { font-size: 16.5px; }
    table { font-size: 14px; } th, td { padding: 7px 10px; }
  }
  @media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } }
"""
JS = """
  // Copy the SKILL.md block. The clipboard call is made inside the click itself. If the browser refuses (no permission,
  // an embedded frame, an old browser), the text is selected instead, so it can be copied by hand.
  (function () {
    var btn = document.getElementById('copy'), pre = document.getElementById('skillmd'), note = document.getElementById('copied');
    function selectAll() { var r = document.createRange(); r.selectNodeContents(pre); var s = window.getSelection(); s.removeAllRanges(); s.addRange(r); pre.focus(); }
    function refused() { selectAll(); note.textContent = 'Copying was refused. The whole file is selected: press Ctrl+C or Cmd+C.'; }
    btn.addEventListener('click', function () {
      var text = pre.textContent;
      try {
        if (!navigator.clipboard || !navigator.clipboard.writeText) { refused(); return; }
        navigator.clipboard.writeText(text).then(function () { note.textContent = 'Copied: ' + text.length + ' characters.'; }, refused);
      } catch (e) { refused(); }
    });
  })();
"""
PAGE = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(CFG["title"])}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<div class="band"><div>
  <span class="bug"><svg viewBox="0 0 26 26" aria-hidden="true"><rect width="26" height="26" rx="4" fill="#2ee6a6"/><path d="M13 13c-2.2-3.4-6.6-3.4-6.6 0s4.4 3.4 6.6 0c2.2-3.4 6.6-3.4 6.6 0s-4.4 3.4-6.6 0z" fill="none" stroke="#06281d" stroke-width="2.2" stroke-linecap="round"/></svg>DevOps Tonight</span>
  <span>{esc(CFG["band"][0])}</span>
  <span class="tally">{esc(CFG["band"][1])}</span>
</div></div>
<main>
  <header>
    <h1>{esc(h1a)}, <em>{esc(h1b)}</em></h1>
    <p class="deck">{inline(lead)}</p>
    <p class="notice">{inline(notice)}</p>
    <ul class="facts">{facts}</ul>
  </header>

  <section class="skill" id="skill-md">
    <div class="strap"><span class="no">copy</span><h2>The whole recipe as one SKILL.md</h2></div>
    <div class="prose"><p>Save this block as <code>SKILL.md</code> in a skill folder named <code>{esc(FM["name"])}</code>. It is complete on its own: front matter, then the instructions. The rest of this page is the same file, rendered for reading, with pictures from the bulletin added beside the checks.</p></div>
    <div class="skillbar"><b>{esc(FM["name"])}/SKILL.md</b><span>{SRC.count(chr(10))} lines, {kb:.0f} KB</span><span id="copied" role="status" aria-live="polite"></span><button type="button" id="copy">Copy</button></div>
    <pre id="skillmd" tabindex="0" aria-label="The SKILL.md file"><code>{esc(SRC)}</code></pre>
  </section>

  <nav aria-label="Sections"><ul class="toc">{toc}</ul></nav>

  {sections_html}

  <footer>{footer}</footer>
</main>
<script>{JS}</script>
</body>
</html>
"""
# ── what a publishable page may not contain, checked on every build ──────────────────────────────────────────────
low = PAGE.lower()
# (the words are written in two halves so that this file does not contain them either)
BANNED = ["git" "hub", "esil" "ver", "lg" "-c4", "ava" "tar", "requ" "est ", "my " "photo", "prep" "_photo", "gm" "ail", "cla" "ude", "anth" "ropic"]
for w in BANNED: assert w not in low and w not in SRC.lower(), ("word that must not appear, in any letter case, pictures' data included", w)
assert PAGE.startswith("<!DOCTYPE html>") and "<title>" in PAGE and "<iframe" not in low and "fetch(" not in low and "xmlhttprequest" not in low
outside = set(re.findall(r'(?:src|href)="(https?://[^"/]+)', PAGE)); loads = set(re.findall(r'<(?:link|script|img|source|video|audio)[^>]*?(?:src|href)="(https?://[^"/]+)', PAGE))
assert loads == {"https://fonts.googleapis.com"}, loads                      # the only thing that loads from outside is the font stylesheet
assert outside <= {"https://fonts.googleapis.com", "https://huggingface.co", "https://pypi.org"}, outside   # every other outside address is a plain link to a model's own page
assert html.unescape(re.search(r'<pre id="skillmd"[^>]*><code>(.*?)</code></pre>', PAGE, re.S).group(1)) == SRC  # the block to copy is the file, byte for byte
assert used == set(os.listdir(f"{D}/img")), ("pictures in img/ that the page does not use", set(os.listdir(f"{D}/img")) - used)
open(f"{D}/index.html", "w", encoding="utf-8").write(PAGE)
size = len(PAGE.encode()); assert size < 4 * 1024 * 1024
print(f"built recipe/index.html: {size / 1e6:.2f} MB, {len(sections)} sections, {len(used)} pictures, SKILL.md {SRC.count(chr(10))} lines / {kb:.0f} KB, description {len(FM['description'])} characters")
