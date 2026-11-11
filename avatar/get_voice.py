"""get_voice.py : fetches what the live avatar's own voice needs and lays it out as the page loads it -> avatar/voice/

The voice is Kokoro (82M parameters, Apache-2.0), the model that voiced the bulletin's first recordings, here in the
export made for browsers: an ONNX file that returns the waveform AND how long each sound lasts. The page runs it with
onnxruntime-web (MIT) in a worker, and turns text into sounds with phonemizer (Apache-2.0 wrapper around eSpeak NG,
which is GPL-3.0). None of that is committed: it is 110 MB of other people's files, all pinned here by version and
checked by hash.

  avatar/voice/src/            the downloads, as they came
  avatar/voice/model.N.bin     the model cut into parts of at most 19 MB (a published page may hold files up to 20 MB)
  avatar/voice/ort.js, ort-wasm.js, ort-wasm.wasm, phonemizer.js       the two libraries, under names that end in .js
  avatar/voice/ort-jspi.js, ort-jspi-wasm.js, ort-jspi.wasm            the same runtime built for a GPU (WebGPU), 18 MB,
                                                                       for browsers that can suspend WebAssembly (JSPI)
  avatar/voice/ort-gpu.js, ort-gpu-wasm.js, ort-gpu.wasm               the GPU build for other browsers, 29 MB
  avatar/voice/v_<name>.bin    the voices (510 x 256 numbers each: the speaker, for every length of sentence)
  avatar/voice/vocab.json      which number the model uses for which sound
  avatar/voice/manifest.json   how many parts, how many bytes, which voices

Run from the repository root:  python3 avatar/get_voice.py          the 8-bit model (92 MB): the one for a processor
                                python3 avatar/get_voice.py full     the full-precision model (326 MB): slower on a
                                                                     processor, but it can run on a GPU, which is far faster"""
import glob, hashlib, io, json, os, shutil, sys, tarfile, urllib.request
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "voice"); S = os.path.join(D, "src"); os.makedirs(S, exist_ok=True)
HF = "https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX-timestamped/resolve/dd4401a9add81ac692d20e240d22ec9dda82cc29/"
VOICES = ["af_heart", "af_bella", "am_michael", "am_puck", "am_fenrir"]
PART = 19 * 1024 * 1024; FULL = sys.argv[1:] == ["full"]; MODEL = "model.onnx" if FULL else "model_quantized.onnx"
FILES = {                                                     # name in src/ : (where from, sha256)
    MODEL: (HF + "onnx/" + MODEL, "651ea8291843a92276a4a003581a215cb07d15e47dde6fcfb1b768f9a1682054" if FULL else "c0c02b3299fd97c34ea92a98e6d41eaa1a739c8f77bf685aac34bd7b34c1132c"),
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
    "ort-jspi.js": member("onnxruntime-web-1.31.1.tgz", "dist/ort.jspi.min.mjs"),
    "ort-jspi-wasm.js": member("onnxruntime-web-1.31.1.tgz", "dist/ort-wasm-simd-threaded.jspi.mjs"),
    "ort-jspi.wasm": member("onnxruntime-web-1.31.1.tgz", "dist/ort-wasm-simd-threaded.jspi.wasm"),
    "ort-gpu.js": member("onnxruntime-web-1.31.1.tgz", "dist/ort.webgpu.min.mjs"),
    "ort-gpu-wasm.js": member("onnxruntime-web-1.31.1.tgz", "dist/ort-wasm-simd-threaded.asyncify.mjs"),
    "ort-gpu.wasm": member("onnxruntime-web-1.31.1.tgz", "dist/ort-wasm-simd-threaded.asyncify.wasm"),
    "phonemizer.js": member("phonemizer-1.2.1.tgz", "dist/phonemizer.js"),
}
for v in VOICES: out[f"v_{v}.bin"] = open(os.path.join(S, f"{v}.bin"), "rb").read()
for old in glob.glob(os.path.join(D, "model.*.bin")): os.remove(old)                # one model at a time is laid out
model = open(os.path.join(S, MODEL), "rb").read(); n = -(-len(model) // PART)
for i in range(n): out[f"model.{i}.bin"] = model[i * PART:(i + 1) * PART]
out["vocab.json"] = json.dumps(json.load(open(os.path.join(S, "tokenizer.json"), encoding="utf-8"))["model"]["vocab"], ensure_ascii=False).encode()
out["manifest.json"] = json.dumps(dict(parts=n, bytes=len(model), voices=VOICES, model="Kokoro-82M v1.0, ONNX with durations, " + ("full precision" if FULL else "8-bit"), sha256=pins[MODEL])).encode()
for name, data in out.items():
    assert len(data) <= 20 * 1024 * 1024 or name == "ort-gpu.wasm", name               # (the GPU runtime is 29 MB: fine from a disk or a server)
    with open(os.path.join(D, name), "wb") as f: f.write(data)
print("\n".join(f"{len(d) / 1e6:7.2f} MB  voice/{k}" for k, d in out.items())); print(f"{sum(len(d) for d in out.values()) / 1e6:7.2f} MB in all (plus voice/worker.js, which is this repository's own)")
