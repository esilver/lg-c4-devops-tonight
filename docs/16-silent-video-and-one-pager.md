# A silent version of the video, and a one-pager to share

Request 12: "can you make a version with just the video and no sound, and then make a one pager i can share on reddit
that shows the proccess of animating the people and what local models were used with images".

## The silent video

`demo/devops-tonight-silent.mp4` is `demo/devops-tonight.mp4` with the sound track removed: the same pictures, copied
without re-encoding (107.2 s, 1024 × 576, 5.1 MB).

```
ffmpeg -i demo/devops-tonight.mp4 -an -c:v copy -movflags +faststart demo/devops-tonight-silent.mp4
```

**A fault found on the way.** The ticker shows the time of day, read from the computer's clock. The video's frames
are rendered several times slower than they play, so in every earlier render the clock on screen gained several
minutes during a two-minute bulletin. `tests/rec_show.js` now makes the page's clock follow the bulletin's own time
while it renders: it starts at the moment rendering starts and advances with the picture. Both versions of the video
were rendered again with that fix (12:27 at six seconds in, 12:29 at a hundred).

## The one-pager (`onepager/`)

One page that shows, with pictures, how the presenters are animated and which models did what. All of them ran
locally, on four CPU cores.

| What | Where |
|---|---|
| The page, self-contained | `onepager/index.html` (2.0 MB) |
| The page as published | https://claude.ai/artifact/J9BWy4AQMGYFciULjomtvm (private to its owner when this was written; the owner shares it from that page) |
| The page as one picture | `onepager/devops-tonight-how-it-was-made.jpg` (2400 × 17,054) and `…-8000.jpg` (scaled to 8000 px tall, for places that refuse taller pictures) |
| The page as three pictures | `onepager/devops-tonight-how-it-was-made-part1.jpg` to `part3.jpg`, cut at section boundaries, for a gallery |

It has eight steps, each with the models used and a picture: a generated photograph, the cut-out, the 65 re-posed
stills, the voice and its timing, the lip reference, the motion fields, the body and hair maps, and the browser.
It ends with a table of the twelve models and whether each one's output is in the page, and four plain notes: nothing
in it is real, it was built by an AI coding agent, where the technique stops, and that licences differ.

**Where its pictures come from** (`onepager/make_images.py`, `onepager/capture.js`):

| Picture | Source |
|---|---|
| The television | The television page in a headless browser, camera moved in, the bulletin held at 6.6 s |
| The five presenters | `gen/work/<name>/frame_lp3.png` |
| Photograph, matte, cut-out, plate | `gen/work/dee/frame.png`, `alpha.png`, `plate3.jpg` |
| Every kind of pose | `tests/poses.js paige`: the page itself forced into each pose |
| The lip-sync network's own picture | `gen/out/w2l_proto_paige.jpg`, from request 10 |
| The mouth, frame by frame | `tests/phoneme_strip.js paige 0 0.3 30 20` |
| The chart of one line | The demo page's chart, photographed at twice the pixel density |
| A turn and a nod as arrows | Drawn from the displacement fields in `gen/cast3.json`, two and a half times their length |
| Body and hair maps | Drawn from `gen/work/<name>/body.json` |
| One breath; what moves | `tests/output/body/stills_paige_breath.jpg`, `body_paige.png` |

To make it again, from the repository root:

```
node onepager/capture.js
(cd tests/output && node ../poses.js paige ../../onepager/src/poses_paige.jpg && node ../phoneme_strip.js paige 0 0.3 30 20 ../../onepager/src/phon_paige.jpg)
gen/venv6/bin/python onepager/make_images.py && python3 onepager/build.py
node onepager/export.js && gen/venv6/bin/python onepager/stitch.py
```

**Design.** The page borrows the bulletin's own broadcast graphics: its navy and mint, a channel band across the top,
and a name strap for each step like the ones that name the presenters on air. It is one column, with wide pictures
running the full width, and it stacks on a phone.

## Checked, and not

- The page was looked at once as rendered, at 1200 px wide; it does not overflow sideways and its three web fonts
  load. It was not opened on a phone.
- Every figure in it is taken from this repository's own numbers: 65 poses a face, 321 images in the bundle, sixteen
  recordings, a 4.4 MB page, about 1,400 lines of page code.
- Licences in it are described from memory, as in [11](11-models-and-licences.md), and it says to check the model cards.
- It links to the television page's public copy. It contains no name, address or other detail of the requester.
