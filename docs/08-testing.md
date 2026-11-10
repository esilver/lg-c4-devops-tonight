# Testing

All checks ran in headless Chromium through Playwright 1.63 on Node 22, with software WebGL
(`--use-gl=swiftshader`). The agent that built this cannot watch video. It can read still images and numbers, so every
check below is one of those two things.

## Scripts

Run them from `tests/output/`; they write their images into the current folder. They need `playwright` to be
resolvable by Node and a Chromium for it.

| Script | What it does | Example |
|---|---|---|
| `shot.js` | Loads the page, screenshots it, changes channel, orbits, toggles power, switches to a phone-sized window. Prints page errors | `node ../shot.js` → `s1.png`…`s4.png` |
| `shot3.js` | Tunes to channels 2 to 5 and saves each picture | `node ../shot3.js` → `c2.jpg`…`c5.jpg` |
| `shot4.js` | Renders the show's picture at chosen moments by calling `chNews(t)` directly, prints the running order, and times 60 frames | `node ../shot4.js info 2 8.5 23` → `n0.jpg`… |
| `shot5.js` | Full page at double pixel density: default view, a close camera, after a channel round trip, and a phone | `node ../shot5.js` → `tv1.png`…`tv4.png` |
| `strip.js` | Renders consecutive frames from a start time at a fixed step, and dumps every line's jaw curve to `curves.json` | `node ../strip.js 7.6 0.016667 100 q` |
| `motion_check.py` | Frame-to-frame change in the mouth region against the grain floor (written for this repository from an inline check) | `python3 ../motion_check.py q 100` |
| `rec.js` | Renders the demo page frame by frame, full frame beside mouth close-up, for encoding to video | `node ../rec.js paige rec_paige` |
| `grid.py` | Tiles `n*.jpg` into a contact sheet | `python3 ../grid.py g1.jpg 1 3 4 5` |
| `shot2.js` | From the cartoon era; it reads fields the current show no longer has. Kept for the record | |
| `fake_assets.py` | From the first photographic version; see [09](09-problems-and-retries.md) | |

The recording in `demo/` was encoded with:

```
ffmpeg -framerate 30 -i rec_paige/f%04d.jpg -vf scale=1920:540:flags=lanczos -c:v libx264 -pix_fmt yuv420p -crf 20 -movflags +faststart demo/paige-lipsync.mp4
```

## What was checked on the final build

| Check | How | Result |
|---|---|---|
| The page loads and runs | `shot.js`, `shot3.js`, `shot5.js` | No page errors; WebGL 2 in use |
| Every scene of the show draws | `shot4.js` at 21 moments, viewed as contact sheets `g1.jpg`…`g3.jpg` | All layouts correct |
| Channels 2 to 5, static burst, banner, power | `shot.js`, `shot3.js` | Working |
| Phone layout | 400 × 800 window | Set in frame, remote on one line |
| Each presenter at their widest mouth | Found from the curves, rendered (`frames/k0.jpg`…`k4.jpg`) | Natural mid-word frames, no seams, no grins |
| Continuity of the mouth | A film strip of 30 frames, 67 ms apart (`seq.jpg` at the time; later overwritten) | Shapes change gradually and stay one face |
| Smoothness at 60 frames a second | `strip.js` + `motion_check.py`, 100 frames of the first anchor | Mouth region: median change 2.75, maximum 5.23. Static background, grain only: median 2.79. The mouth never changes faster than about twice the grain |
| Brow lift and blink | Frames around a brow peak and a blink (`frames/e0.jpg`…`e9.jpg`) | Subtle lift; eyes pass through half-closed |
| Speech curves | `curve1.png` | Closures on p, b, m; rounding on "Good" and "Duty"; spread on "evening" |
| Rebuild | `python3 build.py`, then a byte comparison with the published files | Identical |
| Frame cost | `shot4.js` | 5 to 9 ms per frame of the show in software rendering |

The smoothness numbers are mean absolute differences between consecutive frames on a 0 to 255 scale. Film grain is
redrawn at a random offset every frame, so even a motionless area changes by about 2.8.

## What was not checked

- **How it looks in motion.** No one watched it play during the build. The first lip-sync passed every still-frame check
  and still looked wrong when played, which is the reason for the demo page and the recording.
- **Real hardware.** No GPU, no phone, no Safari, no Firefox. WebP with transparency and WebGL 2 are assumed; WebGL 1 has
  a fallback path that was not exercised.
- **Inside the artifact viewer.** The pages were tested from `file://`. They make no network requests and use no storage,
  so the viewer's sandbox should not matter, but that was not confirmed from inside it.
- **Long runs.** Nothing ran for more than about ten seconds at a time, so slow leaks would not have shown.
- **The stale test images.** Test outputs were overwritten each round. The images in `tests/output/` are the last run of
  each script, so earlier states (the cartoon versions, the first lip-sync) are not pictured there.

## Checks during the picture pipeline

These are images, kept in `gen/out/`:

| Image | Shows |
|---|---|
| `sheet_*.jpg` | Candidate stills, for choosing seeds |
| `frame_*.jpg`, `cmp_paige.jpg` | Refined frames; face crop before and after the first inpaint |
| `cand_*_mouth.jpg`, `cand_*_blink.jpg`, `cand2_*.jpg` | Inpainted mouth and blink candidates |
| `matte_paige.jpg` | Two matting models over green |
| `lp_paige.jpg`, `lp_detail.jpg` | First re-posing test; source against neutral render against open jaw |
| `lp_sweep_paige.jpg` | The 24-pose sweep |
| `lp_masks_paige.jpg`, `lp_masks_2.jpg` | Sprite regions over the face |

## Added in request 8

| Script | What it does |
|---|---|
| `errs.js [page]` | Loads a built page and prints script errors |
| `sound_check.js [seconds]` | Turns sound on, checks decoding and the delay measurement, logs voice position against the picture clock while the bulletin plays, records the set's output to `rec.webm`, dumps the two pieces of music |
| `audio_analyse.py` | Finds each line in that recording by correlation and compares with the timeline; reports levels and the strongest pitches in the music |
| `rec_show.js <dir> [fps]` | Renders every frame of the bulletin's picture, with a timing file |
| `mux.py <dir> <out.mp4>` | Lays a sound track under rendered frames and encodes a video |
| `plot_curve.py [line]` | Draws a line's jaw and lip curves from `curves.json` |

Results on the final build are tabulated in [12](12-voices-and-sound.md). The motion check repeated on that build: mouth
region median 2.83, maximum 5.60, against 2.79 for grain alone.

Still not checked: nobody listened, and only Chromium was run.

## Added in request 9

| Script | What it does |
|---|---|
| `poses.js <presenter> <out.jpg> [name;name]` | A sheet of the face in every kind of pose, each forced directly; with names, only those, twice as large |
| `lipsync.js <page> <out.json>` | Dumps every line's mouth-opening curve from any build, on the recording's clock |
| `lipsync_check.py <json> <wav dir>` | Slides that curve against the loudness of the recording and reports the shift at which they agree best |
| `demo_check.js` | The demo page at desktop and phone width: errors, sideways overflow, the voice switch, the close-up |

`strip.js` now writes all of a line's tracks to `curves.json`, and `mux.py` fits the recording of the set's output to the
timeline at both ends, because the recorder's clock and the page's differ by a few hundredths of a percent.

Results on the final build are in [13](13-more-real.md), with the pose sheets in `tests/output/poses_*.jpg`.

Still not checked: nobody watched or listened, and only Chromium was run.
