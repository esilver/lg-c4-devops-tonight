# Asset inventory

Every image and data file in the repository, with its status:

- **final**: part of the published page, directly or through `assets.json`
- **intermediate**: a step toward a final file
- **rejected**: generated and not used
- **evidence**: made only to look at or measure

Model weights (6.6 GB) and the Python environments are not here. `gen/download_models.py` and
[03](03-still-images.md) say how to get them.

## Built pages and bundles

| File | Status | What it is |
|---|---|---|
| `lg-c4/index.html` | final | The published page, 2.4 MB, self-contained |
| `demo/index.html` | final | The single-presenter demo, 2.4 MB |
| `demo/paige-lipsync.mp4` | evidence | 883 frames at 30 fps, 1920 × 540: full frame beside mouth close-up, rendered from the demo page |
| `assets.json` | final | Everything `build.py` inlines: 6 stills and 5 presenters, 2.3 MB of `data:` URIs |
| `gen/cast_lp.json` | intermediate | The presenter half of `assets.json`, written by `lpexport.py` |
| `gen/cast_assets.json` | rejected | The presenter bundle of the first lip-sync |
| `src/phon.json` | final | Pronunciations of the sixteen lines |

`assets.json` holds 111 images: 6 stills, and per presenter a plate, a cut-out, 16 mouth sprites and 3 eye sprites.

## `gen/out/`: candidates, stills, sheets (35 PNG, 41 JPEG, 20 MB)

| Files | Status | What they are |
|---|---|---|
| `base_paige_21.png`, `base_cy_24.png`, `base_dee_22.png`, `base_sunny_23.png`, `base_mel_21.png` | intermediate | The five chosen candidates, 768 × 432 |
| the other `base_<presenter>_<21–24>.png` (15 files) | rejected | First-round candidates not chosen |
| `base_cy2_31.png`, `_32`, `_33` | rejected | The second anchor's retry |
| `base_<studio, servers, dcext, office, paged, sat>_41.png` | intermediate | B-roll at 768 × 432 |
| `still_<the same six>.png` | final (as JPEG in the bundle) | B-roll refined to 1024 × 576 |
| `bench_lcm_bf16_6_11.jpg`, `_12`, `bench_dpm_bf16_25_11.jpg`, `_12` | evidence | The speed and quality benchmark |
| `sheet21.jpg`, `sheet_24.jpg`, `sheet_paige.jpg`, `sheet_cy.jpg`, `sheet_cy2.jpg`, `sheet_dee.jpg`, `sheet_sunny.jpg`, `sheet_mel.jpg`, `sheet_41.jpg`, `sheet_stills.jpg` | evidence | Contact sheets used to choose |
| `frame_<presenter>.jpg`, `cmp_paige.jpg` | evidence | Refined frames at reduced size; face crop beside the first inpaint |
| `cand_<presenter>_mouth.jpg`, `cand_<presenter>_blink.jpg`, `cand2_<presenter>.jpg`, `cand2_all.jpg` | evidence | Sheets of inpainted mouth and blink candidates |
| `matte_paige.jpg` | evidence | MODNet (top) and BiRefNet-portrait (bottom) over green |
| `lp_paige.jpg`, `lp_detail.jpg`, `lp_sweep_paige.jpg`, `lp_masks_paige.jpg`, `lp_masks_2.jpg` | evidence | Re-posing tests, the 24-pose sweep, sprite regions |

Some sheets were rebuilt as work went on, so a sheet shows the candidates that existed at its last rebuild.

## `gen/work/<presenter>/` (82 MB in all)

The same files exist for `paige`, `cy`, `dee`, `sunny` and `mel`, except where noted.

