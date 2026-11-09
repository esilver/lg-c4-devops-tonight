# The still photographs

Every photograph on channel 1 was generated in the session with an open image model running on the CPU. This document
covers the model, the prompts and seeds, which candidates were kept and why, the refinement passes, and the cut-outs.

All commands run from `gen/`. Scripts use two Python virtual environments, `gen/venv` and `gen/venv2`; the reason for two
is in [09](09-problems-and-retries.md). Exact package versions are in `gen/requirements-venv.txt` and
`gen/requirements-venv2.txt`.

## Machine and setup

- 4 virtual cores (Intel Xeon with AMX and AVX-512 BF16), 15 GB RAM reported, no GPU, Python 3.13.18.
- The UNet and text encoder run in bfloat16, which this CPU accelerates; the VAE stays in float32.

```
python3 -m venv venv
./venv/bin/pip install torch --index-url https://download.pytorch.org/whl/cpu
./venv/bin/pip install diffusers transformers accelerate safetensors peft pillow numpy opencv-python-headless huggingface_hub cmudict
python3 -m venv venv2
./venv2/bin/pip install torchvision==0.29.2 torch --index-url https://download.pytorch.org/whl/cpu
./venv2/bin/pip install transformers timm kornia einops pillow opencv-python-headless onnxruntime
./venv/bin/python download_models.py        # 6.6 GB into gen/models/
```

`download_models.py` was written for this repository; it gathers `dl.py` and the downloads that were typed inline.

## Model and sampler

| Setting | Value |
|---|---|
| Model | Realistic Vision V5.1, a fine-tune of Stable Diffusion 1.5 |
| VAE | `stabilityai/sd-vae-ft-mse` |
| Sampler for new images | DPM-Solver++ multistep, order 2, Karras sigmas, 25 steps, guidance 5.0 |
| Size | 768 × 432, later refined to 1024 × 576 |
| Speed | about 54 seconds per image |

Negative prompt (`sdlib.NEG`):

> cartoon, illustration, painting, drawing, 3d render, cgi, anime, doll, plastic skin, airbrushed, deformed, disfigured,
> extra fingers, bad hands, text, watermark, logo, caption, letters, subtitles, blurry face, cross-eyed, side view,
> profile, looking away, tilted head, nsfw, nude

The four terms "side view, profile, looking away, tilted head" were added after the first twenty candidates, because many
of those faced away from the camera. So seeds 21 to 24 below were made without them, and everything later with them.

### Benchmark (`bench.py`)

Two test images each, same prompt, seeds 11 and 12. The files are `out/bench_*.jpg`.

| Mode | Steps, guidance | Seconds per image |
|---|---|---|
| LCM-LoRA shortcut | 6, 1.5 | 21.5 and 22.4 |
| Full sampler | 25, 5.0 | 53.5 and 54.9 |

Both looked like photographs. The full sampler was kept for quality, since a minute per image was affordable. A second
speed-up LoRA (Hyper-SD) was downloaded and never used.

## Prompts

From [`gen/prompts.py`](../gen/prompts.py). Two fragments are shared:

- `FACE` = "facing the camera, looking straight into the camera, lips closed"
- `STUDIO` = "modern TV news studio, dark blue video walls blurred in background, broadcast footage, studio lighting"

| Key | Prompt |
|---|---|
| `paige` | RAW photo, television news anchor, woman in her mid 30s with long dark brown hair, red blazer, sitting at a news desk, `FACE`, calm expression, medium close-up, `STUDIO` |
| `cy` (first) | RAW photo, television news anchor, Black man in his 40s with short hair, navy suit, white shirt, green tie, sitting at a news desk, `FACE`, calm expression, medium close-up, `STUDIO` |
| `cy2` (retry) | the same with "front view, centered," added before `FACE` |
| `cy` (for refinement) | rewritten to match the chosen picture: "…white shirt, green tie, sitting at a news desk, front view, `FACE`, calm expression, medium close-up, newsroom with monitors blurred in background, broadcast footage, studio lighting" |
| `dee` | RAW photo, television news reporter, man in his late 20s with curly ginger hair, dark green jacket, holding a microphone, standing outside a large modern data center building, `FACE`, medium close-up, overcast daylight, live broadcast footage |
| `sunny` | RAW photo, television weather presenter, Indian woman in her 30s with black bob haircut, teal blouse, standing in a TV studio, `FACE`, slight smile, medium shot, plain dark blue studio wall behind her, broadcast footage, studio lighting |
| `mel` | RAW photo, webcam video call, bald man in his 60s with round glasses, grey suit, purple tie, sitting in a home office, bookshelves behind him, `FACE`, serious expression, medium close-up, natural window light |
| `studio` | RAW photo, wide shot of an empty modern television news studio at night, curved glass anchor desk, huge dark blue video walls, ceiling studio lights, broadcast cameras, cinematic, sharp focus |
| `servers` | RAW photo, long aisle of server racks in a data center, rows of blinking green and blue LED lights, cold aisle, symmetrical, sharp focus |
| `dcext` | RAW photo, exterior of a large windowless modern data center building, security fence, overcast sky, wide shot, documentary photography |
| `office` | RAW photo, dark open-plan office at night, empty desk with computer monitors glowing with lines of code, nobody there, shallow depth of field |
| `paged` | RAW photo, tired software engineer in a hoodie woken up at night, sitting up in bed looking at a glowing smartphone, dark bedroom, blue light on face, documentary photography |
| `sat` | satellite photo from space, swirling white storm clouds over dark blue ocean and green coastline, weather satellite view, high detail |

The text encoder reads 77 tokens. The benchmark prompt ran over and lost its last words ("sharp focus, 8k"). The `cy2`
retry ran over by two words and lost its final "studio lighting"; `logs/log_cy2.txt` shows the warning. The other
prompts fit.

