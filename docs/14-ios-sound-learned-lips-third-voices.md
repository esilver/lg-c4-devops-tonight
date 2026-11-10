# Sound on iPhone, lips from a learned reference, and a third set of voices

Request 10: "Need to fix sound on iOS, also ty lips and the old yaml man still feel off. And the audio model still
leaves to be desired". Four things, taken in turn: the page was silent on iPhones; the lips still looked wrong; the guest
(Y. A. Mel, "the old YAML man") looked wrong; and the voices were not good enough.

As before, the agent that built this cannot watch or listen, and it has no iPhone. What follows is measured or
reasoned, and says which.

## Summary

| Area | Before (request 9) | After |
|---|---|---|
| Sound on iPhone and iPad | silent whenever the ringer switch is off | the page asks iOS for a playback audio session inside the tap; the Sound button shows what is actually happening |
| Lips | opening and shape from a hand-written table of sounds | opening and shape measured from a lip-sync network that was shown each recording, then fitted to each face |
| How far each mouth opens | one hand-set gain per presenter | calibrated: each face is driven until its measured opening matches the reference |
| The guest's mouth | opened about half as far as the others at the same setting | opens as far as the reference says |
| The guest's eyes | nearly shut most of the time (the "watching his screen" pose) | he looks into the camera like the others |
| The guest's picture | 15 pictures a second at half resolution | 25 a second at two thirds, drawn half a picture ahead |
| The guest's voice | cut to telephone bandwidth and overdriven | a laptop microphone in a small room, nearly full bandwidth |
| Voices | Chatterbox (second set), Kokoro kept as an alternative | Phonon (third set), with both earlier sets on the demo page's switch |

## Sound on iPhone and iPad (`src/sound.js`)

**Cause, by reasoning.** On iOS, sound made with the Web Audio API belongs to the "ambient" class, which the ringer
switch silences. Video and audio elements belong to the "playback" class, which it does not. That fits what was
reported: the page was silent on the phone while the MP4 files sent alongside played with sound.

**Fix.** Inside the tap that turns sound on, `sndUnlock()`:

1. sets `navigator.audioSession.type = 'playback'` where that exists (iOS 17 and later);
2. on iPhones and iPads, starts a looping, silent `<audio>` element, which moves the whole page into the playback
   class on older systems;
3. starts a one-sample source, because older systems only unlock an audio context when a source starts in the gesture.

The sound is picked up again when the page returns to the front. The Sound button now reports one of four states: off,
loading (recordings still decoding), on, or "tap again" when the device has not let the context run; a tap in that
state retries instead of switching off.

**What was and was not tested.** Chromium emulating an iPhone runs the new code path without error, the silent element
plays and pauses with the button, and the session type is set. Nothing here can flip a ringer switch, so the fix
itself is unverified until someone tries it on a phone.

## Lips from a learned reference (`gen/lipteach.py`)

Two rounds of rules had been tried: a table saying how far each sound opens the jaw, then the same with three separate
tracks and better timing. The timing was right by measurement and the result still looked wrong. The table itself was
the weak point: it was written by hand, and nothing checked it against real mouths.

This round asks a network trained on real talking faces. Wav2Lip takes a face and 0.2 s of sound and paints the mouth
that goes with the sound. Its picture is 96 pixels across and soft, so it is never shown. It is measured:

1. **Paint.** For every 1/50 s of every line, Wav2Lip paints the mouth on the presenter's own neutral frame.
2. **Measure.** A face-landmark network (2DFAN4, 68 points) finds the lips in that picture. Two numbers are kept: the gap
   between the inner lips and the width of the mouth, both in eye distances.
3. **Calibrate.** The same measurement is made on every pose render of every presenter, passed through the same 96-pixel
   keyhole so both are measured alike (`work/lipcal.json`). That says which of a presenter's own poses shows a given
   opening on that face.
4. **Translate.** The reference's opening becomes a jaw position on that presenter's scale; its width, compared with the
   presenter's neutral, spread and rounded rows at that opening, becomes the lip shape. The curves are stored one
   character per 1/50 s in `speech.json` and the page plays them through the sharp poses.

Details that mattered:

