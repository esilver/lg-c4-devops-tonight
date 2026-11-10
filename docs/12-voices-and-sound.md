# Voices, sound and the second polish pass

Request 8 was "can we make it even better? with perfect audio and just better overall?". This document covers what was
added in answer: spoken voices, lips timed to those voices, sound design, positional audio, and a round of visual fixes.

The agent that built this cannot hear. Everything said about the sound below comes from measurements and from a
speech recogniser, never from listening. Whether the voices are pleasant is for a person to judge.

## Summary of what changed

| Area | Before | After |
|---|---|---|
| Voices | none | 16 spoken lines, five voices, 92 seconds |
| Lip timing | a plausible reading computed from a pronunciation dictionary | the actual length of every sound in the recording |
| Other sound | none | title and closing music, room tone, outdoor air, a video-call sound, server-room hum, TV static and clicks, sounds for the other four channels |
| Listening position | none | level falls with camera distance and off to the side; muffled behind the panel |
| Faces | speech, blinks, brow lifts, nods | plus smiles at seven moments and breathing |
| Room | flat console top with a stepped artefact | artefact fixed; the picture reflects in the lacquered top |
| B-roll | three stills that did not match the script | regenerated |
| Bulletin length | 115.3 s | 110.3 s |
| Page size | 2.4 MB | 3.5 MB |

## Voices (`gen/tts.py`)

The lines are spoken by Kokoro, an open text-to-speech model with 82 million parameters, run on the CPU. It takes
about three seconds to speak a five-second line.

```
python3.12 -m venv venv3
./venv3/bin/pip install torch --index-url https://download.pytorch.org/whl/cpu
./venv3/bin/pip install "kokoro>=0.9" soundfile "misaki[en]"
./venv3/bin/pip install https://huggingface.co/spacy/en_core_web_sm/resolve/main/en_core_web_sm-any-py3-none-any.whl
./venv3/bin/python tts.py            # writes work/tts/NN_<who>.wav and work/tts/lines.json
```

| Presenter | Voice | Accent | Speed |
|---|---|---|---|
| Paige | `af_heart` | American | 1.0 |
| Cy | `am_michael` | American | 1.0 |
| Dee | `am_puck` | American | 1.04 |
| Sunny | `af_bella` | American | 1.0 |
| Mel | `bm_george` | British | 0.96 |

These are the model's stock voices. No real person's voice was cloned or imitated.

### Shown one way, said another

A caption word written `{shown|spoken}` in `tts.py` is displayed as the first part and spoken as the second. Inside the
spoken part, `[word](/phonemes/)` fixes a pronunciation.

| Shown | Spoken |
|---|---|
| 2026 | twenty twenty-six |
| us-east-1 | U.S. east one |
| AI | A.I. |
| DNS | D-N-S, given as phonemes so the full stop after it still makes a pause |
| 503s | five-oh-threes |
| Y. A. | Y A |
| autoscaler | auto-scaler |
| Cy, Dekar, YAML, FinOps | pronunciations given as phonemes |

### What the model reports

Besides audio, the model returns the phoneme string it spoke and how many 25 ms frames each phoneme lasted. Those two
lists are the lip-sync. For the first line:

```
ɡˈʊd ˈivnɪŋ, ðɪs ɪz dˈɛv ˈɑps tənˈIt. ˌIm pˈAʤ dˈuTi, ænd jˈɛs, ˌI ɐm ˌɔn kˈɔl.
```

Capital letters are diphthongs (`A` as in day, `I` as in nine, `O` as in go, `W` as in now, `Y` as in boy), `T` is the
flapped t of "duty", `ˈ` and `ˌ` mark stress, and punctuation carries the length of its pause. `tts.py` records, for every
phoneme, its start, its length and its loudness, and for every caption word the time it starts.

### Checking the words (`gen/asr_check.py`)

Each line was transcribed by Whisper (base, English) and compared with the script. Six of sixteen matched word for word.
The other ten differed only in how the recogniser wrote things down:

- numbers as digits: "2026", "40", "503s", "$9,000", "4,000";
- names by ear: "Sai", "Si" and "say" for Cy, "page" for Paige, "D." for Dee, "Deploy" for Dee Ploy;
- two puns that work when heard: "side to car" for Cy Dekar, and "YAML" for Y. A. Mel;
- "underway" for "under way", "auto scaler" for "auto-scaler".

No line had a wrong, missing or extra word.

## Packaging (`gen/audio_bundle.py` → `src/speech.json`, `src/calib.txt`)

Per line:

1. Trim to 60 ms before the first sound and 160 ms after the last, with short fades.
2. Measure loudness with ffmpeg's EBU R128 meter and apply a plain gain to reach −19 LUFS.
3. Round off the rare peak above 0.6 with a soft knee, so the highest sample is 0.89. The first version scaled whole
   lines down to fit their peaks, which left one presenter 2 dB quieter than the others.
4. Encode as MP3, mono, 24 kHz, 64 kbit/s: 17 to 71 KB a line, 973 KB of base64 in total.
5. Express each phoneme's loudness relative to the line's median vowel.

