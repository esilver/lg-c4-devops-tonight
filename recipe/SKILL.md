---
name: talking-presenter-video
description: Recipe for building a short talking-presenter video (a news bulletin, an explainer) from ONE still image per presenter and a synthetic voice, with downloaded local models on a CPU and no video-generation model. Covers the generated portrait, the cut-out, 65 re-posed stills per face, timed speech, a measured lip-sync reference, optical-flow motion fields, body and hair maps, a browser compositor and frame-by-frame recording. Use when asked to animate a still portrait so that it speaks a script with lip-sync, blinks, brow, head, body and hair movement, to rebuild or adapt the DevOps Tonight presenter pipeline, or to pick local models and starting settings for such a pipeline. It is a recipe with the settings that worked on five generated faces, not runnable code.
---

# Talking presenters, from one still image each

This is how the two-minute news bulletin "DevOps Tonight" was made. It has five presenters. Each one is
a single generated photograph, animated and lip-synced to a synthetic voice. Every model was downloaded
and run on four CPU cores. No video-generation model is involved. The text is written for an AI coding
agent, or an engineer, who wants to build the same thing.

**This is a recipe, not the working code.** It describes what was done and the settings that worked on
these five faces. A rebuild will differ. You write your own scripts, and every measured number here has
to be measured again on your own faces and voices.

## Read this first

- **What comes out.** One MP4 with sound, 1024 × 576, 30 frames a second. The bulletin runs 107.2 s:
  3,215 frames, each drawn by a program and saved as a picture before encoding.
- **The method.** Generate one photograph per presenter. Cut the person out. Have a face re-posing model
  render 65 stills of the same face (mouth shapes, lids, gaze, head turns, brows). Record a synthetic
  voice and time every sound in it. Show each recording to a lip-sync network and measure its mouth,
  never showing its picture. For every video frame, blend the nearest poses, move the result on a mesh,
  and draw it over the background.
- **Nothing in it is real.** The presenters and places were generated from text by an image model. The
  voices are stock voices of open speech models. The news is satire. Nobody's likeness or voice was
  copied. The bulletin says so in its credits. Label your result the same way.
- **What it cannot do.** It is a warp of one photograph per person. Heads turn about six degrees at
  most. Hands never appear. Hair moves as a sheet. Nothing new comes into view. The full list is in
  "What it cannot do".
- **How it was checked.** The AI coding agent that built it cannot watch video or listen. Every check
  was a still picture or a number. The checks below are of that kind, so another agent can run them.
- **How to use this file.** Do the eight steps in order. Each step has In, Do, Out, Check and Settings
  that worked. Do not go on until the check passes. Read "Tried and dropped" before you improvise:
  most shortcuts are already in it.
- **Units.** `iod` is the distance between the two eye centres in pixels of the 1024 × 576 frame. It is
  the ruler for every size below. On the five faces it was 86.4, 98.6, 112.8, 60.9 and 112.8 px.

## What you need

- **Machine.** The bulletin was made on 4 virtual CPU cores (Intel Xeon with AMX and AVX-512 BF16),
  15 GB of RAM, no GPU. Making everything again takes about six hours and about 11 GB of downloads.
- **Software.** Python 3.13, 3.12 and 3.11, PyTorch (CPU build), `diffusers`, `transformers`,
  `onnxruntime` 1.31.1, OpenCV 5.0 (headless), `librosa`, `soundfile`, Node with Playwright and its
  headless Chromium, ffmpeg.
- **Separate Python environments.** Six were used. You need fewer, but keep these apart:
  - Image generation (`torch`, `diffusers` 0.42.1, `transformers`). Do not install `timm` or
    `torchvision` here. A mismatched `torchvision` broke the `diffusers` import.
  - ONNX work (`onnxruntime`, `opencv-python-headless`, `numpy`, `pillow`): matting, re-posing, export,
    lip reference, face parsing. The lip reference also needs `librosa`, `scipy` and `soundfile`.
  - One environment per speech package, because their pins conflict. `kokoro` 0.9.4 did not install on
    Python 3.13, so it ran on 3.12. `chatterbox-tts` 0.1.7 ran on Python 3.11 with `torch` 2.6.0. `ptts`
    0.7.0 ran on Python 3.12. The aligner, the speech recogniser and the pitch tracker ran in the
    Python 3.11 environment (`transformers`, `librosa` 0.11.0).
- **One heavy job at a time.** Pose rendering, the lip reference and the movement measurements each
  want all four cores. Run together they took two to three times as long.

## The models

Twelve models did the work. "Weights only" means an ONNX file: weights and a computation graph. Nothing
from the publisher's repository runs as code, so you write the glue yourself: cropping, normalising,
calling the network, turning its output back into a picture or numbers. "Package" means it installs
with its own code and you call a function.

