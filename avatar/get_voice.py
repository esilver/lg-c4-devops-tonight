"""get_voice.py : fetches what the live avatar's own voice needs and lays it out as the page loads it -> avatar/voice/

The voice is Kokoro (82M parameters, Apache-2.0), the model that voiced the bulletin's first recordings, here in the
export made for browsers: an ONNX file that returns the waveform AND how long each sound lasts. The page runs it with
onnxruntime-web (MIT) in a worker, and turns text into sounds with phonemizer (Apache-2.0 wrapper around eSpeak NG,
which is GPL-3.0). None of that is committed: it is 110 MB of other people's files, all pinned here by version and
checked by hash.

  avatar/voice/src/            the downloads, as they came
  avatar/voice/model.N.bin     the model cut into parts of at most 19 MB (a published page may hold files up to 20 MB)
  avatar/voice/ort.js, ort-wasm.js, ort-wasm.wasm, phonemizer.js       the two libraries, under names that end in .js
  avatar/voice/v_<name>.bin    the voices (510 x 256 numbers each: the speaker, for every length of sentence)
  avatar/voice/vocab.json      which number the model uses for which sound
  avatar/voice/manifest.json   how many parts, how many bytes, which voices

Run from the repository root:  python3 avatar/get_voice.py"""
import hashlib, io, json, os, shutil, tarfile, urllib.request
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "voice"); S = os.path.join(D, "src"); os.makedirs(S, exist_ok=True)
HF = "https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX-timestamped/resolve/dd4401a9add81ac692d20e240d22ec9dda82cc29/"
VOICES = ["af_heart", "af_bella", "am_michael", "am_puck", "am_fenrir"]
PART = 19 * 1024 * 1024
FILES = {                                                     # name in src/ : (where from, sha256)
    "model_quantized.onnx": (HF + "onnx/model_quantized.onnx", "c0c02b3299fd97c34ea92a98e6d41eaa1a739c8f77bf685aac34bd7b34c1132c"),
    "tokenizer.json": (HF + "tokenizer.json", None),
    "onnxruntime-web-1.31.1.tgz": ("https://registry.npmjs.org/onnxruntime-web/-/onnxruntime-web-1.31.1.tgz", None),
    "phonemizer-1.2.1.tgz": ("https://registry.npmjs.org/phonemizer/-/phonemizer-1.2.1.tgz", None),
}
for v in VOICES: FILES[f"{v}.bin"] = (HF + f"voices/{v}.bin", None)
PINS = os.path.join(os.path.dirname(D), "voice_pins.json"); pins = json.load(open(PINS)) if os.path.exists(PINS) else {}
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()
for name, (url, want) in FILES.items():
    p = os.path.join(S, name); want = want or pins.get(name)
    if not os.path.exists(p):
        print("fetching", name, flush=True)
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "get_voice.py"})) as r, open(p + ".part", "wb") as f: shutil.copyfileobj(r, f)
        os.replace(p + ".part", p)
    got = sha(p)
    assert not want or got == want, f"{name}: sha256 is {got}, expected {want}"
    pins[name] = got
json.dump(pins, open(PINS, "w"), indent=1, sort_keys=True)
def member(tgz, path):
    with tarfile.open(os.path.join(S, tgz)) as t: return t.extractfile("package/" + path).read()
out = {
    "ort.js": member("onnxruntime-web-1.31.1.tgz", "dist/ort.wasm.min.mjs"),
    "ort-wasm.js": member("onnxruntime-web-1.31.1.tgz", "dist/ort-wasm-simd-threaded.mjs"),
    "ort-wasm.wasm": member("onnxruntime-web-1.31.1.tgz", "dist/ort-wasm-simd-threaded.wasm"),
    "phonemizer.js": member("phonemizer-1.2.1.tgz", "dist/phonemizer.js"),
}
for v in VOICES: out[f"v_{v}.bin"] = open(os.path.join(S, f"{v}.bin"), "rb").read()
model = open(os.path.join(S, "model_quantized.onnx"), "rb").read(); n = -(-len(model) // PART)
for i in range(n): out[f"model.{i}.bin"] = model[i * PART:(i + 1) * PART]
out["vocab.json"] = json.dumps(json.load(open(os.path.join(S, "tokenizer.json"), encoding="utf-8"))["model"]["vocab"], ensure_ascii=False).encode()
out["manifest.json"] = json.dumps(dict(parts=n, bytes=len(model), voices=VOICES, model="Kokoro-82M v1.0, ONNX with durations, 8-bit", sha256=pins["model_quantized.onnx"])).encode()
for name, data in out.items():
    assert len(data) <= 20 * 1024 * 1024, name
    with open(os.path.join(D, name), "wb") as f: f.write(data)
print("\n".join(f"{len(d) / 1e6:7.2f} MB  voice/{k}" for k, d in out.items())); print(f"{sum(len(d) for d in out.values()) / 1e6:7.2f} MB in all (plus voice/worker.js, which is this repository's own)")
