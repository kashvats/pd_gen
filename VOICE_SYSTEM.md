> **Implementation status — natural speech update:** Real Kokoro ONNX English
> preset speech is now available after explicit installation. Edge is optional
> and requires online permission. Paid/system/mock engines are not registered
> for normal generation. The legacy cloning tone generator is disabled; real
> cloning remains a future goal. Unsupported acting controls are disabled.
> See START_HERE.md for setup and current limitations; aspirational sections
> below are not claims that every planned feature is implemented.

# Voice System

## Goal

Provide reusable, natural, character-consistent voices without requiring paid services.

Voice cloning/reference conditioning is a first-class capability.

---

# Voice types

A voice profile may be:

```txt
Built-in Local Voice
Reference / Cloned Local Voice
Optional Free Online Voice
Experimental Local Voice
```

The application must always support a free local path.

---

# Voice profile

Store reusable profiles under a local voice library.

Example:

```txt
voices/
    main-host/
        voice.json
        references/
            reference-01.wav
            reference-02.wav

    narrator/
        voice.json
```

Example profile:

```json
{
  "version": 1,
  "id": "main-host",
  "name": "Main Host",
  "engine": "local-cloning-engine",
  "voice_type": "reference",
  "language": "en",
  "reference_audio": [
    "references/reference-01.wav"
  ],
  "direction": "Warm, conversational, confident, never announcer-like.",
  "defaults": {
    "speed": 1.0
  },
  "consent_confirmed": true
}
```

---

# Permission / consent

Only create or use a cloned voice when the user owns the voice or has permission from the speaker.

When creating a reference-based profile, require a local acknowledgement:

```txt
I confirm that this is my voice or that I have permission to use it.
```

Store this acknowledgement locally.

Do not design features intended for covert impersonation.

---

# Reference audio

Reference audio quality strongly affects cloning quality.

Recommended guidance:

- one speaker only
- quiet room
- minimal echo
- no background music
- no clipping
- natural speaking style
- use the style/accent you want the generated voice to preserve
- avoid aggressive denoising unless necessary

---

# Reference quality checks

Perform lightweight local checks where practical:

- duration
- silence ratio
- clipping
- very low level
- obvious multiple-channel anomalies
- sample rate
- file corruption

Optional later checks:

- background-noise estimate
- multiple-speaker detection

Quality checking must remain light enough for `SYSTEM_LIMITS.md`.

---

# Preserve originals

Original voice references are user source data.

Never delete them through:

- cache cleanup
- temp cleanup
- failed generation cleanup
- project rebuilds

Deletion must be explicit.

---

# Voice library UI

Example:

```txt
VOICE LIBRARY

Main Host
Reference Voice
Engine: Local Cloning Engine
[Preview] [Edit]

Narrator
Built-in Voice
Engine: Lightweight Local Engine
[Preview] [Edit]

+ Create Voice
```

---

# Create voice flow

```txt
Create Voice
   ↓
Name
   ↓
Choose local speech engine
   ↓
Add reference audio if required
   ↓
Reference quality check
   ↓
Consent acknowledgement
   ↓
Preview
   ↓
Save voice profile
```

---

# Character assignment

A project maps detected characters to voice profiles.

Example:

```json
{
  "Host": "main-host",
  "Co-Host": "maya",
  "Guest": "guest-one"
}
```

Project assignment overrides any global default.

---

# Global character defaults

Optional configuration can remember commonly used mappings.

Example:

```json
{
  "Host": "main-host",
  "Narrator": "main-narrator"
}
```

When a new project contains the same character, suggest the usual voice.

Do not force the assignment.

---

# Character delivery profile

A character can have persistent performance direction independent of the raw voice identity.

Example:

```txt
Host:
Warm, confident podcast host.
Conversational.
Moderate energy.
Subtle emphasis.
Never theatrical.

Co-Host:
Friendly and curious.
Slightly more energetic.
Natural reactions.
```

This direction should be combined with turn-specific context/directions where supported.

---

# Voice consistency

Within a project, the same character should preserve:

- voice identity
- accent
- general vocal age/timbre
- average pace
- baseline energy

Variation in emotion is allowed without changing identity.

---

# Speech engine abstraction

Do not couple voices to one implementation.

Conceptually:

```python
class SpeechEngine:
    def capabilities(self):
        ...

    def list_built_in_voices(self):
        ...

    def synthesize(self, request):
        ...

    def supports_reference_audio(self):
        ...

    def load(self, device):
        ...

    def unload(self):
        ...
```

---

# Candidate local engines

The project may evaluate free/open local engines such as:

- lightweight local TTS engines
- local zero-shot/reference voice engines
- local voice-conversion engines
- experimental research TTS engines

Concrete engines can change over time.

Before making an engine a default, verify its current:

- license
- cost
- model availability
- quality
- RAM/VRAM requirements
- CPU performance
- voice-cloning capability
- language support

The architecture matters more than locking the product to one model name.

---

# Model manager

Models should be installed explicitly.

Example:

```txt
MODELS

Lightweight Local Voice Engine
Installed
2.1 GB

Reference Voice Engine
Installed
3.4 GB

Experimental Studio Engine
Not Installed
```

Show download size before installation.

Never silently download multi-gigabyte models during generation.

---

# Device selection

Each engine may support:

```txt
Auto
CPU
CUDA
```

`Auto` must obey `SYSTEM_LIMITS.md`.

Do not assume CUDA is always faster or safe on a 4 GB GPU.

---

# Preview

Voice preview must be cheap and local when possible.

Use a short standard phrase or a user-entered preview phrase.

Cache preview output when the inputs are unchanged.

---

# Alternate takes

Speech generation may vary naturally between attempts.

Allow multiple takes for a turn.

The voice profile remains the same; only the generated performance changes.

---

# Engine-specific settings

Keep engine-specific settings inside the voice/engine adapter.

The main UI can expose normalized controls such as:

- speed
- expressiveness
- stability/consistency
- temperature/randomness when appropriate

Only show controls that the selected engine actually supports.

---

# Free online engines

Optional genuinely free online engines may be added.

Rules:

- never required
- explicit online label
- explicit consent before uploading reference audio
- must not be able to create charges
- local fallback always available
- removable from the architecture

See `FREE_OPERATION.md`.

---

# Voice data privacy

Default behavior:

```txt
Reference Audio → stays local
Voice Profile → stays local
Generated Audio → stays local
```

Nothing is uploaded unless the user explicitly selects an online engine and confirms it.

---

# Deleting a voice

Before deleting a voice profile, warn if projects reference it.

Do not silently remove reference recordings needed by existing projects.

Prefer "remove from library" and explicit source-data deletion as separate actions.

---

# Future features

Possible later additions:

- voice profile export/import
- multiple references per profile
- reference ranking
- per-language voice settings
- per-character pronunciation overrides
- style presets
- local voice-conversion stage

These must remain free to operate and within system limits.
