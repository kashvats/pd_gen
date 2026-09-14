> **Implementation status — natural speech update:** Real Kokoro ONNX English
> preset speech is now available after explicit installation. Edge is optional
> and requires online permission. Paid/system/mock engines are not registered
> for normal generation. The legacy cloning tone generator is disabled; real
> cloning remains a future goal. Unsupported acting controls are disabled.
> See START_HERE.md for setup and current limitations; aspirational sections
> below are not claims that every planned feature is implemented.

# Audio Quality and Naturalness

## Primary goal

The application should make a Markdown conversation sound alive.

The target is not simply intelligible TTS.

The target is a coherent, natural performance with stable characters and believable conversational timing.

---

# Quality priorities

Prefer:

1. voice identity consistency
2. natural prosody
3. understandable pronunciation
4. conversational timing
5. emotional/contextual appropriateness
6. smooth audio assembly
7. generation speed

---

# Generate whole speaker turns

Normal synthesis unit:

```txt
one complete speaker turn
```

Example:

```md
Host: That's interesting. I hadn't thought about it that way. So what happened next?
```

Prefer generating this as one unit.

Do not split each sentence unless:

- engine limits require it
- memory limits require it
- the user explicitly requests it

Whole-turn synthesis preserves sentence-to-sentence flow.

---

# Long-turn splitting

When a turn must be split:

1. paragraph boundary
2. sentence boundary
3. natural clause boundary

Never split in the middle of a word.

Avoid splitting immediately before or after short dependent phrases.

Reassemble pieces with minimal audible seams.

---

# Conversational context

The current line should not be treated as isolated.

Example:

```md
Host: You actually built one yourself?

Guest: Yeah. Last weekend.

Host: Seriously?

Guest: Seriously. It worked surprisingly well.
```

The second Host turn is a reaction.

The Speech Director may inspect neighboring turns to infer delivery.

Only the current turn is synthesized as spoken content.

---

# Speech Director

The Speech Director creates delivery guidance.

It may infer:

- question
- mild surprise
- excitement
- seriousness
- hesitation
- calmness
- energy level
- pace
- emphasis
- reaction style

It must not rewrite the dialogue.

---

# Deterministic local director first

The initial implementation should use local rules based on:

- punctuation
- explicit Markdown directives
- turn length
- previous/next speaker
- question/exclamation structure
- character profile
- project preset

This is free, fast, offline, and predictable.

A small local model may be added later if hardware permits.

---

# No silent rewriting

Given:

```txt
What did you do?
```

do not silently synthesize:

```txt
Whoa, what did you actually do?!
```

Delivery metadata is separate from text.

---

# Project presets

Provide:

```txt
Natural Conversation
Podcast
Narration
Calm
Energetic
Custom
```

Default:

```txt
Natural Conversation
```

Presets influence delivery/timing, not the actual words.

---

# Character direction

Persistent character direction should influence performance.

Example:

```txt
Host:
Warm and conversational.
Confident but not announcer-like.
Moderate pace.

Co-Host:
Curious.
Slightly higher energy.
Natural reactions.
```

---

# Explicit turn direction

When Markdown contains:

```md
Host [surprised]: You finished already?
```

explicit direction should override weaker automatically inferred direction.

---

# Natural pause engine

Do not insert one fixed pause everywhere.

Pause decisions can depend on:

- speaker change
- punctuation
- question/answer
- interruption/reaction
- paragraph/topic transition
- explicit pause directive

Starting ranges can be approximately:

```txt
quick reaction:        150–300 ms
normal speaker change: 250–500 ms
topic transition:      500–900 ms
```

These are heuristics, not random rules.

---

# Avoid random naturalness hacks

Do not randomly change:

- pitch
- speed
- volume
- pause duration

just to imitate human variation.

Use context and engine behavior.

Randomness that changes voice identity should be minimized.

---

# Pronunciation dictionary

Support global and project pronunciation entries.

Example:

```txt
GPT → G-P-T
SQL → sequel
Nguyen → custom pronunciation
```

The exact representation may depend on the active engine.

Pronunciation configuration must participate in cache hashing.

---

# Text cleanup

Before synthesis:

- remove Markdown formatting markers that should not be spoken
- preserve punctuation that helps prosody
- normalize obviously problematic whitespace
- preserve words exactly
- do not paraphrase
- do not expand abbreviations unless a pronunciation rule says to

---

# Numbers and symbols

When engines pronounce numbers/symbols badly, use a reversible speech-preparation layer.

The displayed Markdown remains unchanged.

Prepared speech text may differ only for pronunciation purposes and must be inspectable/debuggable.

---

# Alternate takes

For important turns:

```txt
Generate Another Take
```

Keep previous takes.

Allow auditioning and selecting the preferred one.

---

# Locked takes

A locked take must survive:

- project reopen
- final reassembly
- unrelated script edits
- cache cleanup

It should regenerate only after explicit unlock or a direct request.

---

# Cache and quality

Cache by synthesis inputs.

Do not reuse an old take if any relevant input changed:

- text
- voice/reference
- engine
- engine version/model identifier
- delivery direction
- speed
- pronunciation
- synthesis settings

---

# Voice consistency

Avoid dramatic identity drift between turns.

Where an engine exposes settings that influence consistency, choose conservative defaults.

A character may sound:

- amused
- serious
- curious
- excited
- calm

while still clearly remaining the same character.

---

# Audio boundaries

Avoid audible:

- clicks
- pops
- cut-off consonants
- clipped tails
- abrupt noise-floor changes

Use tiny fades only where helpful.

Do not trim so aggressively that natural speech endings are removed.

---

# Loudness

Do not aggressively normalize every tiny segment to exactly the same loudness.

That can destroy natural dynamics.

Prefer:

1. sensible per-engine output handling,
2. optional gentle segment correction only when truly needed,
3. final program-level loudness processing.

---

# Intermediate formats

Prefer lossless/high-quality intermediates where practical.

Avoid repeated MP3 → MP3 transcoding.

Possible flow:

```txt
generated WAV
   ↓
assembly
   ↓
master WAV
   ↓
MP3 export
```

---

# Noise / breaths

Do not automatically remove all breaths.

Do not automatically add fake breaths.

Natural engine output should be preserved unless a clear artifact needs correction.

---

# Studio mode

Studio mode may:

- use the best compatible local engine
- use longer context
- apply more careful direction
- allow alternate takes
- use higher-quality intermediates
- perform more careful final assembly

Studio mode must still obey system resource limits.

---

# Quality review UI

For each turn show:

```txt
Speaker
Text
Selected Take
Duration
[Play]
[Another Take]
[Lock]
[Regenerate]
```

The user should be able to fix one bad performance without touching the rest.

---

# Final success test

Given:

```md
Host: Did you really build the whole thing yourself?

Guest: Yeah. It took most of the weekend, though.

Host: That's actually pretty impressive.

Co-Host: Pretty impressive? I'd say that's slightly insane.

Guest: Honestly, that's probably fair.
```

The result should have:

- clearly distinct speakers
- believable question intonation
- a natural short Guest response
- a Host reaction that sounds impressed
- Co-Host timing that makes the joke land
- a relaxed final Guest response
- no obvious stitching artifacts

That is the quality bar.
