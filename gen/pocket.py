"""pocket.py : speak text in a voice copied from a short recording, with Pocket TTS (Kyutai, 100M parameters).

The model is used as ONNX files (the community export KevinAHM/pocket-tts-onnx, weights only); everything that drives
them is written here, including the tokenizer, so it can be carried over to the browser line for line:

  tokenizer       the SentencePiece model file is read directly (it is a small protobuf) and text is cut into pieces by
                  the usual best-path search
  voice           the recording goes through the audio encoder once; its output is fed to the language model, and the
                  state the model is left in IS the voice (it is reused for every line)
  a line          text pieces -> text conditioner -> language model; then, 12.5 times per second of speech: the model
                  gives a conditioning vector and an end-of-speech score, one step of a flow network turns noise into
                  the next audio latent, and the latent is fed back
  audio           the latents go through the audio decoder (24 kHz)

Nothing here says when each sound happens: the model has no notion of it. Timing is measured afterwards (align.py).

  ./venv6/bin/python pocket.py <voice.wav> <out.wav> "Text to say." ["More text." ...]
  ./venv6/bin/python pocket.py voice <recording.wav> <out.pvoice>       the voice file the page uses (the recording after the audio encoder)
Model files are looked for in ../avatar/voice/src/pocket/ (see docs/21)."""
import json, os, struct, sys, time
import numpy as np, onnxruntime as ort, soundfile as sf
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "avatar", "voice", "src", "pocket")

# ── the tokenizer: SentencePiece's model file, read by hand ──
def _fields(b):
    i = 0
    while i < len(b):
        key = 0; s = 0
        while True:
            c = b[i]; i += 1; key |= (c & 127) << s; s += 7
            if c < 128: break
        no, wt = key >> 3, key & 7
        if wt == 0:
            v = 0; s = 0
            while True:
                c = b[i]; i += 1; v |= (c & 127) << s; s += 7
                if c < 128: break
        elif wt == 1: v = b[i:i + 8]; i += 8
        elif wt == 2:
            n = 0; s = 0
            while True:
                c = b[i]; i += 1; n |= (c & 127) << s; s += 7
                if c < 128: break
            v = b[i:i + n]; i += n
        elif wt == 5: v = b[i:i + 4]; i += 4
        else: raise ValueError("unknown wire type")
        yield no, wt, v
class Tokenizer:
    def __init__(self, path):
        self.pieces = []; self.kind = 1; self.dummy = True; self.squeeze = True
        for no, wt, v in _fields(open(path, "rb").read()):
            if no == 1:
                piece, score, typ = "", 0.0, 1
                for n2, w2, v2 in _fields(v):
                    if n2 == 1: piece = v2.decode("utf-8")
                    elif n2 == 2: score = struct.unpack("<f", v2)[0]
                    elif n2 == 3: typ = v2
                self.pieces.append((piece, score, typ))
            elif no == 2:
                for n2, w2, v2 in _fields(v):
                    if n2 == 3: self.kind = v2                      # 1 unigram, 2 BPE
            elif no == 3:
                for n2, w2, v2 in _fields(v):
                    if n2 == 3: self.dummy = bool(v2)
                    elif n2 == 4: self.squeeze = bool(v2)
        assert self.kind == 1, "only unigram models are handled here"
        self.id = {p: i for i, (p, s, t) in enumerate(self.pieces)}
        self.unk = next(i for i, (p, s, t) in enumerate(self.pieces) if t == 2)
        self.longest = max(len(p) for p, s, t in self.pieces)
        self.floor = min(s for p, s, t in self.pieces if t == 1) - 10.0
    def encode(self, text):
        if self.squeeze: text = " ".join(text.split())
        t = ("▁" if self.dummy else "") + text.replace(" ", "▁")
        n = len(t); best = [-1e30] * (n + 1); back = [None] * (n + 1); best[0] = 0.0
        for i in range(n):
            if best[i] < -1e29: continue
            hit = False
            for L in range(1, min(self.longest, n - i) + 1):
                k = self.id.get(t[i:i + L])
                if k is None: continue
                p, s, typ = self.pieces[k]
                if typ not in (1, 4): continue                      # normal and user-defined pieces only
                hit = hit or L == 1
                v = best[i] + (s if typ == 1 else 0.0)
                if v > best[i + L]: best[i + L] = v; back[i + L] = (i, k)
            if not hit and best[i] + self.floor > best[i + 1]: best[i + 1] = best[i] + self.floor; back[i + 1] = (i, self.unk)
        out = []; i = n
        while i > 0: j, k = back[i]; out.append(k); i = j
        return out[::-1]

