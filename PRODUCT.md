> **Implementation status — natural speech update:** Real Kokoro ONNX English
> preset speech is now available after explicit installation. Edge is optional
> and requires online permission. Paid/system/mock engines are not registered
> for normal generation. The legacy cloning tone generator is disabled; real
> cloning remains a future goal. Unsupported acting controls are disabled.
> See START_HERE.md for setup and current limitations; aspirational sections
> below are not claims that every planned feature is implemented.

# Product Specification

## Product

A personal desktop **Markdown-to-Multi-Voice Audio Studio**.

The user writes a normal Markdown script:

```md
# The AI Show

Host: Welcome back to the show.

Co-Host: Today we're talking about AI agents.

Guest: Thanks for having me.
```

The application automatically detects the characters, allows a voice or cloned voice to be assigned to each character, generates natural speech, and creates a polished final audio file.

---

# Product vision

Writing multi-character audio should feel almost as simple as writing Markdown.

The application should handle the production work:

- speaker detection
- voice assignment
- local voice library
- reference-audio voice cloning
- conversational speech direction
- synthesis
- caching
- alternate takes
- pause timing
- audio assembly
- final export

The user should remain in control of the text and the selected performances.

---

# Personal use

This is intentionally a one-person application.

Do not design product features around:

- user accounts
- teams
- collaboration
- permissions
- subscriptions
- payment
- public sharing
- web hosting
- cloud project storage

Projects live on the user's computer.

---

# Core experience

```txt
script.md
   ↓
Open Project
   ↓
Detect Characters
   ↓
Assign Saved / Cloned Voices
   ↓
Preview
   ↓
Generate
   ↓
Review Individual Takes
   ↓
Regenerate Only What Is Needed
   ↓
Export final.mp3 / final.wav
```

---

# Example

Input:

```md
# Episode 5

Host: Did you really build the whole thing yourself?

Guest: Yeah. It took most of the weekend, though.

Host: That's actually pretty impressive.

Co-Host: Pretty impressive? I'd say that's slightly insane.

Guest: Honestly, that's probably fair.
```

Detected speakers:

```txt
Host
Guest
Co-Host
```

Example voice mapping:

```txt
Host     → Main Host Clone
Guest    → Guest Voice
Co-Host  → Co-Host Clone
```

The result should sound like a connected conversation, not five unrelated TTS clips.

---

# Character detection

Character names are not predefined.

Support names such as:

```txt
Host
Co-Host
Guest
Guest 1
Speaker 2
Alex
Maya
Dr. Lee
Dr. Sarah Lee
Professor Smith
AI Assistant
John O'Brien
Narrator
```

A project can contain any reasonable number of characters.

---

# Voice library

Maintain a reusable local voice library.

Each voice profile can contain:

- display name
- speech engine
- reference audio
- language
- default pace
- delivery notes
- engine-specific settings
- consent/ownership acknowledgement
- local model requirements
- optional preferred device

Example:

```txt
Main Host
Type: Reference/Cloned Voice
Engine: Local Engine A
Language: English

Narrator
Type: Built-in Voice
Engine: Local Engine B
Language: English
```

---

# Project-specific character settings

A project should remember:

- which voice is assigned to each character
- character delivery notes
- speed
- pronunciation overrides
- pause preferences
- chosen/locked takes
- output format
- generation quality mode

Closing and reopening the project must not lose these settings.

---

# Natural speech

The core quality goal is natural conversational speech.

Optimize for:

- prosody
- rhythm
- timing
- emphasis
- questions sounding like questions
- reactions sounding like reactions
- emotional continuity
- stable character identity
- pronunciation
- natural transitions between sentences
- natural silence between speakers

Avoid:

- robotic monotone
- sentence-by-sentence chopping
- identical pause length everywhere
- random pitch/speed variation
- aggressive normalization that destroys dynamics
- silent rewriting of the dialogue

See `AUDIO_QUALITY.md`.

---

# Voice cloning

Voice cloning/reference conditioning is a normal part of the product.

The user can create a voice profile from one or more local reference recordings.

The application should:

1. keep the original reference audio locally,
2. validate basic reference quality,
3. associate it with a local voice profile,
4. use a compatible local speech engine,
5. never require cloud upload,
6. optionally support a free online engine only with explicit user consent.

Only voices owned by the user or used with the speaker's permission should be cloned.

---

# Standard and Studio modes

## Standard

Goal:

- good quality
- faster local generation
- lower resource use

## Studio

Goal:

- best naturalness available at $0
- richer context/direction
- high-quality local engine when hardware permits
- optional alternate takes
- more careful final assembly

Studio mode must not mean "use all hardware."

System safety limits still apply.

---

# Alternate takes

Any speaker turn can support:

```txt
Take 1
Take 2
Take 3
```

The user can audition them and choose one.

A selected take can be locked.

Locked takes must not be regenerated unless explicitly unlocked.

---

# Editing

Provide both:

## Markdown view

The original editable Markdown.

## Dialogue view

Structured speaker turns.

Each dialogue block should allow:

- edit text
- change speaker
- preview
- regenerate
- generate another take
- lock selected take
- delete
- duplicate
- reorder if appropriate

The Markdown source remains a first-class file.

---

# Pronunciation

Support project and global pronunciation dictionaries.

Useful for:

- acronyms
- names
- technical terms
- foreign words
- preferred pronunciations

Pronunciation changes must affect the synthesis cache key.

---

# Audio output

Primary exports:

```txt
MP3
WAV
```

Optional later:

```txt
FLAC
M4A
```

Use high-quality/lossless intermediates where practical and encode lossy formats only at final export.

---

# Local projects

Example:

```txt
projects/
    ai-agents/
        script.md
        project.json
        audio/
            segments/
            takes/
            final.mp3

voices/
    main-host/
        voice.json
        references/
            reference-01.wav

models/
cache/
config/
```

---

# Cost requirement

Normal operation must cost exactly $0.

There must always be a free local generation path.

Optional online features are allowed only when they cannot create charges and are not required for the application to function.

See `FREE_OPERATION.md`.

---

# Hardware requirement

The main target machine is:

```txt
AMD Ryzen 5 5600H
32 GB RAM
NVIDIA GTX 1650
4 GB VRAM
```

The product must remain usable on this machine.

See `SYSTEM_LIMITS.md`.

---

# MVP success condition

The MVP succeeds when the user can:

1. open a Markdown script,
2. see dynamically detected speakers,
3. assign saved or reference-based local voices,
4. preview voices,
5. generate complete speaker turns,
6. reuse unchanged generated audio,
7. listen to the assembled conversation,
8. regenerate one bad turn without regenerating everything,
9. export a final audio file,
10. perform the entire core workflow without paying anything.
