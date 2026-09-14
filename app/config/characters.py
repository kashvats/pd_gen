"""Global default character voice mappings and directions."""

import json
from pathlib import Path
from app.config.settings import GLOBAL_CHARACTERS_FILE


class CharacterDefaults:
    """Manages global character default assignments and personality presets."""

    DEFAULT_CONFIG = {
        name: {"voice_name": label, "provider": "kokoro", "voice_id": voice,
               "preset": "Natural Conversation", "direction": "Warm, conversational delivery."}
        for name, voice, label in [
            ("Host", "am_michael", "Michael • American male"),
            ("Co-Host", "af_heart", "Heart • American female"),
            ("Guest", "af_bella", "Bella • American female"),
            ("Narrator", "bm_george", "George • British male"),
        ]
    }

    @classmethod
    def load_defaults(cls) -> dict:
        if GLOBAL_CHARACTERS_FILE.exists():
            try:
                with open(GLOBAL_CHARACTERS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return dict(cls.DEFAULT_CONFIG)

    @classmethod
    def save_defaults(cls, config: dict) -> None:
        with open(GLOBAL_CHARACTERS_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

    @classmethod
    def get_for_speaker(cls, speaker_name: str) -> dict | None:
        defaults = cls.load_defaults()
        # Direct match or case-insensitive match
        if speaker_name in defaults:
            return defaults[speaker_name]
        for name, profile in defaults.items():
            if name.lower() == speaker_name.lower():
                return profile
        return None