- **Timing.** With the stock windowing (the window of sound starts at the frame's own time) the reference's lips shut
  about a tenth of a second before the sounds. Starting the window 75 ms earlier left it still early. How early is
  measured from the audio itself: a "p" has a stretch of silence while the lips are closed, and the reference's lips
  should be tightest in the middle of it. Over the p sounds with a clear silence the reference was 36 ms early in the
  new voices (34 and 44 ms in the two older sets), so it is moved 40 ms later. An earlier estimate that used the
  aligner's m, b and p segments gave nearly the same figure but for a bad reason (its search window often caught a
  neighbouring f or v), and was replaced.
- **A common footing.** The reference's picture of a shut mouth does not measure like the photograph's; in pauses it often
  leaves the lips apart; and it opens some faces far more timidly than others, whatever voice they are given (the same
  two presenters came out smallest in all three sets of voices). So each presenter's readings are standardised: the 12th
  percentile while speaking is "shut" (that is where their m, b and p readings lie) and the 90th percentile is the same
  opening for all five, 0.126 eye distances above shut, set 15% above the middle presenter's because the reference
  under-opens as a whole. The first version took "shut" from the pauses instead, which left one presenter's mouth shut
  for a third of her speech.
- **Pauses.** In a pause the mouth comes to rest whatever the reference drew: nearly shut in a long one, slightly parted
  in a short one.
- **Lip closures.** The reference closes the lips for m, b, p, f and v by itself, at about the right moments. The page adds
  only a guarantee: a short press (30 ms in, 30 ms out) in the middle of each m, b and p, so the lips truly meet. The
  first version kept request 9's closure track, with its long ramps, on top of the reference; together they swallowed
  short vowels between two closures. In "DevOps" the "o" disappeared.
- The rule-based tracks remain in `buildSpeech` and are used for any line that has no reference.

**What the reference showed.** On the first line measured, the reference's typical opening corresponded to 16 jaw units
on that presenter's scale and its widest to 57; the rules had given about 11 and 43. The mouths had been opening about
a third too little: mumbling. And the faces differ far more than the hand-set gains allowed:

| Opening above rest, in eye distances | Paige | Cy | Dee | Sunny | Mel |
|---|---|---|---|---|---|
| at jaw 16 | 0.063 | 0.066 | 0.060 | 0.056 | 0.033 |
| at jaw 32 | 0.126 | 0.127 | 0.123 | 0.115 | 0.074 |
| at jaw 60 (the widest pose) | 0.213 | 0.233 | 0.231 | 0.210 | 0.179 |

At the settings ordinary speech uses, the guest's mouth opened about half as far as anyone else's. His hand-set gain had
been the lowest of the five.

## The guest

Four separate faults, found by looking at his pane frame by frame and at his pose sheet:

1. **His mouth barely moved** (above). Fixed by the calibration.
2. **His eyes were nearly shut.** A guest on a video call was meant to look at his screen, below the camera, using the
   "eyes down" pose at 60%. On his face that pose lowers the lids almost all the way, behind glasses, so he looked
   drowsy for most of the interview. The behaviour is removed; he looks into the camera like the others.
3. **His picture stuttered and lagged.** The video-call look held each picture for 1/15 s, so his lips were on average
   33 ms late and visibly jerky. It is now 25 pictures a second at two thirds resolution instead of half, and he is
   drawn 20 ms ahead so the held picture is on time on average.
4. **His voice was the worst-sounding in the bulletin.** The call effect cut everything above 3.6 kHz and overdrove what
   was left: a telephone, not a video call. It is now a laptop microphone in a small bare room: nearly full bandwidth,
   a little boxiness, a short echo, and much lighter saturation.

His voice is also new, and older (below).

## A third set of voices (`gen/tts3.py`)

**Why the second set was a mistake.** In request 9 the lines were re-recorded with Chatterbox on its reputation, and
two quality estimators could not separate it from the first set. This time the public blind-test leaderboard for open
speech models (Artificial Analysis, read on 10 November 2026) was consulted first. It ranks by listeners' preferences:

| Model | Score (Elo) | Used here as |
|---|---|---|
| Phonon 31M (English), Gradium, October 2026 | 1114 | third voices |
| Kokoro 82M | 1062 | first voices |
| Chatterbox | 1021 | second voices |

