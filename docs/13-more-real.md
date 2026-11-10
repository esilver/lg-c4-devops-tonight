# A more real face and voice

Request 9 came in two messages: "can we make the sound and video/lips/movements feel more real even" and "but also
lips movements needs to be better, and the eye browes everything". This document covers what changed in answer: the
lips, the brows, the eyes, the head, the voices and the sound around them.

The agent that built this cannot watch a moving picture or hear. Every claim below rests on still frames, on numbers
measured from the picture and the sound, and on a speech recogniser. Where a judgement needs an eye or an ear, the
text says so, and the page offers a way to make it (the voice switch on the demo page).

## Summary of what changed

| Area | Before (request 8) | After |
|---|---|---|
| Lip timing | about 41 ms behind the voice | about 14 ms ahead of it, as real lips are |
| Mouth poses | 17 per presenter, cross-faded | 53 per presenter, close enough together that a blend reads as movement |
| Jaw | every sound pulled it to its own target, so it chattered | follows syllables; consonants only pull it part of the way; a very short vowel never reaches full opening |
| Lip closures | part of the same curve as the jaw | their own fast track: shut by the time m, b or p starts, held to the release, never under 67 ms |
| Brows | one "raised" picture faded in | displaced on a mesh, up or down, by an amount that follows the voice |
| Head | slid and tilted as a flat picture | turns and nods on a mesh with measured parallax: the nose travels further than the ears |
| What moves the head and brows | stress marks and a random number | the loudness, pitch and length of each stressed syllable in the recording |
| Eyes | blinks at random | blinks gathered at the ends of phrases, small glances all the time, three authored looks, a guest who watches his screen |
| Smiles | only with the mouth shut | can be kept while talking |
| Voices | one set (stock voices) | a second set, re-recorded with a different speech model; both selectable on the demo page |
| Sound | dry | the viewer's room is heard, more so from further back; richer location sound; an echo on the video call |
| Pacing | every line started 0.25 s after the last ended | each line has its own lead-in; the live cross has a satellite delay |
| Page size | 3.5 MB | 4.3 MB (demo page 5.3 MB, because it carries both sets of voices) |

## The finding that mattered most: the lips were late

In request 8 the timing of each sound came from the speech model itself, which reports how many 25 ms frames it gave
to every phoneme. Adding those up gives each phoneme's start. That sum runs late, by about three frames:

- A forced aligner (below) run on the same recordings puts the phonemes 73 ms earlier than the model's sum (median of 844
  phonemes).
- The sound in each file starts 15 to 85 ms before the "first phoneme" time. Lines that begin with a voiced consonant,
  where the onset is unambiguous, are 55 to 60 ms early.
- The model's own code subtracts three frames when it reports word times, with a comment asking whether that is the
  right offset. The captions used those word times, which is why captions were on time while lips were not.

The effect on the page was measured with `tests/lipsync_check.py`, which slides the mouth-opening curve the page draws
against the loudness of the recording it plays and finds the shift at which they agree best:

| Build | Best agreement when the mouth is shifted by | Meaning |
|---|---|---|
| Request 8, as published | −41 ms (16 lines, −58 to −19) | the mouth was late |
| This build, new voices | +14 ms (16 lines, −7 to +42) | the mouth leads slightly |
| This build, first voices | +24 ms (15 lines with a clear answer, +2 to +44) | the mouth leads slightly |

A mouth that trails its voice by two video frames reads as dubbed. This is the single most likely reason the lips
"felt" wrong, and it was invisible in still frames. The measure itself understates the offset (it compares opening with
loudness, which are related but not the same thing); the aligner's 73 ms is the better estimate of what was wrong.

## Voices

### A second set of recordings (`gen/tts2.py`)

The first voices (Kokoro, request 8) read clearly and evenly. For this pass every line was spoken again by
Chatterbox, a larger open speech model (about half a billion parameters) that copies a voice from a short sample and
is built to sound less read-aloud. Each presenter's sample is one of their own first-round recordings, so the voices
stay recognisably the same five and no real person's voice is involved at any point.

