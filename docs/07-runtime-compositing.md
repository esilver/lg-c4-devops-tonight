# How a frame of the show is put together

Source: [`src/news.js`](../src/news.js), 360 lines. It defines `chNews(t)`, which draws one frame of channel 1 into the
1024 × 576 picture canvas. It keeps no state between frames: everything is a function of the time `t`, which is why the
tests can render any moment directly.

## Data in

| Constant | Filled by | Holds |
|---|---|---|
| `ASSETS` | `build.py` from `assets.json` | `img`: six B-roll stills. `cast`: per presenter a background plate, a cut-out, face measurements, 16 mouth sprites, 3 eye sprites, an opening gain |
| `SPEECH` | `build.py` from `src/speech.json` | each spoken line: the recording, caption word times, and every phoneme with start, length and loudness |
| `SHOW` | written in the file | the running order |

Images are `data:` URIs, loaded into `Image` objects at start. Until all have decoded the channel shows a title slate.
Data URIs do not taint the canvas, so the picture can still be uploaded to WebGL and sampled for the room's light.

## The running order

`SHOW` is a list. An entry is the titles, the credits, or one spoken line with the speaker and a layout:

| Layout | Fields | Looks like |
|---|---|---|
| Solo | `who` | one presenter full frame |
| Solo with story box | `who`, `ots: [still, title]` | a box with a still and a headline beside the anchor, behind their shoulder |
| Live | `who`, `live: place` | hand-held camera, red LIVE tag |
| Cutaway | `cuts: [[fromWord, toWord, still]]` | a still fills the frame between two words while the captions carry on |
| Split | `split: [left, right]`, `title` | two panes over a blurred studio |
| Weather | `wx` | the presenter standing in front of a satellite map |

Consecutive lines with the same layout form one shot, so the camera move runs across them without a jump.

| # | Speaker | Layout |
|---|---|---|
| | | Titles, 5 s |
| 1 | Paige | solo |
| 2 | Cy | solo |
| 3 | Paige | story box "AGENTS REVIEW AGENTS"; cutaway to the paged engineer from "A human…" |
| 4 | Cy | story box "FRIDAY DEPLOY" |
| 5 | Dee | live; opens on the data-centre exterior for "Thanks, Cy." |
| 6 | Dee | live; server aisle until "Sources…" |
| 7, 8 | Cy, Dee | split |
| 9 | Paige | story box "CLOUD FORECAST" |
| 10, 11 | Sunny | weather |
| 12, 13, 14 | Cy, Mel, Cy | split, with Mel on a video call |
| 15 | Paige | solo |
| 16 | Cy | solo |
| | | Credits, 4.5 s |

## Drawing one presenter (`drawActor`)

Each presenter owns two off-screen canvases the size of the frame.

1. **Compose** (`compose`). The cut-out is drawn. Then the mouth: `mouthLayers` turns the jaw and lip values into
   weights on up to four sprites (two jaw levels on the neutral row, two on the spread or rounded row; a pressed-lips
   sprite below zero). `mix` draws weighted layers so that, inside their shared mask, the result is the exact weighted
   average, with the photograph taking whatever weight is left. Then the eyes: brow lift, half-closed and closed, mixed
   the same way.
2. **Warp** (`warp`). The composed cut-out is copied to the second canvas in tiles. Tiles far from the head are 64 px
   and are not moved. Tiles within 3.3 eye-distances of the head are 16 px and are shifted by a smooth bump that is
   strongest at the head and zero at its edge: a sideways drift, an up-and-down bob plus the stress nods, and a small
   tilt about the base of the neck. Tiles overlap by one pixel so no seams open.
3. **Place.** The background plate is drawn; then anything that belongs between background and person (the story box);
   then the warped cut-out, rotated a fraction of a degree about a point far below the frame (a slow sway) and scaled
   slightly more than the background.

While a presenter speaks the head motion runs at full strength; while listening, at 30 %.

