"""Speech intelligence, prosody direction, natural pauses, and pronunciation."""

from app.speech.presets import QUALITY_PRESETS, QualityPreset
from app.speech.pronunciation import PronunciationEngine
from app.speech.pauses import PauseCalculator
from app.speech.context import DialogueContextWindow, build_context_windows
from app.speech.director import SpeechDirector

__all__ = [
    "QUALITY_PRESETS",
    "QualityPreset",
    "PronunciationEngine",
    "PauseCalculator",
    "DialogueContextWindow",
    "build_context_windows",
    "SpeechDirector",
]
