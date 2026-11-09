# Timeline

Everything happened in one session on 9 November 2026. Times are UTC, taken from the publish receipts and from clock
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