`src/speech.json` holds, per line, the MP3 as a `data:` URI, its length, the caption words with start times, and 1,416
phoneme entries across all lines. `build.py` inlines it as the constant `SPEECH`.

### The decoder-delay problem

MP3 encoders add a short start-up delay, and browsers differ in whether their decoder removes it. Left alone that could
put the voice up to 46 ms late in some browsers. `src/calib.txt` is a 3 KB MP3 of silence with a tone burst at exactly
0.100 s, encoded with the same settings. The page decodes it once, sees where the burst lands, and shifts every line by
the difference. In Chromium the measured delay was 0 ms and every decoded line had exactly its original length.

## Lips from the recording (`src/news.js`)

[06](06-speech-engine.md) describes the engine. What changed in this pass:

- The table of mouth targets is keyed by the speech model's phoneme symbols (`VIS`), with the same values as before.
- Each phoneme's start and length come from the recording. Nothing is estimated.
- Pauses are the lengths the model actually paused at punctuation.
- Loudness scales the opening: a vowel's jaw target is multiplied by `0.72 + 0.36 × loudness`, clamped to 0.6…1.3.
- Nods and brow lifts land on loud stressed syllables, with a random share so they are not mechanical.
- The recording starts 0.25 s into its line (`LEAD`) and the line ends 0.3 s after it (`TAIL`).

## The sound engine (`src/sound.js`)

Plain Web Audio, 177 lines, inlined into both pages by `build.py`.

### Starting

Browsers do not let a page make sound until the viewer clicks or presses a key, so the set starts silent. The **Sound**
button (or `M`) creates the audio graph, decodes the sixteen lines, measures the decoder delay, and renders the music.
`VOL −` / `VOL +` (or `-` / `=`) change the level; a volume bar appears on the TV picture.

### The graph

```
voice ─┐
beds  ─┼─ master ─ low-pass (occlusion) ─ panner (the set, in the room) ─ output
music ─┤
TV    ─┘
```

Each kind of voice has its own microphone chain:

| Chain | Used by | Processing |
|---|---|---|
| studio | Paige, Cy, Sunny | high-pass at 70 Hz, and a 5 % send to a 0.35-second room reverb made from decaying noise |
| field | Dee | high-pass at 170 Hz, +3 dB at 2.6 kHz, low-pass at 7.5 kHz, no room |
| call | Mel | band-limited to 280 Hz–3.6 kHz, +4 dB at 900 Hz, gentle saturation |

### Keeping voice and picture together (`sndPlay`)

Every frame the engine works out where in the recording it should be: time into the line, minus `LEAD`, plus the measured
decoder delay, plus the output latency the browser reports, minus 20 ms for the display's own delay. If the playing
source is within 80 ms of that, nothing happens. Otherwise it is restarted at the right offset. So a tab that was asleep,
a channel change or sound switched on mid-sentence all pick up in sync.

The position is computed from the clock as it is at that moment, not from the frame's timestamp. An early version used
the frame's timestamp, and a late frame then pulled the voice backwards.

### Synthesised sound

Nothing below is a recording. All of it is generated in the browser.

| Sound | When | How |
|---|---|---|
| Title music | the 5-second titles | Rendered once with an offline audio context. D major at 132 beats a minute: a sixteenth-note pulse on D, a brass figure D–A–D, then B–A into a held D major chord, three drum hits, a cymbal swell, an opening whoosh |
| Closing music | the credits | The chord with a falling figure D–A–F♯–D |
| Room tone | studio scenes | Low-passed brown noise, very quiet |
| Outdoor air | Dee's report, and his half of the split screen at a lower level | Brown noise below 1.1 kHz plus a little hiss, with a slow gust |
| Server room | the server-aisle cutaway | Low rumble, a 100 Hz hum, fan hiss |
| Static | a channel change | 0.32 s of band-passed noise |
| Power | on and off | a low thump; a short falling tone |
| Channel 2, Plasma | while tuned | three triangle waves as a soft pad |
| Channel 3, Screensaver | each bounce | a blip; three rising notes for a corner |
| Channel 4, Deploy Log | while tuned | a low hum and a tick as each line scrolls in |
| Channel 5, Test Card | while tuned | a quiet 1 kHz tone |

### Where the listener is

The listener is the camera and the set is a source at the panel. Level falls with distance (full at the default
2.55 m). The source has a 140° cone facing the room, so level drops off to the side, and behind the panel a low-pass
filter closes from 18 kHz toward 1.3 kHz. Orbiting does not pan the sound left or right, because the camera always
faces the set.

## The demo page

`demo/index.html` has its own **Sound** button. The recording follows the playhead, including scrubbing and frame
stepping. At half and quarter speed the voice is slowed, which lowers its pitch.

## Visual changes in this pass

