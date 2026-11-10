"""voice_check.py [dir] : does the avatar's own voice say the words, and are the times it reports right?

Reads what avatar/voice_test.js and avatar/test.js saved (tests/output/voice/ by default) and checks it three ways, none
of which uses the voice model's own word for anything:

  words   a speech recogniser (Whisper base, English) transcribes each line; the transcript is compared with the text
  times   a forced aligner (gen/align.py: a phoneme recogniser plus a Viterbi search) finds where each sound is in the
          audio; that is compared with the start the voice worker reported for the same sound
  lips    for the page run: wherever the aligner hears a p, b or m in the audio the page played, is the mouth the
          engine draws shut at that moment? Lips meeting on time is the part of lip sync an eye catches first.

Run from the repository root:  gen/venv4/bin/python tests/voice_check.py"""
import sys, os, json, glob, re, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "gen"))
from align import read16k, align, hear, wer, CLS
D = sys.argv[1] if len(sys.argv) > 1 else "tests/output/voice"
norm = lambda s: re.sub(r"[^a-z0-9' ]", "", s.lower().replace("-", " ")).replace("forty two", "42").replace("percent", "%").split()
def offsets(seg, a16):
    """aligner start minus reported start, for sounds that are not beside a pause (the model folds pauses into those)"""
    idx = [i for i, s in enumerate(seg) if s[0] in CLS and s[2] > 0]; spans, score, _ = align(a16, [seg[i][0] for i in idx]); out = []
    for k, i in enumerate(idx):
        s = seg[i]; nxt = seg[i + 1][0] if i + 1 < len(seg) else "."; prv = seg[i - 1][0] if i else "."
        if nxt in ",.:;?!—…" or prv in ",.:;?!—…" or s[2] > 0.2 or k == 0: continue
        out.append(spans[k][0] - s[1])
    return out
errs, words, tot, rtf = [], 0, 0, []
for f in sorted(glob.glob(f"{D}/line_*.json")):
    L = json.load(open(f)); a, sr, a16 = read16k(f[:-5] + ".wav"); heard = hear(a16); w = wer(norm(L["text"]), norm(heard)); words += w; tot += len(norm(L["text"]))
    e = offsets(L["sp"]["seg"], a16); errs += e; rtf.append(L["took"] / L["secs"])
    print(f"{os.path.basename(f)[:-5]} {L['voice']:10s} words wrong {w} of {len(norm(L['text']))} | heard: {heard}")
if errs:
    e = np.array(errs) * 1000; m = np.median(e)
    print(f"\nwords: {words} wrong of {tot} over {len(rtf)} lines")
    print(f"times: {len(e)} sounds. The aligner hears each one {m:+.0f} ms from where the worker says (median); around that, half are within {np.median(np.abs(e - m)):.0f} ms and 90% within {np.percentile(np.abs(e - m), 90):.0f} ms")
P = f"{D}/own_voice.json"
if os.path.exists(P):
    R = json.load(open(P)); print(f"\npage run: first sound {R['firstSound']:.1f} s after Send; the start was held back {R['held']:.1f} s for later lines; this machine made a line in {R['rtf']:.2f} x its length")
    pe, off, n = [], [], 0
    for i, L in enumerate(R["lines"]):
        if not L.get("sp") or not L.get("curve"): continue
        a, sr, a16 = read16k(f"{D}/page_line_{i}.wav"); seg = L["sp"]["seg"]; pe += offsets(seg, a16)
        # lips: where the aligner hears a p, b or m, is the drawn mouth shut? (the engine draws a shut mouth as a jaw below zero)
        o = np.array([c[0] for c in L["curve"]]); shut = o < -0.05; runs = []; k = 0
        while k < len(o):
            if shut[k]:
                j = k
                while j + 1 < len(o) and shut[j + 1]: j += 1
                runs.append((k + j) / 2 * 0.01); k = j + 1
            else: k += 1
        idx = [q for q, s in enumerate(seg) if s[0] in CLS and s[2] > 0]; spans, _, _ = align(a16, [seg[q][0] for q in idx])
        for k, q in enumerate(idx):
            if seg[q][0] in "pbm":
                n += 1; mid = (spans[k][0] + spans[k][1]) / 2; near = min(runs, key=lambda r: abs(r - mid)) if runs else None
                if near is not None and abs(near - mid) < 0.15: off.append(near - mid)
    if pe: e = np.array(pe) * 1000; print(f"  times in the page's own lines: aligner {np.median(e):+.0f} ms from the worker (median), 90% within {np.percentile(np.abs(e - np.median(e)), 90):.0f} ms of that")
    if n:
        e = np.array(off) * 1000
        print(f"  lips: the aligner hears {n} p, b and m sounds in the {len(R['lines'])} lines the page spoke. The drawn mouth shuts for {len(off)} of them; "
              f"the middle of the shut mouth is {np.median(e):+.0f} ms from the middle of the sound (median), {int((np.abs(e) <= 40).sum())} within 40 ms and {int((np.abs(e) <= 80).sum())} within 80 ms")
