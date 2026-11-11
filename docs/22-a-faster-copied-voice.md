# A faster copied voice

Asked: is there a reason the copied voice feels slower than the other one, even on a desktop? Then: go for it, try.

## What was found

The copied voice (Pocket TTS, [21](21-a-copied-voice.md)) makes speech in steps, 12.5 for every second of it. Each
layer of its language model remembers what has been heard and said in a cache. The published file gives every cache
room for 1000 positions, 49 MB over the six layers, and the graph copies all of it several times at every step: twice
in full to write the new position in, in halves to read the keys and the values back, and once each way between the
page and the runtime. Counted from the graph's operations that is about 540 MB moved per step, whatever the line is.
A line uses a few hundred positions.

The size of 1000 is not part of the arithmetic. The graph takes the size from the cache it is handed; the number
appears only in the file's notes on the shapes of its inputs, outputs and the values between (42 notes). The runtime
checks an input against those notes, which is why a smaller cache had been refused before.

## What was changed

**The caches are sized to the line.** As the worker reads the model file it rewrites each note `dim_value: 1000`
(bytes `08 E8 07`) as `dim_param: "c"` (`12 01 63`), a size left open. It is three bytes for three, so nothing else in
the file moves and the file needs no rebuilding. A voice's caches are then exactly as long as its recording, and a
line works in a copy with room for its words and 32 more positions, lengthened by 32 whenever it fills
(`freeCache`, `room` in `avatar/voice/pocket.js`; `free_cache` in `gen/pocket.py`). If the notes are not found the
size stays at 1000 and everything works as before.

The speech is the same. Six test lines made with the caches at 1000 and made to measure were compared sample for
sample and did not differ.

**A reply's opening is cut short.** The wait before the first sound is the time it takes to make the first piece.
The page now cuts a reply's opening at the first comma ten to forty-eight letters in or, in a long sentence that has
none, before a small word that starts a phrase, and sends it to the voice as soon as that much has been written,
without waiting for the sentence to end (`opening` in `avatar/page.html`). Early in a reply, on a device that does
not make speech comfortably faster than it is spoken, a long piece with no comma is cut the same way, so a short
opening is not held back for a long second piece. A piece cut where nothing was written is said as if a comma
followed and joined to the next without a pause. The hold before the first line now counts the time a line has
already been in the making, which it used to ignore.

**The full-precision files can be tried.** The same model exists at full precision (383 MB in three files against
109 MB). Where the page is hosted on its own, "Voice details" has a button that makes the worker fetch them once from
where they are published and keep them in the browser, and one to go back. In a Claude artifact, which cannot fetch
them, the page gives the links and the viewer adds the files. A phone is not offered them.

## What was measured

In headless Chromium on 4 shared cores, the copied voice, as a multiple of a line's length:

| | Caches at 1000 | Made to measure |
|---|---|---|
| One thread, test voice (68 positions) | 1.87 | 1.14 |
| One thread, a 14 second recording (176 positions) | 1.79 | 1.27 |
| Two threads, the same recording, isolated page | | 0.97 |
| Four threads, test voice, isolated page | | 0.68 |
| Natively, four threads, the same recording, without the timing step | | 0.44 |

Where the time goes now, for a line of 4.1 s on one thread: the voice 2.5 s, the audio decoder 1.6 s, timing the
sounds 0.5 s, pronouncing 0.1 s. The audio decoder is mostly convolutions, which are in floating point in both sets
of files; natively it took the same time with either.

The full-precision files were slower here: 1.40 against 1.18 on one thread. That is one kind of processor. An earlier
readout from an Apple laptop suggested 8-bit arithmetic runs poorly as WebAssembly there, so the switch is offered and
the page's own readout says which is faster.

On a copy of the page hosted on its own (isolated, two workers of two threads each), with a reply of three sentences
whose first is long:

| | Before | After |
|---|---|---|
| First sound after the question | 15.6 to 16.1 s | 4.5 to 4.7 s |
| A line, as a multiple of its length, both workers busy | 2.0 to 2.1 | 1.1 to 1.2 |

Words in short pieces, including ones that end on a comma, were checked with a speech recogniser: 0 wrong of 51.

## What is not known

- How it runs on other processors. Every number here is from one machine.
- How the cut opening sounds. The words are right and the lengths are sensible, but nobody has listened to whether
  the join between an opening and what follows is smooth.
- Whether the full-precision files help anywhere.

## Asked along the way

**Would the same model be faster as a service?** On most devices, yes. Natively on four cores it made a line in 0.44
times its length, against about 0.6 for the same steps in a browser on the same cores, and a server does not depend
on the visitor's device, which matters most on a phone. On a fast desktop the difference would be small once the
network round trip is added. It costs a server that is kept running, or a start of several seconds when it is not.

**Would other models, as services, be faster?** Yes. Hosted voices built for conversation send the first sound in a
few tenths of a second on any device, and some copy a voice from a short recording. The lips could still be timed by
the recogniser in the page, which works on any audio. The cost is a price per character and a recording of the voice
held by the vendor.

Tried afterwards, on a private copy of the page, with one such service (Cartesia). A line came back 0.4 to 1.2 s
after it was asked for, whatever the device, and nothing is downloaded. The service reports when each word starts
and ends; its times for the sounds inside a word turned out to be the word's time divided evenly, so the page
pronounces the line itself and lays each word's sounds out between the word's start and end. Against a reference
aligner on eleven lines the service's word times ran 50 ms late; with that taken off, half the sounds sat within
38 ms of the reference and 90% within 81 ms. The recogniser in the page, on the same lines in the voice made on the
device, gave 21 ms and 60 ms.

The same test showed where a hosted copy of the page had been losing time that the voice was blamed for: the host
(Firebase Hosting) hands a streamed reply to the page only once it is complete. Asked at the function's own address
the first words came after 1.7 s; through the host the whole reply came at once after 2.1 s.

## To run

```
node avatar/pocket_test.js                 # the worker alone: six lines, with where the time went
POCKET_FIT=0 node avatar/pocket_test.js    # the same with the caches at 1000
POCKET_ISOLATED=1 POCKET_THREADS=4 node avatar/pocket_test.js
POCKET_FULL=1 node avatar/pocket_test.js   # the full-precision files, from avatar/voice/src/pocket_full/
node avatar/test.js                        # the page; its last check is the opening
```
