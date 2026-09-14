"""Pronunciation dictionary engine with global, project, and speaker-level overrides."""

import json
import re
from pathlib import Path
from typing import Dict, Optional
from app.config.settings import GLOBAL_PRONUNCIATION_FILE


class PronunciationEngine:
    """Manages phonetic spelling substitutions across global, project, and speaker layers."""

    DEFAULT_GLOBAL_ENTRIES = {
        "OpenAI": "Open A.I.",
        "SQL": "sequel",
        "API": "A.P.I.",
        "APIs": "A.P.I.s",
        "TTS": "T.T.S.",
        "GPT": "G.P.T.",
        "LLM": "L.L.M.",
        "LLMs": "L.L.M.s",
        "UI": "U.I.",
        "GUI": "gooey",
    }

    @classmethod
    def load_global_dict(cls) -> Dict[str, str]:
        if GLOBAL_PRONUNCIATION_FILE.exists():
            try:
                with open(GLOBAL_PRONUNCIATION_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return dict(cls.DEFAULT_GLOBAL_ENTRIES)

    @classmethod
    def save_global_dict(cls, data: Dict[str, str]) -> None:
        with open(GLOBAL_PRONUNCIATION_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def apply_substitutions(
        cls,
        text: str,
        project_dict: Optional[Dict[str, str]] = None,
        speaker_dict: Optional[Dict[str, str]] = None,
    ) -> str:
        """Applies pronunciation dictionary with precedence: Speaker > Project > Global."""
        if not text:
            return ""

        merged: Dict[str, str] = cls.load_global_dict()
        if project_dict:
            merged.update(project_dict)
        if speaker_dict:
            merged.update(speaker_dict)

        result = text
        # Sort by key length descending so longer phrases match before substrings
        sorted_keys = sorted(merged.keys(), key=len, reverse=True)
        for original in sorted_keys:
            replacement = merged[original]
            if not original or not replacement or original == replacement:
                continue

            # Case-insensitive word boundary replacement
            pattern = re.compile(rf'\b{re.escape(original)}\b', re.IGNORECASE)
            result = pattern.sub(replacement, result)

        return result
