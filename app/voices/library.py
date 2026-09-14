"""Local Voice Library manager for storing, querying, and updating voices."""

import json
import shutil
from pathlib import Path
from typing import List, Dict, Optional

from app.config.settings import VOICES_DIR
from app.models.voice import VoiceProfile, VoiceDelivery, ConsentRecord
from app.tts.registry import tts_registry


class VoiceLibrary:
    """Manages locally saved voice profiles and provider presets."""

    def __init__(self, root_dir: Path = VOICES_DIR):
        self.root_dir = root_dir
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self._seed_default_library()

    def _seed_default_library(self):
        """Seeds initial default voices if library is empty."""
        # Add missing neural presets to existing libraries without altering saved voices.
        from app.tts.kokoro_provider import KokoroProvider
        from app.tts.edge_provider import EdgeTTSProvider
        for provider in (KokoroProvider(), EdgeTTSProvider()):
            for voice in provider.list_voices():
                profile_id = f"{provider.provider_id}_{voice.id}"
                if (self.root_dir / profile_id / "voice.json").exists():
                    continue
                self.save_voice(VoiceProfile(
                    id=profile_id, name=voice.name, provider=provider.provider_id,
                    voice_id=voice.id, voice_type="builtin", language=voice.language,
                    description=provider.display_name,
                ))

    def list_voices(self) -> List[VoiceProfile]:
        """Returns all local voice profiles."""
        voices: List[VoiceProfile] = []
        for voice_folder in self.root_dir.iterdir():
            if voice_folder.is_dir():
                v_file = voice_folder / "voice.json"
                if v_file.exists():
                    try:
                        with open(v_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            voices.append(VoiceProfile.from_dict(data))
                    except Exception:
                        pass
        return sorted(voices, key=lambda x: x.name)

    def get_voice(self, voice_id: str) -> Optional[VoiceProfile]:
        """Retrieves a single voice profile by ID."""
        for v in self.list_voices():
            if v.id == voice_id or v.voice_id == voice_id:
                return v
        return None

    def save_voice(self, profile: VoiceProfile) -> Path:
        """Persists a voice profile and directory structure."""
        voice_folder = self.root_dir / profile.id
        voice_folder.mkdir(parents=True, exist_ok=True)
        (voice_folder / "references").mkdir(parents=True, exist_ok=True)

        voice_file = voice_folder / "voice.json"
        with open(voice_file, "w", encoding="utf-8") as f:
            json.dump(profile.to_dict(), f, indent=2)

        return voice_folder

    def delete_voice(self, profile_id: str) -> bool:
        """Deletes a voice profile and associated files."""
        voice_folder = self.root_dir / profile_id
        if voice_folder.exists() and voice_folder.is_dir():
            shutil.rmtree(voice_folder, ignore_errors=True)
            return True
        return False
