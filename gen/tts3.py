"""tts3.py [takes] [line ...] : speak every line a third time, with Phonon (request 10).

Phonon is a small on-device speech model (31 million parameters) published in October 2026. On the public blind-test
leaderboard for open speech models it ranks above both models used before. It comes with named voices; the cast below
was chosen from the publisher's own descriptions of them, since nobody here can listen.

  ./venv5/bin/python tts3.py 3          three takes of each line (seeds 1..3) -> work/tts3/NN_<who>_t<take>.wav
  ./venv5/bin/python tts3.py 3 12       line 12 only
  CAST_mel=Edwin ./venv5/bin/python tts3.py 3 12     try another voice for one presenter (written to work/tts3/alt_<voice>/)

The text is respelled where a name or abbreviation must sound a particular way."""
import os, sys, json, time, numpy as np, soundfile as sf, ptts
CAST = dict(paige="Harper", cy="Miles", dee="Easton", sunny="Juniper", mel="Master Aldric")
LINES = [
 ("paige", "Good evening, this is DevOps Tonight. I'm Paige Duty, and yes, I am on call."),
 ("cy",    "And I'm Sy DeCar. It is twenty twenty-six, and production is, for the moment, up."),
 ("paige", "Our top story: an A.I. agent opened forty pull requests overnight. A second agent approved them. A human is now being paged."),
 ("cy",    "Meanwhile, a routine Friday deploy is under way in U.S. east one. Dee Ploy is at the scene. Dee?"),
 ("dee",   "Thanks, Sy. The pipeline behind me has been green for nine minutes, and nobody here trusts it."),
 ("dee",   "Engineers have checked the dashboards, the rollback plan, and D.N.S. Sources say it is always D.N.S."),
 ("cy",    "Dee, did anyone suggest waiting until Monday?"),
 ("dee",   "One person did, Sy. They have been moved to the platform team. Back to you."),
 ("paige", "Brave work. Now the cloud forecast, with Sunny Uptime."),
 ("sunny", "Thanks, Paige. Pods are stuck pending across the north, while the auto scaler thinks about it."),
 ("sunny", "In the south, scattered five oh threes with a chance of re-tries. Four nines along the coast, and a high of nine thousand dollars in ee-gress."),
 ("cy",    "Joining us is Why A Mel, Staff Yammel Engineer. With agents writing the config now, is your job safe?"),
 ("mel",   "Sy, the agent writes four thousand lines of yammel a day. Someone still has to find the one wrong indent."),
 ("cy",    "Chilling. Thank you for your time."),
 ("paige", "That's all for tonight. Remember: you build it, you run it, and fin ops will ask what it cost."),
 ("cy",    "From all of us in the control plane, good night, and may your pager stay quiet."),
]
if __name__ == "__main__":
    takes = int(sys.argv[1]) if len(sys.argv) > 1 else 3; only = set(int(x) for x in sys.argv[2:]); out = "work/tts3"; alt = False
    for who in CAST:
        if os.environ.get("CAST_" + who): CAST[who] = os.environ["CAST_" + who]; out = "work/tts3/alt_" + CAST[who].replace(" ", "_"); alt = True
    os.makedirs(out, exist_ok=True); ptts.set_num_threads(4)
    tts = ptts.TTS(lang="en"); sr = tts.sample_rate
    if not alt: json.dump([dict(n=i, who=w, voice=CAST[w], spoken=t) for i, (w, t) in enumerate(LINES)], open(f"{out}/script.json", "w"), indent=1)
    for n, (who, text) in enumerate(LINES):
        if only and n not in only: continue
        for k in range(1, takes + 1):
            f = f"{out}/{n:02d}_{who}_t{k}.wav"
            if os.path.exists(f): continue
            t = time.time(); a = np.asarray(tts.synth(text, voice=CAST[who], seed=100 * n + k), dtype=np.float32)
            sf.write(f, a, sr, subtype='FLOAT'); print(f"{n:2d} {who:5s} {CAST[who]:14s} take {k}: {len(a) / sr:5.2f} s in {time.time() - t:4.1f} s, peak {np.abs(a).max():.2f}", flush=True)
    print("done; sample rate", sr, flush=True)
