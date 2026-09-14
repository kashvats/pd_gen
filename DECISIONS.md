# Project Decisions

This file records decisions that AI coding agents should not silently reverse.

---

# D001 — Personal desktop application

Status: Accepted

Decision:

The product is a single-user desktop application for the owner's computer.

Consequences:

- no SaaS architecture
- no public web product
- no authentication requirement
- no team permissions
- local files are the default storage model

---

# D002 — Markdown is the primary authoring format

Status: Accepted

Decision:

The script remains a normal Markdown file.

Consequences:

- portable
- editable outside the app
- easy to version
- easy for humans/AI tools to generate

The visual dialogue editor is a convenience layer, not a replacement for Markdown.

---

# D003 — Speakers are dynamic

Status: Accepted

Decision:

Do not hard-code `Host`, `Co-Host`, or any fixed cast.

Speaker names are discovered from the Markdown.

---

# D004 — Total operating cost must remain $0

Status: Accepted

Decision:

The core product must not require any paid service.

Consequences:

- no required paid TTS
- no required paid voice cloning
- no subscription dependency
- no automatic paid fallback

See `FREE_OPERATION.md`.

---

# D005 — Local/offline path is permanent

Status: Accepted

Decision:

Once models are installed, core generation must work without internet.

Optional free online features may exist but must never replace the local fallback.

---

# D006 — Voice cloning/reference voices are first-class

Status: Accepted

Decision:

Voice identity is not limited to preset voices.

The product supports reusable reference-audio voice profiles.

Reference source files remain local by default.

---

# D007 — Naturalness over raw generation speed

Status: Accepted

Decision:

Prefer coherent, expressive, context-aware speaker turns over the fastest possible synthesis.

System stability still has higher priority than quality.

---

# D008 — Complete speaker turns are the primary synthesis unit

Status: Accepted

Decision:

Do not unnecessarily split every sentence into a separate TTS call.

Split only when engine/system limits require it.

---

# D009 — Dialogue is never silently rewritten

Status: Accepted

Decision:

Speech direction may alter performance but not words.

Any future text-rewriting feature must be explicit and visible.

---

# D010 — Local files / JSON instead of a database

Status: Accepted

Decision:

Use:

- `script.md`
- `project.json`
- local voice profiles
- local cache metadata

Do not add a database unless a concrete need appears that local files cannot reasonably solve.

---

# D011 — Speech engines are adapters

Status: Accepted

Decision:

No model/provider owns the application architecture.

Use a shared `SpeechEngine` abstraction and capability system.

This allows engines to be replaced as free/open models improve.

---

# D012 — Heavy local synthesis concurrency defaults to one

Status: Accepted

Decision:

The target GPU has 4 GB VRAM.

Default to one heavy neural speech job at a time.

Caching and resumability are preferred over parallel model inference.

---

# D013 — Target hardware is a design constraint

Status: Accepted

Target:

```txt
AMD Ryzen 5 5600H
32 GB RAM
GTX 1650
4 GB VRAM
```

Do not design defaults for high-end GPU hardware.

---

# D014 — User data is more important than cache

Status: Accepted

Never automatically delete:

- scripts
- project files
- voice references
- locked takes
- final exports

Only safe-to-regenerate cache data can be automatically cleaned.

---

# D015 — Model downloads are explicit

Status: Accepted

Large model downloads must show size/license/system requirements before installation.

Generation must not silently download models.

---

# D016 — Online can be used, paying cannot

Status: Accepted

Decision:

Internet use is allowed.

Optional online engines are allowed only if they are genuinely free and cannot create charges.

There must always be a local fallback.

---

# D017 — No hidden uploads

Status: Accepted

Decision:

Scripts, reference audio, or generated audio must never be uploaded silently.

Optional online features require clear disclosure/consent.

---

# D018 — FFmpeg handles heavy audio assembly

Status: Accepted

Decision:

Use FFmpeg for concatenation, silence, conversion, and final mastering where practical.

Avoid loading entire long episodes into Python memory.

---

# D019 — Caching is core architecture

Status: Accepted

Decision:

Unchanged synthesis must be reused.

A one-line edit should normally cause one turn to regenerate, not the whole episode.

---

# D020 — Alternate and locked takes are part of the quality workflow

Status: Accepted

Decision:

The user can keep multiple performances, choose one, and lock it.

Locked takes must survive unrelated regeneration.

---

# D021 — Rule-based local Speech Director first

Status: Accepted

Decision:

Initial context-aware delivery analysis uses deterministic local rules.

A small local model may be added later if it safely fits the hardware.

An online model must never become mandatory.

---

# D022 — Studio mode must still obey system limits

Status: Accepted

Decision:

"Studio" means better quality, not unlimited hardware usage.

It may increase care/quality but not ignore RAM/VRAM/CPU limits.

---

# D023 — Voice cloning requires ownership or permission

Status: Accepted

Decision:

The app should support cloning/reference voices only when the user owns the voice or has permission from the speaker.

Store a local confirmation with the voice profile.

---

# Adding future decisions

Use:

```txt
D024 — Decision title

Status: Proposed / Accepted / Deprecated

Decision:
...

Reason:
...

Consequences:
...
```

Do not silently reverse an accepted decision.

If a decision changes, document the replacement and why.


# D024 — Real neural speech and explicit failures

Status: Accepted for this update

The user's current scope is audio from a supplied script. Kokoro ONNX is the
local preset speech engine; Edge remains optional. Removed default registration
of paid providers, the mock engine, and basic system TTS. Legacy cloning generated
only tones and is disabled, with reference profiles preserved. No silent voice
fallback, synthesized silence, or partial exports are accepted. Real cloning
remains a future integration, not an implemented feature of this update.

The initial English Kokoro adapter is CPU-only, serializes inference and limits
ONNX threads through SystemLimits. Model files are downloaded explicitly, never
from synthesis. Plan RAM allowance: 2–4 GB; measured fit/speed on the target
Ryzen 5600H must still be checked. No GPU/VRAM is used. No script/reference upload
is performed by this adapter. Weights are approximately 310 MB and the voice
pack adds roughly 28 MB; the source ZIP does not redistribute them.

Sources verified for this change:
- https://github.com/thewh1teagle/kokoro-onnx (adapter; MIT)
- https://github.com/thewh1teagle/kokoro-onnx/releases (model-files-v1.0)
- https://huggingface.co/hexgrad/Kokoro-82M (82M model; Apache-2.0)
- https://github.com/rany2/edge-tts (online, no key; rate/pitch/volume controls;
  arbitrary custom SSML/acting instructions unsupported)

Dependency: kokoro-onnx 0.6.1, ONNX Runtime CPU, numpy, bundled eSpeak loader,
phonemizer, and psutil. They require installation but no inference payment.
Review transitive dependency licenses when redistributing a packaged executable.
Model-download hashes are recorded locally as fingerprints, not claimed as
independent publisher verification.

# D025 — Preserve speech through assembly

Status: Accepted

Decode each turn to consistent PCM before concatenation. Do not concatenate
mixed MP3/WAV streams directly. Keep fades at at most 5 ms without overlapping
speech. Normalize only the final programme. Preserve leading/explicit pauses,
use measured durations, match output extension to codec, and fail if a speech
turn is missing. SFX is explicitly unsupported in the current speech-only path.

# D026 — Natural delivery does not mean fabricated controls

Status: Accepted

Do not force robotic voices based on speaker names. Do not mutate pitch/speed
based on keyword matches in acting prompts. For the installed engines, voice,
punctuation, and pace determine performance; unsupported controls are disabled.
Regeneration cannot guarantee a different take with deterministic models.