| File | Status | What it is |
|---|---|---|
| `hires.png` | intermediate | The pick enlarged and refined to 1024 × 576 |
| `face0.png` | intermediate | The 512 × 512 face crop after its refinement pass |
| `face0r.png` | intermediate | `face0` after one VAE round trip; this is what was pasted back |
| `frame.png` | intermediate | The frame with the refined face. Input to matting and to re-posing |
| `meta.json` | intermediate | Crop position, landmarks, mouth and eye mask ellipses |
| `alpha.png` | final (inside the cut-out) | The person matte from BiRefNet-portrait |
| `alpha_modnet.png` (Paige only) | rejected | The MODNet matte |
| `frame_lp.png` | final (as plate and cut-out) | `frame.png` with the neutral re-posed render inside the mouth and eye regions |
| `mouth_*.png`, `blink_*.png` | rejected | Inpainted variants from the first lip-sync, 512 × 512 face crops: 13 mouths for Paige, 14 for Cy, 11 each for Dee, Sunny and Mel; 2 blinks each |
| `export/bg.jpg`, `export/fg.png` | rejected | The first lip-sync's plate and cut-out |
| `lp/affine.json` | intermediate | The crop transform and the jaw levels |
| `lp/f_n.png` | final (inside `frame_lp.png`) | Neutral re-posed render, 512 × 512 |
| `lp/f_n1.png`…`f_n5.png`, `f_e0.png`…`f_e4.png`, `f_w0.png`…`f_w4.png`, `f_p.png` | final (as mouth sprites) | The 16 mouth poses |
| `lp/f_half.png`, `f_closed.png`, `f_brow.png` | final (as eye sprites) | The 3 eye poses |
| `lp/masks.png` | evidence | Mouth region in red, eye region in green |
| `lp/src.png`, `lp/t_*.png` (Paige only, 8 files) | evidence | The first re-posing test, including the pitch-correction comparison |
| `lp/s_*.png` (Paige only, 24 files) | evidence | The pose sweep |

### Which inpainted variants the first lip-sync used

From `gen/picks.json`. Everything else in `mouth_*.png` and `blink_*.png` was made and not used.

| Presenter | Used |
|---|---|
| Paige | `sm_2`, `oh_1`, `ee_1`, `oh_2`, `closed_1`, `blink_1` |
| Cy | `ah_2`, `wide_2`, `open_2`, `oh_2`, `closed_1`, `blink_2` |
| Dee | `ah_2`, `ah_1`, `open_1`, `oh_2`, `closed_1`, `blink_2` |
| Sunny | `oh_3`, `ah_1`, `open_1`, `oh_2`, `closed_1`, `blink_1` |
| Mel | `open_1`, `ah_2`, `ee_1`, `oh_2`, `sm_2`, `blink_1` |

## `gen/logs/`

Console output of the long jobs, including library warnings. `log_base.txt` is the first 20 candidates; `log_cy2.txt`
and `log_broll.txt` the retry and B-roll (both end where they were cancelled); `log_prep_<presenter>.txt` the refinement
and first variants; `log_prep2_<presenter>.txt` the extra variants; `log_stills.txt`, `log_matte.txt`, `log_lpx.txt`;
`log_q4.txt` and `log_q5.txt` are just completion markers.

Two logs are incomplete records: `log_prep_paige.txt` was overwritten by her second run, and `log_matte.txt` stops at the
first image because the process was killed ([09](09-problems-and-retries.md), problem 8).

The `queue*.sh` scripts chained those jobs so each started when the previous one ended. They are kept as run, including
jobs that were later cancelled.

## `tests/output/` (11 MB)

The last output of each test script. Earlier rounds were overwritten.

| Files | What they show |
|---|---|
| `s1.png`…`s4.png` | The page: default view, channel 2, powered off seen from behind, phone on channel 3 |
| `tv1.png`…`tv4.png` | Double-density captures: default, close camera, after a channel round trip, phone at the close camera |
| `tv.png` | The cartoon DevOps show on the set, from request 3 |
| `g1.jpg`…`g3.jpg` | Contact sheets of every scene on the final build |
| `g4.jpg` | The sign-off and credits of the first photographic version (request 4) |
| `grid.jpg` | The five presenters at their widest mouth (request 6) |
| `seq.jpg` | The last film strip made: brow lift and blink |
| `curve1.png`, `curve1.json` | The first line's jaw and lip curves |
| `curves.json` | Every line's jaw curve at 60 samples a second |
| `demo1.png` | The demo page before two small fixes |
| `frames/n*.jpg` | Individual frames of the show from the last `shot4.js` runs |
| `frames/k0.jpg`…`k4.jpg` | Each presenter at their widest mouth |
| `frames/e0.jpg`…`e9.jpg` | Frames around a brow lift and a blink |
| `frames/c2.jpg`…`c5.jpg` | Channels 2 to 5 |

Not kept: the raw frame dumps behind the film strips and the recording (about a thousand JPEGs). `strip.js` and `rec.js`
regenerate them.

## Source that is no longer live

| File | What it is |
|---|---|
| `src/history/news_cartoon_devops.js` | The drawn, cartoon version of the show (request 3). The first two versions were this file with a different script and names |
| `src/history/news_photo_v1_inpainted_mouths.js` | The first photographic version (request 4) |

The built pages of all five published versions are in the web artifact's own history, not here.

## Added in request 8

