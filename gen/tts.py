"""tts.py : speak every line of the bulletin with Kokoro and record exactly when each sound happens.
Run from gen/ with the third environment:   ./venv3/bin/python tts.py
Writes work/tts/NN_<who>.wav (24 kHz mono) and work/tts/lines.json (caption words with start times, phonemes with
start time and length, loudness per phoneme). A caption word written {shown|spoken} is displayed one way and said another;
[word](/phonemes/) inside the spoken part fixes a pronunciation."""
import os, json, re, sys
import espeakng_loader; os.environ["ESPEAK_DATA_PATH"] = espeakng_loader.get_data_path()      # the fallback pronouncer needs its data path
import numpy as np, soundfile as sf, torch
from kokoro import KPipeline
torch.set_num_threads(4); torch.manual_seed(0)
SR, FRAME = 24000, 600                      # the model aligns sounds in 25 ms frames
VOICES = dict(paige=("a", "af_heart", 1.0), cy=("a", "am_michael", 1.0), dee=("a", "am_puck", 1.04), sunny=("a", "af_bella", 1.0), mel=("b", "bm_george", 0.96))
LINES = [
 ("paige", "Good evening, this is DevOps Tonight. I'm Paige Duty, and yes, I am on call."),
 ("cy",    "And I'm {Cy|[Cy](/sˈI/)} {Dekar.|[Dekar](/dəkˈɑɹ/).} It is {2026,|twenty twenty-six,} and production is, for the moment, up."),
 ("paige", "Our top story: an {AI|A.I.} agent opened forty pull requests overnight. A second agent approved them. A human is now being paged."),
 ("cy",    "Meanwhile, a routine Friday deploy is under way in {us-east-1.|U.S. east one.} Dee Ploy is at the scene. Dee?"),
 ("dee",   "Thanks, {Cy.|[Cy](/sˈI/).} The pipeline behind me has been green for nine minutes, and nobody here trusts it."),
 ("dee",   "Engineers have checked the dashboards, the rollback plan, and {DNS.|[DNS](/dˌiˌɛnˈɛs/).} Sources say it is always {DNS.|[DNS](/dˌiˌɛnˈɛs/).}"),
 ("cy",    "Dee, did anyone suggest waiting until Monday?"),
 ("dee",   "One person did, {Cy.|[Cy](/sˈI/).} They have been moved to the platform team. Back to you."),
 ("paige", "Brave work. Now the cloud forecast, with Sunny Uptime."),
 ("sunny", "Thanks, Paige. Pods are stuck Pending across the north while the {autoscaler|auto-scaler} thinks about it."),
 ("sunny", "In the south, scattered {503s|five-oh-threes} with a chance of retries. Four nines along the coast, and a high of nine thousand dollars in egress."),
 ("cy",    "Joining us is {Y.|Y} {A.|A} Mel, Staff {YAML|[YAML](/jˈæməl/)} Engineer. With agents writing the config now, is your job safe?"),
 ("mel",   "{Cy,|[Cy](/sˈI/),} the agent writes four thousand lines of {YAML|[YAML](/jˈaməl/)} a day. Someone still has to find the one wrong indent."),
 ("cy",    "Chilling. Thank you for your time."),
 ("paige", "That's all for tonight. Remember: you build it, you run it, and {FinOps|[FinOps](/fˈɪnɑps/)} will ask what it cost."),
 ("cy",    "From all of us in the control plane, good night, and may your pager stay quiet."),
]
def parts(text):
    out = []
    for m in re.finditer(r"\{([^|}]*)\|([^}]*)\}|(\S+)", text):
        out.append((m.group(1), m.group(2)) if m.group(3) is None else (m.group(3), m.group(3)))
    return out
pipes = {}; os.makedirs("work/tts", exist_ok=True); result = []
only = set(int(a) for a in sys.argv[1:])
for n, (who, text) in enumerate(LINES):
    lang, voice, speed = VOICES[who]; pp = parts(text)
    if lang not in pipes: pipes[lang] = KPipeline(lang_code=lang, repo_id="hexgrad/Kokoro-82M")
    spoken = " ".join(s for _, s in pp); caption = " ".join(c for c, _ in pp)
    chunks = list(pipes[lang](spoken, voice=voice, speed=speed, split_pattern=None))
    audio, segs, toks, t0 = [], [], [], 0.0
    for r in chunks:
        a = r.audio.numpy().astype(np.float32); pd = r.pred_dur.tolist(); ph = r.phonemes
        assert len(pd) == len(ph) + 2 and abs(len(a) - sum(pd) * FRAME) <= FRAME, (len(pd), len(ph), len(a), sum(pd) * FRAME)
        t = t0 + pd[0] * FRAME / SR
        for ch, d in zip(ph, pd[1:-1]):
            k0, k1 = int(round((t - t0) * SR)), int(round((t - t0) * SR)) + d * FRAME
            rms = float(np.sqrt(np.mean(a[k0:k1] ** 2))) if d else 0.0
            segs.append([ch, round(t, 4), round(d * FRAME / SR, 4), round(rms, 4)]); t += d * FRAME / SR
        for tk in r.tokens: toks.append((tk.text, tk.whitespace, None if tk.start_ts is None else t0 + tk.start_ts))
        audio.append(a); t0 += len(a) / SR
    audio = np.concatenate(audio)
    # caption words -> start times: a spoken form of k space-separated words takes the next k token groups
    groups, cur = [], []
    for txt, ws, ts in toks:
        cur.append(ts)
        if ws: groups.append(cur); cur = []
    if cur: groups.append(cur)
    words, gi = [], 0
    for cap, say in pp:
        k = len(re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", say).split()); ts = [x for g in groups[gi:gi + k] for x in g if x is not None]
        words.append([cap, round(min(ts), 3) if ts else None]); gi += k
    assert gi == len(groups), (n, gi, len(groups), [t[0] for t in toks])
    for i, w in enumerate(words):                      # a word with no timestamp starts where the previous one did
        if w[1] is None: w[1] = words[i - 1][1] if i else 0.0
    f = f"work/tts/{n:02d}_{who}.wav"
    if not only or n in only: sf.write(f, audio, SR)
    result.append(dict(n=n, who=who, voice=voice, speed=speed, caption=caption, spoken=spoken, phonemes=" | ".join(r.phonemes for r in chunks), dur=round(len(audio) / SR, 3), words=words, seg=segs, wav=f))
    print(f"{n:2d} {who:5s} {len(audio) / SR:5.2f}s chunks={len(chunks)}  {' | '.join(r.phonemes for r in chunks)}", flush=True)
json.dump(result, open("work/tts/lines.json", "w"), ensure_ascii=False)
syms = sorted(set(s[0] for L in result for s in L["seg"])); print("symbols:", " ".join(syms)); print("total speech", round(sum(L["dur"] for L in result), 1), "s")
