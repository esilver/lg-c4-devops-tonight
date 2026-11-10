# LG C4 in WebGL, showing "DevOps Tonight"

A single web page that draws a 65-inch LG C4 television in raw WebGL. The set plays five channels. Channel 1 is
"DevOps Tonight", a two-minute satirical news bulletin with five photographic presenters who speak. Their lips, brows,
eyes and heads move with their voices. The mouths follow a lip-sync network's reading of each recording, fitted to each
face; brows and heads follow the pitch and stress of the voice.

The page uses plain JavaScript only: one inline script, no libraries, no network requests. The presenters and
locations are AI-generated still photographs, and the voices are synthetic. None is a real person or place.

This repository holds everything that produced the page: the page source, the image and animation pipeline, every
intermediate and rejected image, the test scripts, and a written account of each step and each retry. It was built in
one working session on 9 and 10 November 2026 by an AI coding agent (Claude Code) answering ten requests in a row.

## Open it

| What | Where |
|---|---|
| The finished page | [`lg-c4/index.html`](lg-c4/index.html). Open it in a browser straight from disk. |
| One presenter, large, with slow motion, frame stepping, a face close-up and a switch between three sets of voices | [`demo/index.html`](demo/index.html) |
| The whole bulletin as a video with sound | [`demo/devops-tonight.mp4`](demo/devops-tonight.mp4), 1 min 50 s |
| One presenter's lines as a video with sound | [`demo/paige-lipsync.mp4`](demo/paige-lipsync.mp4), full frame beside a face close-up |

Controls on the main page: drag to orbit, scroll or pinch to zoom, `←` `→` change channel, `1`–`5` jump to a channel,
`P` power, `M` sound, `-` `=` volume. Sound starts off, because browsers only allow audio after a click or key press.

## Published copies

| Page | Link | Visibility when this was written |
|---|---|---|
| The television | https://claude.ai/artifact/MVwkTuSzuiyrPJeqyG4HhD | public |
| The single-presenter demo | https://claude.ai/artifact/FoLsFQ1fwAKpfEUVhu1FAQ | private to its owner |

## Rebuild the pages

```
python3 build.py            # the current voices (the third set, Phonon)
python3 build.py second     # the same pages with the second set (Chatterbox) instead
python3 build.py first      # ... or the first set (Kokoro)
```

This inlines `assets.json` (the picture bundle) and `src/speech.json` (the recorded lines, their timing and their pitch)
into `src/news.js`, then drops that and `src/sound.js` into `src/page.html` and `src/demo.html`. The demo page also gets
`src/speech_first.json` and `src/speech_second.json`, the two earlier sets of voices, for its switch. Rebuilding from this repository reproduces both published
pages byte for byte.

Regenerating the pictures, voices and lip reference themselves takes about four and a half hours on a four-core machine
without a GPU and 11 GB of model downloads. [`docs/03-still-images.md`](docs/03-still-images.md),
[`docs/05-lipsync-v2-reposed-faces.md`](docs/05-lipsync-v2-reposed-faces.md), [`docs/12-voices-and-sound.md`](docs/12-voices-and-sound.md)
[`docs/13-more-real.md`](docs/13-more-real.md) and
[`docs/14-ios-sound-learned-lips-third-voices.md`](docs/14-ios-sound-learned-lips-third-voices.md) give the commands.

## What is where

```
lg-c4/index.html      the built page, as published (4.3 MB, self-contained)
demo/                 the single-presenter demo page (6.3 MB) and two recordings
src/                  page.html (the TV), demo.html, news.js (the show), sound.js (audio), speech.json (voices, timing, pitch),
                      speech_first.json and speech_second.json (the two earlier sets of voices)
src/history/          the two earlier versions of the show code that were kept
build.py              assembles the two pages
assets.json           the picture bundle that build.py inlines (data: URIs)
gen/                  the picture pipeline: scripts, logs, model list, and every image it made
gen/out/              candidate stills, contact sheets, final B-roll stills, comparison images
gen/work/<name>/      per presenter: refined frame, face crop, matte, every mouth and eye variant, re-posed renders
gen/work/tts*/        every recording of every line, both speech models, with timing; gen/work/bundle*/ as inlined
tests/                headless-browser scripts used to check the page, and their last outputs
docs/                 the written account
```

