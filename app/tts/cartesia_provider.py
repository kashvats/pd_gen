"""Cartesia Sonic TTS and Voice Cloning adapter."""

from pathlib import Path
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


class CartesiaProvider(TTSProvider):
    """Cartesia Sonic ultra-low latency and expressive TTS provider."""

    BASE_URL = "https://api.cartesia.ai"
    API_VERSION = "2024-06-10"

    @property
    def provider_id(self) -> str:
        return "cartesia"

    @property
    def display_name(self) -> str:
        return "Cartesia Sonic (Online • Free)"

    @property
    def category(self) -> str:
        return "ONLINE_FREE_OPTIONAL"

    @property
    def capabilities(self) -> ProviderCapabilities:

        return ProviderCapabilities(
            voice_cloning=True,
            instant_clone=True,
            style_instructions=True,
            emotion_control=True,
            speed_control=True,
            supported_models=["sonic-english", "sonic-multilingual"],
        )

    def _get_api_key(self) -> str:
        return Settings.get_api_key("cartesia")

    def is_configured(self) -> bool:
        return bool(self._get_api_key())

    def _headers(self) -> dict:
        return {
            "X-API-Key": self._get_api_key(),
            "Cartesia-Version": self.API_VERSION,
            "Content-Type": "application/json",
        }

    def list_voices(self) -> List[VoiceInfo]:
        """Fetches voices from Cartesia API."""
        if not self.is_configured():
            return []

        try:
            resp = requests.get(
                f"{self.BASE_URL}/voices",
                headers=self._headers(),
                timeout=12,
            )
            resp.raise_for_status()
            data = resp.json()

            voices: List[VoiceInfo] = []
            for item in data:
                voices.append(
                    VoiceInfo(
                        id=item.get("id", ""),
                        name=item.get("name", "Unnamed Voice"),
                        provider="cartesia",
                        category="cloned" if item.get("is_owner") else "premade",
                        gender=item.get("gender", "unspecified"),
                        language=item.get("language", "en"),
                        description=item.get("description", ""),
                    )
                )
            return voices
        except Exception:
            return []

    def synthesize(self, request: SynthesisRequest) -> SynthesisResult:
        """Synthesizes dialogue segment via Cartesia API."""
        api_key = self._get_api_key()
        if not api_key:
            raise ValueError("Cartesia API key is not configured. Please add it in Settings or .env.")

        model_id = request.model or "sonic-english"

        # Construct Cartesia synthesis payload
        voice_controls: Dict[str, Any] = {}
        if request.speed != 1.0:
            voice_controls["speed"] = request.speed
        if request.instructions:
            voice_controls["emotion"] = [request.instructions]

        payload = {
            "model_id": model_id,
            "transcript": request.text,
            "voice": {
                "mode": "id",
                "id": request.voice_id,
            },
            "output_format": {
                "container": "wav",
                "encoding": "pcm_s16le",
                "sample_rate": 44100,
            },
        }

        if voice_controls:
            payload["voice"]["__experimental_controls"] = voice_controls

        url = f"{self.BASE_URL}/tts/bytes"
        resp = requests.post(
            url,
            headers=self._headers(),
            json=payload,
            timeout=30,
        )

        if not resp.ok:
            try:
                detail = resp.json().get("message", resp.text)
            except Exception:
                detail = resp.text
            raise RuntimeError(f"Cartesia TTS Error ({resp.status_code}): {detail}")

        audio_bytes = resp.content
        return SynthesisResult(
            audio_bytes=audio_bytes,
            audio_format="wav",
            sample_rate=44100,
            duration_ms=0,
            provider_metadata={"model": model_id, "provider": "cartesia"},
        )

    def clone_voice(self, request: CloneRequest) -> CloneResult:
        """Creates a voice clone on Cartesia from reference audio."""
        api_key = self._get_api_key()
        if not api_key:
            return CloneResult(
                success=False,
                error_message="Cartesia API key is missing.",
            )

        if not request.audio_file_paths:
            return CloneResult(
                success=False,
                error_message="No reference audio files provided.",
            )

        # Cartesia clone endpoint accepts multipart/form-data
        url = f"{self.BASE_URL}/voices/clone/clip"
        headers = {
            "X-API-Key": api_key,
            "Cartesia-Version": self.API_VERSION,
        }

        ref_path = Path(request.audio_file_paths[0])
        if not ref_path.exists():
            return CloneResult(
                success=False,
                error_message=f"Reference file {ref_path} does not exist.",
            )

        try:
            with open(ref_path, "rb") as f:
                files = {"clip": (ref_path.name, f, "audio/wav")}
                data = {
                    "name": request.name,
                    "description": request.description or "Studio Cloned Voice",
                    "language": request.language or "en",
                }
                resp = requests.post(url, headers=headers, data=data, files=files, timeout=60)

            if not resp.ok:
                return CloneResult(
                    success=False,
                    error_message=f"Cartesia cloning failed ({resp.status_code}): {resp.text}",
                )

            res_json = resp.json()
            return CloneResult(
                success=True,
                voice_id=res_json.get("id", ""),
                name=request.name,
                provider="cartesia",
                metadata=res_json,
            )
        except Exception as err:
            return CloneResult(
                success=False,
                error_message=f"Cartesia clone error: {str(err)}",
            )
