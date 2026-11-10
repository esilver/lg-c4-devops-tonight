# Timeline

Everything happened in one session on 9 and 10 November 2026. Times are UTC, taken from the publish receipts and from clock
readings printed while the pipeline ran. Where no reading exists, no time is given. The page was published as a web artifact after each request; the version ids below are that artifact's history.

| # | Request, in the requester's words | Result | Published |
|---|---|---|---|
| 1 | "Create a 3d webgl model of lg c4 tv that shows a fully JavaScript vanilla channel" | The television in raw WebGL with five Canvas 2D channels | 19:29, version `1794252582-9981` |
| 2 | "Channel needs to be an actual vanila js based news show with people etc" | A scripted bulletin with five drawn, cartoon presenters | 19:36, `1794252997-357e` |
| 3 | "Make it about dev ops as of 2026 not about js" | The bulletin rewritten as "DevOps Tonight"; other channels rethemed | 19:41, `1794253270-9fa0` |
| 4 | "Make the video photo realistic" | Photographic presenters and locations, first lip-sync | 21:38, `1794260281-6508` |
| 5 | "Still vanila js?" | An answer only; no change | none |
| 6 | "Lip movement is funny not natural" | Second lip-sync: re-posed faces driven by pronunciation | 22:39, `1794263977-2948` |
| 7 | "Can I see demo after just that presenter so I can judge? Export all scripts and assets to a new repo, with Md files…" | The demo page, a recording, and this repository | demo at 22:47, `1794264437-c1e2` |
| 8 | "can we make it even better? with perfect audio and just better overall?" | Voices, lips timed to them, sound design, visual fixes | 10 Nov 01:26, `1794273969-4f1d`; demo `1794274002-c6fe` |
| 9 | "can we make the sound and video/lips/movements feel more real even", then "but also lips movements needs to be better, and the eye browes everything" | Late lips found and fixed; 53 mouth poses; brows and head moved on a mesh by the voice; glances; a second set of voices; room sound | work in progress 03:04, `1794279858-8b49`; demo `1794279862-fcbf`. Final 07:33, `1794296027-3c43`; demo `1794296082-d6f9` |
| 10 | "Need to fix sound on iOS, also ty lips and the old yaml man still feel off. And the audio model still leaves to be desired" | Sound on iPhone; lips from a lip-sync network, fitted to each face; the guest repaired; a third set of voices | iOS fix 08:30, `1794299421-bfdf`; demo `1794299531-abbb`. New voices 08:57, `1794301057-5e2b`; demo `1794301062-a842`. Final 09:47, `1794304073-cbbe`; demo `1794304077-933e` |
| 11 | "And also body not needs to move a bit as well as hair and need to be as realistic as possible", "I meant needs to move", "His lips are too tight" | Torsos that breathe, shift and turn; hair on a spring; wind for the reporter; every mouth pose rebuilt around a relaxed mouth; new plates | 12:15, `1794312899-c19f`; demo `1794312903-98b9` |
| 12 | "can you make a version with just the video and no sound, and then make a one pager i can share on reddit that shows the proccess of animating the people and what local models were used with images" | A silent copy of the video; a one-page explainer as a page and as pictures | one-pager 12:42, a new private artifact, `1794314566-d971` |

The main page's artifact was private for versions 1 to 3. Its owner made it public some time before version 4 was
published, so versions 4 and 5 went to a public page. The demo page is a separate, private artifact.

## 1. The television (published 19:29)

One HTML file. A 1024×576 Canvas 2D picture is uploaded to the GPU every frame as the screen texture of a box-built
model of a 65-inch C4 on a media console. Five channels: a text-only "Vanilla JS News" with headlines and a ticker,
a plasma effect, a bouncing-logo screensaver, a source-code crawl, and a test card.

Retries in this step:

- The first render was dim and the set was small in frame. Ambient light went from 0.2 to 0.34, the back light from 0.22
  to 0.5, the rear housing was lightened, a separate rear skin was added so the back reads as a surface, the camera moved
  in from 3.1 m to 2.55 m, and the portrait-screen distance factor changed from `1.25 / aspect` to `0.92 / aspect`.
