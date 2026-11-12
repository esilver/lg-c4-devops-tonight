"""build.py [face] : the live avatar page -> avatar/index.html (a presenter) or avatar/index.<face>.html (a face file)

avatar/page.html (the conversation, the voice and the clock) gets the bulletin's own engine, src/news.js, with one
face. The engine is used as it is, with two things left out: the bulletin's script is not laid out (there are no
recordings here; lines are made as they are spoken), and the other presenters and the location stills are not bundled.

A face is either one of the bulletin's presenters (its pictures come from assets.json) or a file avatar/faces/<face>.json
made from a photograph by the same pipeline: {"cast": <as in assets.json>, "style": <how much it moves>, "body": {...}}.
A page built from a face file is written beside index.html under its own name and, like the face files themselves, is
kept out of the repository: a real person's face belongs to that person.
FACES says, for each, which voice it usually has and what the page and the avatar say about whose face it is.

The page also needs the folder avatar/voice/ beside it (the avatar's own voice: avatar/get_voice.py fetches it). Without
that folder the page still works, with a borrowed voice and estimated lips.
Run from the repository root:  python3 avatar/build.py [paige|me|...]        (default: paige)"""
import json, os, sys
who = sys.argv[1] if len(sys.argv) > 1 else "paige"; d = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(d)
GENERATED = dict(persona="You are an AI, friendly and quick. Your face is one AI-generated photograph, not a real person; if asked, say so plainly.",
                 note="A proof of concept. The face is an AI-generated still, not a real person, and the one answering is an AI. Nothing you say is kept by this page.")
FACES = dict(
    paige=dict(voice="af_heart", **GENERATED), sunny=dict(voice="af_bella", **GENERATED), cy=dict(voice="am_michael", **GENERATED), dee=dict(voice="am_puck", **GENERATED), mel=dict(voice="am_fenrir", **GENERATED),
    paige2=dict(voice="af_heart", **GENERATED),                 # a face file made from a second AI-generated picture of Paige (gen/prep_photo.py and friends)
    dog=dict(voice="am_puck",                                   # a face file made from AI-generated pictures of a dog (gen/dog_export.py); the voice is a stand-in until it has one of its own
             persona="You are an AI, friendly and quick. Your face is an AI-generated picture of a dog, brought to life. You are not a dog and not a person, and the voice is a stock one; if asked, say so plainly.",
             note="A proof of concept. The face is an AI-generated picture of a dog, and the one answering is an AI. Nothing you say is kept by this page."),
    me=dict(voice="am_michael",
            persona="You are an AI, friendly and quick. Your face is animated from one photograph of the person who built this page and your voice may be a synthetic copy of theirs, both used with their permission. You are not that person, you do not speak for them and you know nothing about them; if asked, say so plainly.",
            note="A proof of concept. The face is animated from one photograph of this page's owner, and the voice, where the page says it is copied, from a short recording of them. The one answering is an AI, not them. Nothing you say is kept by this page."),
)
face = f"{d}/faces/{who}.json"; extra = ""
if os.path.exists(face):
    F = json.load(open(face)); cast = F["cast"]
    extra = f"STYLE[{json.dumps(who)}] = {json.dumps(F.get('style', 1))}; BODY[{json.dumps(who)}] = {json.dumps(F.get('body', dict(sway=0.75, hz=4, damp=0.5, hair=0)))};\n"
    # a voice copied from that person's recording (gen/pocket.py voice), if there is one: built in, like the face
    pv = f"{d}/faces/{who}.pvoice"
    if os.path.exists(pv): FACES[who] = dict(FACES[who], pvoice=__import__("base64").b64encode(open(pv, "rb").read()).decode())
else: cast = json.load(open(f"{root}/assets.json"))["cast"][who]
news = open(f"{root}/src/news.js", encoding="utf-8").read()
for old, new in (("/*ASSETS*/{ img: {}, cast: {} }", json.dumps({"img": {}, "cast": {who: cast}})), ("buildShow(SPEECH);\n", "")):
    assert news.count(old) == 1, old; news = news.replace(old, new)
html = open(f"{d}/page.html", encoding="utf-8").read()
for old, new in (("/*NEWS*/\n", news + "\n" + extra), ("/*FACE*/{ voice: 'af_heart', persona: '', note: '' }", json.dumps(FACES[who]))):
    assert html.count(old) == 1, old; html = html.replace(old, new)
out = f"index.{who}.html" if os.path.exists(face) else "index.html"
open(f"{d}/{out}", "w", encoding="utf-8").write(html); print(f"built avatar/{out} with {who}: {os.path.getsize(f'{d}/{out}') / 1e6:.2f} MB")
