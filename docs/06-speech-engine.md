# The speech engine

How a line of text becomes two smooth curves, jaw opening and lip shape, that pick poses from the grid described in
[05](05-lipsync-v2-reposed-faces.md). The code is in [`src/news.js`](../src/news.js): the `PHON` table, `buildSpeech`,
`slopes`, `curve` and `speechAt`. All of it runs in the browser.

## Pronunciation (`gen/phon.py` → `src/phon.json`)

The mouth is driven by sounds, not spelling. `phon.py` looks every word of the sixteen spoken lines up in the CMU
Pronouncing Dictionary (the `cmudict` package) and writes, per line, a list of `[caption word, phonemes]`. Phonemes are
ARPAbet with stress marks: `1` primary, `2` secondary, `0` unstressed.

```
Good=G UH1 D | evening,=IY1 V N IH0 NG | this=DH IH1 S | is=IH0 Z | DevOps=D EH1 V AA2 P S | Tonight.=T AH0 N AY1 T
```

Words the dictionary lacks, abbreviations and numbers are given by hand:

| Written | Spoken as |
|---|---|
| DevOps, FinOps | D EH1 V AA2 P S, F IH1 N AA2 P S |
| Cy, Dekar | S AY1, D IH0 K AA1 R |
| YAML | Y AE1 M AH0 L |
| Uptime, autoscaler, retries, config | AH1 P T AY2 M, AO1 T OW0 S K EY2 L ER0, R IY1 T R AY2 Z, K AA1 N F IH0 G |
| 2026 | "twenty twenty six" |
| us-east-1 | "you ess east one" |
| DNS | "dee en ess" |
| 503s | "five oh threes" |
| AI, Y., A. | EY1 AY1, W AY1, EY1 |

Little words use their reduced, mid-sentence forms (`the` = DH AH0, `and` = AH0 N D, `to` = T AH0, `for` = F ER0, and so
on), which is what gives the rhythm its weak beats.

`build.py` inlines `phon.json` into the page as the constant `SPOKEN`. The lines in `SHOW` and the lines in `phon.py` are
matched by order, so a change to the script needs both edited.

## Targets for each sound (`PHON`)

Each phoneme has: jaw opening from 0 to 1 (negative means lips pressed together), lip shape from −1 (rounded) to +1
(spread), how firmly it holds its opening, how firmly it holds its shape, a typical length in milliseconds, and for
diphthongs a second target.

| Sounds | Jaw | Lips | Holds jaw / shape | ms |
|---|---|---|---|---|
| AA (father) | 0.85 | 0 | 1 / 0.6 | 120 |
| AE (cat) | 0.74 | +0.35 | 1 / 0.8 | 120 |
| AH (up) | 0.5 | 0 | 1 / 0.5 | 90 |
| AO (call) | 0.62 | −0.5 | 1 / 1 | 120 |
| EH (yes) | 0.5 | +0.4 | 1 / 0.8 | 95 |
| ER (work) | 0.3 | −0.45 | 1 / 0.9 | 110 |
| IH (is) | 0.32 | +0.5 | 1 / 0.8 | 80 |
| IY (team) | 0.24 | +0.9 | 1 / 1 | 115 |
| UH (good) | 0.26 | −0.75 | 1 / 1 | 85 |
| UW (you) | 0.2 | −1 | 1 / 1 | 115 |
| AW (now) | 0.75 → 0.25 | +0.1 → −0.9 | 1 / 0.7 | 150 |
| AY (nine) | 0.78 → 0.3 | +0.05 → +0.7 | 1 / 0.7 | 150 |
| EY (day) | 0.46 → 0.26 | +0.5 → +0.8 | 1 / 0.9 | 140 |
| OW (go) | 0.5 → 0.22 | −0.6 → −1 | 1 / 1 | 140 |
| OY (deploy) | 0.55 → 0.28 | −0.7 → +0.7 | 1 / 1 | 150 |
| P, B, M | −0.12 (pressed) | 0 | 1 / 0.15 | 70–75 |
| F, V | 0.07 | +0.2 | 0.9 / 0.5 | 65–80 |
| W | 0.14 | −1 | 0.7 / 1 | 60 |
| R | 0.22 | −0.5 | 0.5 / 0.7 | 55 |
| L | 0.32 | +0.1 | 0.35 / 0.3 | 55 |
| Y | 0.2 | +0.7 | 0.5 / 0.7 | 45 |
| T, D, N | 0.13 | +0.3 | 0.55–0.6 / 0.4 | 50–55 |
| S, Z | 0.1 | +0.35 | 0.7 / 0.5 | 65–80 |
| TH, DH | 0.2 | +0.15 | 0.5–0.6 / 0.3 | 40–70 |
| SH, ZH, CH, JH | 0.2 | −0.55 | 0.7 / 0.9 | 70–90 |
| K, G, NG, HH | 0.25–0.35 | 0 | 0.2–0.3 / 0.1 | 50–65 |

