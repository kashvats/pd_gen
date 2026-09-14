"""Deterministic audio caching based on synthesis parameters."""

import hashlib
import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

from app.config.settings import CACHE_DIR


def calculate_audio_hash(
    text: str,
    provider: str,
    voice_id: str,
    model: Optional[str] = None,
    speed: float = 1.0,
    delivery_direction: str = "",
    delivery_settings: Optional[Dict[str, Any]] = None,
    provider_settings: Optional[Dict[str, Any]] = None,
    pronunciation_version: str = "",
    studio_mode: bool = True,
) -> str:
    """Computes a deterministic SHA-256 hash for speech synthesis inputs."""
    data = {
        "pipeline_version": "natural-speech-2",
        "text": text.strip(),
        "provider": provider.lower().strip(),
        "voice_id": voice_id.strip(),
        "model": (model or "").strip(),
        "speed": round(speed, 3),
        "delivery_direction": delivery_direction.strip(),
        "delivery_settings": delivery_settings or {},
        "provider_settings": provider_settings or {},
        "pronunciation_version": pronunciation_version,
        "studio_mode": studio_mode,
    }
    serialized = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class AudioCache:
    """Manages cached synthesis audio files on local disk."""

    def __init__(self, cache_dir: Path = CACHE_DIR):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, audio_hash: str) -> Optional[Path]:
        """Returns path to cached audio file if it exists."""
        for ext in [".wav", ".mp3", ".m4a", ".flac"]:
            candidate = self.cache_dir / f"{audio_hash}{ext}"
            if candidate.exists() and candidate.stat().st_size > 0:
                return candidate
        return None

    def store(self, audio_hash: str, audio_bytes: bytes, audio_format: str = "wav") -> Path:
        """Saves raw audio bytes into cache directory under its hash."""
        ext = f".{audio_format.lstrip('.')}"
        dest = self.cache_dir / f"{audio_hash}{ext}"
        dest.write_bytes(audio_bytes)
        return dest

    def copy_to(self, audio_hash: str, target_path: Path) -> bool:
        """Copies cached file to a target project location."""
        cached = self.get(audio_hash)
        if cached and cached.exists():
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(cached, target_path)
            return True
        return False
