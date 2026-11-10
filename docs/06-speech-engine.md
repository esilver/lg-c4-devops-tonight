# The speech engine

How a spoken line becomes two smooth curves, jaw opening and lip shape, that pick poses from the grid described in
[05](05-lipsync-v2-reposed-faces.md). The code is in [`src/news.js`](../src/news.js): the `VIS` table, `buildSpeech`,
`slopes`, `curve`, `speechAt`, `smileAt` and `blinkAt`. All of it runs in the browser.

This document describes the engine as it is now, driven by recordings. The version before the voices existed, which
estimated timing from a pronunciation dictionary, is summarised at the end.

## Where the timing comes from

Each line is a recording made by a speech model ([12](12-voices-and-sound.md)). The model reports the phonemes it spoke
and how long each lasted, in 25 ms frames. `src/speech.json` carries, for every phoneme of every line, its start time,
its length and its loudness, and for every caption word its start time. `build.py` inlines that as the constant `SPEECH`.

So the lips are not guessing. A `p` closes the mouth for exactly as long as the `p` in the recording lasts.

```
ɡˈʊd ˈivnɪŋ, ðɪs ɪz dˈɛv ˈɑps tənˈIt.        "Good evening, this is DevOps Tonight."
```

The symbols are the speech model's phoneme alphabet. Capital letters are diphthongs, `T` is a flapped t, `ˈ` and `ˌ`
mark primary and secondary stress on the vowel that follows, `ː` lengthens the vowel before it, and punctuation stands
for a pause of the length the model actually paused.

## Targets for each sound (`VIS`)

Each phoneme has: jaw opening from 0 to 1 (negative means lips pressed together), lip shape from −1 (rounded) to +1
(spread), how firmly it holds its opening, how firmly it holds its shape, and for diphthongs a second target.

| Sounds (as in) | Jaw | Lips | Holds jaw / shape |
|---|---|---|---|
| ɑ (father) | 0.85 | 0 | 1 / 0.6 |
| æ (cat), a (British cat) | 0.74, 0.78 | +0.35, +0.2 | 1 / 0.8, 0.7 |
| ʌ (up) | 0.5 | 0 | 1 / 0.5 |
| ɔ (call), ɒ (British wrong) | 0.62, 0.66 | −0.5, −0.35 | 1 / 1, 0.9 |
| ɛ (yes) | 0.5 | +0.4 | 1 / 0.8 |
| ɜ (work) | 0.3 | −0.45 | 1 / 0.9 |
| ɪ (is) | 0.32 | +0.5 | 1 / 0.8 |
| i (team) | 0.24 | +0.9 | 1 / 1 |
| ʊ (good) | 0.26 | −0.75 | 1 / 1 |
| u (you) | 0.2 | −1 | 1 / 1 |
| ə, ɐ, ᵊ, ᵻ (weak vowels) | 0.2 to 0.36 | 0 to +0.4 | 0.5–0.8 / 0.3–0.6 |
| W (now) | 0.75 → 0.25 | +0.1 → −0.9 | 1 / 0.7 |
| I (nine) | 0.78 → 0.3 | +0.05 → +0.7 | 1 / 0.7 |
| A (day) | 0.46 → 0.26 | +0.5 → +0.8 | 1 / 0.9 |
| O (go), Q (British go) | 0.5 → 0.22, 0.4 → 0.22 | −0.6 → −1, −0.2 → −1 | 1 / 1, 0.8 |
| Y (deploy) | 0.55 → 0.28 | −0.7 → +0.7 | 1 / 1 |
| p, b, m | −0.12 (pressed) | 0 | 1 / 0.15 |
| f, v | 0.07 | +0.2 | 0.9 / 0.5 |
| w | 0.14 | −1 | 0.7 / 1 |
| ɹ (r) | 0.22 | −0.5 | 0.5 / 0.7 |
| l | 0.32 | +0.1 | 0.35 / 0.3 |
| j (y) | 0.2 | +0.7 | 0.5 / 0.7 |
| t, d, n | 0.13 | +0.3 | 0.55–0.6 / 0.4 |
| T (flapped t) | 0.2 | +0.2 | 0.3 / 0.2 |
| s, z | 0.1 | +0.35 | 0.7 / 0.5 |
| θ, ð (th) | 0.2 | +0.15 | 0.5–0.6 / 0.3 |
| ʃ, ʒ, ʧ, ʤ (sh, ch, j) | 0.2 | −0.55 | 0.7 / 0.9 |
| k, ɡ, ŋ, h | 0.25–0.35 | 0 | 0.2–0.3 / 0.1 |

These values were chosen by judgement from how the sounds are articulated. They were not fitted to recorded faces.

## From phonemes to segments (`buildSpeech`)

- A stress mark has its own short length in the recording. That time is given to the vowel it marks.
- A space is a word gap. Time passes and nothing is targeted.
- A length mark stretches the vowel before it.
- Punctuation becomes a pause: the mouth returns to rest for as long as the recording pauses.
- A diphthong is two targets, 55 % and 45 % of its length.
- Stress scales a vowel's opening: unstressed × 0.62, secondary × 0.86, primary unchanged, weak vowels × 0.85.
- Loudness scales it again: `0.72 + 0.36 × loudness`, clamped to 0.6…1.3, where loudness is the phoneme's level relative
  to the line's median vowel. Louder syllables open wider.