# ── the model ──
class Pocket:
    def __init__(self, threads=4, temperature=0.7, seed=0):
        self.meta = M = json.load(open(os.path.join(D, "bundle.json"))); self.tok = Tokenizer(os.path.join(D, M["tokenizer_file"]))
        so = ort.SessionOptions(); so.intra_op_num_threads = threads; so.inter_op_num_threads = 1
        load = lambda f: ort.InferenceSession(os.path.join(D, f), so, providers=["CPUExecutionProvider"])
        self.enc, self.txt, self.lm, self.flow, self.dec = load("mimi_encoder.onnx"), load("text_conditioner.onnx"), load("flow_lm_main_int8.onnx"), load("flow_lm_flow_int8.onnx"), load("mimi_decoder_int8.onnx")
        self.sr, self.ld, self.cd = M["sample_rate"], M["latent_dim"], M["conditioning_dim"]; self.frame = M["samples_per_frame"] / self.sr
        self.bos = np.load(os.path.join(D, M["bos_before_voice_file"])).astype(np.float32) if M.get("insert_bos_before_voice") else None
        self.temp = temperature; self.rng = np.random.default_rng(seed)
    def _blank(self, manifest):
        T = dict(float32=np.float32, int64=np.int64, bool=np.bool_)
        return {e["input_name"]: (np.full(e["shape"], np.nan, T[e["dtype"]]) if e["fill"] == "nan" else np.ones(e["shape"], T[e["dtype"]]) if e["fill"] == "ones" else np.zeros(e["shape"], T[e["dtype"]])) for e in manifest}
    def _keep(self, state, result, manifest, offset):
        for e in manifest: state[e["input_name"]] = result[offset + e["index"]]
    def voice(self, wav):
        """the state the language model is in after hearing the recording"""
        a, sr = sf.read(wav, dtype="float32"); assert sr == self.sr, "resample the recording to 24 kHz first"
        if a.ndim > 1: a = a.mean(axis=1)
        emb = self.enc.run(None, {"audio": a.reshape(1, 1, -1)})[0]; emb = emb.reshape(1, -1, emb.shape[-1]).astype(np.float32)
        if self.bos is not None: emb = np.concatenate([self.bos.reshape(1, -1, emb.shape[-1]), emb], axis=1)
        state = self._blank(self.meta["flow_lm_state_manifest"])
        r = self.lm.run(None, {"sequence": np.zeros((1, 0, self.ld), np.float32), "text_embeddings": emb, **state}); self._keep(state, r, self.meta["flow_lm_state_manifest"], 2)
        return state, emb
    @staticmethod
    def tidy(text):
        text = " ".join(text.split()); text = text[0].upper() + text[1:]
        return text + "." if text[-1].isalnum() else text
    def say(self, text, voice, after=None):
        """one line -> (audio, seconds it took, number of frames)"""
        t0 = time.time(); text = self.tidy(text); ids = np.array([self.tok.encode(text)], np.int64); M = self.meta["flow_lm_state_manifest"]
        state = {k: v.copy() for k, v in voice.items()}
        r = self.lm.run(None, {"sequence": np.zeros((1, 0, self.ld), np.float32), "text_embeddings": self.txt.run(None, {"token_ids": ids})[0].reshape(1, -1, self.cd), **state}); self._keep(state, r, M, 2)
        after = after if after is not None else (3 if len(text.split()) <= 4 else 1) + 2      # frames made after the model says the speech is over
        cur = np.full((1, 1, self.ld), np.nan, np.float32); none = np.zeros((1, 0, self.cd), np.float32); lat = []; eos = None
        for step in range(int(np.ceil((ids.shape[1] / 3.0 + 2.0) * self.meta["frame_rate"]))):
            r = self.lm.run(None, {"sequence": cur, "text_embeddings": none, **state}); self._keep(state, r, M, 2)
            if r[1][0][0] > -4.0 and eos is None: eos = step
            if eos is not None and step >= eos + after: break
            x = self.rng.normal(0.0, np.sqrt(self.temp), (1, self.ld)).astype(np.float32) if self.temp > 0 else np.zeros((1, self.ld), np.float32)
            x = x + self.flow.run(None, {"c": r[0], "s": np.array([[0.0]], np.float32), "t": np.array([[1.0]], np.float32), "x": x})[0]      # one step of the flow
            cur = x.reshape(1, 1, self.ld); lat.append(cur)
        ms = self._blank(self.meta["mimi_state_manifest"]); out = []
        for i in range(0, len(lat), 12):
            r = self.dec.run(None, {"latent": np.concatenate(lat[i:i + 12], axis=1), **ms}); out.append(r[0].reshape(-1)); self._keep(ms, r, self.meta["mimi_state_manifest"], 1)
        return (np.concatenate(out) if out else np.zeros(0, np.float32)), time.time() - t0, len(lat), ids.shape[1]
if __name__ == "__main__":
    if sys.argv[1] == "voice":                               # pocket.py voice <recording.wav> <out.pvoice>: the recording as the audio encoder writes it down
        P = Pocket(); a, sr = sf.read(sys.argv[2], dtype="float32"); a = a.mean(axis=1) if a.ndim > 1 else a
        if sr != P.sr: a = __import__("librosa").resample(a, orig_sr=sr, target_sr=P.sr)
        g = min(0.9 / np.abs(a).max(), 0.1 / max(1e-6, float(np.sqrt(np.mean(np.sort(a ** 2)[int(len(a) * 0.6):])))))      # a quiet recording gives a quiet voice: bring it to a speaking level first
        sf.write("/tmp/_pocket_voice.wav", a * g, P.sr); V, emb = P.voice("/tmp/_pocket_voice.wav"); os.remove("/tmp/_pocket_voice.wav")
        emb[0].astype("<f4").tofile(sys.argv[3]); print(f"{sys.argv[3]}: {emb.shape[1]} frames x {emb.shape[2]} numbers ({os.path.getsize(sys.argv[3]) / 1e6:.2f} MB), recording raised {g:.1f} times"); sys.exit()
    P = Pocket(); t = time.time(); V, emb = P.voice(sys.argv[1]); print(f"voice: {emb.shape[1]} frames of conditioning, {time.time() - t:.1f} s", flush=True)
    parts = []
    for text in sys.argv[3:]:
        a, took, n, ntok = P.say(text, V); parts.append(a); parts.append(np.zeros(int(0.25 * P.sr), np.float32))
        print(f"{len(a) / P.sr:5.2f} s of speech in {took:5.2f} s ({took / max(1e-9, len(a) / P.sr):.2f} x), {ntok} pieces, {n} frames: {text}", flush=True)
    sf.write(sys.argv[2], np.concatenate(parts), P.sr)
