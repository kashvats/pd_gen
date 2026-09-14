# AI Agent Instructions

## Purpose

This file tells any AI coding agent what this repository is trying to build and what must not be changed accidentally.

Before making significant code, architecture, dependency, model, storage, or product decisions, read:

- `PRODUCT.md`
- `ARCHITECTURE.md`
- `MARKDOWN_FORMAT.md`
- `VOICE_SYSTEM.md`
- `AUDIO_QUALITY.md`
- `SYSTEM_LIMITS.md`
- `FREE_OPERATION.md`
- `ROADMAP.md`
- `DECISIONS.md`

These files are the source of truth.

---

# One-sentence product definition

Build a **personal, single-user desktop application** that converts Markdown dialogue into highly natural multi-speaker audio using free local voice synthesis/voice cloning, with optional genuinely free online features, while protecting the user's computer from excessive resource usage.

---

# Hard invariants

Do not violate these unless the user explicitly changes the product direction.

## 1. This is not a SaaS product

Do not turn the project into:

- a public website
- a subscription service
- a multi-user system
- a team workspace
- a cloud dashboard
- a billing product
- an account-based service

There is one user: the owner of the computer.

## 2. Normal operation must cost $0

Do not require:

- paid TTS APIs
- paid voice cloning
- paid inference
- subscriptions
- purchased credits
- billing accounts
- credit cards
- metered services that can automatically create charges

Optional online services are allowed only under the rules in `FREE_OPERATION.md`.

## 3. Local/offline operation must remain available

After required models/dependencies are installed, the core workflow must work without internet access.

A network failure must never make the whole application unusable.

## 4. Naturalness is a primary product requirement

Do not optimize only for speed.

The audio should sound like a coherent conversation, not unrelated TTS sentences stitched together.

Read `AUDIO_QUALITY.md`.

## 5. Voice cloning is first-class

The voice system must support:

- built-in/local voices
- reference-audio voice cloning
- saved voice profiles
- per-character voice assignment
- alternate engines

Do not hard-code the app around one voice model.

## 6. Speakers are dynamic

Never hard-code only `Host`, `Co-Host`, or `Guest`.

Any valid speaker name discovered from Markdown should be usable.

## 7. Respect the target hardware

Target system:

```txt
AMD Ryzen 5 5600H
32 GB RAM
NVIDIA GTX 1650
4 GB VRAM
```

Do not assume a high-end modern GPU.

Read `SYSTEM_LIMITS.md` before adding local AI models or changing concurrency.

## 8. Preserve user data

Never automatically delete:

- Markdown scripts
- project configuration
- voice reference recordings
- manually selected/locked takes
- final exports

Cache cleanup may only remove data that is explicitly safe to regenerate.

## 9. No silent dialogue rewriting

A speech-direction system may decide *how* a line is spoken.

It may not silently change *what* the line says.

## 10. Keep providers/engines replaceable

Local speech engines and optional free online engines must be behind interfaces/adapters.

Do not spread engine-specific conditionals throughout the application.

---

# Preferred technology

Default architecture:

```txt
Python
PySide6
local files / JSON
local model files
FFmpeg
bounded background workers
```

Do not introduce a database unless a concrete problem cannot reasonably be solved with local files.

Do not introduce Docker, Redis, PostgreSQL, Kubernetes, microservices, OAuth, analytics, billing, or remote object storage for the personal MVP.

---

# Product flow

```txt
Open Markdown
      ↓
Parse script
      ↓
Detect speakers
      ↓
Load voice profiles
      ↓
Preview / assign voices
      ↓
Plan synthesis
      ↓
Reuse cached/locked takes
      ↓
Generate missing speaker turns
      ↓
Apply conversational timing
      ↓
Assemble with FFmpeg
      ↓
Listen / regenerate individual takes
      ↓
Export final audio
```

---

# Generation unit

The normal synthesis unit is a **complete speaker turn**, not each sentence.

Example:

```md
Host: That's interesting. I hadn't thought about it that way. So what happened next?
```

Prefer one synthesis request for the entire Host turn if the engine can handle it safely.

This improves prosody and continuity.

---

# Resource rule

Never create one thread/process/model job per dialogue segment.

Use bounded queues.

Default heavy local synthesis concurrency should be one job at a time unless profiling proves a higher value is safe.

---

# Dependency rule

Before adding a dependency, model, or service, check:

1. Does it cost money?
2. Can it create charges?
3. Does it require an account or billing method?
4. Does it work locally/offline?
5. What is its license?
6. How much RAM/VRAM does it need?
7. Will it fit the target machine?
8. Is it replaceable?
9. Does it transmit script or voice data externally?
10. Can the app work without it?

Document material decisions in `DECISIONS.md`.

---

# Documentation rule

If implementation changes a documented product or architecture decision, update the relevant Markdown file in the same change.

Do not allow implementation and documentation to drift apart.

---

# Priority order

When requirements conflict, prefer:

```txt
1. Protect user files and system stability
2. Keep total monetary cost at $0
3. Preserve local/offline capability
4. Produce natural audio
5. Preserve voice/character consistency
6. Minimize unnecessary regeneration
7. Keep the UI responsive
8. Generation speed
```