So the second set had been a step down from the first by listeners' ears, which is what the requester heard. Four
entries rank above Phonon: two versions of a model with 35 billion parameters, which does not fit this machine; one
reported as licensed for research only; and one (Ming-3.0-tts) that needs its publisher's own program, which this
session does not run unreviewed, and that was only tested on large graphics cards. Phonon is the highest-ranked model
that could be run here; it is small (31 million parameters), Apache-licensed, installs as a package and speaks about
ten times faster than real time on this CPU.

```
python3.12 -m venv venv5
./venv5/bin/pip install ptts soundfile numpy
./venv5/bin/python tts3.py 3            # three takes of each line -> work/tts3/NN_<who>_t<take>.wav
./venv4/bin/python align.py tts3        # choose takes, time every sound -> work/tts3/lines.json
./venv4/bin/python audio_bundle2.py     # level, trim, pitch, encode -> ../src/speech.json, work/bundle/
```

**Cast.** Phonon comes with 37 named English voices, each with a written description. Nobody here can listen, so the
cast was chosen from those descriptions:

| Presenter | Voice | The publisher's description, shortened |
|---|---|---|
| Paige | Harper | modern, confident and friendly, standard American accent |
| Cy | Miles | resonant and decisive, with genuine dynamic range |
| Dee | Easton | punchy and close in, crisp consonant attack |
| Sunny | Juniper | cheerful presence with real resonance under it |
| Mel | Master Aldric | an old British man, rich and resonant with an aged grain, deliberate pace with weighted pauses |

The guest's earlier voices were of men decades younger than his picture. "Master Aldric" is one of the catalogue's
character voices (a wizard of about eighty), chosen for the aged grain; three alternatives were recorded and measured
(`work/tts3/alt_*`): Edwin and Spencer, brisker and younger, and Old Mortlake, far lower (84 Hz median) and half
whispered. Whether a wizard reads YAML jokes well is a judgement for a listener.

**Takes.** Three per line to begin with (seeds 100 × line + take), scored as in request 9 by a speech recogniser and by
how well each word matches its phonemes. What the recogniser caught:

| Line | Heard | What was done |
|---|---|---|
| 0 | "Paige Judy" in two takes, and again when the set's own output was transcribed | the model says "Duty" with a y-glide. Respelled "Dooty" and recorded again: all three new takes are heard as "Doody", which is "Duty" as an American says it |
| 3, take 1 | "UNADS East 1" | takes 2 and 3 are right |
| 10, all three | "a chance of retrees … in agress" | the model stresses both words wrongly. Respelled "re-tries" and "ee-gress", recorded again; all three new takes are heard correctly |
| 13 | "Shilling." in two takes of three, and in the third when the set's own output was transcribed | the model's "ch" is soft. Six more takes did not settle it: two passed on their own and one of those still came out of the set as "Shilling". Respelled "Tchilling": five trial takes were all heard as "Chilling" three ways (plain, through a duller filter, and through MP3 and Opus as the page and the recorder apply them). Three new takes recorded |
| 14, take 1 | "…what it costs" | takes 2 and 3 are right |

63 takes were recorded in all. The fifteen replaced ones are kept in `work/tts3/rejected/`, the trial respellings in
`work/tts3/respell/`. Takes chosen, lines 0 to 15: 1, 1, 3, 3, 2, 2, 2, 2, 2, 2, 3, 3, 2, 3, 3, 3.

**All three sets are kept.** `src/speech.json` is the third set. The demo page carries all three with a switch named by
model (Phonon, Chatterbox, Kokoro). `python3 build.py first` or `second` builds both pages with an earlier set.

## Measurements

On the final build, with the third voices:

