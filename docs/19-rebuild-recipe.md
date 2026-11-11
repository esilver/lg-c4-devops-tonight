# A recipe for rebuilding the presenters

A reader of the first one-pager ([16](16-silent-video-and-one-pager.md)) asked for enough to rebuild the video with
their own AI coding agent. The first one-pager shows how it was made; this one tells an agent how to make it.

| What | Where |
|---|---|
| The recipe as a skill file | `recipe/SKILL.md` (904 lines): front matter with `name` and `description`, then the instructions |
| The page, self-contained | `recipe/index.html` (1.7 MB), built from that same file by `recipe/build.py`, with pictures and captions from `recipe/figures.json` |
| The page as published | https://claude.ai/artifact/TMYsTdSLTdA3eoTstYdLKu (private to its owner when this was written) |

What it holds:

- **A copyable `SKILL.md`** at the top, complete on its own. The rest of the page is the same file rendered for
  reading, so the two cannot disagree.
- **Eight steps**, each with what goes in, what to do, what comes out, a check that is a number or a picture, and the
  settings that worked.
- **The twelve models** by repository and file name, which are weights only (so the glue has to be written), and
  whether each one's output is in the video or only measured.
- **The numbers that took trial and error**: the 65 poses and both jaw lists, the relaxed-mouth settings per face, the
  smile scale, the lip level of 0.155 eye distances with its gain limits, the 70 ms timing correction for the first
  voice model, the grids, and the body, hair and blink settings.
- **Tried and dropped**: every attempt that was replaced, each with why it was dropped and what replaced it.
- **A plain statement, twice, that it is a recipe and not the working code.**

It covers the bulletin video only. It leaves out the television page, the live avatar, any real person's photograph,
and every detail of who asked for the project. It names no repository.

It was written by a second agent from the documents and scripts here, then read in full before it was published.
The page was looked at at 1200 and 390 px wide: no sideways overflow, no script errors; wide tables scroll inside
themselves on a phone. Licences in it carry the same caveat as [11](11-models-and-licences.md): recalled, not checked.

To build the page again: `python3 recipe/build.py` from the repository root.