- The remote's buttons wrapped on a phone; they were set not to wrap.

## 2. A news show with people (published 19:36)

The news channel became a 102.6-second scripted loop: titles, two anchors at a desk, a field report, a split-screen
exchange, weather, an interview and a sign-off. The five characters were drawn shape by shape in Canvas 2D (head, hair
style, jacket, tie or blouse, glasses), with blinking, a head bob while speaking and a mouth that opened on a pair of
sine waves. Subtitles typed out at 30 characters a second.

One fix: the corner channel logo overlapped the end of long subtitles, so it was removed from the news channel.

The source for versions 1 and 2 was edited in place and is not kept as separate files. Version 3's show code is
`src/history/news_cartoon_devops.js`; it is version 2's code with the script, names and branding replaced.

## 3. DevOps, 2026 (published 19:41)

The script was rewritten around current DevOps themes: an AI agent opening forty pull requests that a second agent
approves, a Friday deploy in us-east-1, pods stuck Pending, a Staff YAML Engineer. The cast was renamed (Paige Duty,
Cy Dekar, Dee Ploy, Sunny Uptime, Y. A. Mel). The yellow JS logo became a mint infinity loop. The other four channels
lost their JavaScript jokes too: the code crawl became a deploy log and the test card reads `tv 1/1 Running`.

The stories are invented. No 2026 news was looked up.

## 4. Photographic video (19:46 to 21:38)

This step replaced the cartoon with photographs. There is no way to draw convincing people from code, and the session
had no image-generation tool, so an open image model was installed and run on the session's CPU.

Times in this table are good to a minute or two.

| Time | What happened |
|---|---|
| 19:46 | Checked the machine (4 cores, 15 GB, no GPU) and which download hosts were reachable |
| 19:46–19:54 | Installed PyTorch (CPU) and the diffusion libraries; downloaded the model (4.7 GB in 38 seconds) |
| 19:54–19:57 | Benchmarks: 22 s per image with a 6-step shortcut, 54 s with the full 25-step sampler. Both looked photographic; the full sampler was kept |
| 19:57–20:16 | 20 candidate stills: five presenters × four seeds |
| 20:02–20:15 | Meanwhile, the new show code was written and exercised with placeholder pictures |
| 20:15 | The queue failed: an unrelated install had broken the image library. Fixed and restarted. See [09](09-problems-and-retries.md) |
| 20:16–20:23 | First presenter refined; first mouth and blink variants made by inpainting |
| 20:23–20:26 | More candidates for the second anchor (three made, three cancelled) |
| 20:24 | A matting model that needs to run its own downloaded code was refused by the session's permission check; a weights-only version was used instead |
| 20:26–20:32 | Six B-roll stills (a second round was cancelled because the first was good) |
| 20:32–21:02 | The other four presenters refined, each with ten mouth and blink variants |
| 21:02–21:17 | B-roll finished at full size; mattes; three more mouth variants per presenter; a wider set for the second anchor |
| 21:20–21:35 | Export, page tests, a standing "AI-generated" note |
| 21:38 | Published. The session's worker restarted around this point; nothing was lost |

The image pipeline is described in [03](03-still-images.md) and the first lip-sync in
[04](04-lipsync-v1-inpainted-mouths.md).

## 5. "Still vanilla JS?"

Answered by inspecting the built page: one inline script, no external references, about 46 KB of code and markup, and 46
embedded images. The honest answer was "the code, yes; the photographs were made offline with Python tools".

## 6. Natural lip movement (published 22:39)

The first lip-sync flipped between separately generated mouth pictures about eleven times a second, which read as a flap.
The second one:

1. re-poses each presenter's own photograph into a small grid of mouth and eye poses with a face-animation model, so every
   pose is the same face ([05](05-lipsync-v2-reposed-faces.md));
2. drives that grid from each line's pronunciation with smooth curves ([06](06-speech-engine.md)).

In order:

