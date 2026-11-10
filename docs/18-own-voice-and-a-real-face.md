# The avatar gets its own voice, exact lips, and a face from a photograph

Two requests, worked on side by side. The first: build the live avatar's voice on Kokoro, the cheapest way found
to have a voice that says when every sound happens ([17](17-live-avatar-poc.md) guessed the lips from spelling).
The second: make the avatar from the requester's own photograph.

## At a glance

| | [17](17-live-avatar-poc.md) | Now |
|---|---|---|
| Voice | Claude's, or the browser's | The avatar's own: Kokoro, run in the browser on the viewer's device. The borrowed voices remain as the fallback |
| Which sounds | guessed from spelling (about sixty rules) | pronounced by eSpeak NG, in the alphabet the voice model was trained on |
| When each sound happens | planned at an assumed pace, corrected by the voice's line and position signals | the durations the voice model itself used to make the audio, read on the audio clock |
| Lips against the sound | not measurable | for 29 of 29 p, b and m sounds the drawn mouth is shut within 40 ms of the sound |
| Face | one of the bulletin's five | any of the five, or one made from a photograph by the same pipeline |

## The voice (`avatar/voice/worker.js`)

Kokoro (82 million parameters) voiced the bulletin's first recordings ([12](12-voices-and-sound.md)). Its export for
browsers, `onnx-community/Kokoro-82M-v1.0-ONNX-timestamped`, returns two things for a line: the waveform, and one
duration for every sound it was given. So the times are not estimated afterwards; they are what the audio was made
from. The 8-bit file is used (`model_quantized.onnx`, 92 MB). Its durations differ from the full-precision file's
at 3 of 84 sounds, by one 25 ms step each.

A worker does three things for each line, so the picture keeps moving meanwhile:

1. **Text to sounds.** The `phonemizer` package (eSpeak NG compiled to WebAssembly) pronounces each clause as a
   whole, so little words are reduced as in speech. Its symbols are rewritten into Kokoro's alphabet, which is also
   the engine's: diphthongs and affricates become one letter (`aɪ` to `I`, `tʃ` to `ʧ`), r-coloured vowels are
   spelled out (`ɚ` to `əɹ`), length marks go. Punctuation is kept, because the model pauses on it.
2. **Sounds to audio.** onnxruntime-web runs the model on the processor. Durations come back as fractions of a
   25 ms step and are rounded as the model rounds them; their sum then matches the waveform's length exactly.
3. **Audio to what the engine needs.** Every sound with its start, length and loudness; the caption's words with
   their starts; the pitch, measured from the waveform by autocorrelation every 20 ms and kept only inside voiced
   sounds. The silence the model leaves before and after a line is trimmed, and every line is brought to one loudness.

