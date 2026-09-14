"""Free Lightweight Local Speech Engine running 100% offline."""

import io
import math
import struct
import wave
from typing import List

from app.tts.base import (
    TTSProvider,
    EngineCapabilities,
    EngineCategory,
    SynthesisRequest,
    SynthesisResult,
    VoiceInfo,
    CloneRequest,
    CloneResult,
)


class LightweightLocalEngine(TTSProvider):
    """Fast, reliable, free local speech engine running completely offline on CPU."""

    def __init__(self):
        self._is_loaded = True
        self._voices = [
            VoiceInfo(
                id="local_host_natural",
                name="Local Host (Natural Male)",
                provider="local_lightweight",
                category="premade",
                gender="male",
                language="en",
                description="Warm, clear, natural local host voice (100% Offline)",
            ),
            VoiceInfo(
                id="local_cohost_expressive",
                name="Local Co-Host (Expressive Female)",
                provider="local_lightweight",
                category="premade",
                gender="female",
                language="en",
                description="Friendly, articulate, expressive local co-host (100% Offline)",
            ),
            VoiceInfo(
                id="local_guest_thoughtful",
                name="Local Guest (Articulate Neutral)",
                provider="local_lightweight",
                category="premade",
                gender="neutral",
                language="en",
                description="Engaging, natural conversational local guest (100% Offline)",
            ),
            VoiceInfo(
                id="local_narrator_deep",
                name="Local Narrator (Deep Resonance)",
                provider="local_lightweight",
                category="premade",
                gender="male",
                language="en",
                description="Calm, resonant, measured storytelling voice (100% Offline)",
            ),
        ]

    @property
    def provider_id(self) -> str:
        return "local_lightweight"

    @property
    def display_name(self) -> str:
        return "System Speech • basic quality / offline"

    @property
    def category(self) -> EngineCategory:
        return "LOCAL_FREE"

    @property
    def capabilities(self) -> EngineCapabilities:
        return EngineCapabilities(
            local=True,
            free=True,
            voice_cloning=False,
            built_in_voices=True,
            style_instructions=False,
            emotion_tags=False,
            speed_control=True,
            cpu=True,
            cuda=False,
            languages=["en"],
            supported_models=["lightweight-prosody-v1"],
        )

    def is_configured(self) -> bool:
        return True

    def load(self, device: str = "cpu") -> None:
        self._is_loaded = True

    def unload(self) -> None:
        pass

    def list_voices(self) -> List[VoiceInfo]:
        return list(self._voices)

    def synthesize(self, request: SynthesisRequest) -> SynthesisResult:
        """Synthesizes speech locally with genuine offline human speech."""
        import tempfile
        import os

        text = request.text.strip()
        if not text:
            text = "..."

        try:
            import pyttsx3
            engine = pyttsx3.init()
            installed_voices = engine.getProperty("voices") or []

            # Match voice by gender / name
            target_gender = "female" if ("female" in request.voice_id or "cohost" in request.voice_id) else "male"
            for v in installed_voices:
                v_name_lower = v.name.lower()
                if target_gender == "female" and ("zira" in v_name_lower or "female" in v_name_lower or "eva" in v_name_lower):
                    engine.setProperty("voice", v.id)
                    break
                elif target_gender == "male" and ("david" in v_name_lower or "male" in v_name_lower or "mark" in v_name_lower):
                    engine.setProperty("voice", v.id)
                    break

            # Adjust speech rate (normal is ~175-180 wpm)
            rate = int(175 * max(0.5, min(2.0, request.speed)))
            engine.setProperty("rate", rate)

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name

            engine.save_to_file(text, tmp_path)
            engine.runAndWait()

            with open(tmp_path, "rb") as f:
                audio_data = f.read()

            try:
                os.remove(tmp_path)
            except Exception:
                pass

            if len(audio_data) <= 44:
                raise RuntimeError("System speech produced no audio.")

            # Calculate duration from wav file or text length
            sample_rate = request.output_sample_rate or 22050
            try:
                with wave.open(io.BytesIO(audio_data), "rb") as wf:
                    frames = wf.getnframes()
                    rate = wf.getframerate()
                    sample_rate = rate
                    duration_ms = int((frames / float(rate)) * 1000)
            except Exception:
                words = text.split()
                duration_ms = int(((len(words) * 0.38) / max(0.2, request.speed)) * 1000)

            return SynthesisResult(
                audio_bytes=audio_data,
                audio_format="wav",
                sample_rate=sample_rate,
                duration_ms=duration_ms,
                provider_metadata={"engine": "local_lightweight", "local": True, "free": True},
            )

        except Exception as exc:
            raise RuntimeError(f"System speech failed: {exc}. Select Kokoro for neural speech.") from exc

    def clone_voice(self, request: CloneRequest) -> CloneResult:
        return CloneResult(
            success=False,
            error_message="Lightweight engine uses built-in voices. Use Local Cloning Engine for reference cloning.",
        )