Why the warp is done in an untransformed canvas first: tiles drawn straight into the zoomed and rotated picture would
get antialiased edges and show a faint grid. Drawing them on whole-pixel positions and placing the result with a single
draw avoids that.

## Camera

- **Solo:** a slow push-in from 1.035× to 1.085× over the shot, about the frame centre. The person is scaled 1.2 % to
  3.4 % more than the background about their face, which gives depth.
- **Story box:** starts at 1.10× and shifts 46 px so the anchor moves away from the box. The box goes on whichever side
  the anchor leaves free.
- **Live:** the same push-in plus a hand-held wobble of a few pixels and a fifth of a degree.
- **Stills** (titles, cutaways): 1.07× to 1.14× with a 34-pixel drift.

## Other layouts

- **Split.** Each pane crops 5.9 eye-distances of height around the face. The speaker's pane has a white border. Mel's
  pane is copied through a 231 × 170 buffer at 15 frames a second to look like a video call.
- **Weather.** The satellite still at 1.22× with a slow drift and a blue tint; three forecast tiles (`Pending`, `99.99%`,
  `503`) with small animated icons; the tile being talked about is outlined, switching on a word of the line. The
  presenter's cut-out is drawn with no background plate, scaled 1.08×, with her face at (250, 250).

## On top

- Film grain: a 256 × 256 noise tile at a random offset each frame, blended in overlay mode at 11 %, and a vignette. Both
  go under the graphics, as a camera's would.
- Channel logo top right; LIVE tag and place name top left on live shots.
- Name strap, the first time each presenter is on camera, for 3.8 seconds.
- Captions, centred, a word at a time ([06](06-speech-engine.md)).
- Ticker at the bottom with a clock showing the viewer's local time.
- Credits include the line "Presenters and locations are AI-generated stills, animated in plain JavaScript".

## Cost

In headless Chromium with software rendering, a frame of the show takes 5 to 9 ms. A shot draws between roughly 700 and 1,800
small tiles, depending on how large the face is in frame, and up to seven sprites.

## The demo page

[`src/demo.html`](../src/demo.html) includes the same `news.js` untouched and adds its own `drawPresenter`, a copy of
`drawActor` with switches for head movement and parallax, plus a transport bar and a chart of the two speech curves. It
plays each presenter's lines back to back. Time there is virtual, so half speed slows blinks and head movement too.

## Added in request 8

- `showAt(t)` returns the line on air and the time into it. `chNews` and the sound engine both use it, so picture and
  sound always agree on where the bulletin is. `cutAt(line, time)` does the same for cutaways.
- `drawActor` takes a smile weight, and stretches the cut-out by ±0.35 % about the bottom of the frame as breathing.
- The page now carries [`src/sound.js`](../src/sound.js). Everything about sound is in [12](12-voices-and-sound.md).
- The sprite count per presenter is 17 mouth poses and 3 eye poses. The built page is 3.5 MB.

## Changed in request 9

Drawing one presenter is now ([13](13-more-real.md) has the detail):

1. `faceAt` works out the whole face for this moment: mouth, smile, blink, gaze, brows, head.
2. `compose` copies the cut-out, then for the mouth region and the eye region blends the poses in a small canvas of
   the region's size, cuts the mix to the region's shared mask and lays it on the cut-out.
3. `warpGL.draw` uploads that picture to a second WebGL canvas and draws it on a mesh moved by six displacement fields
   and a tilt. Without WebGL there, `warpFlat` does the old slide.
4. The background plate, anything between (the over-the-shoulder box), then the warped presenter with the body's sway,
   lean and breathing.

Presenters are animated on the show's clock, not the wall clock, so a given moment of the bulletin always looks the
same. A second set of recordings can be swapped in with `buildShow(set)`, which lays the bulletin out again.

Cost in headless Chromium with software rendering: about 18 to 25 ms a frame for the bulletin's picture.
