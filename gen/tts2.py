"""tts2.py [takes] : speak every line again with a more expressive speech model (Chatterbox), keeping each presenter's
voice by using their first-round recording as the voice reference. The references are themselves synthetic, so no real
person's voice is involved.   ./venv4/bin/python tts2.py 2    -> work/tts2/NN_<who>_t<take>.wav
The model reads plain text, so names and abbreviations are respelled the way they should sound."""
import os, sys, time, json, torch, soundfile as sf
torch.set_num_threads(4)
from chatterbox.tts import ChatterboxTTS
REF = dict(paige="work/tts/02_paige.wav", cy="work/tts/03_cy.wav", dee="work/tts/05_dee.wav", sunny="work/tts/10_sunny.wav", mel="work/tts/12_mel.wav")
STYLE = dict(paige=(0.5, 0.5), cy=(0.5, 0.5), dee=(0.6, 0.5), sunny=(0.6, 0.5), mel=(0.4, 0.45))      # (expressiveness, pace/adherence)
LINES = [
 ("paige", "Good evening, this is DevOps Tonight. I'm Paige Duty, and yes, I am on call."),
 ("cy",    "And I'm Sy DeCar. It is twenty twenty-six, and production is, for the moment, up."),
 ("paige", "Our top story: an A I agent opened forty pull requests overnight. A second agent approved them. A human is now being paged."),
 ("cy",    "Meanwhile, a routine Friday deploy is under way in U S east one. Dee Ploy is at the scene. Dee?"),
 ("dee",   "Thanks, Sy. The pipeline behind me has been green for nine minutes, and nobody here trusts it."),
 ("dee",   "Engineers have checked the dashboards, the rollback plan, and D N S. Sources say it is always D N S."),
 ("cy",    "Dee, did anyone suggest waiting until Monday?"),
 ("dee",   "One person did, Sy. They have been moved to the platform team. Back to you."),
 ("paige", "Brave work. Now the cloud forecast, with Sunny Uptime."),
 ("sunny", "Thanks, Paige. Pods are stuck pending across the north, while the auto scaler thinks about it."),
 ("sunny", "In the south, scattered five oh threes with a chance of retries. Four nines along the coast, and a high of nine thousand dollars in egress."),
 ("cy",    "Joining us is Why A Mel, Staff Yammel Engineer. With agents writing the config now, is your job safe?"),
 ("mel",   "Sy, the agent writes four thousand lines of yammel a day. Someone still has to find the one wrong indent."),
 ("cy",    "Chilling. Thank you for your time."),
 ("paige", "That's all for tonight. Remember: you build it, you run it, and fin ops will ask what it cost."),
 ("cy",    "From all of us in the control plane, good night, and may your pager stay quiet."),
]
if __name__ == "__main__":
    takes = int(sys.argv[1]) if len(sys.argv) > 1 else 2; only = set(int(x) for x in sys.argv[2:]); os.makedirs("work/tts2", exist_ok=True)       # tts2.py 5 1 : up to five takes, line 1 only
    model = ChatterboxTTS.from_pretrained(device="cpu"); json.dump([dict(n=i, who=w, spoken=t) for i, (w, t) in enumerate(LINES)], open("work/tts2/script.json", "w"))
    for n, (who, text) in enumerate(LINES):
        if only and n not in only: continue
        for k in range(1, takes + 1):
            f = f"work/tts2/{n:02d}_{who}_t{k}.wav"
            if os.path.exists(f): continue
            t = time.time(); torch.manual_seed(100 * n + k); ex, cfg = STYLE[who]
            wav = model.generate(text, audio_prompt_path=REF[who], exaggeration=ex, cfg_weight=cfg, temperature=0.8)
            a = wav.squeeze(0).numpy(); sf.write(f, a, model.sr); print(f"{n:2d} {who:5s} take {k}: {len(a) / model.sr:5.2f} s in {time.time() - t:4.0f} s", flush=True)
    print("done", flush=True)
