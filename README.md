# System design prep

Interactive lessons for system design interview prep. Live at https://manoletre.github.io/system-design-prep/

| Lesson | Topic |
|---|---|
| [Dodo 1](lessons/dodo-1/) | Supabase → GCP zero-downtime migration, catch-up & cutover math, voice latency budget & LiveKit, idempotent PMS writes |

## How the lessons work (player v4)

The player is ported from [liquid-ai-prep](https://github.com/manoletre/liquid-ai-prep) (`source/build/template.html`). Each chapter is full screen, one at a time: **question** (write a prediction; the video isn't loaded yet) → **learn** (video with click-to-play steps that auto-pause; → / ← / R) → **compare** (your answer next to the model answer, Got it / Partly / Missed, and a "what was unclear" note) → **pen-and-paper practice**. A lesson can end with an interview drill and always ends with "Revisit your answers", which has a button to copy ratings and unclear notes for the coach. Answers live in localStorage under `lap:<lesson id>:<question id>:answer|rating|note|revealed`.

Wherever a quantity is computed by hand, a chapter shows two fully worked examples (one an edge case), then a faded example (the last step is yours, with a "Check your last step" box), then the practice problem.

## Creating a new lesson

1. **Scenes.** Add one `StepScene` per chapter to `source/manim/sd_scenes.py`. Wrap each step in `self.begin("key")` … `self.end()`; `end()` adds the 1.8 s hold and records timestamps to `source/manim/steps/<Scene>.json`.
2. **Render.** Draft with `/workspace/ml-tutor/.venv/bin/manim -ql --disable_caching sd_scenes.py <Scene>` and check the step-end frames with `python3 /workspace/ml-tutor/manim/endframes.py media/videos/sd_scenes/480p15 /tmp/ef <Scene>`. Final: `manim -r 1920,1080 --fps 30 --disable_caching sd_scenes.py <Scene>` (this rewrites the step JSON with the final timings).
3. **Content.** In `source/build/content.py`, add a lesson dict like `D1` (`id`, `slug`, `title`, `h1`, `sub`, `key`, `chapters`, optional `drill`, `summary`) and register it in `LESSONS`. Each chapter has `scene`, `file`, `title`, `short`, `hook` (`{id, q, model}`, the prediction), `steps` (`(key, title, html)`, keys matching the scene's `begin()` keys) and `check` (`{id, q, model}`, the practice). New symbols go in `SYM_ALL` / `MACROS` in `build.py` plus a `.k-<key>` color in `template.html`. Keep question ids stable once published: they are the localStorage keys.
4. **Build.** `python3 source/build/build.py [lesson id]` encodes the videos and posters and writes `lessons/<slug>/index.html`.
5. **Verify.** `BASE=https://manoletre.github.io/system-design-prep/lessons/ python3 source/build/test_lesson.py dodo1` (or a local server that supports HTTP Range requests; `python -m http.server` can't seek video).
6. **Publish.** Add a card to `index.html` and a row above, then commit and push. GitHub Pages serves `main`.
