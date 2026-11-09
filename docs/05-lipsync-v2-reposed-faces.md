# Lip-sync, second attempt: one face, re-posed

The fix for [04](04-lipsync-v1-inpainted-mouths.md) has two halves. This document covers the pictures: making every
mouth and eye pose from the presenter's own photograph, so that all of them are the same face. The other half, the motion,
is in [06](06-speech-engine.md).

- Inference: [`gen/lp.py`](../gen/lp.py)
- Experiments: `gen/lp_sweep.py`, and the test list at the bottom of `lp.py`
- Production renders: [`gen/lpx.py`](../gen/lpx.py)
- Sprites and bundle: [`gen/lpexport.py`](../gen/lpexport.py), `gen/assets2.py`, `gen/cast_lp.json`
- Images: `gen/work/<name>/lp/`

## The model

LivePortrait is a face-animation model. It encodes a portrait once, describes the face by 21 implicit 3-D keypoints, and
redraws the portrait for any new set of keypoints. Moving a few keypoints opens the jaw, rounds the lips or closes the
eyes while everything else stays the same person.

The session used an ONNX export of its networks from `warmshao/FasterLivePortrait`. ONNX files are weights and a
computation graph, so nothing from that repository is executed as code; the glue in `lp.py` was written here. Only six
files were downloaded. Four are used:

| File | Input | Output |
|---|---|---|
| `appearance_feature_extractor.onnx` | image 1×3×256×256 | appearance volume 1×32×16×64×64 |
| `motion_extractor.onnx` | image 1×3×256×256 | `pitch`, `yaw`, `roll` (66 bins each), `t` (3), `exp` (63), `scale` (1), `kp` (63) |
| `stitching.onnx` | source and driving keypoints, 126 numbers | 65 numbers: a keypoint correction and an x, y shift |
| `warping_spade.onnx` | appearance volume, driving keypoints, source keypoints | image 1×3×512×512 |

`stitching_lip.onnx` and `stitching_eye.onnx` were downloaded in case they were needed and are not used.

## What `lp.py` does

1. **Crop.** A square of side 5.06 × the eye distance, centred 0.07 × that distance below the midpoint of the eyes, and
   rotated so the line from the eyes to the mouth is vertical. These numbers approximate the model's usual crop (2.3 × the
   face landmarks' bounding box, shifted up by an eighth). The crop is resampled to 512 × 512, and to 256 × 256 for the
   networks.
2. **Encode.** The appearance volume and the motion values come from one pass each. Head angles are read from the 66 bins
   as `sum(softmax × index) × 3 − 97.5` degrees.
3. **Source keypoints.** `x_s = scale × (kp · R + exp) + t`, where `R` is the rotation built from the head angles and only
   the x and y parts of `t` are applied.
4. **Pose.** Offsets are added to `exp` (table below), giving driving keypoints `x_d` by the same formula.
5. **Stitch.** The stitching network nudges `x_d` so the shoulders and background stay aligned with the source.
6. **Render.** The generator returns a 512 × 512 image.

Each render takes about 5.5 seconds on this machine.

### Expression offsets

Index is the keypoint (0 to 20) and axis; the value is added per unit of the control.

| Control | Offsets added to `exp` | Used range |
|---|---|---|
| `aaa` (jaw opens) | [19].y += 0.001, [19].z += 0.0001, [17].y −= 0.0001 | −8 to 68 |
| `eee` (lips spread) | [20].z −= 0.001, [20].y −= 0.001, [14].y −= 0.001 | 7 |
| `woo` (lips round) | [14].y += 0.001, [3].y −= 0.0005, [7].y −= 0.0005, [17].z −= 0.0005 | 12 |
| `blink` | [11].y −= 0.001, [13].y += 0.0003, [15].y −= 0.001, [16].y += 0.0003 | −9 (half), −17 (closed) |
| `brow` (raise, when positive) | [1].y += 0.001, [2].y −= 0.001 | 9 |
| `smile` | [20].y −= 0.01, [14].y −= 0.02, [17].y += 0.0065, [17].z += 0.003, [13].y and [16].y −= 0.00275, [3].y and [7].y −= 0.0035 | tested, not used |
| pupil x, y | [11] and [15], x and y | tested, not used |

These indices and coefficients follow the expression sliders in LivePortrait's own editing tools. They were written from
memory, not copied from a file, and then confirmed by rendering: each control did what its name says (the sweep below).

## Experiments, in order

**First test** (`work/paige/lp/t_*.png`, sheet `out/lp_paige.jpg`). The neutral render matched the source closely: mean
absolute difference 5.57 on a 0 to 255 scale over the face, visually a touch softer (`out/lp_detail.jpg`). Jaw, spread,
round and blink all worked on the first run.

**Head-pitch correction.** The editing tools tilt the head back slightly as the jaw opens (`pitch −= aaa × 0.05`). That
moves the whole face, which is wrong here because only the lower face is pasted into a fixed photograph.