| Change | Detail |
|---|---|
| Smiles | One more re-posed render per presenter (`lp/f_smile.png`, smile 0.5, mouth closed), cut as a 17th mouth sprite. A line can list `[who, from, to]`; the smile eases in and gives way as the mouth opens to speak. Used seven times: both anchors at the end of their greetings and sign-offs, Paige handing to the weather, Sunny as she starts, and Cy as Dee says "moved to the platform team" |
| Breathing | The cut-out is stretched vertically by ±0.35 % about the bottom of the frame on a 4.2-second cycle, so shoulders and head rise and settle by about a pixel |
| Reflection | Upward-facing glossy surfaces (console top, stand plate) follow the reflected ray to the screen plane and add the picture there, blurrier and fainter with distance. With the console this shallow it shows only from a raised camera, which is physically right |
| Console artefact | The console body and its top slab had coplanar top faces and flickered against each other as a stepped pattern, visible since the first version. The body now stops under the slab |
| B-roll | `dcext2` seed 52: a glass-and-concrete building like the one behind the reporter. `paged2` seed 51: the engineer now holds a lit phone. `office2` seed 52: dusk, not daylight. The model still would not make the office dark |
| Remote | Sound and volume buttons. On phones the volume buttons are hidden |

## Measurements

From `tests/sound_check.js` and `tests/audio_analyse.py`, which turn sound on in headless Chromium, play one whole
bulletin in real time, and record the set's output.

| Check | Result |
|---|---|
| Lines decoded | 16 of 16, each exactly its original length |
| Decoder delay measured by the calibration clip | 0 ms |
| Output latency reported by the browser | 32 ms |
| Scheduled voice position against the picture clock | mean 3.5 ms, maximum 10.6 ms, over 802 samples and 16 lines |
| Where each line starts in the recording against the timeline | all 16 within 8.9 ms of one another, after a constant offset from the recorder starting late |
| Level of each line in the recording | −23.1 to −24.6 dBFS |
| Level of the title music | −25.8 dBFS, just under the voices |
| Strongest pitches in the music | 73, 147, 293, 587 Hz (D); 220, 440, 880 Hz (A); 370 Hz (F♯); 494 Hz (B). The intended notes |
| The recording, transcribed by the recogniser | every line recognised, including the outdoor report and the video call |
| Sound against picture in `demo/devops-tonight.mp4` | each voice within −1 to +8 ms of its place |

The transcript and analysis are in `tests/output/audio_analysis.txt`; the recording is `tests/output/rec.webm`.

## Videos

| File | What it is |
|---|---|
| `demo/devops-tonight.mp4` | The whole bulletin, 110 s: every frame of the TV's picture rendered at 30 fps, over the recording of what the page played, shifted so the first line sits on the timeline |
| `demo/paige-lipsync.mp4` | Paige's four lines, full frame beside a mouth close-up, over the plain recordings placed on the timeline |

```
cd tests/output
node ../sound_check.js 112 && ffmpeg -i rec.webm -ac 1 -ar 24000 rec.wav
node ../rec_show.js rec_show 30
../../gen/venv3/bin/python ../mux.py rec_show ../../demo/devops-tonight.mp4 --engine rec.wav sound_check.json
node ../rec.js paige rec_paige
../../gen/venv3/bin/python ../mux.py rec_paige ../../demo/paige-lipsync.mp4 --scale 1920x540
```

## Problems in this pass

| Problem | Cause | What was done |
|---|---|---|
| Installing the speech package pulled an old release and then failed building spaCy | Its current release does not support Python 3.13, so pip fell back to one whose dependencies had no ready-made build | A third environment on Python 3.12 (`gen/venv3`) |
| The tokeniser's language model could not be found | It is not on the Python package index | Installed its wheel from the Hugging Face Hub |
| The first test exited with code 1 and no Python error | The fallback pronouncer's C library could not find its data and called `exit` | Set `ESPEAK_DATA_PATH` before importing |
| "…and DNS. Sources say…" ran together with no pause | "D.N.S." swallowed the full stop after it | Gave DNS as phonemes with its own full stop |
| The page failed to load: `Cannot access 'clamp' before initialization` | The new speech code ran at load, before a helper defined further down the file | Moved the helpers up |
| The first sync test reported 50 to 80 ms of error | Mostly the test: it read a frame clock that was stale by one slow software-rendered frame. Partly real: scheduling used the frame's timestamp | The engine now schedules against the live clock; the test reads the same clock. Error fell to a few milliseconds |
| The sync test printed errors of several seconds | For one sample after each line change it compared the new line with the old line's source | The test now skips that sample |
| One presenter was 2 dB quieter | Whole lines were scaled down to fit their peaks | Soft knee on peaks instead |
| The reflection did not show from the usual camera | Geometry: the picture's bottom edge is 7 cm above a 22 cm-deep shelf, so only a raised camera sees it | Left as it is |
| Image generation slowed to 155 s an image | It was sharing four cores with browser tests | Waited |

## Limits

- Nobody has listened to it. The voices were chosen by reputation and checked for words, level and timing only.
- The voices are synthetic stock voices. They read evenly; they do not act.
- Sound needs a click. That is the browser's rule, not a choice.
- Only Chromium was tested. The calibration clip is there for other browsers' decoders, but they were not tried.
- The music was composed by rule from consonant notes and never heard by its author.
