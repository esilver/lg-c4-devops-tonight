# LG C4 in WebGL, showing "DevOps Tonight"

A single web page that draws a 65-inch LG C4 television in raw WebGL. The set plays five channels. Channel 1 is
"DevOps Tonight", a two-minute satirical news bulletin with five photographic presenters whose mouths, eyes and
heads move as they speak.

The page uses plain JavaScript only: one inline script, no libraries, no network requests. The presenters and
locations are AI-generated still photographs. None is a real person or place. There is no audio.

This repository holds everything that produced the page: the page source, the image and animation pipeline, every
intermediate and rejected image, the test scripts, and a written account of each step and each retry. It was built in
one working session on 9 November 2026 by an AI coding agent (Claude Code) answering seven requests in a row.

## Open it

| What | Where |
|---|---|
| The finished page | [`lg-c4/index.html`](lg-c4/index.html). Open it in a browser straight from disk. |
| One presenter, large, with slow motion and frame stepping | [`demo/index.html`](demo/index.html) |
| A 29-second recording of one presenter | [`demo/paige-lipsync.mp4`](demo/paige-lipsync.mp4), full frame beside a mouth close-up |

Controls on the main page: drag to orbit, scroll or pinch to zoom, `←` `→` change channel, `1`–`5` jump to a channel,
`P` power.

## Published copies

| Page | Link | Visibility when this was written |
|---|---|---|
| The television | https://claude.ai/artifact/MVwkTuSzuiyrPJeqyG4HhD | public |
| The single-presenter demo | https://claude.ai/artifact/FoLsFQ1fwAKpfEUVhu1FAQ | private to its owner |

## Rebuild the pages

```
python3 build.py
```

This inlines `assets.json` (the picture bundle) and `src/phon.json` (pronunciations) into `src/news.js`, then drops the
result into `src/page.html` and `src/demo.html`. Rebuilding from this repository reproduces both published pages byte for
byte.

Regenerating the pictures themselves takes about two hours on a four-core machine without a GPU and 6.6 GB of model
downloads. [`docs/03-still-images.md`](docs/03-still-images.md) and
[`docs/05-lipsync-v2-reposed-faces.md`](docs/05-lipsync-v2-reposed-faces.md) give the commands.

## What is where

```
lg-c4/index.html      the built page, as published (2.4 MB, self-contained)
demo/                 the single-presenter demo page and a recording of it
src/                  page.html (the TV), demo.html, news.js (the show), phon.json (pronunciations)
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

## Known limits

- Nobody watched the result play during the build. The agent can only inspect still frames, so smoothness was checked by
  measuring consecutive frames, not by eye. [`docs/08-testing.md`](docs/08-testing.md) has the numbers.
- There is no audio. The mouth follows a pronunciation timeline, not a voice.
- Only heads, mouths, eyes and brows move. Bodies and backgrounds are still photographs with a camera move on top.
- The page was run in headless Chromium with software rendering at desktop and phone sizes. It was not tried on a real
  phone GPU or in Safari or Firefox.
- The reporter stands in front of a glass office building, while his establishing shot is a windowless data centre.
- The news stories are jokes built on DevOps themes. They are not real 2026 headlines.