These values were chosen by judgement from how the sounds are articulated. They were not fitted to recorded speech.

## Timing (`buildSpeech`)

- Every length is multiplied by `RATE` = 1.05.
- Stress scales vowels: unstressed × 0.62 length and × 0.58 opening; secondary × 0.9 and × 0.86; primary unchanged.
- Each word gets its own opening factor between 0.88 and 1.12 from a hash, so repeated words do not land identically.
- A word that ends a phrase (before `, ; . ? ! :`) is stretched × 1.2.
- A pause follows punctuation: 0.42 s after `. ? ! :` and 0.22 s after `, ;`. The mouth returns to rest during it.
- Speech starts 0.3 s into the line. Just before, the lips part slightly (0.07 at 0.2 s) as for a breath.
- A diphthong is two targets, 55 % and 45 % of its length.
- The line lasts until 0.4 s after the last sound.

The sixteen lines total 105.8 seconds. With the 5-second titles and 4.5-second credits the bulletin loops every 115.3
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
- two for pressed lips and for pauses, at 30 % and 78 %, so the closure is held for a moment;
- rest at the very start, the breath, and rest 0.16 s after the last sound.

Between keyframes the value follows a monotone cubic (Fritsch–Carlson). It passes through every target, keeps moving
through intermediate ones, flattens only at genuine peaks and troughs, and never overshoots (so the jaw cannot go below
closed by accident). A first idea, easing in and out between each pair of targets, was not built because it would stop
at every sound and look mechanical.

`speechAt(line, time, presenter)` evaluates both curves and returns the state used for drawing. Positive jaw values are
multiplied by the presenter's gain and clamped to −0.12…1.

## Stress drives the head and brows

`buildSpeech` records the time of every primary-stressed vowel with a weight from 0 to 1 (the word's random factor).

- Weight above 0.42: a small downward nod, a Gaussian bump about 0.22 s wide, 2.3 px × weight.
- Weight above 0.7: the brows lift, a bump about 0.3 s wide, up to 85 % of the brow pose.

About six in ten stressed syllables nod and three in ten lift the brows.

## Blinks (`blinkAt`)

Time is cut into 1.1-second slots. Each slot has a 31 % chance of a blink at a random offset, so blinks average one every
3.5 seconds without a fixed rhythm. A blink lasts 0.27 s: 70 ms to close, 40 ms shut, 160 ms to open. It passes through
the half-closed pose on the way.

## Captions

A caption word appears when its first sound starts. Line breaks are computed on the whole line so words do not jump
between lines as they appear.

## What was measured

`tests/output/curve1.png` plots both curves for the first line with word boundaries and stress marks.
`tests/output/curves.json` holds the jaw curve of every line at 60 samples a second. From it, on the final build:

| Measure | Value |
|---|---|
| Jaw-opening peaks above 0.15 | 1.3 to 3.2 per second across lines (the lowest is the shortest line) |
| Mean opening while a line plays | 0.15 to 0.27 |
| Widest opening in a line | 0.55 to 0.97 |

The smoothness check is in [08](08-testing.md).

## Limits

- No audio. The timing is a plausible reading, not a recording.
- One opening axis. Jaw and lip opening move together; a real `f` (lower lip to teeth) or `th` is only approximated.
- English only, and only these sixteen lines have pronunciations.
