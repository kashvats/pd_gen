> **Implementation status — natural speech update:** Real Kokoro ONNX English
> preset speech is now available after explicit installation. Edge is optional
> and requires online permission. Paid/system/mock engines are not registered
> for normal generation. The legacy cloning tone generator is disabled; real
> cloning remains a future goal. Unsupported acting controls are disabled.
> See START_HERE.md for setup and current limitations; aspirational sections
> below are not claims that every planned feature is implemented.

# Development Roadmap

## Objective

Build the smallest reliable version of:

```txt
Markdown
→ dynamic characters
→ saved/reference voices
→ natural local speech
→ cached speaker turns
→ polished final audio
```

while keeping monetary operating cost at $0 and respecting the target hardware.

---

# Phase 0 — Repository and safety foundation

Create:

- documentation files
- configuration paths
- logging
- error-handling conventions
- system resource manager skeleton
- project folder conventions

Definition of done:

The project has a clear architecture and does not begin with web/SaaS assumptions.

---

# Phase 1 — Desktop shell

Build:

- PySide6 main window
- Open Markdown
- Save Markdown
- recent projects
- settings
- basic status bar

Definition of done:

A `.md` file can be opened, edited, saved, and reopened locally.

---

# Phase 2 — Parser

Build:

- speaker-turn parser
- dynamic speaker detection
- multiline dialogue
- heading handling
- blank-line handling
- stable ordering
- parser tests
- `[PAUSE: ...]`

Definition of done:

Arbitrary dialogue scripts parse reliably without treating normal headings as speakers.

---

# Phase 3 — Structured dialogue view

Build:

- dialogue blocks
- speaker labels
- edit
- delete
- duplicate
- preview placeholder
- synchronization with Markdown

Definition of done:

The script is easy to inspect as speaker turns.

---

# Phase 4 — Local project format

Build:

- `project.json`
- character assignments
- project settings
- recent-project metadata
- version/migration field

Definition of done:

Project configuration survives application restart without a database.

---

# Phase 5 — Voice library

Build:

- local voice profiles
- reference-audio folders
- create/edit/delete workflow
- consent acknowledgement
- character → voice mapping
- global default suggestions

Definition of done:

The user can create reusable local voices and assign them to detected characters.

---

# Phase 6 — Model/engine abstraction

Build:

- `SpeechEngine` interface
- capability model
- registry
- model manager
- hardware compatibility metadata
- lazy load/unload

Definition of done:

The application is not tied to one speech engine.

---

# Phase 7 — First lightweight local engine

Integrate one engine that is:

- free
- locally runnable
- reasonably light for the target system
- usable for basic speech

Use it to prove the complete local generation path.

Definition of done:

One dialogue turn can be generated locally with Wi-Fi disconnected.

---

# Phase 8 — Reference/voice-cloning local engine

Integrate a compatible free local engine that can condition on reference audio.

Requirements:

- local reference files
- no required cloud upload
- engine adapter
- preview
- safe CPU/GPU fallback
- model loading inside system limits

Definition of done:

Two characters can use distinct reference-based voices locally.

---

# Phase 9 — Generation planner and cache

Build:

- deterministic synthesis hash
- cache lookup
- generation plan
- per-turn status
- bounded generation queue
- pause/resume/cancel

Definition of done:

Changing one turn only regenerates that turn.

---

# Phase 10 — Natural speech direction

Build local rule-based Speech Director using:

- punctuation
- explicit directives
- neighboring turns
- character profile
- conversation preset

Definition of done:

Questions, reactions, and simple emotional cues receive appropriate delivery metadata without rewriting dialogue.

---

# Phase 11 — Natural timing

Build:

- quick-reaction timing
- normal speaker-change timing
- topic-transition timing
- explicit pause handling
- user override

Definition of done:

The final conversation does not use the exact same pause everywhere.

---

# Phase 12 — FFmpeg assembly

Build:

- ordered manifest
- silence nodes
- safe concatenation
- lossless master path
- gentle final loudness processing
- MP3/WAV export

Definition of done:

A multi-speaker project becomes one clean final audio file.

---

# Phase 13 — Player and timeline

Build:

- play/pause
- seek
- current time
- turn markers
- previous/next turn
- click turn to seek

Definition of done:

The user can review the generated conversation comfortably.

---

# Phase 14 — Alternate takes

Build:

- generate another take
- take list
- preview
- select
- lock
- preserve locked take

Definition of done:

A bad performance can be replaced without regenerating the project.

---

# Phase 15 — Pronunciation system

Build:

- global dictionary
- project dictionary
- per-character overrides if useful
- preview pronunciation
- cache-key integration

Definition of done:

Recurring names/acronyms can be corrected without editing every line.

---

# Phase 16 — Studio mode

Studio mode may enable:

- best compatible local engine
- richer direction
- more careful timing
- alternate takes
- higher-quality intermediates

Definition of done:

Studio mode increases quality without ignoring `SYSTEM_LIMITS.md`.

---

# Phase 17 — Free online optional engines

Only after local generation is reliable.

Add optional online engine support only when a service is verified as:

- genuinely free
- unable to create charges
- optional
- privacy-disclosed
- replaceable

Definition of done:

Online failure never breaks local generation.

---

# Phase 18 — SFX and richer Markdown

Add:

```md
[SFX: applause]
```

and improve:

```md
Host [excited]: Welcome back!
```

Definition of done:

The AST supports more production nodes without breaking old scripts.

---

# Phase 19 — Optional small local intelligence

Only if it fits the target hardware.

Potential uses:

- better speech-direction inference
- pronunciation suggestions
- emotion classification

It must remain optional and free.

Do not make a large local LLM mandatory.

---

# MVP boundary

The MVP is complete when:

```md
# My Podcast

Host: Welcome everybody.

Co-Host: Thanks for listening.

Guest: It's great to be here.
```

can be opened locally, speakers are detected, three free local voices/reference voices are assigned, audio is generated safely, unchanged turns are cached, and one final audio file is exported at $0 operating cost.

Advanced AI writing features are not part of the MVP.
