# Problems, dead ends and retries

Everything that failed, was done twice, or was tried and dropped, grouped by the request it belongs to. The request
numbers match [01](01-timeline.md).

## Request 1: the television

| Problem | What was done |
|---|---|
| The first render was dim, and the set was small in the frame | Raised ambient light (0.2 → 0.34) and the back light (0.22 → 0.5), lightened the rear housing, added a rear skin, moved the camera in (3.1 m → 2.55 m), relaxed the portrait-screen distance factor (1.25 → 0.92 over the aspect ratio) |
| The remote's buttons wrapped on a phone | Set them not to wrap |

## Request 2: a news show with people

| Problem | What was done |
|---|---|
| The corner logo overlapped the end of long subtitles | Removed the logo on the news channel |

## Request 3: DevOps

No failures. One thing was done without being asked: the other four channels lost their JavaScript jokes too, so the set
would not contradict the new theme. This was reported at the time.

## Request 4: photographic video

### Choosing an approach

| Option | Outcome |
|---|---|
| Draw more realistic people in code | Rejected. Shading and texture can be improved, but the result stays an illustration |
| Real photographs of real people, animated | Rejected. It would put invented words in the mouths of identifiable people |
| A scanned 3-D head model | Rejected. One bald head for five characters, external assets, and an uncanny result |
| Generate synthetic photographs with an open image model on the session's CPU | Chosen, after confirming the downloads were reachable and a test image took under a minute |

### Failures and fixes

| # | Problem | Cause | What was done |
|---|---|---|---|
| 1 | `ValueError: final_sigmas_type zero is not supported for algorithm_type deis` on the first full-quality run | The model ships with a DEIS sampler config, and the DPM-Solver class inherited its algorithm type | Set `algorithm_type="dpmsolver++", solver_order=2` in `sdlib.load` |
| 2 | The benchmark prompt was cut off | The text encoder reads 77 tokens | Shortened the production prompts. The `cy2` retry still lost two words |
| 3 | Many of the first 20 candidates faced away or tilted | Nothing in the prompt forbade it | Added "side view, profile, looking away, tilted head" to the negative prompt for everything after |
| 4 | No good candidate for the second anchor at first glance | As above | Queued six more with "front view, centered". A closer look at seed 24 from the first batch showed it was the best, so the retry was stopped after three |
| 5 | The queued refinement and candidate jobs died at once with `Could not import module 'CLIPImageProcessor'` | Installing `timm` for a matting model pulled in a `torchvision` build that did not match the CPU build of PyTorch. `import torchvision` then failed (`operator torchvision::nms does not exist`), and the diffusion library imports it indirectly | Uninstalled `torchvision`, `timm` and `kornia` from the first environment, made a second environment (`venv2`) for matting, restarted the queue. About a minute lost |
| 6 | The first matting model could not be run | BiRefNet's PyTorch release loads its network definition as Python code from the model repository (`trust_remote_code=True`). The session's automatic permission check refused to run code from an external source | Not worked around. Switched to ONNX exports, which are weights only, with the inference written in `matte_onnx.py`. The refused script is kept as `gen/matte.py`; it never ran |
| 7 | The quick matting model (MODNet) left a pale halo around hair | Model quality | Used BiRefNet-portrait (ONNX) instead: 40 s per image, clean edges |
| 8 | The matting process was killed by the kernel, twice | Memory. A second image in the same process pushed the session over its shared memory limit, first while an image job was also running, then on its own | One image per process, and the runtime's memory arena disabled. The first kill left one presenter without a matte until this was understood |
| 9 | Inpainted mouths stayed shut or turned into smiles | The wording ("speaking", "teeth visible") pulls toward a closed mouth or a grin | Three more rounds of wording. "Surprised" and a negative prompt of "smile, grin, laughing" produced neutral open mouths. Details in [04](04-lipsync-v1-inpainted-mouths.md) |
| 10 | The second anchor's mouth barely opened in any variant | Strength 0.92 kept too much of the closed mouth | A separate run at strength 1.0 with stronger wording (`gen/extra.py`) |
| 11 | A bright fringe around the weather presenter's hair over the dark map | Her original background was a bright screen, and soft matte edges carried its colour | Tightened the matte and replaced edge colours with colours grown from the interior |
| 12 | Split-screen panes cut off the top of the hair | Crop too tight | Crop height 5.4 → 5.9 eye-distances, centred higher |
| 13 | The story box overlapped the channel logo, and one anchor sits right of centre | Fixed position | The box picks the free side, sits lower, and the camera shifts 46 px with a little more zoom |
| 14 | The name strap reappeared every time a presenter came back | Rule was "speaker changed" | Show it only on a presenter's first appearance |
| 15 | The video-call effect was too coarse | 154 × 114 at 12 frames a second | 231 × 170 at 15 |
| 16 | Publishing was refused with HTTP 422 | The page's owner had made it public since the last publish, and the publishing tool requires that to be acknowledged | Read the page's state, republished stating that it is public |
| 17 | The session's worker process restarted during publishing | Not known | Checked that the built file was intact and carried on |