```
python3.11 -m venv venv4
./venv4/bin/pip install torch==2.6.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cpu
./venv4/bin/pip install chatterbox-tts
./venv4/bin/python tts2.py 2            # two takes of each line -> work/tts2/NN_<who>_t<take>.wav
./venv4/bin/python tts2.py 5 1          # up to five takes of line 1 only
```

| Presenter | Voice sample | Expressiveness | Adherence |
|---|---|---|---|
| Paige | `work/tts/02_paige.wav` | 0.5 | 0.5 |
| Cy | `work/tts/03_cy.wav` | 0.5 | 0.5 |
| Dee | `work/tts/05_dee.wav` | 0.6 | 0.5 |
| Sunny | `work/tts/10_sunny.wav` | 0.6 | 0.5 |
| Mel | `work/tts/12_mel.wav` | 0.4 | 0.45 |

The model reads plain text, so names and abbreviations are respelled the way they should sound: "Sy DeCar", "A I",
"U S east one", "D N S", "five oh threes", "Why A Mel", "Yammel", "fin ops", "auto scaler". A take of a five-second line
takes 20 to 35 seconds on four cores. The seed of take *k* of line *n* is 100 *n* + *k*. The model marks its output
with an inaudible watermark (its publisher's, built in).

### Choosing takes (`gen/align.py`)

This model can slip: add a word, drop one, or read a name another way. Every take was therefore checked twice, and the
script picks the take with the fewest wrong words, then the one whose worst word matches its phonemes best.

1. A speech recogniser (Whisper, base English) transcribes the take. Its text is compared with the script after
   normalising things it writes differently ("2026", "US East 1", "$9,000", and its hearing of the invented names).
2. The forced aligner scores how well each word's sound matches the phonemes that word should have.

37 takes were recorded and scored: two of each line, and five more of line 1 after its first two were rejected. What the
recogniser caught:

| Line | Take | Heard | What happened |
|---|---|---|---|
| 1 | both first takes | "And I'm Side Decker" | "Sy Dekkar" was read as *Decker*, losing the pun on "sidecar". Respelled "Sy DeCar" and recorded five more times; all five are heard as "side of car" or "side to car". Take 4 was chosen. The two "Dekkar" takes are kept in `work/tts2/rejected/`. |
| 3 | 2 | ends "…is at the scene." | the closing "Dee?" is missing from the transcript; take 1 has it |
| 4 | 1 | "Say thanks, Sai." | an extra word at the start; take 2 is clean |
| 9 | 2 | "Thanks, Mage." | take 1 says "Paige" |
| 12 | 2 | "See, the agent…" | "Sy" read as "see"; take 1 says "Si" |
| 15 | 1 | "…may your pagers stay quiet" | plural; take 2 says "pager". This one was only noticed when the set's own output was transcribed (see Measurements), and the take was swapped then. |
| 6 | both | "Did anyone suggest…" | the recogniser drops the opening "Dee,". The aligner finds it: 0.18 to 0.53 s, followed by a 0.33 s pause. Kept. |

Takes chosen, lines 0 to 15: 2, 4, 1, 1, 2, 1, 1, 2, 2, 1, 1, 2, 1, 1, 2, 2. `work/tts2/takes.json` has every take's
transcript and scores. A take can be forced by hand with `work/tts2/pick.json`; none was.

### Timing by forced alignment

Chatterbox does not report when its sounds happen, so the timing is measured from the audio. A phoneme recogniser
(wav2vec 2.0, the checkpoint trained to write speech as phonetic symbols) gives, for every 20 ms, the likelihood of each
phoneme. The line's known phoneme sequence, the same one the first voices were made from, is laid over that in the most
likely way by a Viterbi search written in `align.py`. Details that mattered:

- The recogniser's alphabet is finer than the script's and writes an r-coloured vowel as one symbol. Each script phoneme
  is therefore matched by a small set of the recogniser's symbols (`CLS` in the script), and a symbol such as "ɑːɹ"
  counts for both the vowel and the r.
- The first pass, with the usual "nothing new" frames between sounds, says where each phoneme is most certain. A second
  look places the boundary between two neighbours halfway between the midpoint of their certain frames and the frame
  where the second becomes likelier than the first.
- Silence inside a phoneme's stretch is a pause, not part of the sound. Edges are pulled in to where there is signal, and
  a gap of 0.12 s or more that the script did not ask for becomes a pause of its own.
- Caption words appear with the first sound of their first spoken word. The first attempt mapped the old word times
  through the phoneme times and showed words about 180 ms early after a pause, because the old word times were on the
  corrected clock and the old phoneme times were not.

**How accurate it is.** The first voices come with exact relative timing, so they make a test
(`./venv4/bin/python align.py check`). Leaving out sounds next to pauses, where the two disagree by definition:

| | Constant difference from the model's sum | Scatter around it: median | 90% within |
|---|---|---|---|
| Phoneme starts | −73 ms | 20 ms | 55 ms |
| Phoneme centres | −62 ms | 15 ms | 47 ms |

The constant is the lateness described above. The scatter is the aligner's own error: typically under one video frame,
occasionally a frame and a half. The mouth is driven by phoneme centres.

### Pitch (`gen/audio_bundle2.py`)

Brows and head follow the pitch of the voice, so each line's pitch contour is measured (probabilistic YIN, 60 to 440 Hz,
a value every 10 ms) and stored as one character per 40 ms: half semitones above or below that speaker's median, or "-"
where the voice is not sounding. Speaker medians: Paige 198 Hz, Cy 123 Hz, Dee 117 Hz, Sunny 218 Hz, Mel 127 Hz.