1. Found weights-only (ONNX) files for a face-animation model and confirmed they load.
2. Wrote the inference glue and tested it on one presenter. It worked on the first run.
3. Compared renders with and without a head-pitch correction. The correction moved the whole face, so it was switched off.
4. Rendered a sweep of 24 poses to choose natural ranges for jaw opening, lip spread, lip rounding, blink and brow.
5. Rendered 20 poses for each of the five presenters (about two minutes each, roughly 22:21 to 22:32).
6. Meanwhile generated pronunciations and wrote the speech engine and the new compositing.
7. The page failed to load because of a name clash with the TV code. Renamed the constant.
8. Checked film strips, curve plots and a 60-frames-a-second smoothness measurement, ran the full regression, and published
   at 22:39.

## 7. Demo and export (demo published 22:47)

- `demo/index.html`: one presenter at a time, full frame, with play and pause, frame stepping, half and quarter speed, a
  mouth close-up, and a chart of the two curves that drive the mouth.
- `demo/paige-lipsync.mp4`: the first anchor's four lines, rendered frame by frame from the demo page and encoded.
- This repository. The working folder was copied as it stood, the test scripts were moved into `tests/` with their
  paths adjusted, three helper scripts were added (they are marked as such in their headers), and these documents were
  written. `python3 build.py` was run in the copy to confirm it reproduces both pages byte for byte.

## 8. Voices, sound and polish (10 November, published 01:26)

Described in full in [12](12-voices-and-sound.md). In order:

1. The speech model's current release would not install on the session's Python, so a third environment was made.
2. All sixteen lines were spoken with five voices and transcribed back by a speech recogniser as a check.
3. The lip animation was changed to follow the measured length of every sound in each recording.
4. A sound engine was written: voice kept in step with the picture, synthesised music and ambience, TV sounds, and
   level that depends on where the camera is.
5. Sound was added to the demo page.
6. Smiles, breathing, a reflection of the picture in the console, a fix for a console artefact, and three regenerated
   B-roll stills.
7. One whole bulletin was played in a headless browser while its sound output was recorded, then analysed.
8. Two videos with sound were rendered, both pages were published, and the work was pushed to the branch
   `claude/audio-and-polish`.

## 9. A more real face and voice (10 November, published 03:04 and 07:33)

Described in full in [13](13-more-real.md). In order:

1. Tested whether a head turn can be reproduced by moving a picture: rendered each face turned and nodded a few degrees,
   measured the optical flow, warped the neutral face by it and compared. It can (`gen/lp_motion.py`, `gen/lpflow.py`).
2. Installed a second speech model in a fourth environment and confirmed it copies a voice from one of the first
   recordings.
3. 01:44: queued two takes of every line with that model, then a dense set of mouth poses and two brow poses for
   every presenter, then a row of smiling mouths.
4. Meanwhile wrote the forced aligner. Testing it on the first voices, whose timing is known, showed a constant
   73 ms: the first voices' timing had been late all along. Confirmed from the sound onsets and from the speech
   model's own code.
5. Wrote the new export (opaque poses with one mask per region, displacement fields for head and brows) and the new
   show code: three mouth tracks, a mesh for the head in a second WebGL canvas, and movement built from each line's
   phrases, stressed syllables and pitch.
6. 02:28: all takes scored. One line's name was read wrong; respelled it and recorded five more takes. Two takes with
   slips lost to their clean alternates.
7. 02:36: audio bundled with pitch contours. The first contours had tracker errors; filtered them.
8. Wrote a lip-sync measurement and ran it on the old and new builds: 41 ms late before, slightly early now.
9. Ran two speech-quality estimators over both sets of voices. They could not tell them apart, so the first voices
   were re-timed and kept, and a switch was added to the demo page.
10. 02:49: all poses rendered. Exported all five presenters, looked at every pose on a sheet per presenter, and dropped
    the eye variants that drooped.
11. Tuned against measurements: brows and blinks calmed, closing from a wide-open mouth slowed, blinks kept away from
    cuts, nods strengthened slightly.
12. Sound: the viewer's room, location sound, the video-call echo; then measured the outdoor bed, found it far too
    loud, and brought it down.
13. 03:04: published both pages as work in progress, at the requester's request ("can you publish the current state
    artifact then continue").
