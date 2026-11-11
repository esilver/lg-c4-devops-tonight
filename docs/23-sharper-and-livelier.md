# A sharper picture and a livelier face

Asked: the avatar made from a photograph is "still uncanny valley"; make it look more real. Worked in rounds on one
short clip (`avatar/record.js`, two lines, 30 pictures a second): one change, render, look at stills, measure, keep or
revert. Nobody watched it move; what was looked at and what was only measured is said at the end.

## At a glance

| | Before | Now |
|---|---|---|
| Fine detail of the eyes in a finished picture (variance of the Laplacian; the photograph has 332) | 74 | about 240 looking at the viewer |
| The same for hair, and for the shirt | 80, 70 | 360, 245 |
| Skin texture kept in the stored cut-out (cheek; photograph 10.5) | 4.1 | 7.6 |
| Pictures in which the eyes are the photograph's own, not a softer pose mixed in | 17% | 57% |
| Blinks in the clip | 35 a minute, two 0.33 s apart | 23 a minute, at least 2 s apart |
| Longest stretch without a blink in a minute, mostly at rest | 14 s | 4.8 s |
| A blink | 270 ms, three to four pictures shut, brows soft | 220 ms, two to three shut, brows untouched |
| Glances away | none (darts of under a pixel) | while finding the words of about half the longer phrases; now and then when listening |
| Tilt of the head while speaking | within 1° | within 3.3° |
| Pictures in which the head is all but still, while speaking | 19% | 5% |
| The head at rest | 0.03 px a picture over 8 s: a photograph that blinks | resettles every few seconds: 0.04 px a picture, within 2 by 3 px over 8 s and 10 by 5 px over 50 s. Still little |
| Page built from the photograph | 1.50 MB | 1.64 MB |

## Where the softness came from

Measured along the way from the photograph to the screen, on the eyes:

1. **The stored poses.** Wherever a mouth or an eye can change, the page is made of re-posed renders, and the model
   that makes them draws a little soft: 332 became 260. The cut-out was also stored at a WebP quality that removed
   skin texture.
2. **The page.** The picture was resampled twice with plain averaging of the four nearest pixels: by the mesh that
   turns the head, and again by the 2D canvas for the presenter's slight zoom, at a fractional offset. 233 became 74.
   This was most of it, and it applied to the five generated faces as much as to the photograph.

What was done (`src/news.js`, `avatar/page.html`, `gen/lpexport3.py`):

- The mesh reads the picture with a Catmull-Rom cubic (nine reads), and does the zoom itself, so the picture is
  resampled once. The avatar page draws at a whole-pixel offset.
- What one resampling still takes (about a third of the finest detail at half a pixel off) is given back by adding
  part of the difference from the four neighbours, inside the figure only, so the outline gets no rim. The amount
  (0.2) was set so that a finished picture measures what the stored picture does, not more; 0.45 overshot the photograph.
- For a face made from a photograph, the exporter moves the photograph onto every render (dense optical flow) and
  takes what is finer than a few pixels from the photograph, where the two show the same thing. Teeth, the inside of
  the mouth, shut lids and a turned iris stay the render's. Detail travels with the skin when the jaw drops.
- Poses are stored at WebP quality 86 instead of 80 and the cut-out at 96 instead of 88, for such a face. That is the
  0.14 MB. (Quality 92 for the poses came to 1.87 MB for little more.)
- The eyes rest exactly on the viewer two thirds of the time. They used to sit a little off centre always, which
  moved the iris by less than a pixel and cost a quarter of their sharpness, since any gaze pose is a render mixed in.

The teeth were not the flat band they looked: the raw renders have separate teeth. The band was the page's blur.

## Eyes and head

- **Blinks** that belong to the speech are kept on the show's clock, so one cannot be followed at once by the next
  line's or a stray one. Stray blinks come one in every three seconds or so, anywhere in them, not by a small chance
  every second (which now and then left the eyes open for a quarter of a minute). A blink is shorter and hardly held.
  The eye poses of a photograph keep the neutral picture above the lids: the model lowered and softened the brows when
  it shut the eyes.
- **Glances.** A speaker looks aside while finding the words of about half the longer phrases: eyes first, the head a
  touch after, back well before the phrase ends, often with a blink on the way out. A listener looks away now and
  then. Glances go nearly all the way to the gaze pose, because half-way the pose and the photograph's eyes show as
  two irises. The downward pose is really lowered lids, and is used less.
- **Head.** A larger tilt with each phrase, a third-size nod on the lesser stresses, a wander while speaking, and a
  resettle every few seconds whether speaking or not. A nod's return takes twice as long as its drop (it was as
  quick, a twitch of 3° in a seventh of a second once the nods were larger).
- This face is packed with more movement and sway: `python3 avatar/faces/pack.py me 1.3 1.5 4 0.5 0`.

The mesh was first pushed to four fifths of its measured turn and nod and 3.4° of tilt on stills, with no fault at the
neck or the outline, so the movement added stays inside what it can draw.

## Tried and not kept

- **Camera grain on the avatar page** (the bulletin's, at a third of its strength). The photograph has almost no
  noise and the backdrop does not change at all between pictures, which may be one of the things that says "a still".
  But the change is too small to see in a still and is a moving effect; nothing showed it to be better.

## Checked, and not

- Looked at: stills of every round, enlarged; consecutive pictures through blinks, a glance, the largest jumps of the
  mouth, the largest tilt. Measured: sharpness in fixed boxes, the engine's own record of gaze, blinks, head and body
  for every picture, differences between consecutive pictures.
- One frame placed twice side by side did not look the same on both sides to the one judging (the right copy looked
  darker and softer). So sharpness is claimed from the numbers and from pairs looked at in both orders, never from
  one side-by-side.
- Not judged: anything at speed. Whether the nods, the wander and the glances feel right, whether blinks sit well with
  the speech, whether the head at rest now moves enough (by the numbers it is still close to still), and the sound.
- `node avatar/test.js`: all seven lines ok. The bulletin and demo pages build and load without script errors with
  the changed engine; they are not rebuilt in the repository here.
- Phones were not tried. Per picture the mesh now makes thirteen texture reads for each of 0.6 million pixels instead
  of one; nothing else was added to a frame.

## What still looks made

- The shut-eye pose itself (one lid puffier than the other) and the half-shut picture, which is a cross-fade. A gaze
  to one side is weaker than to the other. Both need new poses from the re-posing model.
- With neutral lips only a lower row of teeth; no tongue.
- The picture is 1024 pixels wide. A phone screen has more; the photograph does too (1.56 times).
- The light on the face does not change as the head turns.
- No expression follows what is being said: a greeting is spoken with the same face as anything else.