### Done to save time

- The page code for this version was written and exercised with placeholder pictures while the real ones were still
  generating (`tests/fake_assets.py`).
- The second round of B-roll (seed 42) and the last three second-anchor retries were cancelled once the first results
  were good enough.

### Anticipated, so never hit

- The image library's own image-to-image and inpainting pipelines assume one number format throughout. With the UNet in
  bfloat16 and the VAE in float32 they would have failed, so a small sampler was written by hand (`sdlib.ddim`).
- Images loaded from separate files could taint the canvas inside a sandboxed viewer and block the upload to WebGL.
  Everything is inlined as `data:` URIs instead.

### Done without being asked

- A standing line under the controls saying channel 1 is satire with AI-generated presenters, and the same in the
  credits. The page was public by then, and photographic fake news footage without a label could mislead.

## Request 6: natural lip movement

### Choosing an approach

| Option | Outcome |
|---|---|
| Warp the photograph to open the jaw and paint in a mouth interior | Kept as a fallback. It gives continuous motion, but usually looks like a puppet |
| Morph between the existing inpainted mouths with optical flow | Kept as a fallback. Smoother, but the mouths would still be different mouths |
| Run a face-animation model from its source repository | Not attempted. It means executing third-party code, which is what was refused in problem 6 |
| Run the same model from ONNX weights with glue written here | Chosen |
| Generate a voice and drive the lips from audio | Out of scope. Nobody asked for sound |

### Failures and fixes

| # | Problem | Cause | What was done |
|---|---|---|---|
| 18 | With the usual head-pitch correction the whole face moved as the jaw opened | The correction tilts the head back; here only the lower face is pasted into a fixed photograph | Switched it off. Upper-face change fell from 19.71 to 1.10 |
| 19 | "ee" at the tested strength was a grimace, and a full blink was a squeeze | Ranges too wide | Spread 10 → 7, blink −20 → −17, chosen from the sweep |
| 20 | Sprite regions sprawled into hair and shoulders, with stray blobs | Tiny differences far from the mouth passed the threshold | Restricted each region to an ellipse in face units. Sprite data for the first anchor fell from 301 KB to 166 KB |
| 21 | The page did not load; the test waited 30 seconds and timed out | `Identifier 'PH' has already been declared`: the TV code already uses `PH` for the panel height | Renamed the new constant to `SPOKEN` |
| 22 | Articulation looked faint in the film strips | Opening gains were set cautiously | Raised the gains (for example 0.92 → 1.05) |
| 23 | Speech was a little slow, and the mouth began drifting open 0.3 s before the first word | Rate 1.12; the curve started from the line's first instant | Rate 1.05; rest is held until a small breath just before the first sound |
| 24 | Blinks came at a fixed period per presenter | First version used a fixed period | Random slots, as in [06](06-speech-engine.md) |

## Request 7: demo and export

| # | Problem | What was done |
|---|---|---|
| 25 | Presenter names in the demo read "PAige Duty" | A capitalisation slip; fixed |
| 26 | Word labels on the demo's chart vanished when they overlapped | Two label rows |
| 27 | The session is not permitted to create GitHub repositories | Asked for an empty repository to push to |
| 28 | `tests/fake_assets.py` would overwrite the real `assets.json` if run | Changed to write `assets_fake.json`, and marked as historical |

## Downloaded or generated and never used

| Item | Why it exists |
|---|---|
| Hyper-SD LoRA | A second speed-up option; the full sampler was fast enough |
| LCM-LoRA | Used for the benchmark only |
| BiRefNet PyTorch weights | Problem 6 |
| MODNet | Problem 7 |
| `stitching_lip.onnx`, `stitching_eye.onnx` | Fetched in case direct lip and eye retargeting were needed; keypoint offsets were enough |
| Gaze and smile poses in the sweep | Tested; left out of the show |
| 70 inpainted mouth and blink variants (60 mouths, 10 blinks) | The first lip-sync. It used 30 of them; all were replaced |
| `gen/cast_assets.json`, `gen/work/*/export/` | The first lip-sync's bundle and cut-outs |

None of the model files are in this repository; `gen/download_models.py` lists them.
