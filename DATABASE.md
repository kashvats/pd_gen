# Storage & Data Model — Local JSON Architecture

The application uses a local JSON-based file storage structure optimized for zero-latency desktop workflows.

---

# Directory Layout

```txt
data/
├── config/
│   ├── pronunciation.json          # Global pronunciation substitutions
│   └── characters.json             # Global character voice defaults
│
├── voices/
│   └── {voiceId}/
│       ├── voice.json              # VoiceProfile metadata & delivery parameters
│       └── references/             # Preserved original audio samples (.wav)
│           ├── reference_01.wav
│           └── reference_02.wav
│
├── cache/
│   └── {sha256_hash}.wav           # Deterministic synthesis audio cache
│
└── projects/
    └── {projectId}/
        ├── project.json            # Project metadata, speaker mappings, AST nodes
        ├── script.md               # Raw markdown source
        └── audio/
            ├── takes/              # Individual dialogue segment takes
            │   ├── {segmentId}_take_1.wav
            │   └── {segmentId}_take_2.wav
            └── final.mp3           # Assembled master track
```

---

# Data Models

### 1. `project.json`
```json
{
  "id": "proj_12345",
  "name": "The AI Show — Episode 1",
  "markdown": "Host: Welcome...",
  "speakers": {
    "Host": {
      "name": "Host",
      "voice_name": "My Host Voice",
      "provider": "elevenlabs",
      "voice_id": "21m00Tcm4TlvDq8ikWAM",
      "preset": "Podcast",
      "direction_prompt": "Warm, engaging host.",
      "delivery": {
        "pace": 1.0,
        "energy": 0.7,
        "expressiveness": 0.75,
        "warmth": 0.7
      }
    }
  },
  "script_nodes": [],
  "segments_generation": {
    "seg_001": {
      "segment_id": "seg_001",
      "speaker": "Host",
      "status": "complete",
      "active_take_index": 0,
      "takes": [
        {
          "take_number": 1,
          "audio_path": "...",
          "generation_hash": "...",
          "duration_ms": 3200,
          "is_locked": false
        }
      ]
    }
  },
  "settings": {
    "output_format": "mp3",
    "generation_mode": "studio",
    "normalize_loudness": true,
    "target_lufs": -16.0
  }
}
```

### 2. `voice.json`
```json
{
  "id": "clone_host_123",
  "name": "My Host Voice",
  "provider": "elevenlabs",
  "voice_id": "custom_eleven_id",
  "voice_type": "instant_clone",
  "language": "en",
  "delivery": {
    "pace": 1.0,
    "energy": 0.7,
    "expressiveness": 0.75,
    "warmth": 0.7,
    "style": "natural conversational host"
  },
  "reference_files": [
    "data/voices/clone_host_123/references/reference_01.wav"
  ],
  "consent": {
    "confirmed": true,
    "speaker_name": "Host Speaker",
    "statement": "I confirm that this is my voice or that I have permission...",
    "timestamp": "2026-09-07T17:00:00"
  }
}
```