## Candidates and picks

`gen_base.py <keys> <seeds>` writes `out/base_<key>_<seed>.png`. Contact sheets are `out/sheet_*.jpg`.

| Presenter | Seeds made | Picked | Why, and what was wrong with the others |
|---|---|---|---|
| Paige | 21, 22, 23, 24 | **21** | Frontal, centred, eye contact, red blazer. 22: navy clothes, busy garbled screens. 23: the same face repeated three times. 24: side view |
| Cy | 21, 22, 23, 24, then `cy2` 31, 32, 33 | **24** | Frontal with eye contact in a newsroom of dashboards, green tie. He wears a shirt, not the navy suit asked for. 21: leaning sideways. 22: looking down. 23: wide and tilted. 31: looking away. 32: usable alternative. 33: tilted close-up. Seeds 34 to 36 were cancelled once 24 was chosen |
| Dee | 21, 22, 23, 24 | **22** | Frontal and centred. No microphone appeared in any candidate. 21: off to one side, head tilted. 23: wider, grinning. 24: looking away |
| Sunny | 21, 22, 23, 24 | **23** | Frontal, teal blouse, clean outline for cutting out. 21: two women. 22: good alternative. 24: a studio camera in frame |
| Mel | 21, 22, 23, 24 | **21** | Looks like a video call. 22 and 23: a hand raised beside the head. 24: good alternative |

B-roll: one seed each (41) for `studio`, `servers`, `dcext`, `office`, `paged`, `sat`. All six were usable, so the planned
second seed (42) was cancelled. The contact sheet is `out/sheet_41.jpg`.

Known mismatches with the prompts, accepted as they were: Dee has no microphone; the "paged" engineer has no phone in
view; the "office" is daylit, not dark; Dee's backdrop is a glass office building while `dcext` is windowless.

## Refinement (`prep.py`, first half)

`prep.py <key> <seed>` turns the 768 × 432 pick into the final 1024 × 576 frame in `work/<key>/`.

1. **Enlarge.** Lanczos resize to 1024 × 576, then image-to-image at strength 0.3 (6 of 20 steps), guidance 5, seed 1,
   with the same prompt. Output: `hires.png`. About 50 seconds.
2. **Find the face.** OpenCV's YuNet detector gives the eye centres and mouth corners (`facelib.landmarks`).
3. **Crop.** A square of side 3.6 × the distance between the eyes (rounded to 8), centred 0.45 of that distance below the
   eye line, scaled to 512 × 512.
4. **Refine the face.** Image-to-image at strength 0.35 (7 of 20 steps), seed 2, prompt "RAW photo, close-up portrait of
   *description*, lips closed, looking at the camera, detailed skin texture, sharp focus". Output: `face0.png`. About 20
   seconds.
5. **Round trip.** `face0r.png` is `face0.png` encoded and decoded once through the VAE, so it has exactly the softness
   that every inpainted variant will have.
6. **Paste back.** `face0r` goes into the frame through a feathered ellipse. Output: `frame.png`, with `meta.json`
   holding the crop and landmarks.

Image-to-image and inpainting use a small DDIM sampler written in `sdlib.py` (`ddim`), not the library's pipelines,
because the library pipelines assume one number format for every part of the model. It uses trailing timesteps, no added
noise, and for inpainting it re-imposes the known region at each step at the matching noise level.

Face measurements from `meta.json` (pixels in the 1024 × 576 frame):

| Presenter | Eye distance | Face crop (x, y, side) | Crop enlargement |
|---|---|---|---|
| Paige | 86.4 | 348, 81, 312 | 1.64× |
| Cy | 98.6 | 443, 45, 352 | 1.45× |
| Dee | 112.8 | 455, 90, 408 | 1.25× |
| Sunny | 60.9 | 495, 100, 216 | 2.37× |
| Mel | 112.8 | 435, 48, 408 | 1.25× |

The second half of `prep.py` makes mouth and blink variants by inpainting. That belongs to the first lip-sync and is
described in [04](04-lipsync-v1-inpainted-mouths.md).

## B-roll at full size (`stills.py`)

```
./venv/bin/python stills.py studio=41 servers=41 dcext=41 office=41 paged=41 sat=41
```

The same enlarge step as above. Output: `out/still_<key>.png`.

## Cut-outs (`matte_onnx.py`, then the export scripts)

Each presenter is separated from the background so that the two can move independently and so the weather presenter can
stand in front of the map.

```
./venv2/bin/python matte_onnx.py birefnet work/paige/frame.png work/paige/alpha.png     # one image per process
```

- The matte comes from BiRefNet-portrait in ONNX form, run at 1024 × 1024, about 40 seconds per image. Output:
  `work/<key>/alpha.png`.
- A lighter model, MODNet, was tried first (2 seconds). It left a pale halo around the hair. Its matte for Paige is kept
  as `work/paige/alpha_modnet.png`, and `out/matte_paige.jpg` shows both over green.
- Run one image per process. Two in one process ran out of memory twice.

The export step (`lpexport.py` now, `export.py` in the first lip-sync) then:

- tightens the matte: `alpha' = clip((alpha − 0.25) / 0.7, 0, 1)`;
- replaces edge colours with colours grown outward from the solid interior (OpenCV Telea inpainting, radius 4), which
  removes the fringe of the old background. Sunny's hair showed a bright halo over the dark map before this;
- makes a background plate by painting the person out (Telea, radius 7, over the dilated matte) and blurring the fill.
  Only the plate's rim is ever seen, when the presenter shifts by a few pixels.

The cut-out is stored as WebP with transparency and the plate as JPEG, both inside `assets.json`.
