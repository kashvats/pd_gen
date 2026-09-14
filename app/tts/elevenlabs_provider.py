"""ElevenLabs TTS and Instant Voice Cloning adapter."""

import os
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


class ElevenLabsProvider(TTSProvider):
    """ElevenLabs TTS and Voice Cloning provider."""

    BASE_URL = "https://api.elevenlabs.io/v1"

    @property
    def provider_id(self) -> str:
        return "elevenlabs"

    @property
    def display_name(self) -> str:
        return "ElevenLabs (Online • Free Tier)"

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
            stability_control=True,
            similarity_control=True,
            supported_models=[
                "eleven_multilingual_v2",
                "eleven_turbo_v2_5",
                "eleven_flash_v2_5",
            ],
        )

    def _get_api_key(self) -> str:
        return Settings.get_api_key("elevenlabs")

    def is_configured(self) -> bool:
        return bool(self._get_api_key())

    def _headers(self) -> dict:
        return {
            "xi-api-key": self._get_api_key(),
            "Content-Type": "application/json",
        }

    def list_voices(self) -> List[VoiceInfo]:
        """Fetches available voices from ElevenLabs API."""
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
            for item in data.get("voices", []):
                cat = item.get("category", "premade")
                labels = item.get("labels") or {}
                voices.append(
                    VoiceInfo(
                        id=item["voice_id"],
                        name=item["name"],
                        provider="elevenlabs",
                        category=cat,
                        gender=labels.get("gender", "unspecified"),
                        language=labels.get("language", "en"),
                        preview_url=item.get("preview_url"),
                        description=item.get("description") or labels.get("description", ""),
                    )
                )
            return voices
        except Exception as err:
            return []

    def synthesize(self, request: SynthesisRequest) -> SynthesisResult:
        """Synthesizes dialogue segment via ElevenLabs API."""
        api_key = self._get_api_key()
        if not api_key:
            raise ValueError("ElevenLabs API key is not configured. Please add it in Settings or .env.")

        # In Studio Quality mode, prefer eleven_multilingual_v2 for rich prosody
        model_id = request.model or (
            "eleven_multilingual_v2" if request.studio_mode else "eleven_turbo_v2_5"
        )

        stability = request.settings.get("stability", 0.50)
        similarity = request.settings.get("similarity_boost", 0.75)
        style = request.settings.get("style", 0.40)
        use_speaker_boost = request.settings.get("use_speaker_boost", True)

        payload: Dict[str, Any] = {
            "text": request.text,
            "model_id": model_id,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity,
                "style": style,
                "use_speaker_boost": use_speaker_boost,
            },
        }

        # Query parameter for output format: 44.1kHz 128kbps / 192kbps
        format_param = "mp3_44100_128" if not request.studio_mode else "mp3_44100_192"
        url = f"{self.BASE_URL}/text-to-speech/{request.voice_id}?output_format={format_param}"

        resp = requests.post(
            url,
            headers=self._headers(),
            json=payload,
            timeout=30,
        )

        if not resp.ok:
            try:
                err_json = resp.json()
                detail = err_json.get("detail", {}).get("message", resp.text)
            except Exception:
                detail = resp.text
            raise RuntimeError(f"ElevenLabs TTS Error ({resp.status_code}): {detail}")

        audio_bytes = resp.content
        return SynthesisResult(
            audio_bytes=audio_bytes,
            audio_format="mp3",
            sample_rate=44100,
            duration_ms=0,  # Will be inspected via ffprobe/audio header
            provider_metadata={"model": model_id, "provider": "elevenlabs"},
        )

    def clone_voice(self, request: CloneRequest) -> CloneResult:
        """Uploads reference recordings to create an instant voice clone."""
        api_key = self._get_api_key()
        if not api_key:
            return CloneResult(
                success=False,
                error_message="ElevenLabs API key is missing. Configure it in Settings or .env.",
            )

        if not request.audio_file_paths:
            return CloneResult(
                success=False,
                error_message="No reference audio files provided for voice cloning.",
            )

        url = f"{self.BASE_URL}/voices/add"
        headers = {"xi-api-key": api_key}
        data = {
            "name": request.name,
            "description": request.description or "Cloned via Natural Audio Studio",
            "labels": '{"cloned": "true", "studio": "true"}',
        }

        files = []
        file_handles = []
        try:
            for p in request.audio_file_paths:
                path = Path(p)
                if path.exists():
                    f = open(path, "rb")
                    file_handles.append(f)
                    files.append(("files", (path.name, f, "audio/wav")))

            if not files:
                return CloneResult(
                    success=False,
                    error_message="Valid reference audio files were not found on disk.",
                )

            resp = requests.post(url, headers=headers, data=data, files=files, timeout=60)
            if not resp.ok:
                try:
                    err_msg = resp.json().get("detail", {}).get("message", resp.text)
                except Exception:
                    err_msg = resp.text
                return CloneResult(
                    success=False,
                    error_message=f"ElevenLabs Cloning Failed ({resp.status_code}): {err_msg}",
                )

            res_data = resp.json()
            voice_id = res_data.get("voice_id", "")
            return CloneResult(
                success=True,
                voice_id=voice_id,
                name=request.name,
                provider="elevenlabs",
                metadata={"response": res_data},
            )
        except Exception as err:
            return CloneResult(
                success=False,
                error_message=f"Voice clone error: {str(err)}",
            )
        finally:
            for f in file_handles:
                try:
                    f.close()
                except Exception:
                    pass