| Check | Result |
|---|---|
| Script errors on load, both pages, desktop and phone width; the voice switch; the close-up (`errs.js`, `demo_check.js`) | none |
| iPhone-only sound code in an emulated iPhone (`ios_sound_check.js`) | runs on both pages: keep-alive element playing, session type set, context running, 16 lines decoded; stops again on the second tap |
| The reference against the sounds, before the page touches it | mean opening on open vowels 0.54, mid vowels 0.39, close vowels 0.41, s z t d n 0.44, w and r 0.11 with the lips rounded (shape −0.45), m b p 0.04, f v 0.03 |
| The reference's timing (`lipteach.py map`) | lips tightest 35 ms before the middle of the silence of a p (17 sounds; half of them between 48 and 18 ms), moved 40 ms later |
| The reference against the forced lip presses | of 60 m, b and p sounds the reference's own opening at the press is under 0.07 for three quarters; over 0.3 for five |
| Mouth on the page (`face_stats.py`) | typical opening while speaking 0.34 to 0.50 per line (request 9's rules: 0.19 to 0.29), widest 0.71 to 1.09; direction changes 3.4 to 8.5 a second; 58 lip presses |
| Head, brows, eyes | 61 nods, 28 brow lifts, 18 blinks a minute by whoever is speaking; turns within 3.7°, nods to 3.4° down |
| Smoothness, first line at 60 frames a second (`motion_check.py`) | mouth region: median step 2.69, largest 5.26, against 2.78 for film grain alone; no isolated jump anywhere on the head |
| Sound engine, one whole bulletin (`sound_check.js`) | all 16 lines decoded and played; voice within 9.1 ms of the picture clock, mean 3.0 ms |
| Line starts in the recording of the set's output (`audio_analyse.py`) | within 7.9 ms of each other |
| Levels in that recording | lines −22.9 to −26.1 dBFS; the guest on the call −23.8 (3 dB hotter than the others before his chain was levelled); outdoor bed alone −41.1; studio room tone −49.6 |
| Words after the microphone chains and beds (`asr_engine.py`, `tests/output/asr_engine.txt`) | all sixteen lines come back as scripted, allowing for the invented names ("Paige Doody", "side to car", "why ML") |

**Mouth against loudness.** `lipsync_check.py`, which in request 9 showed the lips 41 ms late and then 14 ms early,
gives +4 ms here but is no longer a sharp instrument: the agreement at the best shift is 0.24, against 0.45 for the
rule-based mouth. The old mouth was built partly from the loudness of each syllable, so it agreed with loudness by
construction. The reference opens the mouth for what is being said, which is related to loudness but is not the same
thing; its timing is checked against the silences of p sounds instead (above).

The videos were made from this build. `demo/devops-tonight.mp4`: 107.2 s, 1024 × 576, every frame rendered from the
page, with the engine's own recorded output fitted to the timeline. `demo/paige-lipsync.mp4`: 26.7 s, the first
anchor's four lines, full frame beside the face close-up, with the bundled recordings placed on the timeline.

## Problems and retries in this pass

1. **MediaPipe's landmark model could not be used**: the current package no longer bundles it. A 68-point landmark
   network in ONNX form was used instead, with glue written here.
2. **The lip reference was 80 ms early** with the stock windowing (above).
3. **Two mispronounced words** in the new voices (above).
4. **The first cast for the guest clipped**: one take peaked at 1.05 and the first files were written as 16-bit. Takes are
   now written as floating point and levelled later.
5. **Measuring is slow**: about four pictures a second on four cores, so 14 minutes for the 4,300 fiftieths of a second
   of the new voices. The two older sets were measured 25 times a second instead of 50.
6. **The first mappings of the reference were wrong in three ways**, each found by looking at a strip of mouth frames
   labelled with the sound being made (`tests/phoneme_strip.js`) or at the numbers: "shut" was taken from the pauses,
   where the reference leaves the lips apart; the timing was estimated in a way that caught the wrong closures; and
   request 9's closure track, kept on top, swallowed short vowels. All three are described under "Details that mattered".
7. **A lip press in the wrong place**: a "p" after a pause is given the whole pause by the timing, and a press in the
   middle of that shut an open mouth a fifth of a second early. The press for p and b now sits just before the release.
8. **Three words needed respelling** for the new model, two of them only found by transcribing the set's own output.
9. **The session's machine restarted twice** while pages were being published; each time the publish was checked
   before being repeated.

## What is still not right, or not known

- The iPhone fix has not been tried on an iPhone.
- The lip reference is itself a network's opinion. It was trained on real faces and is far better founded than a
  hand-written table, but its mouths are soft and it tends to under-open rather than over-open.
- There is still no pose for the lower lip against the upper teeth (f, v).
- Three stronger speech models exist that could not be run here. The largest is far beyond this machine. If a better
  voice is wanted than Phonon gives, the practical routes are a machine with a graphics card, or a commercial speech
  service and an API key.
- Nobody has heard any of the three sets except the requester.