- The recording starts 0.25 s into the line. Just before the first sound the lips part slightly (0.07), as for a breath.
- The line lasts until 0.3 s after the recording ends.

The sixteen lines take 100.8 seconds. With the 5-second titles and 4.5-second credits the bulletin loops every 110.3
seconds.

## Coarticulation

Real mouths do not visit every target. A `k` between two open vowels barely closes; a `p` always closes. So each sound's
effective target is a mix of its own and its neighbours':

```
effective = hold × own + (1 − hold) × (weighted mean of the two neighbours, weighted by their holds)
```

done separately for jaw (using the jaw hold) and lips (using the shape hold).

## Curves (`slopes`, `curve`)

Keyframes:

- one per sound, 45 % of the way through it;
- two for pressed lips and for pauses longer than 0.1 s, at 30 % and 78 %, so the closure is held for a moment;
- rest at the start, the breath, and rest 0.12 s after the recording ends.

Between keyframes the value follows a monotone cubic (Fritsch–Carlson). It passes through every target, keeps moving
through intermediate ones, flattens only at genuine peaks and troughs, and never overshoots (so the jaw cannot go below
closed by accident). A first idea, easing in and out between each pair of targets, was not built because it would stop
at every sound and look mechanical.

`speechAt(line, time, presenter)` evaluates both curves and returns the state used for drawing. Positive jaw values are
multiplied by the presenter's gain and clamped to −0.12…1.

## Stress drives the head and brows

`buildSpeech` records the time of every primary-stressed vowel with a weight from 0 to 1: 55 % from how loud it is and
45 % from a hash, so emphasis follows the voice without becoming mechanical.

- Weight above 0.42: a small downward nod, a Gaussian bump about 0.22 s wide, 2.3 px × weight.
- Weight above 0.7: the brows lift, a bump about 0.3 s wide, up to 85 % of the brow pose.

## Smiles (`smileAt`)

A line may list `[who, from, to]` as fractions of its length. The smile eases in over 0.3 s and, unless it runs to the end
of the line, eases out over 0.35 s. While the same person is speaking, the smile's weight is multiplied by
`1 − 5 × jaw opening` (clamped), so it gives way as soon as the mouth opens. A listener in a split screen can smile while
the other person talks.

## Blinks (`blinkAt`)

Time is cut into 1.1-second slots. Each slot has a 31 % chance of a blink at a random offset, so blinks average one every
3.5 seconds without a fixed rhythm. A blink lasts 0.27 s: 70 ms to close, 40 ms shut, 160 ms to open. It passes through
the half-closed pose on the way.

## Captions

A caption word appears when its first sound starts in the recording. Line breaks are computed on the whole line so words
do not jump between lines as they appear.

## What was measured

`tests/output/curve1.png` plots both curves for the first line with word boundaries and stress marks
(`tests/plot_curve.py`). `tests/output/curves.json` holds both curves of every line at 60 samples a second. From it, on
the final build:

| Measure | Value |
|---|---|
| Jaw-opening peaks above 0.15 | 1.5 to 3.0 per second across lines |
| Mean opening while a line plays | 0.15 to 0.29 |
| Widest opening in a line | 0.65 to 1.00 |

The smoothness check is in [08](08-testing.md) and the sound-to-picture checks in [12](12-voices-and-sound.md).

## Limits

- One opening axis. Jaw and lip opening move together; a real `f` (lower lip to teeth) or `th` is only approximated.
- The model's timing is in 25 ms steps.
- English only, and only these sixteen lines.

## The version before the voices (request 6)

Until the voices were added, there was nothing to take timing from, so it was estimated:

- `gen/phon.py` looked every word up in the CMU Pronouncing Dictionary and wrote `src/phon.json` (ARPAbet phonemes with
  stress marks). Both files are still in the repository; the page no longer uses them.
- Each phoneme had a typical length in milliseconds, scaled by stress (unstressed × 0.62, secondary × 0.9), by a rate of
  1.05, and by 1.2 for the last word of a phrase. Pauses were fixed: 0.42 s after a full stop, 0.22 s after a comma.
- Every word got a random opening factor between 0.88 and 1.12, and nods and brow lifts used that same random number.
- The mouth targets, coarticulation and curves were the same as now.

That bulletin ran 115.3 seconds. The code is in the repository's history at commit `abbc9b4`.

## Superseded in request 9

The curves described above were replaced. [13](13-more-real.md) describes what `buildSpeech` does now: three separate
tracks (jaw, lip closure, lip shape) sampled 120 times a second, timing from a forced aligner for the second voices
and corrected by 70 ms for the first, and brows, head and blinks driven by each line's phrases, stressed syllables and
pitch. The target table is the same idea with different numbers: consonants now carry a jaw height and a weight, and
p, b, m, f and v carry a closure. `speechAt` returns only the mouth; `faceAt` returns the whole face.
