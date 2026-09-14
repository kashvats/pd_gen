# System Limits

## Target computer

The application is primarily designed for:

```txt
CPU: AMD Ryzen 5 5600H
CPU layout: 6 cores / 12 threads
RAM: 32 GB
GPU: NVIDIA GTX 1650
VRAM: 4 GB
```

These constraints are part of the product requirements.

---

# Primary safety rule

Never maximize resource usage by default.

A slower stable generation is better than:

- frozen UI
- system instability
- CUDA out-of-memory
- excessive swapping
- disk exhaustion
- long periods of unnecessary 100% CPU/GPU usage

---

# Performance profiles

Provide:

```txt
Safe
Balanced
Performance
```

Default:

```txt
Balanced
```

Never automatically switch to Performance.

---

# Balanced defaults

Initial conservative defaults:

```txt
Heavy local neural synthesis jobs: 1
Final FFmpeg assembly jobs:        1
CPU worker budget:                 about 6 logical threads
Free-online network jobs:          bounded separately if used
```

These can be adjusted after real profiling.

---

# Safe mode

Suggested:

```txt
Heavy local synthesis: 1
CPU worker budget:      about 4 logical threads
FFmpeg jobs:            1
GPU use:                conservative / optional
```

Designed to keep the computer comfortable for other work.

---

# Performance mode

May use somewhat more CPU or a faster compatible device configuration.

It must still:

- keep queues bounded
- reserve RAM
- avoid VRAM exhaustion
- keep the UI responsive
- run only one heavy local model job unless proven safe otherwise

---

# GPU rule

4 GB VRAM is limited.

Do not assume a modern speech model fits on CUDA simply because CUDA is present.

Before loading a local model on GPU:

- check available VRAM
- know approximate model/runtime needs
- leave headroom for Windows/display
- prefer CPU when uncertain

A model that requires substantially more VRAM must not be a default dependency.

---

# VRAM target

As an initial conservative policy, avoid intentionally planning around more than roughly:

```txt
3.0–3.2 GB application VRAM
```

This is a soft planning limit, not a promise that every workload at that size will be safe.

Runtime free-VRAM checks are more important than a fixed number.

---

# CUDA OOM behavior

If CUDA out-of-memory occurs:

1. stop scheduling new GPU work,
2. preserve completed audio,
3. unload/clear the failed model where safe,
4. do not loop-retry the same GPU operation,
5. offer CPU fallback or a lighter engine,
6. keep the application usable.

A CUDA OOM must not corrupt the project.

---

# RAM policy

32 GB total RAM does not mean the app may consume 32 GB.

Aim to leave a substantial reserve for:

- Windows
- browser
- editor/IDE
- filesystem cache
- other applications

Prefer file-based/streaming workflows.

---

# RAM targets

Initial guidance:

```txt
Normal app + lightweight generation: preferably under 8 GB
Heavy generation:                   preferably under 16 GB
Danger zone:                        avoid sustained app use above ~20 GB
```

Actual decisions should use *available memory*, not only these static numbers.

---

# Low-memory behavior

If available RAM becomes too low:

- stop launching new heavy tasks
- allow current safe tasks to complete
- unload unused models
- release temporary buffers
- warn the user
- preserve completed work
- allow resume later

Do not intentionally drive the system into severe swapping.

---

# CPU policy

The Ryzen 5 5600H has 12 logical threads.

Default heavy worker settings should not consume all 12 for long periods.

Balanced initial target:

```txt
about 6 logical threads
```

Safe:

```txt
about 4
```

Performance may increase after profiling.

FFmpeg thread count should also be bounded when appropriate.

---

# UI responsiveness

Never run heavy work on the PySide GUI thread.

The UI must remain responsive during:

- model loading
- synthesis
- file conversion
- hashing
- FFmpeg assembly
- model scanning

Use background workers and signals/events.

---

# Local synthesis concurrency

Default:

```txt
1 heavy neural speech generation at a time
```

Do not run several large inference jobs in parallel on a 4 GB GPU.

Sequential generation plus caching is the preferred strategy.

---

# FFmpeg concurrency

Default:

```txt
1 major FFmpeg job
```

Do not assemble multiple full episodes simultaneously.

---

# Model loading

Load heavy models lazily.

Normally keep only the currently active heavy speech model loaded.

When switching to another heavy engine:

```txt
finish/save work
unload old model
load new model
```

Do not keep several large models in VRAM simultaneously.

---

# Local model downloads

Never silently download large models.

Before downloading, show:

- model name
- purpose
- download size
- license
- expected RAM
- expected VRAM
- CPU support
- install path

Require explicit action.

---

# Disk protection

Audio/model caches can grow large.

Before major generation/model installation, check free disk space.

Maintain a safety reserve.

Suggested default:

```txt
minimum free disk reserve: 10 GB
```

Optionally combine this with a percentage-based warning.

---

# Cache limit

Suggested default cache budget:

```txt
20 GB
```

Make it configurable.

Automatic cleanup may delete only safe-to-regenerate cache files.

Never automatically delete:

- script.md
- project.json
- voice references
- locked takes
- final exports

---

# Temporary files

Use a dedicated temp directory.

Example:

```txt
cache/temp/
```

Clean stale temp files after crashes when safe.

Never confuse temp files with user source files.

---

# Project audio memory

Do not decode hours of audio into one giant Python array.

Prefer:

- per-turn files
- FFmpeg concat manifests
- streaming/process-based transforms
- temporary lossless files

---

# Model manager

Each installed model should have metadata such as:

```json
{
  "id": "engine-model",
  "path": "models/engine-model",
  "size_bytes": 0,
  "cpu_supported": true,
  "cuda_supported": true,
  "estimated_vram_mb": null,
  "license": "verify-at-install"
}
```

Do not load a model whose requirements are unknown without warning/testing.

---

# Hardware compatibility test

Provide a small test mode for an installed engine:

```txt
Load model
Generate short preview
Measure time
Measure peak RAM if available
Measure peak VRAM if available
Unload model
```

Use this to decide whether the engine should be marked:

```txt
Recommended
CPU Only
Experimental
Unsafe on GPU
```

---

# Temperature / sustained load

The application does not need to directly control hardware temperature.

Resource limits should avoid unnecessary sustained maximum load.

Optional temperature display may be added later if reliable, but it is not required for MVP.

---

# Pause, resume, cancel

Long generation must support:

```txt
Pause
Resume
Cancel
```

Pause:

- stops scheduling new work
- preserves completed turns

Cancel:

- stops the generation job safely
- preserves the project and completed cache

Resume:

- reuses completed work
- continues remaining turns

---

# Free-online concurrency

If an optional free online engine is added, its network requests must also be bounded.

Do not create one request per script line simultaneously.

Free service limits must be respected without ever switching to paid usage.

---

# System monitor

Optional generation display:

```txt
CPU:       41%
RAM:       10.2 / 32 GB
VRAM:      2.4 / 4 GB
Disk Free: 120 GB
Engine:    Local
Queue:     18 remaining
```

Update every few seconds, not many times per second.

---

# Absolute AI-agent rule

When considering a new local AI feature, evaluate it against:

```txt
Ryzen 5 5600H
32 GB RAM
GTX 1650 4 GB VRAM
```

If it is too heavy:

1. find a lighter model,
2. use CPU if practical,
3. make it optional,
4. or use a genuinely free online alternative with local fallback.

Do not simply assume stronger hardware.