| File | Status | What it is |
|---|---|---|
| `src/speech.json` | final | The sixteen recordings as MP3 `data:` URIs with word and phoneme timing, 1.0 MB |
| `src/calib.txt` | final | The 3 KB calibration clip for measuring decoder delay |
| `src/sound.js` | final | The sound engine |
| `src/phon.json`, `gen/phon.py` | superseded | Dictionary pronunciations for the first speech engine |
| `gen/work/tts/NN_<who>.wav` | intermediate | Each line as the speech model produced it, 24 kHz |
| `gen/work/tts/lines.json` | intermediate | Phonemes, lengths, loudness and word times for each line |
| `gen/work/tts/mp3/` | final (the MP3s) | Each line trimmed and levelled, as WAV and MP3, plus the calibration clip |
| `gen/work/<presenter>/lp/f_smile.png` | final (as a mouth sprite) | The smile pose |
| `gen/out/base_dcext2_*.png`, `base_paged2_*.png`, `base_office2_*.png`, `still_*2.png`, `sheet_broll2.jpg` | final (seeds 52, 51, 52) and rejected | Second-round B-roll |
| `demo/devops-tonight.mp4` | evidence | The whole bulletin with sound, 110 s |
| `demo/paige-lipsync.mp4` | evidence | Replaced: now with sound, 26.6 s |
| `tests/output/rec.webm` | evidence | The set's sound output for one whole bulletin, as the page played it |
| `tests/output/music_intro.mp3`, `music_outro.mp3` | evidence | The two pieces of synthesised music as the page rendered them |
| `tests/output/audio_analysis.txt`, `sound_check.json` | evidence | The analysis of that recording and the sync log |
| `tests/output/g_smile.jpg`, `g_broll2.jpg`, `refl.png`, `reg.jpg` | evidence | Smile moments, new B-roll in use, the reflection from above, desktop and phone layouts |

`assets.json` now holds 116 images.

## Added in request 9

| File | Status | What it is |
|---|---|---|
| `assets.json` | final | Rebuilt by `gen/assets3.py` from `gen/cast2.json`: 321 images (6 stills; per presenter a plate, a cut-out, a mouth mask, 53 mouth poses, an eye mask, 6 eye poses) and six motion fields per presenter, 3.15 MB |
| `gen/cast2.json` | intermediate | The presenter half of `assets.json`, written by `gen/lpexport2.py` |
| `gen/cast_lp.json`, `gen/lpexport.py`, `gen/assets2.py` | superseded | The 17-pose bundle of requests 6 and 8 |
| `src/speech.json` | final | The second voices: 16 MP3s with word and phoneme timing and pitch contours, 1.0 MB |
| `src/speech_first.json` | final (demo page) | The first voices in the same form, phoneme times corrected by 70 ms |
| `gen/work/<presenter>/lp/d_n01.png` … `d_n11.png`, `d_e1_0.png` … `d_w2_7.png` | final (as mouth poses) | The dense pose set: 11 + 4 × 8 renders |
| `gen/work/<presenter>/lp/d_sg_0.png` … `d_sg_7.png`, `d_sh.png` | final | Smiling mouths at eight openings; a half smile. `d_sg_0` also supplies the smiling eyes |
| `gen/work/<presenter>/lp/d_browup.png`, `d_browdn.png` | final (as motion fields) | Brows raised and lowered |
| `gen/work/<presenter>/lp/f_yawp.png`, `f_yawn.png`, `f_pitp.png`, `f_pitn.png` | final (as motion fields) | Head turned 6° either way, nodded 5° either way |
| `gen/work/<presenter>/lp/f_gl.png`, `f_gr.png`, `f_gd.png` | final (as eye poses) | Eyes left, right, down |
| `gen/work/<presenter>/lp/dense.json` | intermediate | The jaw values of the dense set |
| `gen/work/<presenter>/lp/masks2.png` | evidence | Mouth region in red, eye region in green, brow band in blue |
| `gen/work/<presenter>/frame_lp2.png` | final (as plate and cut-out) | The frame with the neutral render inside the new regions |
| `gen/work/<presenter>/lp/f_n1.png` … `f_n5.png`, `f_e*.png`, `f_w*.png`, `f_brow.png`, `f_smile.png`, `frame_lp.png` | superseded | The first pose set; `f_n`, `f_p`, `f_half`, `f_closed` are still used |
| `gen/work/tts2/NN_<who>_t<k>.wav` | final (the chosen takes) and rejected | 35 takes by the second speech model |
| `gen/work/tts2/rejected/01_cy_t*_dekkar.wav` | rejected | The two takes with the name read wrong |
| `gen/work/tts2/script.json`, `takes.json`, `lines.json` | intermediate | The respelled text; every take's transcript and scores; the chosen takes with their timing |
| `gen/work/tts/cb_test_paige.wav`, `cb_test_cy.wav` | evidence | The first test of the second speech model |
| `gen/work/bundle/`, `gen/work/bundle_first/` | final (the MP3s) | Each line of each set trimmed and levelled, as WAV and MP3 |
| `gen/work/voice_quality.json`, `gen/logs/log_voice_quality.txt` | evidence | The quality estimates for both sets |
| `gen/out/flow_<presenter>.jpg` | evidence | Neutral face, the same moved by the measured field, and the real turned render |
| `gen/out/lp2_paige.jpg`, `masks2_paige.jpg` | evidence | First look at the new brow and mouth renders; the regions over the face |
| `gen/logs/log_tts2*.txt`, `log_lpx2.txt`, `log_lpx3*.txt`, `log_align*.txt`, `log_q8.txt`, `log_q9.txt` | evidence | Logs of this pass (progress bars removed) |
| `demo/devops-tonight.mp4`, `demo/paige-lipsync.mp4` | evidence | Replaced with recordings of this build |
| `tests/output/poses_<presenter>.jpg`, `poses_big*.jpg` | evidence | Every pose forced, per presenter; brow and gaze poses at double size (including the drooping eyes that were dropped, `poses_big_dee.jpg`) |
| `tests/output/strip_new1.jpg`, `strip_look.jpg`, `strip_split_*.jpg`, `g_scenes_a.jpg`, `g_scenes_b.jpg` | evidence | Film strips of the first line, the glance on "Dee?", the two conversations; every scene |
| `tests/output/demo_desktop.png`, `demo_phone.png`, `demo_closeup.png`, `demo_first_voices.png` | evidence | The demo page |
| `tests/output/tv_new_desktop.png`, `tv_new_phone.png` | evidence | The television page on this build at desktop and phone size, with the camera moved in close |
| `tests/output/lipsync*.json`, `lipsync_report.txt` | evidence | Mouth curves of the three builds compared, and the result |
| `tests/output/rec.webm`, `audio_analysis.txt`, `sound_check.json`, `asr_engine.txt` | evidence | Replaced: the set's output for this build, its analysis, and its transcript |