14. Transcribed the set's own output; that caught a take saying "pagers". Swapped the take, recorded the output again,
    rendered both videos (done by 03:21) and wrote this account. The session was then idle for about four hours; the
    final pages, unchanged since 03:25, were published at 07:33 and 07:34.

## 10. Sound on iPhone, learned lips, the guest, a third set of voices (10 November, published 08:30, 08:57 and 09:47)

Described in full in [14](14-ios-sound-learned-lips-third-voices.md). In order:

1. Looked up why a page is silent on an iPhone while videos play (the ringer switch and the audio session class), wrote
   the fix and a button that reports the real state, checked it in an emulated iPhone, and published at 08:30.
2. Looked up how open speech models currently rank in blind listening tests. The second set of voices turned out to
   rank below the first. Installed the highest-ranked model that runs on this machine and recorded three takes of every
   line in about a minute.
3. Looked at the guest frame by frame: eyes nearly shut, mouth barely moving, a stuttering picture. Measured his pose
   renders: his mouth opens about half as far as the others'.
4. Scored the takes, respelled two words the new model mispronounced, recorded that line again, chose a voice for the
   guest from four candidates.
5. Downloaded a lip-sync network and a landmark network as weights and wrote the code to run them. A first try on one
   line worked, showed the mouths had been opening a third too little, and showed the stock windowing is 80 ms early.
6. Measured every pose of every presenter for the calibration, and started measuring the reference on all sixteen new
   recordings.
7. Removed the guest's screen-watching pose, raised his picture to 25 a second, replaced the telephone effect on his
   voice, and added the three-way voice switch to the demo page. Published the new voices at 08:57 while the reference
   was still being measured.
8. Mapped the reference onto each face, checked the result frame by frame and by measurement, recorded the set's output
   again, rendered both videos, and published the final pages.

## 11. Body, hair and looser lips (10 November, published 12:15)

Described in full in [15](15-body-hair-and-looser-lips.md). In order:

1. 09:59: looked at the guest's mouth at four jaw settings and at the co-anchor and the reporter frame by frame.
   All three talk through a closed-lip smile.
2. Rendered a grid of settings for the guest, then for the other four: taking part of the smile out and letting the
   lips a little forward loosens every mouth, and the guest's jaw can go half as far again.
3. 10:14: downloaded a face-parsing network, checked its labels at two crop sizes, and started rendering the whole
   pose set again around a relaxed mouth (65 poses a face, done 11:10).
4. Built the body, hair and wind maps, extended the mesh, and wrote the breath, posture, hair-spring and wind code.
   Recorded a presenter with the camera off and measured the frames: the picture did what was asked to a tenth of
   a pixel.
5. Fixed what the first measurements and charts showed: a pinned band holding the shoulders, shoulders bouncing on
   stressed words, a body rocking with the phrases, a breath that was too quick.
6. Measured the lip reference again on the new base frames, calibrated the new poses and raised the common opening.
7. Found the halo the old plates left beside a moving figure; changed the plate; tried having the image model paint
   the room behind each presenter and set that aside.
8. In between, the requester wrote "claude/audio-and-polish push" (the branch was already pushed in full) and "can
   you publish current state than continue?": both pages were published at 12:15 and the work was pushed at 12:20.
9. Measured all five presenters on the final build, rendered both videos, and wrote this up.

## 12. A silent video and a one-pager (10 November, one-pager published 12:42)

Described in [16](16-silent-video-and-one-pager.md). The silent copy showed that the clock in the ticker had been
running fast in every rendered video; the renderer was fixed and both videos were made again. The one-pager was
built from pictures already in the repository plus four captures, published as a new private page, and exported
as pictures because a link is not always what a forum wants.

At 21:00 the one-pager was republished without the television: the requester wanted it to describe only how the video
is made, to link beside the video.

## 13. A live avatar, as a proof of concept (10 November, published 22:22)

Described in [17](17-live-avatar-poc.md). After the post went up the requester said the real goal was an avatar of
themselves, and asked whether what exists could be the base of a quick live proof of concept. The artifact viewer
offers a call to Claude, a voice and dictation, so the page only had to join those to the engine: a guess at the
mouth from the spelling of the reply, and a clock that keeps it in step with the voice.
