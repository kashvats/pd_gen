> **Implementation status — natural speech update:** Real Kokoro ONNX English
> preset speech is now available after explicit installation. Edge is optional
> and requires online permission. Paid/system/mock engines are not registered
> for normal generation. The legacy cloning tone generator is disabled; real
> cloning remains a future goal. Unsupported acting controls are disabled.
> See START_HERE.md for setup and current limitations; aspirational sections
> below are not claims that every planned feature is implemented.

# Architecture

## Architecture goal

Build the simplest reliable local architecture that supports:

- Markdown parsing
- dynamic speakers
- reusable local voice profiles
- local voice cloning/reference conditioning
- multiple replaceable speech engines
- natural speech direction
- caching
- resumable generation
- audio assembly
- safe use of limited hardware
- zero monetary operating cost

---

# Recommended stack

```txt
Python
PySide6
FFmpeg
JSON / local files
PyTorch or engine-specific runtimes only where required
bounded worker queues
```

No database is required for the MVP.

---

# High-level pipeline

```txt
Markdown File
      ↓
Parser
      ↓
Script AST
      ↓
Speaker Detection
      ↓
Character / Voice Mapping
      ↓
Speech Director
      ↓
Generation Planner
      ↓
Cache / Locked-Take Check
      ↓
Local Speech Engine
      ↓
Generated Turn Audio
      ↓
Pause / Timeline Builder
      ↓
FFmpeg Assembly
      ↓
Final Audio
```

Optional genuinely free online engines may plug into the same engine interface, but the local path remains primary.

---

# Suggested source tree

```txt
app/
├── main.py
│
├── ui/
│   ├── main_window.py
│   ├── project_browser.py
│   ├── markdown_editor.py
│   ├── dialogue_editor.py
│   ├── character_panel.py
│   ├── voice_library.py
│   ├── voice_editor.py
│   ├── generation_panel.py
│   ├── audio_player.py
│   ├── model_manager.py
│   └── settings_dialog.py
│
├── parser/
│   ├── markdown_parser.py
│   ├── speaker_detector.py
│   ├── directives.py
│   ├── ast.py
│   └── validation.py
│
├── speech/
│   ├── director.py
│   ├── context.py
│   ├── pronunciation.py
│   ├── text_prepare.py
│   └── timing.py
│
├── engines/
│   ├── base.py
│   ├── registry.py
│   ├── capabilities.py
│   ├── local/
│   │   ├── lightweight_engine.py
│   │   ├── cloning_engine.py
│   │   └── experimental_engine.py
│   └── online_free/
│       └── optional_engine.py
│
├── voices/
│   ├── library.py
│   ├── profile.py
│   ├── references.py
│   ├── quality_check.py
│   └── consent.py
│
├── generation/
│   ├── planner.py
│   ├── queue.py
│   ├── worker.py
│   ├── retry.py
│   ├── cache.py
│   ├── takes.py
│   └── manifest.py
│
├── audio/
│   ├── ffmpeg.py
│   ├── assemble.py
│   ├── normalize.py
│   ├── silence.py
│   └── formats.py
│
├── projects/
│   ├── project.py
│   ├── project_store.py
│   ├── recent.py
│   └── migration.py
│
├── models/
│   ├── manager.py
│   ├── metadata.py
│   └── hardware_check.py
│
├── system/
│   ├── resources.py
│   ├── limits.py
│   ├── device.py
│   └── disk.py
│
└── config/
    ├── settings.py
    └── paths.py
```

Names can change, but responsibilities should remain separated.

---

# Script representation

Use a structured AST rather than passing raw Markdown through every layer.

Example:

```python
@dataclass
class DialogueNode:
    id: str
    order: int
    speaker: str
    text: str
    directives: dict

@dataclass
class PauseNode:
    id: str
    order: int
    duration_ms: int

@dataclass
class SoundEffectNode:
    id: str
    order: int
    path_or_name: str
```

Future nodes can be added without redesigning the generation engine.

---

# Speech engine abstraction

Use one shared interface.

Conceptually:

```python
class SpeechEngine(Protocol):
    id: str

    def capabilities(self) -> EngineCapabilities:
        ...

    def load(self, device: str) -> None:
        ...

    def unload(self) -> None:
        ...

    def synthesize(self, request: SynthesisRequest) -> SynthesisResult:
        ...
```

Example request:

```python
@dataclass
class SynthesisRequest:
    text: str
    language: str | None
    voice_profile_id: str
    reference_audio: list[str]
    direction: str | None
    speed: float
    pronunciation: dict
    engine_settings: dict
```

Do not make the rest of the application know engine-specific implementation details.

---

# Engine capability system

Different engines can support different features.

Example:

```python
@dataclass
class EngineCapabilities:
    local: bool
    free: bool
    voice_cloning: bool
    built_in_voices: bool
    style_instructions: bool
    emotion_tags: bool
    cpu: bool
    cuda: bool
    languages: list[str]
```

The UI should only expose features supported by the active engine.

---

