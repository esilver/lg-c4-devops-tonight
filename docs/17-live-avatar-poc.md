# A live avatar, as a proof of concept

The requester's goal turned out to be an avatar of themselves, and the question was whether what exists could be the
base of a quick proof of concept that talks back in real time. It could. `avatar/` is that proof of concept, with the
first anchor standing in until there is a photograph of the requester.

## What it is

One page (`avatar/index.html`, 0.47 MB). You type or say something; the presenter looks aside while the reply is
fetched, then says it, with lips, brows, nods, breathing and hair as in the bulletin, and the words appear under the
picture as they are spoken.

| Piece | Where it comes from |
|---|---|
| The face and all its movement | The bulletin's engine, `src/news.js`, unchanged, with one presenter's pictures |
| The reply | Claude, through the artifact viewer's `sample` capability (one or two spoken sentences, the quick tier) |
| The voice | One of Claude's voices, through the `tts` capability. Where that is not offered (Safari, the mobile apps), the browser's own speech synthesis. Where there is none, the words are mouthed and shown |
| Your side | Typing, or the viewer's `dictation` capability where it is offered (a Chromium tab, the desktop app) |

Published as a private page: https://claude.ai/artifact/SEzGoZDjdWwejkZzg7agtC (version `1794349388-e1ff`, declaring
`sample`, `tts` and `dictation`).

## How the lips can be live

The bulletin's lips come from recordings that were measured ahead of time. Here nothing exists ahead of time, and
the page cannot see the audio of either voice. So:

1. **A guess at the sounds from the spelling** (`sounds`). About sixty rules of English spelling give the engine's
   own sound symbols. It does not need to get the word right, only the mouth: where the lips meet, where they round,
   where the jaw drops. Little words are reduced, the first vowel of other words is stressed.
2. **A plan in time** (`plan`). Each sound gets a length, scaled to an assumed pace of thirteen letters a second, with
   pauses at punctuation and an invented melody (falling through the sentence, lifting on some stressed words, rising
   at a question) so that the engine's nods and brows have something to follow. The engine's rule-based mouth,
   kept since request 9 as the fallback for a line without a lip reference, turns that into jaw, lip and closure curves.
3. **A clock that follows the voice** (`sync`, `reach`, `finish`). The reply is spoken a sentence at a time. Claude's
   voice reports when each line starts and how many milliseconds of it have been heard; the browser's voice reports
   each word as it starts. The plan is re-anchored at every report, and how long each line really took against the plan
   sets the pace for the lines that follow.

What the engine laid out a moment ago for a sound that has only just started (the smile letting go, the breath in)
is eased in over a seventh of a second, and both are also started as soon as the reply arrives, before the voice does.

## Checked, and not

`node avatar/test.js` runs the page headless with stand-ins that follow the documented interfaces: a reply after
300 ms, and a voice that "speaks" at eleven letters a second, slower than the page assumes.

| Check | Result |
|---|---|
| States | thinking, speaking, idle, in that order |
| Lines | all three sentences of the reply reached in turn |
| Mouth | open (above 0.2) for half of the speaking time, widest 0.88, shut at the end |
| The clock | the pace estimate moved from 1.00 towards the stand-in's 1.18 (1.09 after three lines) |
| Opened from disk, with nothing provided | a stock line is mouthed at the planned pace; no errors |

Not checked, because it cannot be from here: the real reply, either real voice, dictation, and whether the lips
look right against the sound. The agent cannot watch or listen, and the viewer's capabilities exist only inside the
viewer.

The lips are no longer a guess where the avatar has its own voice: see [18](18-own-voice-and-a-real-face.md).

## What it is not

- The lips are plausible, not exact. They are a guess from spelling, timed by line starts and positions.
- The voice is Claude's or the device's. It is not the requester's.
- It answers in turns. It does not listen while it speaks, and there is a second or two of thinking before each answer.
- It carries no memory beyond the last dozen messages, and the page keeps nothing.

## To put another face in it

`python3 avatar/build.py <name>` builds the page with any presenter in `assets.json`. A new face goes through the
pipeline of docs 03, 05 and 15 first (a frame, a matte, the 65 poses, the maps), about half an hour of computing.