The old pose renders and both old bundles stay in the repository because earlier documents refer to them.

## Added in request 10

| File | Status | What it is |
|---|---|---|
| `src/speech.json` | final | Now the third voices (Phonon): 16 MP3s with timing, pitch and the lip reference curves |
| `src/speech_second.json` | final (demo page) | The second voices (Chatterbox), moved here from `src/speech.json` |
| `src/speech_first.json` | final (demo page) | The first voices (Kokoro), as before |
| `gen/work/tts3/NN_<who>_t<k>.wav` | final (the chosen takes) and rejected | 48 takes by the third speech model, three of each line, 32-bit float |
| `gen/work/tts3/rejected/10_sunny_t*_retrees.wav`, `00_paige_t*_judy.wav`, `13_cy_t*_softch.wav` | rejected | Fifteen takes with a word mispronounced or unclear |
| `gen/work/tts3/respell/10_*.wav`, `00_*.wav`, `13_*.wav` | evidence | Trial takes of respellings of those three lines |
| `gen/work/tts3/alt_Edwin/`, `alt_Spencer/`, `alt_Old_Mortlake/` | rejected | The guest's line in three other voices |
| `gen/work/tts3/script.json`, `takes.json`, `lines.json` | intermediate | The text as spoken and the cast; every take's transcript and scores; the chosen takes with timing |
| `gen/work/bundle/` | final (the MP3s) | Now the third voices, trimmed and levelled |
| `gen/work/bundle_second/`, `gen/work/bundle_first/` | final (demo page) | The second and first voices |
| `gen/work/lipcal.json` | intermediate | The calibration: lip opening and mouth width of every pose of every presenter |
| `gen/work/bundle*/lip_raw.json` | intermediate | The lip reference as measured: opening, lip height and width for every 1/50 s (1/25 s for the two older sets) of every line |
| `gen/out/w2l_proto_paige.jpg` | evidence | Six frames of the lip-sync network's own picture of the first anchor, from the first trial |
| `gen/logs/log_align3.txt`, `log_lipteach*.txt` | evidence | Logs of this pass |
| `tests/output/strip_mel_pane.jpg`, `poses_big_mel.jpg`, `mel_now.jpg` | evidence | The guest before (eyes nearly shut, mouth barely open), his eyes-down and half-blink poses, and after |
| `tests/output/phon_paige.jpg` | evidence | The first anchor's mouth, frame by frame, labelled with the sound being made and the opening drawn |
| `tests/output/strip_taught_paige.jpg`, `strip_taught_mel.jpg` | evidence | Film strips with the learned lips: the first line, and the guest's answer |