| Render at `aaa = 60` | Change in the eyes and forehead vs neutral | Change at the hair and shoulder border |
|---|---|---|
| with the correction (`t_a60.png`) | 19.71 | 5.59 |
| without (`t_a60nc.png`) | 1.10 | 2.52 |

The correction was switched off (`comp=0`). The jaw drops and the upper face stays put.

**Sweep** (`gen/lp_sweep.py`, files `work/paige/lp/s_*.png`, sheet `out/lp_sweep_paige.jpg`). 24 poses: neutral; jaw at 10, 22,
36, 52, 75; spread 6 and 10 with the jaw closed, at 22 and (for 10) at 45; round 8 and 14 with the jaw closed, at 22 and
(for 14) at 45; jaw at −8; smile 0.3; blink −10 and −20; brow 8 and 15; pupils ±8. What it showed:

- Jaw 0 to 75 is a smooth, natural progression. 100 looks like a shout.
- Spread 10 with an open jaw is a grimace. 6 to 7 is a natural "ee".
- Round 8 to 14 gives "oh" and "oo".
- Jaw −8 presses the lips together, right for m, b and p.
- Blink −10 is half closed; −20 is squeezed shut, so −17 was used.
- Brow 8 is a natural lift; 15 is wide-eyed.
- Pupils moved convincingly. Gaze was left out of the show to keep the scope small.

## The pose set (`lpx.py`)

Twenty poses per presenter, 116 to 126 seconds each:

| Name | Pose | Count |
|---|---|---|
| `n` | neutral | 1 |
| `n1`…`n5` | jaw at 0.14, 0.30, 0.50, 0.72, 1.0 of 68 | 5 |
| `e0`…`e4` | spread 7, with jaw at 0, 0.14, 0.30, 0.50, 0.72 of 68 | 5 |
| `w0`…`w4` | round 12, with the same five jaw openings | 5 |
| `p` | jaw −8, lips pressed | 1 |
| `half`, `closed` | blink −9, −17 | 2 |
| `brow` | brow 9 | 1 |

```
./venv2/bin/python lpx.py paige cy dee sunny mel        # writes work/<name>/lp/f_*.png and affine.json
```

## From renders to sprites (`lpexport.py`)

1. **Place.** Each 512 × 512 render is warped back into the 1024 × 576 frame with the crop's transform. When the crop
   shrinks by more than 8 % it is first reduced with area averaging, then placed, to avoid aliasing.
2. **Find what moves.** For the mouth poses, take the largest per-pixel difference from the neutral render across all
   sixteen; the same for the three eye poses. Keep pixels that differ by more than 5.
3. **Restrict.** Keep only pixels inside a region where that feature can live, in units of the eye distance:
   mouth, an ellipse centred 1.25 below the eye line with radii 1.3 × 1.2, and at least 0.32 below the eye line; eyes, an
   ellipse centred 0.14 above the eye line with radii 1.4 × 0.78, and no lower than 0.42 below it.
4. **Soften.** Dilate, close, and blur by 0.05 × the eye distance. This is the region's one shared mask.
5. **Rebase.** Inside both masks the photograph is replaced by the neutral render, giving `frame_lp.png`. Now the still
   and every sprite come from the same renderer, so blending between them cannot show a seam.
6. **Cut.** Every pose is cropped to its mask's bounding box and saved as WebP (quality 82) with the mask as transparency.
7. The cut-out and background plate are made from `frame_lp.png` as described in [03](03-still-images.md).

`work/<name>/lp/masks.png` shows the two masks (mouth in red, eyes in green).

**Retry.** The first export skipped step 3. Small differences in the hair and shoulders made the masks sprawl (351 × 216
and 264 × 225 pixels for Paige, 301 KB of sprites, with stray blobs). With the restriction they are 224 × 206 and
213 × 152, and 166 KB. `out/lp_masks_paige.jpg` and `out/lp_masks_2.jpg` are the "after" pictures.

### Result per presenter

| Presenter | Mouth sprites (16) | Eye sprites (3) | Cut-out | Plate | Opening gain |
|---|---|---|---|---|---|
| Paige | 143 KB | 22 KB | 35 KB | 52 KB | 1.05 |
| Cy | 198 KB | 29 KB | 30 KB | 42 KB | 1.00 |
| Dee | 274 KB | 33 KB | 41 KB | 61 KB | 1.12 |
| Sunny | 97 KB | 14 KB | 24 KB | 40 KB | 1.05 |
| Mel | 274 KB | 38 KB | 40 KB | 58 KB | 0.95 |

Sizes are base64 text as stored in `assets.json`. "Opening gain" scales how wide each presenter opens their mouth; it was
0.92, 0.86, 1.0, 0.92 and 0.8 at first and was raised once the film strips showed the articulation was faint.

```
./venv/bin/python lpexport.py          # writes cast_lp.json
./venv/bin/python assets2.py           # adds the B-roll stills and writes ../assets.json
```
