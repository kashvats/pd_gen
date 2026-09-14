"""TTS Provider abstraction layer and provider adapters."""

from app.tts.base import (
    TTSProvider,
    ProviderCapabilities,
    SynthesisRequest,
    SynthesisResult,
    VoiceInfo,
    CloneRequest,
    CloneResult,
)
from app.tts.registry import tts_registry

__all__ = [
    "TTSProvider",
    "ProviderCapabilities",
    "SynthesisRequest",
    "SynthesisResult",
    "VoiceInfo",
    "CloneRequest",
    "CloneResult",
    "tts_registry",
]
