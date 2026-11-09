# Lip-sync, first attempt: inpainted mouths

This version was published at 21:38 and judged "funny, not natural". It was replaced by the method in
[05](05-lipsync-v2-reposed-faces.md). Everything it produced is kept here as the record of the attempt.

- Show code: [`src/history/news_photo_v1_inpainted_mouths.js`](../src/history/news_photo_v1_inpainted_mouths.js)
- Pipeline: second half of `gen/prep.py`, `gen/extra.py`, `gen/export.py`, `gen/assets.py`, `gen/picks.json`
- Images: `gen/work/<name>/mouth_*.png`, `blink_*.png`, `export/`, and the sheets `gen/out/cand_*.jpg`, `cand2_*.jpg`
- Bundle: `gen/cast_assets.json`

## Idea

Keep the photograph and repaint only the mouth. For each presenter, ask the image model for several versions of the
512 × 512 face crop in which the mouth is in a different position, cut each mouth out as a small sprite, and have the page
swap sprites as the presenter speaks. Blinks work the same way with the eyes.

## Making the variants

Inpainting ran on the face crop (`face0.png`), with the same model that made the photograph. The model has no special
inpainting weights, so the sampler repaints the masked area and, at every step, puts back the rest of the image at the
matching noise level.

| Setting | Value |
|---|---|
| Strength | 0.92 (15 of 16 steps) |
| Guidance | 6.0 |
| Mouth mask | ellipse, centre 0.20 × mouth width below the mouth centre, radii 0.78 × and 0.58 × mouth width, blurred 6 px |
| Eye mask | two ellipses on the eye centres, radii 0.36 × and 0.22 × the eye distance, blurred 5 px |
| Prompt | "RAW photo, close-up portrait of *description*, *mouth or eye wording*, detailed skin texture, sharp focus" |
| Time | about 31 seconds each |

The variants came in four rounds, each a response to what the previous one produced.

**Round 1, Paige only** (seeds 101, 102; files `mouth_small_*`, `mouth_open_*`, `mouth_ee_*`, `mouth_oo_*`, `blink_*`):

| Name | Wording | What came out |
|---|---|---|
| small | lips slightly parted, mouth slightly open, speaking | closed lips both times |
| open | mouth open, talking, teeth visible, saying ah | an open smile with teeth |
| ee | mouth wide, talking, showing upper teeth, saying ee | 1: slightly open; 2: a wide grin |
| oo | lips rounded and pushed forward, mouth small and round, saying ooh | closed lips, no rounding |
| blink | eyes closed, eyelids shut, eyelashes | convincing closed eyes both times |

The blinks worked at once. The mouths either stayed shut or smiled.

**Round 2, everyone** (`mouth_closed_1`, `mouth_sm_1/2`, `mouth_open_1/2`, `mouth_oh_1/2`, `mouth_ee_1`, `blink_1/2`).
The wording changed, and "smile, grin, laughing" went into the negative prompt for the neutral shapes:

| Name | Wording | Extra negative |
|---|---|---|
| closed | lips pressed together, mouth closed, neutral expression | smile, grin, laughing |
| sm | lips parted, mouth slightly open, mid-sentence, neutral expression | smile, grin, laughing |
| open | mouth open, talking, teeth visible, saying ah | none |
| oh | mouth open in a small round O shape, saying oh, surprised | smile, grin, laughing, teeth |
| ee | mouth wide, talking, showing upper teeth, saying ee | none |

"Surprised" was the word that finally produced a neutral open mouth. For Paige `oh_1` is a relaxed open mouth and `oh_2` a
round O.

**Round 3, four presenters** (`mouth_ah_1/2` with seeds 103 and 104, `mouth_oh_3` with seed 103): "jaw dropped, mouth
open, speaking mid-word, neutral expression", to get open mouths that are not grins.

**Round 4, Cy only** (`gen/extra.py`: `mouth_wide_1/2/3`, seeds 105 to 107, strength 1.0, guidance 7): his mouths barely
opened in rounds 2 and 3. "mouth wide open, speaking loudly, saying ah, teeth and tongue visible" gave one very wide and
one natural open mouth.

## Which were used (`gen/picks.json`)

The page had five mouth shapes besides rest: 1 slightly open, 2 open, 3 teeth, 4 round, 5 lips pressed.

| Presenter | 1 | 2 | 3 | 4 | 5 | Blink |
|---|---|---|---|---|---|---|
| Paige | sm_2 | oh_1 | ee_1 | oh_2 | closed_1 | blink_1 |
| Cy | ah_2 | wide_2 | open_2 | oh_2 | closed_1 | blink_2 |
| Dee | ah_2 | ah_1 | open_1 | oh_2 | closed_1 | blink_2 |
| Sunny | oh_3 | ah_1 | open_1 | oh_2 | closed_1 | blink_1 |
| Mel | open_1 | ah_2 | ee_1 | oh_2 | sm_2 | blink_1 |

Every other variant in `gen/work/<name>/` was generated and not used.

## How the page used them

- Each letter of the caption mapped to a shape: `a` open, `e i` teeth, `o u w` round, `m b p` pressed, other letters
  slightly open, punctuation rest.
- Each character lasted 62 ms, with 200 ms at commas and 340 ms at full stops.
- The shape was sampled every 90 ms and cross-faded over 55 ms.
- A blink every 3.3 to 5.2 seconds, faded in and out.

## Why it looked wrong

1. **Different mouths, not one mouth moving.** Each sprite was a separate generation. Teeth, lip thickness and expression
   changed from sprite to sprite: one is a pout, the next a toothy smile. Swapping them reads as a face changing
   expression eleven times a second.
2. **A cross-fade is not motion.** Fading from a closed mouth to an open one shows both at half strength. Lips never
   travel.
3. **Letters are not sounds.** "Tonight" has a silent `gh`; "one" starts with a `w` sound. Spelling gave the wrong shapes
   and an even, mechanical rhythm with no stress.
4. **The jaw never moved.** Only the lip area was repainted.

What did work and was carried forward: the photographs, the face crop and landmarks, the cut-outs, the idea of sprites
that share one soft mask, and the head warp.