`gen/models/w2l/` (the lip-sync and landmark networks, 390 MB) is not committed.

## Added in request 11

| File | Status | What it is |
|---|---|---|
| `gen/work/<name>/lp4/*.png` (65 a presenter), `affine.json`, `dense.json`, `masks.png` | intermediate | The pose set built on a relaxed mouth: 512-pixel crops, where they sit in the frame, the settings they were rendered with, and the mouth, eye and brow masks |
| `gen/work/<name>/lp/` | superseded | The earlier pose sets, kept because earlier documents refer to them |
| `gen/work/<name>/frame_lp3.png` | intermediate | The base frame: the photograph with the relaxed mouth and eyes laid in |
| `gen/work/<name>/body.json`, `body.jpg` | intermediate | The body, hair and wind maps on an 8-pixel grid with the torso's measurements; the maps drawn over the presenter |
| `gen/work/<name>/plate3.jpg` | final | The plate behind the presenter, as bundled |
| `gen/cast3.json`, `assets.json` | final | The picture bundle of this build (3.27 MB) |
| `gen/cast2.json` | superseded | The bundle of requests 9 and 10 |
| `gen/work/lipcal.json`, `gen/work/bundle*/lip_raw.json` | intermediate | Calibration and lip reference, measured again on the new poses and base frames |
| `gen/work/lipcal_r10.json`, `gen/work/bundle*/lip_raw_r10.json` | superseded | The same as they were in request 10 |
| `gen/out/relax_grid_<name>.jpg` | evidence | The first look: each face at several settings of smile and lip rounding, by jaw opening |
| `gen/out/face_parse_two_crops.jpg`, `gen/out/bodymaps.jpg` | evidence | What the face parser labels at two crop sizes; the three maps over all five presenters |
| `gen/out/plates_before.jpg`, `plate_halo_before_after.jpg` | evidence | The old plates; the halo they left beside a figure that has moved, and the first fix |
| `gen/out/plates_tried/` | rejected | Three plates painted by the image model, and two comparisons |
| `gen/logs/log_lpx4.txt`, `log_lipteach4_*.txt`, `log_plate.txt` | evidence | Logs of this pass |
| `tests/output/poses_<name>_relaxed.jpg` | evidence | Twelve mouth poses of each presenter as the page now draws them |
| `tests/output/poses_big_mel2.jpg`, `poses_big_mel3.jpg` | evidence | The guest at the same four jaw settings, before and after |
| `tests/output/phon_cy.jpg`, `phon_dee.jpg` | evidence | Before: the co-anchor and the reporter talking through a smile, frame by frame |
| `tests/output/phon_mel_relaxed.jpg` | evidence | After: the guest's mouth, frame by frame, labelled with the sound being made |
| `tests/output/body_check.txt`, `body/measured_<name>.json`, `body/body_<name>.png` | evidence | The movement measurements, their series, and a chart for each presenter |
| `tests/output/body/stills_*.jpg` | evidence | Breath out against breath in, and calm against a gust, as pairs of frames with a red and cyan overlay |
| `demo/devops-tonight.mp4`, `demo/paige-lipsync.mp4` | final | Rendered again from this build |

`gen/models/parse/` (the face parser, 94 MB) is not committed.

## Added in request 12

| File | Status | What it is |
|---|---|---|
| `demo/devops-tonight-silent.mp4` | final | The bulletin video with no sound track |
| `onepager/page.html`, `onepager/img/` | final (source) | The one-page explainer and its twenty pictures |
| `onepager/index.html` | final | The same page with its pictures inlined (2.0 MB), as published |
| `onepager/devops-tonight-how-it-was-made.jpg`, `…-8000.jpg`, `…-part1.jpg` to `part3.jpg` | final | The page as one picture at full size, as one picture 8000 px tall, and as three |
| `onepager/src/` | intermediate | Four frames of the video, and three captures: the demo page's chart, a pose sheet, a labelled mouth strip |
| `onepager/capture.js`, `make_images.py`, `build.py`, `export.js`, `stitch.py` | scripts | Gather the pictures, build the page, photograph it |

`onepager/slices/` (the photographs the pictures are stitched from) is not kept.
