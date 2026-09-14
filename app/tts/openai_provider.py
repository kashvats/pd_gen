"""OpenAI TTS provider adapter."""

from typing import List, Dict, Any, Optional
import requests

from app.config.settings import Settings
from app.tts.base import (
    TTSProvider,
    ProviderCapabilities,
    SynthesisRequest,
    SynthesisResult,
    VoiceInfo,
    CloneRequest,
    CloneResult,
)


class OpenAIProvider(TTSProvider):
    """OpenAI TTS provider adapter."""

    BASE_URL = "https://api.openai.com/v1"

    PREMADE_VOICES = [
        ("alloy", "Alloy", "neutral", "Versatile, balanced, and clear conversational voice"),
        ("echo", "Echo", "male", "Warm, grounded, and engaging male voice"),
        ("fable", "Fable", "neutral", "British-accented, storytelling, articulate voice"),
        ("onyx", "Onyx", "male", "Deep, authoritative, resonant podcast host voice"),
        ("nova", "Nova", "female", "Energetic, friendly, expressive conversational voice"),
        ("shimmer", "Shimmer", "female", "Clear, bright, upbeat female voice"),
    ]

    @property
    def provider_id(self) -> str:
        return "openai"

    @property
    def display_name(self) -> str:
        return "OpenAI (Online • Free/Key)"

    @property
    def category(self) -> str:
        return "ONLINE_FREE_OPTIONAL"

    @property
    def capabilities(self) -> ProviderCapabilities:

        return ProviderCapabilities(
            voice_cloning=False,
            instant_clone=False,
            style_instructions=True,
            emotion_control=False,
            speed_control=True,
            supported_models=["tts-1-hd", "tts-1"],
        )

    def _get_api_key(self) -> str:
        return Settings.get_api_key("openai")

    def is_configured(self) -> bool:
        return bool(self._get_api_key())

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._get_api_key()}",
            "Content-Type": "application/json",
        }

    def list_voices(self) -> List[VoiceInfo]:
        voices = []
        for vid, vname, gender, desc in self.PREMADE_VOICES:
            voices.append(
                VoiceInfo(
                    id=vid,
                    name=vname,
                    provider="openai",
                    category="premade",
                    gender=gender,
                    language="en",
                    description=desc,
                )
            )
        return voices

    def synthesize(self, request: SynthesisRequest) -> SynthesisResult:
        """Synthesizes speech using OpenAI TTS endpoint."""
        api_key = self._get_api_key()
        if not api_key:
            raise ValueError("OpenAI API key is not configured. Please add it in Settings or .env.")

        # In Studio mode, default to tts-1-hd
        model_id = request.model or ("tts-1-hd" if request.studio_mode else "tts-1")

        payload: Dict[str, Any] = {
            "model": model_id,
            "input": request.text,
            "voice": request.voice_id.lower(),
            "response_format": "mp3",
            "speed": max(0.25, min(4.0, request.speed)),
        }

        url = f"{self.BASE_URL}/audio/speech"
        resp = requests.post(
            url,
            headers=self._headers(),
            json=payload,
            timeout=30,
        )

        if not resp.ok:
            try:
                err_msg = resp.json().get("error", {}).get("message", resp.text)
            except Exception:
                err_msg = resp.text
            raise RuntimeError(f"OpenAI TTS Error ({resp.status_code}): {err_msg}")

        audio_bytes = resp.content
        return SynthesisResult(
            audio_bytes=audio_bytes,
            audio_format="mp3",
            sample_rate=44100,
            duration_ms=0,
            provider_metadata={"model": model_id, "provider": "openai"},
        )

    def clone_voice(self, request: CloneRequest) -> CloneResult:
        return CloneResult(
            success=False,
            error_message="OpenAI does not currently support custom user voice cloning via public API.",
        )