| Model | Get it from | Comes as | Used for | Is its output in the video? |
|---|---|---|---|---|
| Realistic Vision V5.1 (a Stable Diffusion 1.5 fine-tune) with SD VAE ft-MSE | [`SG161222/Realistic_Vision_V5.1_noVAE`](https://huggingface.co/SG161222/Realistic_Vision_V5.1_noVAE): `model_index.json`, `scheduler/`, `text_encoder/`, `tokenizer/`, `unet/`, `vae/`. [`stabilityai/sd-vae-ft-mse`](https://huggingface.co/stabilityai/sd-vae-ft-mse): `config.json`, `diffusion_pytorch_model.safetensors` | Weights for the `diffusers` package, which has the pipeline code. One small image-to-image loop was written by hand (step 1) | Every still: five presenters, six locations | Yes, as the photographs |
| YuNet face detector | [`opencv/face_detection_yunet`](https://huggingface.co/opencv/face_detection_yunet): `face_detection_yunet_2023mar.onnx` | Weights only, but OpenCV has the code: `cv2.FaceDetectorYN` | Eye centres, mouth corners, face box | No. It measures |
| BiRefNet-portrait | [`onnx-community/BiRefNet-portrait-ONNX`](https://huggingface.co/onnx-community/BiRefNet-portrait-ONNX): `onnx/model.onnx` | Weights only. Write the glue (step 2) | The person matte | Yes, as the edge of the cut-out |
| LivePortrait, ONNX export | [`warmshao/FasterLivePortrait`](https://huggingface.co/warmshao/FasterLivePortrait), folder `liveportrait_onnx/`: `appearance_feature_extractor.onnx`, `motion_extractor.onnx`, `stitching.onnx`, `warping_spade.onnx` | Weights only. Write the glue (step 3). Fetch only these files, not the repository's compiled plugins or its wheel | 65 poses of each face | Yes. Mouth and eye poses are shown as pixels. Head and brow poses are used only to measure motion |
| Phonon 31M (English) | PyPI package [`ptts`](https://pypi.org/project/ptts/) 0.7.0. It fetches [`gradium/phonon-31m-en`](https://huggingface.co/gradium/phonon-31m-en) and the voices in [`gradium/phonon-voices`](https://huggingface.co/gradium/phonon-voices) on first use | Package | The voices in the video | Yes, as the sixteen spoken lines |
| Kokoro-82M | PyPI packages [`kokoro`](https://pypi.org/project/kokoro/) 0.9.4 and [`misaki`](https://pypi.org/project/misaki/) 0.9.4, model [`hexgrad/Kokoro-82M`](https://huggingface.co/hexgrad/Kokoro-82M). Also needs the [`spacy/en_core_web_sm`](https://huggingface.co/spacy/en_core_web_sm) wheel | Package | The first voices, replaced. Still used for two things: the phoneme sequence of each line, and testing the aligner | Not as sound. Its phoneme strings are the script the aligner follows |
| Chatterbox | PyPI package [`chatterbox-tts`](https://pypi.org/project/chatterbox-tts/) 0.1.7, model [`ResembleAI/chatterbox`](https://huggingface.co/ResembleAI/chatterbox) | Package | The second voices, replaced | No |
| wav2vec 2.0 phoneme recogniser | [`facebook/wav2vec2-lv-60-espeak-cv-ft`](https://huggingface.co/facebook/wav2vec2-lv-60-espeak-cv-ft): `config.json`, `vocab.json`, `pytorch_model.bin` | Loads with `transformers` (`Wav2Vec2ForCTC`). The forced alignment on top is glue you write (step 4) | When every sound happens in a recording | As timing only |
| Whisper base (English) | [`openai/whisper-base.en`](https://huggingface.co/openai/whisper-base.en) | Loads with the `transformers` speech-recognition pipeline | Checking that each take says the right words | No. It measures |
| Wav2Lip, ONNX export | [`facefusion/models-3.0.0`](https://huggingface.co/facefusion/models-3.0.0): `wav2lip_96.onnx` | Weights only. Write the glue (step 5) | The lip reference: what the mouth should do for each recording | As two curves per line. Never as pixels |
| 2DFAN4 face landmarks, ONNX export | [`facefusion/models-3.0.0`](https://huggingface.co/facefusion/models-3.0.0): `2dfan4.onnx` | Weights only. Write the glue (step 5) | Measuring lips, in Wav2Lip's picture and in the poses | No. It measures |
| BiSeNet face parser, ONNX export | [`facefusion/models-3.0.0`](https://huggingface.co/facefusion/models-3.0.0): `bisenet_resnet_34.onnx` | Weights only. Write the glue (step 7) | Labels for hair, skin, neck and cloth | As three small maps per presenter |

Not a model, but it does model-sized work: OpenCV's DIS optical flow (`cv2.DISOpticalFlow_create`),
used for the motion fields in step 6 and for the movement measurements in step 8.

Also fetched, and not part of the result:

| Item | Source | What happened |
|---|---|---|
| LCM-LoRA for SD 1.5 | `latent-consistency/lcm-lora-sdv1-5`, `pytorch_lora_weights.safetensors` | Speed benchmark only |
| Hyper-SD | `ByteDance/Hyper-SD`, `Hyper-SD15-8steps-lora.safetensors` | Never run |
| MODNet | `Xenova/modnet`, `onnx/model.onnx` | One test matte. Left a halo around hair |
| BiRefNet, PyTorch release | `ZhengPeng7/BiRefNet` | Never ran. It loads Python code from the model repository |
| LivePortrait lip and eye retargeting | `stitching_lip.onnx`, `stitching_eye.onnx` in the same folder | Fetched in case. Keypoint offsets were enough |
| Wav2Lip GAN variant | `wav2lip_gan_96.onnx` in `facefusion/models-3.0.0` | Compared once in the first trial. Every measurement uses `wav2lip_96.onnx` |
| SQUIM quality estimators | `torchaudio` 2.6.0, `SQUIM_SUBJECTIVE` and `SQUIM_OBJECTIVE` | Scored two voice sets the same (4.31 and 4.31). No help in choosing |
| CMU Pronouncing Dictionary | PyPI package `cmudict` 1.1.3 | Timing guessed from spelling, before there were voices. Replaced |

## Order of work

| Step | Needs | Makes |
|---|---|---|
| 1. A photograph of nobody | A text prompt per presenter | `frame.png` (1024 × 576), five landmark points, `iod` |
| 2. Cut the person out | `frame.png`. The final cut-out and plate also need the base frame from step 3 | `alpha.png`, the cut-out, the plate |
| 3. Re-pose the face 65 times | `frame.png`, landmarks | 65 renders, a mouth mask, an eye mask, the base frame |
| 4. Record a voice and time every sound | The script | Per line: a levelled recording, phoneme times, word times, a pitch contour |
| 5. Ask a lip-sync network, then measure its answer | Base frame, mouth mask, poses, recordings, phoneme times | Per line: a jaw curve and a lip-shape curve, 50 values a second |
| 6. Turn two pictures into motion | Neutral render, six posed renders, `alpha.png` | Six displacement fields per face |
| 7. Find the body and the loose hair | `frame.png`, `alpha.png`, landmarks | Three maps per presenter and four torso measurements |
| 8. Composite every frame, then record it | All of the above | Frames, then the MP4 |

## Step 1. A photograph of nobody

**With:** Realistic Vision V5.1; SD VAE ft-MSE; YuNet

### In

One text prompt per presenter: who they are, what they wear, where they are. Put this fragment in every
presenter prompt: `facing the camera, looking straight into the camera, lips closed`. Example:
`RAW photo, television news anchor, woman in her mid 30s with long dark brown hair, red blazer, sitting
at a news desk, facing the camera, looking straight into the camera, lips closed, calm expression,
medium close-up, modern TV news studio, dark blue video walls blurred in background, broadcast footage,
studio lighting`.

### Do

1. Load the checkpoint with `StableDiffusionPipeline`, with its VAE replaced by `sd-vae-ft-mse` and the
   safety checker off. Run the UNet and the text encoder in `bfloat16` and keep the VAE in `float32`.
2. Use the DPM-Solver++ multistep sampler, order 2, Karras sigmas. Set `algorithm_type="dpmsolver++"`
   and `solver_order=2` yourself. The checkpoint ships a DEIS sampler config, and without this the first
   run fails with `final_sigmas_type zero is not supported for algorithm_type deis`.
3. Generate four candidates per presenter at 768 × 432, 25 steps, guidance 5.0, seeds 21 to 24. About
   54 seconds an image.
4. Put the candidates on a contact sheet and pick one. Reject: side views, a head that looks down or
   away, a tilted head, two people, the same face repeated, a hand beside the head, objects crossing
   the outline.
5. Enlarge the pick with Lanczos to 1024 × 576. Then run image-to-image with the same prompt at strength
   0.3 (6 of 20 steps), guidance 5, seed 1. About 50 seconds.
6. Run YuNet on the result. Keep the eye centres, the mouth corners and the face box of the largest
   face. Compute `iod`.
7. Refine the face. Crop a square of side 3.6 × `iod` (rounded to a multiple of 8), centred 0.45 × `iod`
   below the eye line. Scale it to 512 × 512. Run image-to-image at strength 0.35 (7 of 20 steps),
   guidance 5, seed 2, with the prompt `RAW photo, close-up portrait of <description>, lips closed,
   looking at the camera, detailed skin texture, sharp focus`. Paste it back through a feathered ellipse
   (radii 212 × 232 px of the 512 crop, blurred 16 px). Save as `frame.png`. The bulletin also passed
   the refined crop once through the VAE before pasting it. That served the inpainted mouths that were
   later dropped, so you can leave it out.
8. The library's image-to-image pipelines assume one number format for the whole model. With a
   `bfloat16` UNet and a `float32` VAE they do not fit, so write the loop yourself. It is short. Use
   trailing timesteps `round(linspace(1000, 0, steps + 1))[:-1] - 1`, keep the last
   `round(steps × strength)` of them, add noise to the encoded image at the first one, apply
   classifier-free guidance, and take plain DDIM steps with no added noise.

The location stills are made the same way: one seed each, then the enlarging pass.

### Out

`frame.png` per presenter. A small JSON file with the five landmark points, the face box and `iod`.
One 1024 × 576 still per location.

### Check

- YuNet finds a face in `frame.png` (score threshold 0.5) and the largest one is your presenter.
  Print `iod`. The smallest face used here had 60.9 px between the eyes. Nothing smaller was tried.
- Look at the picture. It should show one person, frontal, eyes on the camera, lips closed, with a clean
  outline against the background.
- Read the log for a truncation warning. The text encoder reads 77 tokens. Two prompts here ran over and
  silently lost their last words.
- Expect mismatches with the prompt. The reporter never got the microphone he was asked to hold.

### Settings that worked

| Setting | Value | What it means |
|---|---|---|
| Frame | 1024 × 576 | Every later picture, mask, field and map is in this frame |
| First size | 768 × 432 | Candidates are cheap at this size: about a minute each |
| Sampler | DPM-Solver++ multistep, order 2, Karras sigmas, 25 steps, guidance 5.0 | Chosen over a 6-step LCM shortcut after a benchmark: 54 s against 22 s, kept for quality |
| Enlarge | strength 0.3, 20 steps, guidance 5.0, seed 1 | Adds detail without changing the person |
| Face refine | crop 3.6 × `iod`, 0.45 × `iod` below the eye line, strength 0.35, seed 2 | A small face gets redrawn at 512 px |
| Negative prompt | `cartoon, illustration, painting, drawing, 3d render, cgi, anime, doll, plastic skin, airbrushed, deformed, disfigured, extra fingers, bad hands, text, watermark, logo, caption, letters, subtitles, blurry face, cross-eyed, side view, profile, looking away, tilted head, nsfw, nude` | The last four pose terms were added after many of the first twenty candidates faced away |

## Step 2. Cut the person out

**With:** BiRefNet-portrait (ONNX, weights only)

### In

`frame.png`. For the final cut-out and plate, the base frame from step 3.

### Do

1. Write the matting glue. Resize the picture to 1024 × 1024 (bilinear). Scale to 0 to 1. Normalise
   with mean (0.485, 0.456, 0.406) and standard deviation (0.229, 0.224, 0.225). Run the network. Take
   the first channel of its last output. If the values fall outside 0 to 1, apply a sigmoid. Resize back
   to the frame. Save as `alpha.png`. About 40 seconds an image.
2. Run one image per process, with onnxruntime's CPU memory arena switched off
   (`enable_cpu_mem_arena = False`). A second image in the same process was killed for memory, twice.
3. Make the cut-out from the base frame of step 3, so that it agrees with the pose renders:
   - Tighten the matte: `alpha2 = clip((alpha - 0.25) / 0.7, 0, 1)`.
   - Replace the edge colours. Inpaint (OpenCV Telea, radius 4) every pixel where `alpha2 <= 0.98`,
     so that colours grow outwards from the solid interior. This removes the fringe of the old
     background.
   - Store colour plus `alpha2`. The bulletin used WebP at quality 88.
4. Make the plate, the photograph with the person painted out:
   - The hole is every pixel where alpha is above 6 of 255, grown by an 11 × 11 ellipse. That keeps
     the real background up to five pixels from the outline.
   - Fill the hole with Telea inpainting, radius 7.
   - Soften the fill with depth into the hole. Blend towards a Gaussian blur of sigma 4 with weight
     `clip((depth - 2) / 10, 0, 1)`. Then blend towards sigma 12 with weight
     `clip((depth - 14) / 26, 0, 1)`.

### Out

`alpha.png`, the cut-out (colour and transparency), the plate.

### Check

- Lay the cut-out over flat green and over a dark picture. Look at the hair. There should be no pale
  halo and no bright fringe of the old background.
- Shift the cut-out 16 px sideways over the plate and look along the outline. The strip of plate that
  shows should read as out-of-focus background. It must not show a soft ghost of the head or a hard edge
  that follows the outline.
- The matte should be white on the person, black elsewhere, and grey only in a thin band at the hair.

### Settings that worked

| Setting | Value | What it means |
|---|---|---|
| Matte input | 1024 × 1024 | The size this export of the network expects |
| Matte tighten | subtract 0.25, divide by 0.7 | Drops the faint outer haze and makes the interior fully solid |
| Edge colours | Telea radius 4 where `alpha2 <= 0.98` | Edge pixels take the person's colours, not the background's |
| Plate safety margin | 5 px (an 11 × 11 ellipse) | Real background is kept right up to the person, because the body later moves 10 to 20 px |
| Plate softening | sigma 4 from 2 px in, sigma 12 from 14 px in | The strip a moving figure uncovers looks like blurred background, not streaks |

## Step 3. Re-pose the face 65 times

**With:** LivePortrait (ONNX export, weights only)

### In

`frame.png` and the landmark points.

### Do

Write the glue first. The model encodes a portrait once, describes the face by 21 keypoints in 3-D,
and redraws the portrait for any new keypoints.

1. **Crop.** A square of side 5.06 × `iod`. Its centre is 0.07 × `iod` from the midpoint of the eyes
   towards the mouth. Rotate it so that the line from the eyes to the mouth is vertical. Resample to
   512 × 512, and to 256 × 256 for the two encoders. Keep the transform: every render goes back into
   the frame with it.
2. **Encode.** `appearance_feature_extractor.onnx` (input `img`, 1×3×256×256, values 0 to 1) gives the
   appearance volume, 1×32×16×64×64. `motion_extractor.onnx` (same input) gives `pitch`, `yaw`, `roll`
   (66 bins each), `t` (3), `exp` (63), `scale` (1) and `kp` (63). An angle in degrees is
   `sum(softmax(bins) × index) × 3 - 97.5`.
3. **Keypoints.** `x = scale × (kp · R + exp)`, then add the x and y of `t`. `R` is the transpose of
   `Rz · Ry · Rx` built from pitch, yaw and roll. The source keypoints `x_s` use the values as read.
4. **Pose.** Add offsets to `exp` (table below). For head poses add degrees to yaw or pitch. Compute the
   driving keypoints `x_d` the same way.
5. **Stitch.** `stitching.onnx` (input `input`: `x_s` and `x_d` flattened, 126 numbers) returns 65
   numbers. Add the first 63 to `x_d`. Add the last two to the x and y of every keypoint.
6. **Render.** `warping_spade.onnx` (inputs `feature_3d`, `kp_driving`, `kp_source`) returns the image,
   1×3×512×512, values 0 to 1. About 6.5 seconds a render.
7. Leave out the head-pitch correction that the model's editing tools apply (they tilt the head back
   by 0.05° per jaw unit). Only the lower face is pasted into a fixed photograph here, so the upper
   face must stay put.

Offsets added to `exp`, per unit of each control. `[k]` is the keypoint, 0 to 20. They follow the
sliders of the model's own editing tools. They were written from memory and then confirmed by
rendering, so confirm them the same way.

| Control | Offsets per unit | Values used |
|---|---|---|
| `aaa`, jaw opens | [19].y +0.001, [19].z +0.0001, [17].y −0.0001 | −8 (lips pressed) to 60, or 90 on one face |
| `eee`, lips spread | [20].z −0.001, [20].y −0.001, [14].y −0.001 | 3.5 and 7 |
| `woo`, lips round and come forward | [14].y +0.001, [3].y −0.0005, [7].y −0.0005, [17].z −0.0005 | 2 to 4 at rest, up to 15 |
| `smile` | [20].y −0.01, [14].y −0.02, [17].y +0.0065, [17].z +0.003, [13].y and [16].y −0.00275, [3].y and [7].y −0.0035 | −0.25 to −0.10 at rest, 0.38 for the broad smile |
| `blink` | [11].y −0.001, [13].y +0.0003, [15].y −0.001, [16].y +0.0003 | −9 half closed, −17 closed |
| `px`, eyes sideways | [11].x and [15].x: +0.0007 and +0.001 per unit when positive, +0.001 and +0.0007 when negative | −7 and 7 |
| `py`, eyes up or down | [11].y −0.001, [15].y −0.001, and the brow control is reduced by `py / 2` | −7 (down) |
| `brow`, positive | [1].y +0.001, [2].y −0.001 | 13 |
| `brow`, negative | [1].x −0.001, [2].x +0.001, [1].y +0.0003, [2].y −0.0003 | −12 |
| head | degrees added to yaw or pitch | yaw ±6.0, pitch ±5.0 |

Now render the pose set. Every photograph here smiles with closed lips. Poses built on that smile make
the presenter talk through a held smile, lips stretched thin. So the neutral pose is a **relaxed
mouth**: some of the smile taken out and the lips let a little forward. All speech poses are built on
it.

| Poses | Count | Settings, on top of the relaxed mouth unless noted |
|---|---|---|
| Relaxed mouth, the neutral pose | 1 | the face's rest settings only |
| The photograph's own expression | 1 | no offsets at all |
| Jaw, relaxed lips | 11 | `aaa` = 4, 8, 12, 16, 21, 26, 32, 38, 45, 52, 60 |
| Lips half spread, fully spread | 8 + 8 | `eee` 3.5 and 7, each at `aaa` = 0, 5, 10, 16, 22, 30, 38, 48. Smile taken out, lips not pushed forward |
| Lips half rounded, fully rounded | 8 + 8 | `woo` = rest + 6 and rest + 12 (at most 15), at the same eight jaw values. Smile taken out |
| Smiling broadly | 8 | `smile` 0.38 with no rest settings, at the same eight jaw values |
| Lips pressed, for m, b, p | 1 | `aaa` −8 |
| Lids | 2 | `blink` −9 and −17 |
| Eyes left, right, down | 3 | `px` −7, `px` 7, `py` −7 |
| Head turned, both ways | 2 | yaw +6.0 and −6.0 |
| Head nodded, both ways | 2 | pitch +5.0 and −5.0 |
| Brows raised, lowered | 2 | `brow` 13 and −12 |
| **Total** | **65** | 7 to 14 minutes a face |

Rest settings per face. To choose them, render a small grid first: rows are `smile` 0, −0.15, −0.3,
and −0.2 with `woo` 3; columns are jaw 0, 16, 32, 48. Pick the row with fuller lips whose corners do
not turn down.

| Face | `smile` at rest (how far the smile is taken out) | `woo` at rest (lips let forward) | Jaw gain |
|---|---|---|---|
| Paige | −0.10 | 2 | 1 |
| Cy | −0.20 | 3 | 1 |
| Dee | −0.20 | 3 | 1 |
| Sunny | −0.20 | 3 | 1 |
| Mel | −0.25 | 4 | 1.5 |

Jaw gain multiplies every `aaa` value for that face. Mel's mouth opened about half as far as the others
at the same setting, so his jaw list runs to 90 model units. At 90 he is still a believable open mouth.
At 120 he shouts.

Then cut the regions:

8. Put each render back into the frame with the crop transform. If the crop shrinks by more than 8 %,
   reduce it with area averaging first.
9. **Mouth mask.** Over the 53 mouth poses, take the largest difference from the neutral render at each
   pixel (mean of the three channels). Keep pixels above 5 on a 0 to 255 scale. Keep only those inside
   an ellipse centred 1.25 × `iod` below the eye line with radii 1.35 × `iod` by 1.2 × `iod`, and at
   least 0.34 × `iod` below the eye line. Grow by 0.11 × `iod`, close the holes, and feather with a
   Gaussian of 0.05 × `iod`.
10. **Eye mask.** The same from six eye poses: lids half and fully closed, eyes left, right and down,
    and the eyes of the closed-mouth broad smile. The ellipse is centred 0.05 × `iod` below the eye line
    with radii 1.2 × `iod` by 0.25 × `iod`. Grow by 0.06 × `iod`, feather 0.035 × `iod`. It must stop
    below the brows.
11. **Base frame.** Inside both masks, replace the photograph by the neutral render. Now the still and
    every pose come from the same renderer, so a blend cannot show a seam.
12. **Store.** Crop every pose to its mask's bounding box and store it opaque. Store each mask once.

### Out

Per face: 65 renders at 512 × 512, the crop transform, the two jaw lists, the base frame, one mouth
mask with 53 mouth poses, one eye mask with 6 eye poses.

### Check

- Render with no offsets and compare with the source crop. On the first face the mean absolute
  difference over the face was 5.57 on a 0 to 255 scale, and the render looked a touch softer.
- Render jaw 60 and compare the eyes and forehead with the neutral render. Without the pitch correction
  the change was 1.10. With it, 19.71. If your upper face moves, the correction is still on.
- Make a contact sheet of the poses and look at it. It should show the same person in every tile. The
  jaw row opens step by step. The pressed pose has the lips meeting. "ee" pulls the corners back
  without a grimace. "oo" is round. Half-closed lids are half closed, and closed lids are not squeezed.
  The head visibly turns each way.
- Print the mask sizes. Mouth regions here were 168 to 314 px wide and 152 to 283 px tall. Eye regions
  were 134 to 273 px wide and 50 to 92 px tall. A mask that reaches into the hair or shoulders, or has
  stray blobs, is missing the ellipse.
- Overlay the masks on the face. The eye mask must not touch the brows.

### Settings that worked

| Setting | Value | What it means |
|---|---|---|
| Crop | 5.06 × `iod`, lifted 0.07 × `iod` | Approximates the model's usual framing of a face |
| Jaw list, relaxed row | 0, 4, 8, 12, 16, 21, 26, 32, 38, 45, 52, 60 | Steps are close enough that a blend of two neighbours reads as movement. Value 0 is the base frame itself |
| Jaw list, shaped rows | 0, 5, 10, 16, 22, 30, 38, 48 | The same idea for the spread, rounded and smiling rows |
| Broad smile | `smile` 0.38 | Measured against the photographs' own expression. It is 1 on the smile scale of step 8 |
| Spread | 7 at most | 10 with an open jaw is a grimace |
| Closed lids | −17 | −20 is a squeeze, −10 is half closed |
| Lips pressed | `aaa` −8 | Right for m, b and p |
| Difference threshold | 5 of 255 | What counts as "this pixel moves" |

## Step 4. Record a voice and time every sound

**With:** Phonon 31M (package `ptts`); Kokoro-82M (package `kokoro`); wav2vec 2.0 phoneme recogniser; Whisper base

### In

The script: for each line, who speaks, the text as shown in captions, and the text as spoken.

### Do

1. **Respell for the speech model.** Write names and abbreviations the way they should sound. Examples
   that were needed: "Sy DeCar", "A.I.", "U.S. east one", "D.N.S.", "five oh threes", "Why A Mel",
   "Yammel", "fin ops", "auto scaler", "re-tries", "ee-gress", "Dooty", "Tchilling". Keep the caption
   text separate.
2. **Record takes.** Three takes of each line, seed `100 × line + take`. With `ptts`:
   `TTS(lang="en")`, then `synth(text, voice=..., seed=...)`. The cast was chosen from the publisher's
   written descriptions of its named voices: Harper, Miles, Easton, Juniper, Master Aldric. Write the
   takes as 32-bit float WAV. One take peaked at 1.05 and clipped when written as 16-bit. Phonon speaks
   about ten times faster than real time on this CPU.
3. **Check the words.** Transcribe every take with Whisper. Lower-case both texts, strip punctuation,
   and map the recogniser's spellings of numbers and invented names onto the script's. Count wrong
   words by edit distance.
4. **Get the phoneme sequence of each line**, with stress marks. Here Kokoro had read the same lines
   first, and its pipeline returns the phonemes it speaks, so those strings were used. Any
   text-to-phoneme tool will do. The engine in step 8 needs to know where m, b and p are, where the
   stressed vowels are, and where the pauses are.
5. **Forced alignment.** Resample the take to 16 kHz. The recogniser gives a probability for each of its
   symbols every 20 ms. Its alphabet is finer than the script's, so list, for each script phoneme, the
   recogniser symbols that count as it, and add their probabilities. Examples: the vowel of "father"
   matches `ɑː ɑ ɑːɹ ɒ a aː`; r matches `ɹ ɚ ɑːɹ ɔːɹ ɛɹ ɪɹ ʊɹ ɜː oːɹ aɪɚ`; a flapped t matches
   `ɾ t d`. Then run a Viterbi search over the sequence blank, phoneme 1, blank, phoneme 2, and so on,
   letting two different phonemes touch. Place the boundary between two neighbours halfway between two
   estimates: the frame where the second becomes likelier than the first, and the midpoint between
   their certain frames. Time in seconds is `frame × 0.02 + 0.0025`.
6. **Clean up.** Silence inside a phoneme's stretch is a pause, not sound. Pull the edges in to where
   there is signal (quiet means under 3.5 % of the 95th-percentile level, in 10 ms frames). A gap of
   0.12 s or more that the script did not ask for becomes a pause of its own. A caption word appears
   with the first sound of its first spoken word.
7. **Choose the take** with the fewest wrong words. Break ties by the take whose worst word matches its
   phonemes best.
8. **Level.** Trim to 80 ms before the first sound and 180 ms after the last. Fade 15 ms in and 30 ms
   out. Measure loudness with ffmpeg's `ebur128` filter and apply a plain gain to reach −19 LUFS. Round
   off the rare peak above 0.6 with a soft knee, `0.6 + 0.29 × tanh((x - 0.6) / 0.29)`, so nothing
   exceeds 0.89. Keep 24 kHz mono.
9. **Pitch.** Track it with pYIN, 60 to 440 Hz, one value every 10 ms. Keep a value only inside a
   voiced phoneme, give or take 20 ms. Drop a value more than 10 semitones from the speaker's median,
   and one more than 4 semitones from the median of its neighbours. Store the median of each 40 ms in
   half semitones about the speaker's median.
10. **The 70 ms correction.** If you take timing from a speech model's own report, test it against the
    audio first. Kokoro reports how many 25 ms frames each phoneme lasts. Adding those up gives each
    phoneme's start, and that sum runs late. Against the aligner, on Kokoro's own recordings, the
    model's phoneme starts were 73 ms late and its phoneme centres 62 ms late (median of 844 phonemes).
    The sound in each file also starts before the "first phoneme" time. The fix is a constant: move
    that model's phoneme times 0.07 s earlier. Times that come from the aligner get no shift. The
    voices in the video were timed by the aligner, so their shift is 0.

### Out

Per line: the levelled recording, a list of phonemes with start, length and loudness, caption words
with start times, and a pitch string.

### Check

- The Whisper transcript of every chosen take equals the script after normalising: 0 wrong words. Then
  transcribe the finished sound track too. Two mispronounced words here were only caught there.
- Test the aligner on recordings whose timing is known. Here that test printed, for phoneme starts:
  aligner minus model −73 ms, scatter around that median 20 ms, 90 % within 55 ms. For centres: −62 ms,
  median 15 ms, 90 % within 47 ms. The constant is the model's lateness. The scatter is the aligner's
  own error and should stay under about one video frame.
- Slide the mouth-opening curve of the finished animation against the loudness of the recording, in
  10 ms steps up to 150 ms each way. With the late timing the best fit had the mouth 41 ms behind the
  voice. After the correction the mouth led by 14 ms, as real lips do. A mouth two frames behind its
  voice reads as dubbed, and no still frame shows it.
- Every line has the same loudness and no sample above 0.89.
- Plot one pitch string. Runs of exactly +12 semitones in hiss or silence, or a span of 27 semitones in
  one line, mean the three pitch filters are missing.

### Settings that worked

| Setting | Value | What it means |
|---|---|---|
| Takes | 3 per line, seed `100 × line + take` | Speech models slip: an added word, a dropped one, a name read another way |
| Timing shift, first speech model only | −0.07 s | Its reported sound times run about three of its 25 ms frames late against its own audio |
| Aligner hop | 0.02 s | The recogniser hears in 25 ms windows, 20 ms apart |
| Unscripted pause | 0.12 s or more | Shorter gaps stay part of the neighbouring sounds |
| Trim | 0.08 s before, 0.18 s after | Room for the fades without cutting a sound |
| Loudness | −19 LUFS, soft knee at 0.6 | Scaling whole lines down to fit their peaks left one presenter 2 dB quieter |
| Pitch range | 60 to 440 Hz, frame 1536 and hop 240 samples at 24 kHz | Covers all five voices |
| Pitch code | one character per 40 ms: `chr(78 + round(2 × semitones))`, limited to ±24, `-` where unvoiced | Brows and head follow this contour |

## Step 5. Ask a lip-sync network, then measure its answer

**With:** Wav2Lip (ONNX, weights only); 2DFAN4 (ONNX, weights only)

### In

The base frame, the mouth mask and the pose renders (step 3). The levelled recordings and phoneme times
(step 4). The face box from YuNet.

### Do

Hand-written rules for which sound opens the mouth how far were tried twice and looked wrong. So a
network trained on real talking faces is asked instead. Its picture is 96 px across and soft, so it is
measured and never shown.

1. **Wav2Lip glue, sound.** Resample to 16 kHz. Pre-emphasis 0.97. STFT with `n_fft` 800, hop 200 (80
   frames a second), window 800. 80 mel bands from 55 to 7600 Hz. Convert to decibels,
   `20 × log10(max(1e-5, S)) - 20`, then scale with `clip(8 × (dB + 100) / 100 - 4, -4, 4)`.
2. **Wav2Lip glue, face.** Take the face box, with its height stretched by 4 % for chin room. Resize it
   to 96 × 96. The input `target` has six channels: the face with its lower half blacked out, then the
   whole face, values 0 to 1. The input `source` is 16 mel frames (0.2 s) shaped 1×80×16. The output is
   a 96 × 96 face. Paste it back into the frame at the box.
3. **Windowing.** For picture `i` at 50 pictures a second, start the window at mel frame
   `round(i × 80 / 50) - 6`. That is 75 ms before the picture's own time. The stock code starts the
   window at the picture's time, and then every mouth is about a tenth of a second early.
4. **Landmark glue.** Scale the face box so that its longer side is 195 px, centred in a 256 × 256
   crop, values 0 to 1. 2DFAN4 returns 68 points on a 64-unit grid. Multiply by 4 and map back to the
   frame.
5. **Measure** three numbers per picture, in units of `iod`: the opening (points 62 to 66, the inner
   lips), the outer lip height (points 51 to 57) and the mouth width (points 48 to 54).
6. **Calibrate each face.** Make the same measurement on the base frame and on every mouth pose laid
   into the base frame through the mouth mask. First pass each through the same keyhole: shrink the
   face box to 96 × 96 and enlarge it again. Now you know which jaw value shows which opening on that
   face.
7. **Fix the timing.** A "p" has a stretch of silence while the lips are closed. Find each p with a
   clear silence: at least 30 ms that is 28 dB or more below the recording's 90th-percentile level.
   Within 70 ms either side of the middle of that silence, find where the reference's opening is
   smallest. Take the median offset over all such sounds and move the reference by it.
8. **Put the faces on a common footing.** For each presenter, over all samples inside speech sounds:
   "shut" is the 12th percentile of the opening, and the loud end is the 90th percentile minus shut.
   The gain is `clip(0.155 / loud_end, 1.0, 2.2)`.
9. **Translate.** Target opening = the face's own shut measurement + `max(0, reading - shut) × gain`.
   Look that opening up in the face's calibration to get a jaw value. Divide by 46 for the engine's
   opening. Above 0.9, halve the excess. For the lip shape, first subtract from the measured width the
   difference between the reference's width in long pauses and the face's own width at rest. Then
   compare it with the widths of the face's relaxed, fully spread and fully rounded rows at that jaw
   value: −1 is rounded, +1 is spread. Smooth both with a median of three and a 1-2-1 filter.
10. Store the two curves per line, one value per 1/50 s.

It is slow: about 14 minutes on four cores for the bulletin's 4,320 samples.

### Out

A calibration file (opening and width of every mouth pose of every face). Per line, a jaw curve from
−0.12 to 1.3 and a lip-shape curve from −1 to 1, at 50 values a second.

### Check

- Print the calibration. The opening must rise with the jaw value on every face. Opening above shut,
  in units of `iod`, at jaw 16, 32 and 60:

| Face | Jaw 16 | Jaw 32 | Jaw 60 | Mouth width at rest |
|---|---|---|---|---|
| Paige | 0.066 | 0.129 | 0.218 | 0.752 |
| Cy | 0.067 | 0.133 | 0.247 | 0.809 |
| Dee | 0.058 | 0.122 | 0.233 | 0.767 |
| Sunny | 0.061 | 0.120 | 0.222 | 0.812 |
| Mel, with jaw gain 1.5 | 0.039 | 0.139 | 0.288 | 0.739 |

- Print the timing offset. Here the reference's lips were tightest 35 ms before the middle of the
  silence of a p (17 sounds, half of them between 48 and 18 ms early). It was moved 40 ms later, the
  nearest whole sample.
- Average the reference's opening by kind of sound. Here: open vowels 0.54, mid vowels 0.39, close
  vowels 0.41, s z t d n 0.44, w and r 0.11 with rounded lips, m b p 0.04, f v 0.03. Lip sounds must
  come out near shut.
- Print each line's typical and widest opening after translation. Here: typical 0.38 to 0.58, widest
  0.83 to 1.10. If one presenter's mouth is shut for a third of their speech, "shut" was taken from the
  wrong place.
- Draw the finished mouth frame by frame, every 1/20 s, each frame labelled with the sound being
  made. It should be shut on m, b and p, round on w and "oo", and open on "ah".

### Settings that worked

| Setting | Value | What it means |
|---|---|---|
| Rate | 50 measurements a second | 25 was used for voice sets that mattered less; it halves the work |
| Window start | 6 mel frames (75 ms) early | Removes most of the stock code's lead |
| Remaining shift | measured: 35 ms early, so moved 40 ms later; limited to ±80 ms | What is left after the window change. Measure it on your own recordings |
| "Shut" | 12th percentile of the opening while speaking | That is where the m, b and p readings lie. Pauses do not work: the network leaves the lips apart there |
| Loud end | 90th percentile above shut | The opening reached in clear, loud syllables |
| Common level | 0.155 × `iod` | Every presenter's loud end is brought to this: about a centimetre between the lips. A judgement, not a measurement |
| Gain limits | 1.0 to 2.2 | Nobody is scaled down. A timid reading is raised at most 2.2 times |
| Gains found | Paige 1.36, Cy 1.00, Dee 1.98, Sunny 2.05, Mel 1.33 | The network opens some faces far more timidly than others, whatever the voice |
| Jaw scale | 46 jaw units = an opening of 1 | The widest pose is 60, so the curve can reach 1.3 |

## Step 6. Turn two pictures into motion

**With:** OpenCV DIS optical flow (no network)

### In

The neutral render and six posed renders in frame coordinates: head turned each way, nodded each way,
brows raised, brows lowered. `alpha.png`.

### Do

Cross-fading between a head facing ahead and a head turned shows two faint heads. Optical flow between
the two renders says where each point of the face goes instead.

1. Compute dense optical flow (DIS, medium preset) from the neutral render to each posed render, in
   grey levels.
2. Blur each field: Gaussian of 0.06 × `iod` for the four head fields, 0.03 × `iod` for the two brow
   fields.
3. Weight the head fields so they fade to nothing before the edge of the model's crop and outside the
   person. Weight = (inside the crop, eroded with a square of side 0.25 × `iod`) × (matte above 0.1,
   grown with a 9 × 9 square), blurred by 0.12 × `iod`.
4. Weight the brow fields with a band. It starts 0.13 × `iod` above the eye line, reaches full strength
   0.12 × `iod` higher, and fades sideways and towards the hairline.
5. Name the head fields by what they do on screen: which one carries the nose right, which one down.
   Do not trust the sign of the angle.
6. Sample all six on a grid with a step of `clip(round(0.11 × iod), 6, 14)` px. Set the border of the
   grid to zero. Store each field as signed bytes with its own scale, `127 / largest value`.

### Out

Six displacement fields per face: right, left, down, up, brows up, brows down. Here the grids were
49 × 47 points at 10 px, 52 × 44 at 11, 53 × 49 at 12, 49 × 48 at 7 and 55 × 45 at 12, in 35 to 40 KB a
face.

### Check

- Move the neutral render by the turn field and compare it with the real turned render. Here the mean
  difference left over was 2.6 to 5.0 grey levels, against 17 to 23 between the two renders.
- Read the field at the nose. At 6° it moved 11 px on the smallest face and 21 px on the largest. The
  ears and hairline should barely move. Raised brows moved 2.8 to 7.2 px.
- Draw the field as arrows over the face. They should all point one way, be longest at the nose, and
  vanish at the shoulders.

### Settings that worked

| Setting | Value | What it means |
|---|---|---|
| Head poses | yaw ±6°, pitch ±5° | The largest turn the fields are measured at. The bulletin stays within about 3.7° |
| Grid step | about a ninth of `iod`, between 6 and 14 px | Fine enough for the nose, small enough to store |
| Field storage | signed byte with a scale per field | A first version stored eighths of a pixel and silently clipped at 15.9 px |
| Brow band | from 0.13 × `iod` above the eye line | Brows move; the eyes under them are left alone |

## Step 7. Find the body and the loose hair

**With:** BiSeNet face parser (ONNX, weights only)

### In

`frame.png`, `alpha.png`, the landmark points.

### Do

1. Write the glue. A 512 × 512 crop, normalised with the same mean and standard deviation as in step 2,
   goes into input `input`. The output has 19 classes per pixel; take the largest. The labels used:
   1 to 13 are the face, 14 and 15 the neck, 16 cloth, 17 hair.
2. Run it twice per presenter. The network was trained on tight face crops, so use a tight crop of side
   4.0 × `iod`, and a wide crop of the whole frame height (side at least 6.0 × `iod`). The wide one is
   what finds long hair lying on the chest. Trust the tight labels except along the crop's border.
3. Find the chin: the lowest face pixel within 0.35 × `iod` of the face's centre column. Find where the
   clothes begin beside the neck: the 4th percentile of the heights of cloth pixels within 1.8 × `iod`
   of the centre. Do not look in the middle column. With an open neckline the cloth there starts a
   hand's width below the shoulders.
4. **Body map**, 0 on the head and 1 on the torso. Face skin is 0. Cloth is 1. Everything else goes by
   height: a smooth ramp from 0.05 × `iod` above the chin or collar, whichever is higher, to
   0.35 × `iod` below the lower of the two. Blur by 0.12 × `iod` inside the matte.
5. **Hair map**, 0 on the scalp and 1 where hair is loose. For hair pixels take the larger of two
   values: "hang", a ramp from 0.25 to 1.75 × `iod` below the eye line, and "puff", 0.45 × how far the
   pixel stands outside a skull ellipse (full at 0.45 × `iod`). Multiply by `1 - 0.45 × body ramp`, so
   that hair lying on the shoulders swings about half as far. Blur by 0.07 × `iod`.
6. **Wind map**, only for a presenter outdoors. For hair pixels: more the further from the face (full
   at 0.5 × `iod`, never under 0.15), and most within 0.3 × `iod` of the outline. Blur by 0.06 × `iod`.
7. Note four torso numbers: the shoulder line (0.5 × `iod` below where the clothes begin), the torso's
   middle, half the shoulder width, and the chin.
8. Sample each map every 8 px: 129 × 73 values, one byte each.

### Out

Per presenter: a body map, a hair map, a wind map where needed, and the four torso numbers.

### Check

- Draw the maps over the photograph: torso green, loose hair red, wind blue. The clothes should be
  green, the face clear, the neck graded. Red should appear only where hair hangs below the ears or
  stands away from the skull. Wind should sit on the outline of the hair.
- Print the hair share. Here hair was 45 % of the first anchor's cut-out and more than half of it was
  loose; a bob was loose in its lower quarter; short hair and a bald head gave none.
- Draw the shoulder line. It should cross the top of the shoulders, not the chest.

### Settings that worked

| Setting | Value | What it means |
|---|---|---|
| Map grid | 8 px, 129 × 73 values | Movement is smooth, so a coarse map is enough |
| Two crops | 4.0 × `iod` and the frame height | One crop size cannot label both the face and hair on the chest |
| Hair on the shoulders | swings 0.55 as far | It bounced as freely as hair in the air before this |
| Wind floor | 0.15 | Even sheltered hair of an outdoor presenter stirs a little |

## Step 8. Composite every frame, then record it

**With:** no model; plain JavaScript; Canvas 2D and one small WebGL mesh; headless Chromium; ffmpeg

### In

Everything from steps 1 to 7, bundled into one page as `data:` URIs: per presenter a plate, a cut-out,
two masks, 53 mouth poses, 6 eye poses, six motion fields and the maps; and per line the recording, its
timing, its pitch and its two lip curves. For the bulletin that came to 321 small images and sixteen
recordings.

### Do

Write the animation as a function of time. `draw(t)` paints the frame for show time `t` and keeps no
state between frames, so any moment can be rendered directly. The one exception is the hair's spring,
which starts afresh whenever the clock jumps.

**One presenter, one frame:**

1. Work out the face for this moment: opening `o`, lip shape `s`, smile `g`, blink, gaze, brows, head
   turn, nod and tilt. Then the body: shift, tilt, lean, shoulder turn, breath, hair.
2. **Mouth.** `o × 46` picks two neighbouring jaw steps. `s` picks the relaxed row and the half or full
   row beside it: spread when `s` is positive, rounded when negative. So at most four poses are
   blended, plus the smile row. Below 0, blend in the pressed-lips pose, at full weight at −0.12. Start
   from the base frame's own pixels in a small canvas, add each pose with the opacity that leaves the
   exact weighted mix, cut the result to the mouth mask, and lay it on the cut-out.
3. **Eyes.** The same with the eye poses: gaze, half and fully closed lids, and the smiling eyes.
4. **Mesh.** Upload the composed cut-out as a texture. Draw it on a mesh whose points sit on the
   motion-field grid, continued over the whole frame. Each point carries the six displacements, a tilt
   weight and the three map values. The vertex shader adds: the weighted sum of the six fields; a tilt
   about the neck; the body's shift, tilt and lean; the breath lift; the shoulder turn; the hair's
   spring; the wind. Then it applies the pinning.
5. **Layers.** Draw the plate. Draw anything that belongs between background and person. Draw the
   warped cut-out, scaled 1.2 % to 3.4 % more than the plate about the face. Add the camera move, film
   grain, a vignette, then captions and graphics on top.

**What drives it:**

- **Mouth.** The two curves from step 5. In a pause the mouth comes to rest whatever the reference
  drew. A short press is added in each m, b and p so the lips truly meet.
- **Smile.** A scale of three points: 0 is the relaxed mouth, used while speaking; 0.5 is the
  photograph's own expression, worn while listening; 1 is the broad smile, used where the script asks
  for one.
- **Brows and nods.** Each stressed vowel gets a weight from its loudness, its pitch and its length.
  The strongest syllables carry a nod. The strongest high-pitched ones lift the brows.
- **Head.** It resettles for every phrase, rides the pitch of the voice a little, and drifts slowly.
- **Blinks.** At about half of the phrase ends, around glances, and at random in between.
- **Breath.** In through the gap before each phrase, out while the phrase is spoken, quiet breathing
  between lines.
- **Body and hair.** The torso shifts with some phrases, follows a head turn late, and dips into a
  stressed word. Loose hair hangs on a damped spring that follows the head.

**Record:**

1. Open the page in headless Chromium with software WebGL: flags `--use-gl=swiftshader` and
   `--enable-unsafe-swiftshader`.
2. For frame `i` from 0 to `floor(length × 30) - 1`, call `draw(i / 30)` and save the canvas as a JPEG
   at quality 0.92.
3. If anything on screen shows the time of day, make the page's clock follow show time while rendering.
   Frames render several times slower than they play, and the clock in the first videos gained minutes.
4. Build the sound track: each line's recording placed at its start time on the show's clock. The
   finished video used a recording of the page's own sound output instead, fitted to the timeline.
5. Encode: `ffmpeg -framerate 30 -i f%05d.jpg -i track.wav -c:v libx264 -pix_fmt yuv420p -crf 20
   -c:a aac -b:a 128k -shortest -movflags +faststart out.mp4`.

### Out

The frames, then the MP4: 1024 × 576, 30 frames a second. Here 3,215 frames, 107.2 s.

### Check

- `ffprobe -v error -select_streams v:0 -show_entries stream=width,height,nb_frames -of csv=p=0
  out.mp4` prints `1024,576,3215` for the bulletin. Yours prints your own frame count.
- Force every kind of pose through the engine and put the results on one sheet. Look at each tile:
  turns, nods, tilt, brows, lids, gaze, smiles and the mouth grid, all on one unchanged face.
- Smoothness. Render 100 frames at 60 a second and take the mean absolute difference between
  consecutive frames in the mouth region. Here: median 2.69, largest 5.26, against 2.78 for film grain
  alone in a still corner. No isolated jump.
- Body. Render a presenter three ways: as shown, with the hair's spring and wind off, with body and
  hair off. Optical flow between matching frames is what each part adds. Here it agreed with what the
  engine asked for to about 0.1 px on the body and 0.25 px on hair. Shoulders rose and fell over 4.6 to
  6.9 px. The body carried the head 11 to 21 px sideways.
- The figure never lifts off the bottom edge. Count how much of the bottom row it covers: here 99.7 %
  to 102.3 % of what it covers when still. Optical flow is not reliable in the last rows of a picture.
- Count events over the whole bulletin. Here, on the build before body and hair were added: 58 lip
  presses, 61 nods, 28 brow lifts, 18 blinks a minute by whoever is speaking. First settings gave 31
  blinks a minute and five or six brow lifts in nine seconds, which is too much.
- Sound against picture. Find each line's recording in the video's sound track by correlation. On the
  first video with sound, each voice sat within −1 to +8 ms of its place.
- A frame took about 25 ms to draw in software rendering.

### Settings that worked

The mouth and face:

| Setting | Value | What it means |
|---|---|---|
| Track sampling | 120 a second | Mouth tracks are sampled this often and smoothed forwards and backwards |
| Smoothing | jaw 0.010 s, lip shape 0.025 s, lip press 0.005 s | Time constants. Nothing moves faster than a face can |
| Opening range | −0.12 to 1.3 | Below 0 the lips are pressed. 1 is 46 jaw units |
| Smile scale | 0, 0.5, 1 | Relaxed while speaking; the photograph's own expression while listening; a broad smile |
| Smile release | lets go 0.45 to 0.15 s before the first sound, returns 0.35 to 1.1 s after the last | A smile is something that happens, not something worn while talking |
| Smile and rounding | smile × (1 − 0.6 × rounding) | Lips cannot round and smile at once |
| Smiling eyes | only above 0.5 | The eyes join in for a smile broader than the photograph's own |
| Lip press, m | starts 12 % into the sound; ends at 85 % of it, or 0.12 s after it starts if that is sooner | A short press in the middle |
| Lip press, p and b | ends 25 ms before the end of the sound, lasts up to 70 ms | Just before the release. A press in the middle of a p after a pause shut the mouth a fifth of a second early |
| Lip press, limits | at least 40 ms; 30 to 90 ms in, 30 to 70 ms out | Slower where the mouth is still open. Long ramps swallowed short vowels |
| Pauses | opening × 0.1 in a pause over 0.5 s, × 0.4 in a shorter one | The reference tends to leave the lips apart |
| Breath before speaking | opening 0.07, from 0.3 s to 0.07 s before the first sound | Lips part slightly, as for a breath |
| Lead-in | 0.28 s by default; 0.22 to 0.95 s per line | Listening time before a voice starts. The longest is a satellite delay |
| Tail | 0.26 s | A line ends this long after its recording |
| Blink | 0.27 s: 65 ms to close, 40 ms shut, 165 ms to open | Passes through the half-closed pose |
| Blink spacing | none within 0.9 s of another, none in the last 0.5 s of a line | A cut once landed on closed eyes |
| Random blinks | slots of 1.25 s, 1 in 5 has a blink, 14 % of those are double | Keeps the rhythm irregular |
| Eye darts | a small jump about every 0.85 s | Eyes are never quite still |
| Nod | weight 0.45 or more, and the strongest within 0.45 s | Only syllables that stand out |
| Brow lift | weight 0.7 or more, pitch 1.5 semitones or more above the median, 1.3 s apart, strength 0.3 to 0.65 | More than this looks like mugging |
| Head limits | turn within ±1 field (6°), nod −0.9 to 1 field (5°), brows up to 0.92 | Never beyond what was measured |

The body, the hair and the picture:

| Setting | Value | What it means |
|---|---|---|
| Pinning | 0.5 × `iod` up from the bottom edge, 0.45 × `iod` in from each side | Up-and-down movement fades to nothing at the bottom, sideways movement at the sides. A band 0.9 × `iod` tall held the shoulders still |
| Tilt | full at the face, none 3.3 × `iod` away, about a point 1.6 × `iod` below the face centre | The head tilts about the neck and the shoulders stay |
| Breath lift | 0.11 × `iod` for a whole breath; the head takes a quarter | About 7 mm at life size |
| Breath widening | 0.7 % | The chest widens as it fills |
| Breath timing | in ends 40 ms before the first sound; in for `clamp(0.8 × gap, 0.14, 0.6)` s; out at 0.1 a second of speech; between lines in for 1.5 s, out for 2.4 s | A short gap allows only a quick top-up |
| Body resettles | on 45 % of phrases, 0.02 to 0.07 × `iod`, over 1.1 s (the head takes 0.55 s) | Resettling on every phrase rocked the body from side to side |
| Shoulders follow the head | smoothed over 0.3 s; shift 0.03 × `iod` per unit of head turn | They take up a look to the side, not a quick nod |
| Stress dip | 0.022 × `iod` down and 0.8 % lean, 0.12 s behind the nod | Twice this bounced the shoulders on every stressed word |
| Shoulder turn | 0.1 × `iod` at the middle of the chest; 0.35 of it at the shoulder line, all of it 1.4 × `iod` below | The outline hardly moves and the collar stays under the neck |
| Sway | Paige 1, Cy 0.75, Dee 2, Sunny 1.8, Mel 0.9 | More for the two who stand |
| Hair spring, cycles a second | Paige 1.8, Cy 4, Dee 3.4, Sunny 2.4 | Long hair is slow, curls are fast |
| Hair spring, damping | Paige 0.32, Cy 0.5, Dee 0.42, Sunny 0.38 | How soon the swing dies |
| Hair swing | Paige 1.6, Cy 0.8, Dee 1.1, Sunny 1.5, Mel 0 | How far loose hair trails the head |
| Hair limits | at most 0.14 × `iod`; up-and-down is 0.6 of sideways; stepped every 4 ms; restarts when the clock jumps by more than 0.25 s | Keeps the spring stable through cuts and seeks |
| Wind | lean 0.012 to 0.042 × `iod`, flutter up to 0.011 × `iod` | Gusts for the one presenter outdoors |
| How much each moves | Paige 1, Cy 0.9, Dee 1.2, Sunny 1.25, Mel 0.85 | Scales head resettling, nods and brows per presenter |
| Camera | push-in from 1.035 to 1.085 over a shot; person scaled 1.012 to 1.034 against the plate | A little depth between person and set |
| Grain | a 256 px noise tile at a random offset, overlay at 0.11 | It also hides small blending steps |
| Video-call pane | copied through a 308 × 227 buffer 25 times a second, drawn 20 ms ahead | A held picture is on average half its interval old |

## Tried and dropped

Do not repeat these. Each row was built, tested or weighed up, and then replaced or rejected.

| Step | What was tried | Why it was dropped | What replaced it |
|---|---|---|---|
| 1 | Drawing the presenters in code | However it is shaded, it stays an illustration | Generated photographs |
| 1 | A scanned 3-D head model | One head for five characters, outside assets, an uncanny result | Generated photographs |
| 1 | LCM-LoRA shortcut, 6 steps at guidance 1.5 | 22 s against 54 s, and both looked like photographs. A minute an image was affordable, so quality won | The full sampler. A second speed-up, Hyper-SD, was never run |
| 1 | Prompts with nothing against turned heads | Many of the first twenty candidates faced away or tilted | Four pose terms in the negative prompt |
| 2 | BiRefNet's PyTorch release | It runs Python code from the model repository (`trust_remote_code`). It was not run | The ONNX export, with the glue written by hand |
| 2 | MODNet | 2 s an image, but a pale halo around hair | BiRefNet-portrait, 40 s an image |
| 2 | Two mattes in one process | Killed for memory, twice | One image per process, memory arena off |
| 2 | A plate blurred from 8 px outside the outline | A soft halo stayed where the head had been once the figure moved 10 to 20 px | Real background to 5 px from the outline, fill softened with depth |
| 2 | Plates painted by the image model | Left free (strength 0.97) it put a bright panel along the outline of a head. Held closer (0.65) it drew edges that follow the hole. 2 to 6 minutes a plate, no clear gain | The softened inpainting fill |
| 3 | Inpainted mouths: the image model repaints the mouth of the face crop, the page swaps the pictures | Each was a different mouth, so it read as a face changing expression. A cross-fade is not motion. The jaw never moved. Mouths stayed shut or turned into grins through four rounds of wording | Poses of one face from the re-posing model |
| 3 | Mouth shape per letter of the caption, 62 ms a character | Letters are not sounds, and the rhythm was mechanical | Phoneme timing from the recording |
| 3 | Running the re-posing model from its source repository | It means running third-party code. Not attempted | ONNX weights, with the glue written by hand |
| 3 | The head-pitch correction | The whole face moved as the jaw opened: 19.71 against 1.10 | Switched off |
| 3 | Spread 10, blink −20, jaw 100 | A grimace, a squeeze, a shout | Spread 7, blink −17, jaw 60 |
| 3 | Masks from the difference alone | They sprawled into hair and shoulders with stray blobs | Restricted to an ellipse in face units |
| 3 | 17 poses with six jaw openings | A blend of two distant poses shows two faint mouths | 53 mouth poses, close together |
| 3 | Each pose stored with its own soft edge | Blends were not exact | Opaque poses and one shared mask per region |
| 3 | Poses built on the photograph's closed-lip smile | Everyone talked through a held smile, lips thin | The relaxed mouth. Half the smile out was too much: corners turned down |
| 3 | The eyes drawn under raised brows | They widened on one face and drooped on two, who looked sleepy | Brows are moved by a motion field; the eye area is left alone |
| 4 | Timing estimated from a pronunciation dictionary and typical sound lengths | A plausible reading, not the recording | Timing from the recording |
| 4 | The first speech model's own timing, used as reported | About 70 ms late | The −0.07 s shift, then forced alignment |
| 4 | Kokoro voices | Clear, but read evenly. A more expressive voice was wanted | Kept as the phoneme source. Voices replaced |
| 4 | Chatterbox voices, cloned from the Kokoro recordings | Picked on reputation. Quality estimators scored both sets 4.31. A listeners' blind-test ranking, read on 10 November 2026, put it below Kokoro (1021 against 1062; Phonon 1114). It also slips words and takes 20 to 35 s a take | Phonon, the highest-ranked model that ran on this machine |
| 4 | Quality estimators as a stand-in for an ear | They did not separate the voice sets | A listeners' ranking |
| 4 | "No wrong words, then best match" as the take rule | A take with an extra word tied with one that was merely spelled oddly | Fewest wrong words first |
| 4 | Scaling whole lines down to fit their peaks | One presenter ended 2 dB quieter | A soft knee on the peaks |
| 5 | A hand-written table of mouth targets per sound, one curve | Looked wrong. The jaw chattered | Three tracks, then the reference |
| 5 | The same table with separate jaw, closure and shape tracks | Timing was right by measurement and it still looked wrong. Nothing had checked the table against real mouths. It opened a third too little | The measured lip reference. The rules stay as a fallback for a line with no reference |
| 5 | One hand-set opening gain per presenter | Faces differ far more than the gains allowed. One mouth opened half as far as the others | Calibration by landmarks |
| 5 | MediaPipe for landmarks | The current package no longer bundles the model | 2DFAN4 as ONNX |
| 5 | Wav2Lip's stock windowing | Lips shut about a tenth of a second early | Window 75 ms earlier, then the measured shift |
| 5 | Timing the reference against the aligner's m, b, p segments | The search window often caught a neighbouring f or v | The silence inside each p |
| 5 | "Shut" taken from the pauses | The network leaves the lips apart in pauses. One presenter's mouth was shut for a third of her speech | The 12th percentile while speaking |
| 5 | A common level of 0.13 with scaling down | Mouths still opened too little. The presenter the network opened furthest was cut by a fifth | 0.155, and never below 1 |
| 5 | The old closure track kept on top of the reference | Its long ramps swallowed short vowels between two closures | A short press only |
| 6 | Fading to a "brows raised" picture; sliding the head as a flat picture | Two faint brows; no parallax | Displacement fields on a mesh |
| 6 | Fields stored in eighths of a pixel | Clipped at 15.9 px without warning | A scale per field |
| 7 | "Breathing" by stretching the whole figure 0.35 % on a 4.2 s cycle | The whole figure moved as one piece, head and all, on a fixed cycle | Maps, and breath tied to the phrases |
| 7 | The shoulder line read in the middle column | Found a hand's width too low under an open neckline | Read beside the neck |
| 8 | A pinned band 0.9 × `iod` tall | It held the shoulders of the two closest-framed presenters | Pinning per direction and per edge |
| 8 | A full dip on every stressed word; resettling on every phrase | Shoulders bounced; the chest rocked 16 px one way and 10 the other | Half the dip with a lag; 45 % of phrases |
| 8 | A fixed share of a breath in any gap | A 0.19 s gap got 0.42 of a breath: three pixels of shoulder in a sixth of a second | Depth depends on the time available |
| 8 | A shoulder turn of the whole torso | It dragged the neck sideways under a still head | The turn grows from the collar down |
| 8 | A guest who looks down at his screen, using the eyes-down pose at 60 % | Behind glasses the lids nearly closed. He looked drowsy | He looks into the camera |
| 8 | A video-call look at 15 pictures a second, half resolution | Lips 33 ms late on average and visibly jerky | 25 a second at two thirds, drawn 20 ms ahead |
| 8 | Brows and blinks at first settings | 31 blinks a minute; brows at full strength in nine lines of sixteen | Thresholds and spacing as in step 8 |
| 8 | A jaw free to shut at any speed | It went from wide open to pressed in one frame | Closing takes longer from a wide mouth |
| 8 | Rendering with the computer's clock | The on-screen clock gained minutes in a two-minute video | The page's clock follows show time |
| 8 | Synthetic breath sounds | Could not be tuned without hearing them | Not done. The body breathes; the sound track does not |

## What it cannot do

- It is a warp of one photograph per person. A turned shoulder shows no new side of a jacket. Cloth
  does not crease. Hair does not part. Hands never come into view.
- Heads turn about six degrees at most. The motion fields are measured at 6° and 5°, and the bulletin
  stays within about 3.7°. A glance to the side is mostly eyes.
- There is no pose for the lower lip against the upper teeth. f and v are drawn as a nearly shut mouth.
- Teeth and tongue are whatever the re-posing model drew for each jaw opening.
- The lip reference is a network's opinion. Its mouths are soft and it tends to under-open. The common
  level of 0.155 is a judgement.
- The strip of plate that a moving figure uncovers is a softened guess, not what was behind the person.
- The voices read evenly. They do not act, and they have no breaths. English only.
- Nobody watched or listened during the build. Amounts of movement were set from how far real bodies
  move and from still frames. If the body reads as too still or too busy, change the sway values and
  the factors in the body's settings.
- Only headless Chromium with software rendering was run. No phone, no GPU, no other browser.
- Backgrounds are still photographs with a camera move on top.

## Licences

**Licences were not checked.** The models were downloaded and used for a private demonstration without
their licence texts being read. The column below is what was recalled about each one, not something
that was verified. Read each model card before you reuse anything. Some of these terms restrict
commercial use, and terms change.

| Model | Licence as recalled, unverified |
|---|---|
| Realistic Vision V5.1 | CreativeML OpenRAIL-M |
| SD VAE ft-MSE | MIT |
| YuNet | MIT |
| BiRefNet-portrait | MIT |
| LivePortrait | MIT for the original project. The export's own terms were not looked at |
| Phonon 31M | Apache 2.0 for the model. The voices' own terms were not looked at |
| Kokoro-82M | Apache 2.0 |
| Chatterbox | MIT. Its output carries its publisher's inaudible watermark |
| wav2vec 2.0 phoneme recogniser | Apache 2.0 |
| Whisper base | MIT |
| Wav2Lip | The original project allows research and personal use only, not commercial use |
| 2DFAN4 | BSD for the original project. The export's own terms were not looked at |
| BiSeNet face parser | MIT for the original project. It was trained on CelebAMask-HQ, a dataset released for non-commercial research. The export's own terms were not looked at |

Two results carry a restriction even though no picture from the network is shown. The mouth curves
were derived by measuring Wav2Lip's output. The body and hair maps were built from the labels of a
parser trained on a research-only dataset. For commercial use, make both another way.
