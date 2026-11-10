# LG C4 in WebGL, showing "DevOps Tonight"

A single web page that draws a 65-inch LG C4 television in raw WebGL. The set plays five channels. Channel 1 is
"DevOps Tonight", a two-minute satirical news bulletin with five photographic presenters who speak, with mouths, eyes
and heads that move with their voices.

The page uses plain JavaScript only: one inline script, no libraries, no network requests. The presenters and
locations are AI-generated still photographs, and the voices are synthetic. None is a real person or place.

This repository holds everything that produced the page: the page source, the image and animation pipeline, every
intermediate and rejected image, the test scripts, and a written account of each step and each retry. It was built in
one working session on 9 and 10 November 2026 by an AI coding agent (Claude Code) answering eight requests in a row.

## Open it

| What | Where |
|---|---|
| The finished page | [`lg-c4/index.html`](lg-c4/index.html). Open it in a browser straight from disk. |
| One presenter, large, with slow motion and frame stepping | [`demo/index.html`](demo/index.html) |
| The whole bulletin as a video with sound | [`demo/devops-tonight.mp4`](demo/devops-tonight.mp4), 1 min 50 s |
| One presenter's lines as a video with sound | [`demo/paige-lipsync.mp4`](demo/paige-lipsync.mp4), full frame beside a mouth close-up |

Controls on the main page: drag to orbit, scroll or pinch to zoom, `←` `→` change channel, `1`–`5` jump to a channel,
`P` power, `M` sound, `-` `=` volume. Sound starts off, because browsers only allow audio after a click or key press.

## Published copies

| Page | Link | Visibility when this was written |
|---|---|---|
| The television | https://claude.ai/artifact/MVwkTuSzuiyrPJeqyG4HhD | public |
| The single-presenter demo | https://claude.ai/artifact/FoLsFQ1fwAKpfEUVhu1FAQ | private to its owner |

## Rebuild the pages

```
python3 build.py
```

This inlines `assets.json` (the picture bundle) and `src/speech.json` (the recorded lines and their timing) into
`src/news.js`, then drops that and `src/sound.js` into `src/page.html` and `src/demo.html`. Rebuilding from this repository
reproduces both published pages byte for byte.

Regenerating the pictures and voices themselves takes about two hours on a four-core machine without a GPU and 7 GB of
model downloads. [`docs/03-still-images.md`](docs/03-still-images.md) and
[`docs/05-lipsync-v2-reposed-faces.md`](docs/05-lipsync-v2-reposed-faces.md) give the commands.

## What is where

```
lg-c4/index.html      the built page, as published (2.4 MB, self-contained)
demo/                 the single-presenter demo page and a recording of it
src/                  page.html (the TV), demo.html, news.js (the show), sound.js (audio), speech.json (voices and timing)
src/history/          the two earlier versions of the show code that were kept
build.py              assembles the two pages
assets.json           the picture bundle that build.py inlines (data: URIs)
gen/                  the picture pipeline: scripts, logs, model list, and every image it made
gen/out/              candidate stills, contact sheets, final B-roll stills, comparison images
gen/work/<name>/      per presenter: refined frame, face crop, matte, every mouth and eye variant, re-posed renders
tests/                headless-browser scripts used to check the page, and their last outputs
docs/                 the written account
```

## Documentation

| File | Covers |
|---|---|
| [`docs/01-timeline.md`](docs/01-timeline.md) | The seven requests, what each produced, and when |
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

## Known limits

- Nobody watched or listened to the result during the build. The agent can only inspect still frames and numbers, so
  motion was checked by measuring consecutive frames and sound by measurement and a speech recogniser.
  [`docs/08-testing.md`](docs/08-testing.md) and [`docs/12-voices-and-sound.md`](docs/12-voices-and-sound.md) have the numbers.
- The voices are stock synthetic voices. They read clearly and evenly; they do not act.
- Only heads, mouths, eyes and brows move. Bodies and backgrounds are still photographs with a camera move on top.
- The page was run in headless Chromium with software rendering at desktop and phone sizes. It was not tried on a real
  phone GPU or in Safari or Firefox.
- The news stories are jokes built on DevOps themes. They are not real 2026 headlines.