The tracker also reports "pitch" in hiss and in silence. The first contours had runs of exactly +12 semitones during
fricatives and pauses, and one two-second line appeared to span 27 semitones. Three filters fixed it: a value counts
only inside a voiced phoneme (give or take 20 ms), a value more than 10 semitones from the median is discarded, and so is
one more than 4 semitones from the median of its neighbours. 58% of the 2,250 values are voiced.

### Are the new voices more real? Not shown

This is the honest position: nothing measured here says the second voices sound more real than the first.

`gen/voice_quality.py` runs two published estimators (torchaudio's "SQUIM") over both sets. One predicts the opinion score
listeners would give, judged against a recording of a real person; the other predicts standard quality measures.

| Mean of 16 lines | First voices | Second voices |
|---|---|---|
| Predicted opinion score (1 to 5) | 4.31 | 4.31 |
| Predicted quality, PESQ (1 to 4.5) | 3.56 | 3.71 |
| Predicted intelligibility, STOI (0 to 1) | 0.993 | 0.995 |
| Voice above noise and distortion (dB) | 23.8 | 23.9 |

Per presenter the opinion score differs by at most 0.04. The pitch contours do not favour the new set either: over a
line, the first voices typically range from about 3 semitones below the median to 6 or 8 above, the second voices from
about 4 below to 3 to 7 above, and the two male anchors' new voices move less than their old ones. What the second set
has is a different delivery, with its own pauses and pace (total 89.6 s against 92), which may or may not be heard as
more natural.

So both are kept. The pages are built with the second set. The demo page carries both, with a switch that re-times
the lips to whichever is playing. `python3 build.py first` builds both pages with the first set instead. If a listener
prefers the first voices, that one command is the whole change.

The first voices are also better than they were: their phoneme times are moved 70 ms earlier
(`audio_bundle2.py tts`), which is the lateness fix applied to them.

## The mouth

### 53 poses instead of 17 (`gen/lpx2.py`, `gen/lpx3.py`)

The first pose set had six jaw openings. Blending between two poses that far apart shows two faint mouths at once.
The new set, rendered with the same re-posing model as before:

| Row | Lips | Jaw openings |
|---|---|---|
| neutral | as in the photo | 12: 0 (the photo itself), 4, 8, 12, 16, 21, 26, 32, 38, 45, 52, 60 |
| e1, e2 | half and fully spread ("ee") | 8 each: 0, 5, 10, 16, 22, 30, 38, 48 |
| w1, w2 | half and fully rounded ("oo") | 8 each |
| sg | smiling | 8 |
| | lips pressed (m, b, p); half smile, mouth shut | 1 each |

Neighbouring poses differ by a pixel or two at the lips. That is 54 renders per presenter including two brow poses.
The first 45 took seven and a half to nine and a half minutes a presenter while sharing the machine with the voice
jobs; the nine smiling ones about a minute and a half.

At run time the jaw value picks two neighbouring steps in a row and the lip shape picks two neighbouring rows, so at
most four poses are blended, plus the smile row. A smile with the mouth shut grows through the half smile. Rounded
lips push a smile back, because a mouth cannot do both.

### Storage (`gen/lpexport2.py`)

Each pose used to be stored with its own soft-edged transparency. Now the poses are opaque and each region has one
shared mask, stored once. The page copies the photo's own pixels into a small canvas, adds each pose with the opacity
that leaves the exact weighted mix, cuts the result to the mask and lays it back on the cut-out without changing the
cut-out's edge. Mouth regions range from 169 × 152 (Sunny) to 315 × 279 (Dee); the 53 poses take 169 to 490 KB a
presenter.

### Three tracks instead of one (`buildSpeech` in `src/news.js`)

Three things move a mouth, at different speeds. They used to share one curve; now each has its own, sampled 120 times a
second and smoothed forwards and backwards so nothing moves faster than a face can.

| Track | Driven by | Behaviour |
|---|---|---|
| Jaw | vowels | A vowel sets a target, scaled by stress and by the loudness of that syllable in the recording. A vowel under about 0.1 s only gets part of the way. Consonants pull the jaw towards their own height with a weight: s and z strongly (teeth together), t, d, n moderately, k, g, h hardly. Pauses bring the mouth to rest; before the next phrase the lips part for a breath. |
| Lip closure | p, b, m (full), f, v (most of the way) | Shut by the moment the sound starts, held to the release (all of an m, 70% of a p), never less than 55 ms. Closing takes longer from a wide-open mouth (50 to 120 ms) than from a nearly shut one. |
| Lip shape | every sound | Rounding and spreading; strongly rounded sounds start 30 ms early and colour the weaker sounds before them. |

The opening drawn is the jaw value scaled down by the closure; full closure switches to the pressed-lips pose.
An opening of 1 is now 46 units of the re-posing model's jaw scale, where the widest pose is 60 and the old ceiling
was 68: stressed open vowels reach the low 40s, typical speech sits between 10 and 20.

Measured on the final curves (`tests/output/curves.json`):

- 57 lip closures in the bulletin; the shortest lasts 67 ms, the median 83 ms.
- The jaw changes direction 4.5 to 6.6 times a second, which is two to three open-and-shut cycles: the rate of syllables.
- The largest change of opening within one 30-frames-a-second frame is 0.54 of the scale. Before closing was made to
  take longer from a wide mouth it was 0.88: a jaw going from wide open to pressed in a thirtieth of a second.

## Brows

The re-posing model renders each face with brows raised and with brows lowered. Instead of fading to those pictures,
the page measures where the brows went (dense optical flow from the neutral render) and moves the live picture by that
field, scaled. A raised brow at half strength is the brow halfway up, not two brows.

- The field is kept only in a band from just above the upper eyelid to the hairline. Raised brows move 2.8 px (Sunny, the
  smallest face) to 7.2 px (Cy) at full strength; lowered brows move mostly inwards.
- **Dropped:** the eyes the model draws under raised brows. On Paige they widen; on Cy and Dee they droop and the
  presenter looks sleepy. The eye area now stays as it is when the brows move.
- **Fixed:** the eye region at first reached up to the brows, so an eye pose would have overwritten part of a moving
  brow. It now stops below them.

When they move: a stressed syllable that stands out and is spoken more than 1.5 semitones above the speaker's median
lifts the brows for a quarter to half a second; a question ends with them up; a little lift comes with the breath
before speaking; and they ride gently on the pitch. Emphasis on low pitch, and the one line marked grave ("Chilling."),
lowers them. First settings gave five or six lifts in a nine-second line and peaks at full strength in nine lines out of
sixteen, which is mugging; the threshold, spacing (1.3 s) and strength were brought down to 33 lifts in the bulletin,
peaking between 0.4 and 0.8.

## Head

### Real turns, as displacement fields (`gen/lp_motion.py`, `gen/lpexport2.py`)

The re-posing model was asked for each face turned 6° right and left and nodded 5° down and up. Dense optical flow from
the neutral render to each gives four fields: where every pixel of the head goes. `gen/lpflow.py` is the test that this
works: moving the neutral render by the field reproduces the real turned render with a mean difference of 2.6 to 5.0
grey levels left over, against 17 to 23 between the two renders. At 6° the nose moves 11 px (Sunny) to 21 px (Dee) while
the ears and hairline barely move, which is the parallax a flat slide cannot give.

The fields fade to nothing before the edge of the model's crop and outside the person's matte, so shoulders and
background stay still. With the two brow fields that makes six per presenter, sampled on a grid about a ninth of the eye
distance apart (7 to 12 px, roughly 50 × 47 points), stored as signed bytes with their own scale: 35 to 40 KB a
presenter.
A first version stored them in eighths of a pixel and silently clipped anything beyond 15.9 px; it was caught before the
page used it.

### The mesh (`warpGL` in `src/news.js`)

The composed presenter (cut-out plus mouth and eye poses) is uploaded as a texture to a second, small WebGL canvas and
drawn on a mesh that covers the frame. Each vertex carries the six displacements and a weight for tilting; the vertex
shader adds them up with the frame's weights, and the result is drawn back into the 2D picture. Tilt is a rotation
about the neck that fades out towards the shoulders. If that WebGL context is not available the old flat slide is used
and the brows stay put.

### What moves it (`faceAt`)

| Movement | Source |
|---|---|
| Where the head rests | Each phrase (speech between pauses) has its own slight turn, pitch and tilt, usually to the other side from the last. The shift starts just before the phrase and takes about half a second. It settles when the line ends. |
| Nods | The stressed syllables that stand out most (louder, higher, longer than their neighbours within 0.45 s). A small lift, the drop on the syllable, the return; up to about 3°. Each also turns and tilts the head a little to one side and leans the body in by a few tenths of a percent. |
| Riding the voice | The chin follows the pitch contour (higher voice, slightly higher chin) and tips back a touch as the jaw drops. |
| Before speaking | A breath: chin and brows lift slightly in the 0.4 s before the first sound. |
| Questions | Chin up and a tilt with the brows. |
| Listening | Someone on screen who is not speaking takes up a small tilt, and nods at about half of the speaker's phrase ends. Down the satellite link the reporter nods as the question lands, 0.4 of the way through his 0.85 s delay. |
| Authored | A slow shake of the head on "nobody here trusts it" and on "Chilling."; a turn towards the monitor with the looks below. |
| Always | A slow drift of a fraction of a degree. |

Over the bulletin: 80 nods, 2 to 8 a line; turns within 3.6° either way; nods to 3.7° down and 2° up; tilt within 1.5°.

## Eyes

- **Blinks** used to be random. Now about half of all phrase ends carry one, glances begin and end with one, and the
  random ones keep away from those. None is allowed in the last half second of a line, after one cut landed on closed
  eyes, and none within 0.9 s of another. One in seven random blinks is double. Whoever is speaking blinks 16 times a
  minute (31 at first settings; people in conversation average about 20 to 26, people reading far fewer).
- **Glances.** Three gaze poses (left, right, down) are blended in. The eyes make a small jump about every 0.85 s.
- **Authored looks.** Cy looks and turns towards the monitor on "Dee?" and holds it to the cut. Paige looks towards the
  weather wall on "with Sunny Uptime".
- **The guest on the video call** mostly looks at his screen, below the camera, and into the lens more often while he
  is the one talking.
- **Smiling eyes.** The eye region takes the eyes of the smile render in proportion to the smile.

## Sound (`src/sound.js`)

- **The viewer's room.** The set's sound also reaches the listener off the walls: four early reflections per ear and a
  short, dulled tail (0.42 s). It bypasses the directional cone and grows with distance: about 16 dB under the direct
  sound from the default seat; at the back of the room the direct sound has dropped 7 dB and the room is only about
  2 dB under it.
- **Exact levels.** Browsers scale a reverb's impulse response by a rule of their own. Worked through, that rule left
  request 8's "little studio room" 42 dB under the voice, which is nothing. Both rooms are now built to stated gains
  with that scaling switched off. The studio is a treated room, so it gets a trace: about 24 dB under.
- **On location.** The reporter's voice comes back faintly off the building (58 ms). Behind him: rooftop cooling plant
  (a low band around 118 Hz with two faint tones) and traffic far off that comes and goes over about 20 seconds.
  The first mix of these was far too loud, 7 dB under the voice with most of its energy between 80 and 160 Hz. It now
  sits about 14 dB under.
- **The video call.** A small bare room around a laptop microphone (27 ms echo with feedback) and the hiss of an open
  line that comes up when the guest speaks.
- **Pacing.** Each line has its own lead-in: 0.22 to 0.5 s in the studio, 0.95 s and 0.85 s for the reporter (a
  satellite delay, filled by the establishing shot the first time and by his listening the second), 0.6 s for the
  guest on the call.

Not done: breaths. The second voices have none of their own (the run-in to each line is 68 dB under the speech), and
synthetic ones could not be tuned without hearing them.

## The demo page (`src/demo.html`)

- **New voices / First voices** switches the recordings and lays the whole show out again on their timing.
- The close-up now frames brows to chin.
- The chart has five lanes on one time axis, one per measure because their scales differ: jaw opening, lip shape, the
  pitch of the voice, brows, head. A hairline under the pointer reads out all five at that moment; the playhead does the
  same otherwise. The three series colours (#3987e5, #d95926, #199e70) were checked for separation under simulated
  colour-blindness and for contrast on the panel colour; the two colours used before failed the lightness check.
- It uses the show's own presenter drawing with a switch for head movement, instead of a copy of it.

## New and changed tests (`tests/`)

| Script | What it checks |
|---|---|
| `poses.js` | One sheet per presenter with every kind of pose forced directly: turns, nods, tilt, brows, lids, gaze, smiles, and the mouth grid. `tests/output/poses_<name>.jpg` |
| `lipsync.js`, `lipsync_check.py` | The mouth-opening curve of any build against the loudness of its recordings |
| `demo_check.js` | The demo page at desktop and phone width: errors, sideways overflow, the voice switch, the close-up |
| `strip.js` | Now also writes every line's tracks at 60 samples a second: jaw, lip shape, turn, nod, tilt, brows, blink, gaze, smile, pitch, and the events behind them |
| `sound_check.js`, `audio_analyse.py`, `mux.py`, `rec.js`, `rec_show.js` | Follow the per-line lead-ins; read the bundled recordings from `gen/work/bundle/` |

## Measurements on the final build

| Check | Result |
|---|---|
| Script errors on load, both pages, at desktop and phone width | none |
| Mouth against loudness (`lipsync_check.py`, `tests/output/lipsync_report.txt`) | the mouth leads by 14 ms (−7 to +42 over 16 lines); in request 8 it trailed by 41 ms |
| Aligner against known timing (`align.py check`) | phoneme centres: median error 15 ms, 90% within 47 ms |
| Lip closures (`face_stats.py`) | 57; shortest 67 ms, median 83 ms, longest 317 ms |
| Jaw | typical opening while speaking 0.19 to 0.29 of the scale, widest 0.94; direction changes 4.5 to 7.2 a second; largest change in one 30 fps frame 0.54 |
| Head | 80 nods; turns within 3.6°, nods to 3.7° down, tilt within 1.5° |
| Brows | 33 lifts, peak strength per line 0.41 to 0.92; 2 lowerings |
| Blinks of whoever is speaking | 27 in 101 s |
| Smoothness, first line at 60 frames a second (`motion_check.py`) | mouth region: median step 2.62, largest 4.61, against 2.77 for film grain alone; no isolated jump anywhere on the head |
| Every pose forced (`poses.js`) | sheets for all five presenters were looked at; one fault found and removed (drooping eyes under raised brows) |
| Sound engine, one whole bulletin played in a headless browser (`sound_check.js`) | all 16 lines decoded and played; the voice stayed within 19.5 ms of the picture clock (mean 4.0 ms), so it was never restarted |
| Line starts in the recording of the set's output (`audio_analyse.py`) | within 34 ms of each other; the spread is a steady drift of 0.03% between the recorder's clock and the page's, not a property of the page |
| Levels in that recording | lines −22.9 to −25.1 dBFS; outdoor bed alone −37.8 (14 dB under the reporter); studio room tone −49.7; open video-call line −49.5 |
| Words after the microphone chains, echoes and beds (`asr_engine.py`, `tests/output/asr_engine.txt`) | all sixteen lines come back as scripted, allowing for the invented names ("side a car" for Cy Dekar, "YML" for Y. A. Mel) |
| Predicted opinion score (`voice_quality.py`) | 4.31 for both sets of voices |
| Cost | 18 to 25 ms a frame for the bulletin's picture, headless Chromium with software rendering |

The recording is taken before the room and listening-position stage, so the room reflections were computed, not
measured.

The videos were made from this build. `demo/devops-tonight.mp4`: 110.3 s, 1024 × 576, every frame rendered from the
page, with the engine's own recorded output fitted to the timeline at both ends. `demo/paige-lipsync.mp4`: 27.5 s, the
first anchor's four lines, full frame beside the face close-up, with the bundled recordings placed on the timeline.

## Problems and retries in this pass

1. **Two heavy jobs on four cores.** The take-scoring run did not finish in 20 minutes while pose rendering was using
   the same cores; restarted with two threads it took two and a half. The same thing made the first re-recorded take
   need 274 s and the next four 20 s each, once rendering was paused for them.
2. **Take choice, first rule.** "No wrong words, then best match" treated a take with an extra word the same as one with
   an unusual spelling, and chose "Say thanks, Sai." Changed to fewest wrong words first.
3. **A name read wrong** (line 1), found by the recogniser, fixed by respelling and five more takes.
4. **A plural** (line 15), found only when the set's own output was transcribed.
5. **Caption words early after pauses**: see Timing.
6. **Pitch tracker reporting pitch in hiss**: see Pitch.
7. **Eye region overlapping the brows; drooping eyes under raised brows**: see Brows.
8. **Motion fields clipped at 15.9 px**: see Head.
9. **Brows and blinks overdone** at first settings: see Brows and Eyes.
10. **A cut on closed eyes**: see Eyes.
11. **A jaw faster than a jaw**: see The mouth.
12. **Outdoor bed too loud; studio reverb inaudible**: see Sound.
13. **Demo close-up ran off the picture** for the two presenters who stand to one side; the framing is now clamped.
    A chart label was clipped at the left edge.
14. **The quality estimators did not separate the two voice sets**, which changed the plan from "replace the voices"
    to "offer both".

## What is still not real

- Bodies and backgrounds are still photographs. Shoulders sway and breathe as a whole; hands never move; the blurred
  figure behind the first anchor never moves.
- The head moves within about 3° of where it was photographed. Larger turns would show the limits of moving a picture.
- Teeth and tongue are whatever the re-posing model drew for each jaw opening. There is no pose for the lower lip
  against the upper teeth (f, v); those are drawn as a nearly shut mouth.
- The voices have no breaths, and whether the second set sounds more natural than the first has not been heard by anyone.
- Everything was run in headless Chromium with software rendering. The second WebGL canvas for the head was not tried
  on a phone GPU, Safari or Firefox; without it the page falls back to the flat head movement.