## Documentation

| File | Covers |
|---|---|
| [`docs/01-timeline.md`](docs/01-timeline.md) | The ten requests, what each produced, and when |
| [`docs/02-webgl-tv.md`](docs/02-webgl-tv.md) | The television model, shaders, camera, channels and remote |
| [`docs/03-still-images.md`](docs/03-still-images.md) | Generating the photographs: model, prompts, seeds, picks, refinement, matting |
| [`docs/04-lipsync-v1-inpainted-mouths.md`](docs/04-lipsync-v1-inpainted-mouths.md) | The first lip-sync, which looked unnatural, and why |
| [`docs/05-lipsync-v2-reposed-faces.md`](docs/05-lipsync-v2-reposed-faces.md) | The second lip-sync: one face re-posed into a grid of mouth and eye poses |
| [`docs/06-speech-engine.md`](docs/06-speech-engine.md) | From a line of text to smooth jaw and lip curves |
| [`docs/07-runtime-compositing.md`](docs/07-runtime-compositing.md) | How each video frame is put together in the browser |
| [`docs/08-testing.md`](docs/08-testing.md) | What was checked, how, and what was not |
| [`docs/09-problems-and-retries.md`](docs/09-problems-and-retries.md) | Every failure, dead end and second attempt |
| [`docs/10-asset-inventory.md`](docs/10-asset-inventory.md) | Every image and data file, and whether it is final, intermediate or rejected |
| [`docs/11-models-and-licences.md`](docs/11-models-and-licences.md) | The models used, where they came from, and what to check before reuse |
| [`docs/12-voices-and-sound.md`](docs/12-voices-and-sound.md) | The second pass: voices, lips timed to them, sound design, visual fixes |
| [`docs/13-more-real.md`](docs/13-more-real.md) | The third pass: late lips found and fixed, 53 mouth poses, brows and head moved on a mesh by the voice, a second set of voices, room sound |
| [`docs/14-ios-sound-learned-lips-third-voices.md`](docs/14-ios-sound-learned-lips-third-voices.md) | The fourth pass: sound on iPhone, lips taken from a lip-sync network and fitted to each face, the guest repaired, a third set of voices |

## Known limits

- Nobody watched or listened to the result during the build. The agent can only inspect still frames and numbers, so
  motion was checked by measuring consecutive frames and sound by measurement and a speech recogniser.
  [`docs/08-testing.md`](docs/08-testing.md), [`docs/12-voices-and-sound.md`](docs/12-voices-and-sound.md) and
  [`docs/13-more-real.md`](docs/13-more-real.md) have the numbers.
- There are three sets of synthetic voices. The pages use the third, from the highest-ranked open speech model that
  runs on this machine; the demo page switches between all three. Stronger models exist that could not be run here.
  None of the sets has breaths.
- Sound on iPhone and iPad depends on a fix that could not be tried on a real device.
- The mouths follow a network's reading of the sound. That is better founded than the hand-written rules it replaced,
  but it is still a model's opinion, and there is no pose for f and v.
- Heads, mouths, eyes and brows move, and shoulders sway and breathe as a whole. Hands and backgrounds are still
  photographs with a camera move on top.
- The page was run in headless Chromium with software rendering at desktop and phone sizes. It was not tried on a real
  phone GPU or in Safari or Firefox. The head movement uses a second WebGL canvas; without one it falls back to a
  simpler movement.
- The news stories are jokes built on DevOps themes. They are not real 2026 headlines.
