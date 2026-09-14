"""Free Edge Neural Speech Engine providing ultra-natural voices at $0 cost."""

import asyncio
import io
import tempfile
import os
from pathlib import Path
from typing import List, Optional

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


class EdgeTTSProvider(TTSProvider):
    """Studio-grade free neural TTS engine powered by edge-tts (100% free, $0 cost)."""

    def __init__(self):
        self._voices = [
            VoiceInfo(
                id="en-US-GuyNeural",
                name="Guy (Natural American Male • Host)",
                provider="edge_tts",
                category="premade",
                gender="male",
                language="en-US",
                description="Ultra-natural, warm, conversational podcast host",
            ),
            VoiceInfo(
                id="en-US-JennyNeural",
                name="Jenny (Expressive American Female • Co-Host)",
                provider="edge_tts",
                category="premade",
                gender="female",
                language="en-US",
                description="Lively, clear, expressive conversational co-host",
            ),
            VoiceInfo(
                id="en-US-ChristopherNeural",
                name="Christopher (Deep American Male • Narrator)",
                provider="edge_tts",
                category="premade",
                gender="male",
                language="en-US",
                description="Deep, authoritative, measured narration voice",
            ),
            VoiceInfo(
                id="en-US-AriaNeural",
                name="Aria (Articulate American Female • Guest)",
                provider="edge_tts",
                category="premade",
                gender="female",
                language="en-US",
                description="Confident, articulate, intelligent guest voice",
            ),
            VoiceInfo(
                id="en-US-EricNeural",
                name="Eric (Casual American Male • Guest)",
                provider="edge_tts",
                category="premade",
                gender="male",
                language="en-US",
                description="Relaxed, friendly, modern conversational speaker",
            ),
            VoiceInfo(
                id="en-GB-SoniaNeural",
                name="Sonia (British Female • Co-Host)",
                provider="edge_tts",
                category="premade",
                gender="female",
                language="en-GB",
                description="Polished, engaging British English speaker",
            ),
            VoiceInfo(
                id="en-GB-RyanNeural",
                name="Ryan (British Male • Host)",
                provider="edge_tts",
                category="premade",
                gender="male",
                language="en-GB",
                description="Distinguished, clear British English presenter",
            ),
            VoiceInfo(
                id="en-US-SteffanNeural",
                name="Steffan (American Male)",
                provider="edge_tts",
                category="premade",
                gender="neutral",
                language="en-US",
                description="American English neural voice",
            ),
        ]

    @property
    def provider_id(self) -> str:
        return "edge_tts"

    @property
    def display_name(self) -> str:
        return "Edge Neural Voices (Free • High Naturalness)"

    @property
    def category(self) -> EngineCategory:
        return "ONLINE_FREE_OPTIONAL"

    @property
    def capabilities(self) -> EngineCapabilities:
        return EngineCapabilities(
            local=False,
            free=True,
            voice_cloning=False,
            built_in_voices=True,
            style_instructions=False,
            emotion_tags=False,
            speed_control=True,
            cpu=True,
            cuda=False,
            languages=["en-US", "en-GB"],
            supported_models=["edge-neural-v1"],
        )

    def is_configured(self) -> bool:
        return True

    def list_voices(self) -> List[VoiceInfo]:
        return list(self._voices)

    def synthesize(self, request: SynthesisRequest) -> SynthesisResult:
        """Synthesizes speech with neural quality using edge-tts."""
        import edge_tts

        voice = request.voice_id
        if not voice or voice in ("default", "local_host_natural", "mock_host_voice"):
            voice = "en-US-GuyNeural"
        elif voice in ("local_cohost_expressive", "mock_cohost_voice"):
            voice = "en-US-JennyNeural"
        elif voice in ("local_guest_thoughtful", "mock_guest_voice"):
            voice = "en-US-AriaNeural"
        elif voice in ("local_narrator_deep", "mock_narrator_voice"):
            voice = "en-US-ChristopherNeural"
        elif voice in ("ai_robot_voice", "robot_voice"):
            voice = "en-US-SteffanNeural"

        if not request.settings.get("allow_online"):
            raise RuntimeError("Edge sends script text to Microsoft online. Enable online permission first.")
        # Edge supports rate/pitch/volume, not acting instructions. Preserve voice identity.
        speed_pct = round((max(0.7, min(1.3, request.speed)) - 1.0) * 100)
        pitch_val = 0
        volume_val = 0

        rate_str = f"{'+' if speed_pct >= 0 else ''}{speed_pct}%"
        pitch_str = f"{'+' if pitch_val >= 0 else ''}{pitch_val}Hz"
        volume_str = f"{'+' if volume_val >= 0 else ''}{volume_val}%"

        from app.parser.text_cleaner import clean_text_for_speech
        text = clean_text_for_speech(request.text.strip())
        if not text:
            raise ValueError("Cannot synthesize empty dialogue.")


        async def _run_synth() -> bytes:
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice,
                rate=rate_str,
                pitch=pitch_str,
                volume=volume_str,
            )
            audio_buffer = bytearray()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_buffer.extend(chunk["data"])
            return bytes(audio_buffer)


        try:
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                audio_data = asyncio.run(_run_synth())
            else:
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    audio_data = pool.submit(asyncio.run, _run_synth()).result()

            if not audio_data:
                raise RuntimeError("Edge returned no speech audio.")

            words = text.split()
            word_count = max(1, len(words))
            duration_ms = int(((word_count * 0.38) / max(0.2, request.speed)) * 1000)

            return SynthesisResult(
                audio_bytes=audio_data,
                audio_format="mp3",
                sample_rate=24000,
                duration_ms=duration_ms,
                provider_metadata={"provider": "edge_tts", "voice": voice, "free": True},
            )
        except Exception as exc:
            raise RuntimeError(f"Edge speech failed: {exc}. Retry or select a local Kokoro voice; "
                               "no substitute voice or silence was generated.") from exc

    def clone_voice(self, request: CloneRequest) -> CloneResult:
        return CloneResult(
            success=False,
            error_message="Edge Neural engine uses premade high-naturalness voices.",
        )