**The 70 ms correction.** The model's audio runs ahead of the durations it reports. A forced aligner
(`gen/align.py`, a phoneme recogniser that knows nothing of the model's timing) heard each of 337 sounds 67 ms
before the reported time (median). The bulletin's pipeline had found and corrected the same constant
(`SHIFT = -0.07` in `gen/audio_bundle2.py`). The worker subtracts 70 ms; after that the aligner and the worker
differ by +2 ms (median), half the sounds within 20 ms and 90% within 60 ms. The aligner itself hears in 20 ms steps.

## The clock (`avatar/page.html`)

With a borrowed voice the page had to work out where the voice was. With its own it plays the audio itself, through
the Web Audio API, so the mouth is drawn for "the audio clock now, less the time sound takes to leave the device,
less the moment this line's first sample was scheduled". Nothing drifts and nothing is estimated.

- **Lines.** A reply is cut into sentences, a long sentence once more at a comma. Every line is asked for at once.
  Each is scheduled on the audio clock as it arrives, 0.1 s after the one before.
- **Slow devices.** One worker makes one line at a time on one core. Using several cores inside one worker needs a
  cross-origin isolated page, which a published page is not. So where the device has the cores, two or three
  workers are started, each handed the model the one before it used, and lines are made side by side.
- **Holding back.** If the lines still being made could not keep up with the speaking, the start waits, up to four
  seconds, so the reply does not stall in the middle. On a device that is slower than speech even with its workers,
  Claude is asked for one sentence.
- **Mouth size.** Real speech is quicker than the estimate was, and the engine opens the jaw less for a sound that
  is over sooner. With the voice's own times the jaw reached 0.57 at the 90th percentile, against 0.66 with
  estimated ones. Own-voice lines are scaled by 1.16 to bring that back. Lip closures are not scaled.
- **With no Claude in the view** (opened from a disk or a server), the avatar says back what is typed. That makes a
  local copy useful for looking at the lips.

## Where the voice's parts come from

`avatar/get_voice.py` fetches everything into `avatar/voice/`, pinned by version and checked by hash
(`avatar/voice_pins.json`): the model cut into parts of at most 19 MB, five voices, the two libraries. A page served
with that folder beside it runs entirely from it. None of it is committed (110 MB of other people's files).

A page published as a Claude artifact is different. Only files that were read in full are published there, and a
model, a WebAssembly runtime and a 1.3 MB bundle cannot be. So the published page carries two files, the page and
the worker, and:

- the two libraries are imported from the jsDelivr CDN (`onnxruntime-web@1.31.1`, `phonemizer@1.2.1`);
- the model and at least one voice are files the viewer adds once. The page gives the links (the Kokoro repository
  on Hugging Face), takes the files through a file chooser and keeps them in the browser (IndexedDB) for the next
  visit. If the CDN will not hand over the runtime's `.wasm` file, the page asks for that file as well;
- until then, and whenever any of this fails, a borrowed voice speaks and the lips are estimated, as in 17. The page
  says which, and why, under the picture.

## A face from a photograph

The requester's photograph went through the bulletin's pipeline as a sixth face. Three things differ from the five:

- **No diffusion.** `gen/prep_photo.py` only frames the photograph: scaled so the eyes are 98 px apart, placed on
  the 1024 × 576 frame, the plain backdrop continued to both sides. The photograph stays the photograph.
- **Its own relaxed mouth.** `REST` is smile −0.15, lips forward 3, chosen from a grid
  (`gen/relax_grid_photo.py`): at −0.10 the corners still held up, from −0.25 they turned down. No extra jaw gain.
  Opening gain 1.25.
- **Two export fixes for a plain backdrop** (`gen/lpexport3.py`, for faces listed in `PLAIN` and `OUTLINE` only): a
  smooth fill for the background plate, because the usual fill left a faint figure in it; and the mouth region faded
  out just inside the cut-out's outline, because a thin light line stood inside the jaw when the mouth was shut.
  Re-exporting two of the five with the edited script gave byte-identical files.

`avatar/build.py <face>` builds the page from `avatar/faces/<face>.json`, and the page and the avatar then say whose
face it is: animated from a photograph of the page's owner, with a stock voice that is not theirs, answered by an AI
that is not them.

**The face is not in this repository.** The photograph, everything made from it, and any page, screenshot or video
that shows it are listed in `.gitignore`. The scripts that make them are here.

What was seen on the stills, and is weak: with neutral lips the model draws only a lower row of teeth; full rounding
is a strong pout; a half blink is uneven for a frame or two; "brows down" does nothing on this face; the mouth and
eye regions are a little softer than the photograph.

## Measured

On the four shared processor cores of the build machine, in headless Chromium.

| | |
|---|---|
| Words (Whisper base on 8 test lines, 106 words) | 5 counted wrong: 3 are the recogniser's spelling ("you're" for "you are", "42%"), 2 are real ("pack" for "peck", "It" for "I") |
| Times (aligner against worker, 336 sounds) | +2 ms median; half within 20 ms, 90% within 60 ms |
| Lips on the page (7 lines, two turns) | the aligner hears 29 p, b and m; the engine's mouth is shut for all 29, its middle −3 ms from the sound's (median), all within 40 ms |
| Lips in a finished video (`avatar/record.js`, 20 s, 24 p, b and m) | a frame with the mouth shut within 150 ms of 21, by a crude count of dark and tooth-coloured pixels; nearest such frame 11 ms away (median). One of the three it missed was looked at: the lips are together there |
| Speed | on one core here a line takes 1.3 times as long to make as to say with the machine otherwise idle (34.9 s of speech in 46.3 s), and up to 1.8 times while it was also rendering poses. So on this machine the voice is slower than speech; a faster core, or several workers on idle cores, is what makes it keep up |
| First sound after Send | 5 to 8 s here, of which up to 4 s is the hold-back |
| Starting the voice | 8 to 12 s from the folder; 11 s from the viewer's files |
| As published (`avatar/test_published.js`) | first visit asks for model and voice; after adding them the voice starts and a reply is spoken with it; a voice added later appears; after a reload nothing needs adding; with no `.wasm` from the CDN the page asks for it too |

## Checked, and not

- Nobody has watched or listened. The agent cannot; the numbers above are what stands in for that.
- The published page was not run in the real viewer. Whether its frame allows WebAssembly, imports from the CDN in
  a worker, and storage, is unknown. The test answers the CDN's addresses from local copies.
- Speed on any other device is unknown. The page shows it under the picture once the voice is ready.
- Only American English, five American voices. Names and unusual words are pronounced by rule.
- Phones and Safari were not tried. Sound on iPhones uses the same unlock as the bulletin ([14](14-ios-sound-learned-lips-third-voices.md)).
- The face was judged on stills only.

## Files

| | |
|---|---|
| `avatar/voice/worker.js` | The voice: text to sounds, the model, times, pitch |
| `avatar/get_voice.py`, `avatar/voice_pins.json` | Fetch and lay out the voice's files; their hashes |
| `avatar/page.html`, `avatar/build.py` | The page; build with a presenter or a face file |
| `avatar/voice_test.js`, `avatar/test.js`, `avatar/test_published.js` | The worker alone; the page three ways; the page as published |
| `tests/voice_check.py`, `tests/video_check.py` | Words, times and lips, against a recogniser and an aligner |
| `avatar/record.js` | A video of the avatar speaking, picture and sound laid on one clock |
| `gen/prep_photo.py`, `gen/relax_grid_photo.py`, `gen/lipcal_photo.py`, `avatar/faces/*.py`, `avatar/faces/check.js` | A face from a photograph, and the sheets to judge it by |

To run it with its own voice from a disk:

```
python3 avatar/get_voice.py && python3 avatar/build.py paige
python3 -m http.server -d avatar 8000        # then open http://localhost:8000/
```