# Local-first engine registry

The engine registry should distinguish:

```txt
LOCAL_FREE
ONLINE_FREE_OPTIONAL
DISABLED
```

Paid engines are not part of the supported normal architecture.

Candidate local engines may be evaluated over time, but engine selection must remain replaceable.

Before adding any concrete model, verify:

- current license
- download size
- RAM need
- VRAM need
- CPU fallback
- quality
- voice-cloning support
- language support

Do not hard-code assumptions from old documentation.

---

# Voice profiles

Voice profiles should be local files.

Example:

```json
{
  "id": "main-host",
  "name": "Main Host",
  "engine": "local-cloning-engine",
  "language": "en",
  "reference_audio": [
    "references/reference-01.wav"
  ],
  "defaults": {
    "speed": 1.0
  },
  "direction": "Warm, natural conversational host.",
  "consent_confirmed": true
}
```

Project voice assignment references the voice profile ID.

---

# Project file

Use a readable `project.json`.

Example:

```json
{
  "version": 1,
  "name": "AI Agents",
  "script": "script.md",
  "quality_mode": "studio",
  "default_pause_ms": 350,
  "characters": {
    "Host": {
      "voice_profile": "main-host"
    },
    "Guest": {
      "voice_profile": "guest-voice"
    }
  }
}
```

Keep migrations simple and versioned.

---

# Generation planner

Before synthesis, build a plan.

Example:

```txt
120 speaker turns

85 cached
12 locked
23 need synthesis
```

Only generate the 23 missing turns.

The planner should calculate the expected engine/device needs before starting.

---

# Cache design

Cache keys must include every synthesis-relevant input:

- spoken text
- engine
- model/version identifier
- voice profile/reference fingerprint
- direction
- speed
- pronunciation mapping
- relevant engine settings

Do not include irrelevant project metadata.

A deterministic hash can be used as the cache key.

---

# Takes

Each dialogue turn can have multiple audio takes.

Store:

- generated take path
- cache key
- creation time
- engine
- settings
- duration
- selected status
- locked status

The selected locked take takes precedence over automatic regeneration.

---

# Generation queue

Use a bounded queue.

For local neural synthesis, default concurrency:

```txt
1 heavy inference job
```

Do not parallelize heavy GPU/CPU model inference by default.

Network-only optional free engines may use separate bounded concurrency if later implemented, but they must still respect system and service limits.

---

# Model lifecycle

Heavy local models should be loaded lazily.

Prefer:

```txt
load engine when needed
generate queued turns
unload when switching heavy engines
```

Do not load every installed speech model at application startup.

Do not keep several large models in VRAM at the same time.

---

# Speech Director

The Speech Director produces delivery metadata without changing dialogue text.

Input can include:

- current speaker turn
- previous turn
- next turn
- character direction
- explicit Markdown direction
- punctuation
- project style

Output can include:

- pace hint
- energy
- emotion/style
- emphasis hints
- pause recommendation

The first version should use deterministic local rules.

A small local model may be added later if it fits `SYSTEM_LIMITS.md`.

Optional free online analysis must never be required.

---

# Audio files

Prefer high-quality intermediates.

Possible flow:

```txt
speech engine output
      ↓
WAV/FLAC intermediate where practical
      ↓
timeline / silence
      ↓
FFmpeg assembly
      ↓
gentle loudness processing
      ↓
final WAV
      ↓
optional MP3 export
```

Avoid repeatedly re-encoding already lossy files.

---

# FFmpeg

FFmpeg should handle:

- concatenation
- silence
- trims/fades when needed
- sample-rate conversion
- channel conversion
- loudness processing
- final encoding

Do not load the entire episode into Python arrays when FFmpeg can stream/process files.

---

# UI threading

Never run:

- neural synthesis
- model loading
- FFmpeg
- large file scanning
- hashing of huge files

on the main PySide UI thread.

Use background workers with progress and cancellation.

---

# System resource manager

All heavy work must respect a central resource policy.

The resource manager controls:

- heavy inference concurrency
- CPU thread budget
- GPU device choice
- VRAM checks
- available RAM checks
- FFmpeg concurrency
- disk reserve
- cache size

See `SYSTEM_LIMITS.md`.

---

# Online integration rule

Optional online integrations must:

- be genuinely $0 at time of integration
- never be able to automatically create charges
- be clearly marked online
- require explicit consent before uploading script/voice data
- fail back to local operation
- remain removable without architectural redesign

See `FREE_OPERATION.md`.

---

# Security and privacy

Because this is local software:

- do not collect telemetry by default
- do not upload projects automatically
- do not upload voice references automatically
- do not require accounts
- do not store secrets unnecessarily
- keep user files readable and portable

---

# Failure handling

A failed segment must not invalidate the project.

Failures should preserve:

- completed cache entries
- selected takes
- locked takes
- project metadata
- original script

Generation can resume from remaining work.

---

# Architecture rule

Prefer straightforward local modules over infrastructure.

Do not introduce a server architecture merely because it is common in web products.
