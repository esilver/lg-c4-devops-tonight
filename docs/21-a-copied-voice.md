# A voice copied from a recording, with the sounds timed in the page

Asked for: the avatar speaking in the requester's own voice, really close and not an approximation, still in the
browser, and still knowing when each sound happens. They tried Pocket TTS in a browser demo with a 14 second
recording of themselves and judged it good.

## What it is

| | |
|---|---|
| The voice | Pocket TTS (Kyutai, 100M parameters, CC BY 4.0), as the community ONNX export `KevinAHM/pocket-tts-onnx` (weights only, 8-bit, 146 MB with the audio encoder left out) |
| The timing | ZIPA small (`anyspeech/zipa-small-crctc-500k`, a Zipformer CTC phone recogniser, 8-bit, 71 MB, CC BY 4.0, weights only) |
| The code that drives both | `gen/pocket.py` and `gen/align_small.py` (the same thing natively, written first), `avatar/voice/pocket.js` (in the page) |
| What both voices share | `avatar/voice/speech.js`: pronouncing, pitch, and packing a line for the engine |

Pocket TTS has no notion of when a sound happens. So each line it makes is listened to again by the recogniser, and
the line's known sounds are laid over what it hears (a Viterbi search), as `gen/align.py` did for the bulletin with a
1.2 GB recogniser. The steps are in the head of `pocket.js`.

A voice is one small file (`.pvoice`, 0.7 MB for 14 s): the recording after the model's audio encoder, made
beforehand by `gen/pocket.py voice`. The encoder is therefore not needed in the page. The recording was 18 dB below
a normal speaking level and the model copies the level too, so it is raised first.

## Measured

| | |
|---|---|
| Small aligner against exact timings (8 Kokoro lines, 336 sounds) | centres +20 ms (a constant, now subtracted); around that, half within 22 ms, 90% within 58 ms |
| Small aligner against the large one, on the copied voice | centres: half within 14 ms, 90% within 38 ms |
| The page's worker, 6 lines (words by Whisper) | 0 real errors in 81 words (2 are the recogniser's spelling) |
| The page's worker, times against the large aligner (244 sounds) | -6 ms median; half within 20 ms, 90% within 46 ms |
| Speed natively, 4 threads | a line in 0.45 to 0.57 times its length |
| Speed in headless Chromium, one thread | 1.6 times its length: the voice 1.1, the audio decoder 0.3, timing 0.1 (since brought to about 1.2: see [22](22-a-faster-copied-voice.md)) |
| A tongue-twister | came out garbled once natively: the model samples, and there is no time for second takes |

## In the page

A third group in the voice list. The page built for a face file carries that person's `.pvoice`, like the face.
The model's six files cannot be published with the page, so the viewer adds them once (links are shown) and they are
kept in the browser. Up to two workers. "Voice details" shows where the time goes.

## Checked, and not

- All page tests pass, with a test voice made from a synthetic recording.
- The copied voice was heard by its owner in clips made natively, not yet in the page.
- Speed in the real viewer is unknown; the earlier voice's 8-bit model ran no faster there than here.
- The recording and the voice file made from it are not in this repository.
