# A faster voice, speaking while the reply is still being written, and hands-free

The live avatar's own voice ([18](18-own-voice-and-a-real-face.md)) worked in the real viewer, but slowly: the page
said a line took 1.5 times as long to make as to say, on a fast laptop. Asked why, and then asked to make it fast
and not to wait for the whole reply before speaking.

## What the page now shows about itself

A "Voice details" readout under the voice row: the model and where it runs, the workers and threads, the cores the
browser reports, whether it offers the page a GPU, a start-up test, the last line made (pronouncing against the
model), a plain arithmetic check of the worker's core, and whether added files are kept between visits.

The readout from the requester's laptop (a recent Apple chip, Chrome) settled the question:

| | Build machine | That laptop |
|---|---|---|
| Thirty million square roots in the worker | 58 ms | 18 ms |
| Start-up test line, 8-bit model | 1.22 times its length | 1.14 times its length |
| GPU offered to the page | no | yes |

A core three times as fast made the model no faster. So the processor is not the limit there; the 8-bit model's
integer arithmetic, run as WebAssembly, is. That is a reading of two numbers, not something traced further. The
full-precision model is no way round it on a processor: here it took 2.15 times a line's length as WebAssembly,
against 1.32 for the 8-bit one.

## The GPU

The same export has a full-precision file (`onnx/model.onnx`, 326 MB) that onnxruntime-web can run on a GPU through
WebGPU. The worker now chooses per model:

- the full-precision model, where the browser gives the worker a GPU adapter: the WebGPU build of the runtime, one
  worker (the GPU is where the work is done);
- anything else: WebAssembly on the processor, as before, with two or three workers.

Starting on a GPU ends with a test line. If creating the session fails, or the test line comes back empty, not
finite or with a missing duration, the worker falls back to the processor with the same model and the page says why.

The viewer switches by adding the other model file. The voice starts again with it, and only that model is kept.
The page offers the full-precision file where a GPU is on offer, and the 8-bit one back where the GPU could not run it.

**The GPU runtime, in the real viewer.** The first attempt there ended with "its runtime file could not be fetched".
The WebGPU build of the runtime is a 29 MB file, and the viewer's frame fetches the 15 MB processor runtime from the
same CDN without trouble; a size limit on what a page may fetch is the likely reason, though it was not confirmed.
The runtime also comes in a smaller GPU build (18 MB) for browsers that can suspend WebAssembly (JSPI). The worker
now tries that one first, then the larger. If the view refuses both, the page says so and offers the file as a
download to add by hand, after which the voice starts again.

**A storage limit found on the way.** Chrome will not keep a single value of 326 MB in IndexedDB; the 92 MB model
had fitted. Added files are now stored as blobs, which the browser keeps as files. The earlier code also deleted the
old model before the new one was safely stored; it now stores first.

`avatar/get_voice.py full` lays out the full-precision model for a page run from a disk; both layouts now include
the GPU build of the runtime.

## Speaking while Claude is still writing

The page's call to Claude can report the reply as it is written. Each sentence that is finished goes to the voice at
once, so the first one is being made, and usually spoken, while the rest is still arriving. Lines are scheduled on
the audio clock as before; the list of lines simply grows. Stopping, or asking something new, also stops Claude
writing. A borrowed voice (Claude's, the browser's) still needs the whole reply first.

## Hands-free

Asked next: not to have to press Speak for every question. The viewer's speech input stays open for up to an hour
once a click has started it, so Speak is now a toggle. While it is on, what is said is sent after 0.9 s of silence,
the avatar answers, and it is listening again.

- **Speaking over it interrupts it.** The first version ignored the microphone while the avatar was thinking or
  speaking, so that with loudspeakers it would not answer its own voice. That also meant it could not be interrupted,
  which was the first thing tried. Now, during that time and for 1.2 s after, what is heard is compared with what the
  avatar is saying. Words it is saying are taken as its own voice coming back and ignored. Two or more words it is
  not saying (at least half of what was heard), or a single "stop", "wait" and the like, are the viewer: the avatar
  stops at once, mid-word, and what the viewer goes on to say becomes the next question.
- **A speaker who is still talking is waited for.** A live guess from the speech input holds the send back; the
  silence is counted from the last settled piece.
- Listening ends when the view is hidden or the platform's own Stop is pressed; one click starts it again.

## Checked, and not

- **The GPU itself was not run.** The build machine has no GPU and its headless browser offers no WebGPU, with any
  flag tried. What was run: the switch to the full-precision model, its fall-back to the processor (voice ready,
  reply spoken), one model kept after the switch, and that the CDN serves both GPU runtime files. And, with a worker
  told that a GPU is on offer when none is: a view that refuses the GPU runtime (the page offers the file), then the
  file added by hand (the GPU runtime loads, the GPU start is attempted and fails, the processor takes over).
- Streaming was run with a stand-in that delivers the reply in eight parts; all four page tests pass with it.
  How much sooner the first sound comes with the real Claude was not measured.
- Speed on a GPU is unknown until the readout from one is seen.
- Hands-free was run with a stand-in for the speech input: one click, a question in two pieces with the speaker
  still talking between them, the avatar's own words "heard" during and just after its answer (ignored), a second
  question with no click, and a third answer spoken over (stopped at once, the new question answered). The real
  speech input was not, nor how a real recogniser writes down the avatar's voice from a loudspeaker: if it mishears
  two words in a row, the avatar will interrupt itself.

## Files

`avatar/voice/worker.js` (engine choice, GPU start and fall-back), `avatar/page.html` (readout, streaming, model
switch, blob storage), `avatar/get_voice.py` (`full`, GPU runtime), `avatar/test_published.js` (steps 5 and 6: the
full-precision model added in place of the 8-bit one; a pretended GPU whose runtime the view refuses), `avatar/voice_test.js` (`VOICE_DIR` to try another layout).
