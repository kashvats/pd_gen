"""Built-in Mock/Simulated TTS provider for offline development and testing."""

import io
import math
import struct
import wave
import time
from typing import List
from app.tts.base import (
    TTSProvider,
    ProviderCapabilities,
    SynthesisRequest,
    SynthesisResult,
    VoiceInfo,
    CloneRequest,
    CloneResult,
)


class MockProvider(TTSProvider):
    """Generates valid WAV audio offline for testing and mock mode."""

    def __init__(self):
        self._voices = [
            VoiceInfo(
                id="mock_host_voice",
                name="Studio Host (Mock)",
                provider="mock",
                category="premade",
                gender="male",
                language="en",
                description="Simulated clear podcast host voice",
            ),
            VoiceInfo(
                id="mock_cohost_voice",
                name="Studio Co-Host (Mock)",
                provider="mock",
                category="premade",
                gender="female",
                language="en",
                description="Simulated friendly co-host voice",
            ),
            VoiceInfo(
                id="mock_guest_voice",
                name="Studio Guest (Mock)",
                provider="mock",
                category="premade",
                gender="neutral",
                language="en",
                description="Simulated articulate guest voice",
            ),
            VoiceInfo(
                id="mock_narrator_voice",
                name="Studio Narrator (Mock)",
                provider="mock",
                category="premade",
                gender="male",
                language="en",
                description="Simulated calm narrator voice",
            ),
        ]

    @property
    def provider_id(self) -> str:
        return "mock"

    @property
    def display_name(self) -> str:
        return "Offline Studio Simulator (Local • Free)"

    @property
    def category(self) -> str:
        return "LOCAL_FREE"

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
            supported_models=["mock-natural-v1", "mock-studio-v2"],
        )

    def is_configured(self) -> bool:
        return True

    def list_voices(self) -> List[VoiceInfo]:
        return list(self._voices)

    def synthesize(self, request: SynthesisRequest) -> SynthesisResult:
        """Synthesizes valid PCM WAV audio with speech-like natural cadence."""
        words = request.text.split()
        word_count = max(1, len(words))
        # Approximate reading speed: ~150 words per minute -> 400ms per word
        base_duration_sec = (word_count * 0.38) / max(0.2, request.speed)
        base_duration_sec = max(0.6, min(base_duration_sec, 60.0))

        sample_rate = request.output_sample_rate or 44100
        total_samples = int(base_duration_sec * sample_rate)

        # Base fundamental pitch according to voice
        base_freq = 160.0
        if "cohost" in request.voice_id or "female" in request.voice_id:
            base_freq = 220.0
        elif "host" in request.voice_id:
            base_freq = 135.0
        elif "narrator" in request.voice_id:
            base_freq = 120.0

        # Adjust pitch if delivery indicates question or excitement
        if request.instructions and "surprise" in request.instructions.lower():
            base_freq *= 1.15

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav_out:
            wav_out.setnchannels(1)  # Mono
            wav_out.setsampwidth(2)  # 16-bit
            wav_out.setframerate(sample_rate)

            # Generate speech-like waveform with subtle formant harmonics and envelope
            frames = bytearray()
            for i in range(total_samples):
                t = i / sample_rate
                # Envelope: attack (20ms) and decay (30ms)
                env = 1.0
                attack_samples = int(0.02 * sample_rate)
                decay_samples = int(0.03 * sample_rate)
                if i < attack_samples:
                    env = i / attack_samples
                elif i > total_samples - decay_samples:
                    env = max(0.0, (total_samples - i) / decay_samples)

                # Formant synthesis / slight pitch modulation
                pitch_mod = 1.0 + 0.05 * math.sin(2 * math.pi * 3.5 * t)
                if request.text.strip().endswith("?") and i > total_samples * 0.7:
                    # Upward pitch inflection for question
                    pitch_mod += 0.2 * ((i - total_samples * 0.7) / (total_samples * 0.3))

                freq = base_freq * pitch_mod
                # Fundamental + 2nd & 3rd harmonic
                sample_val = (
                    0.6 * math.sin(2 * math.pi * freq * t) +
                    0.25 * math.sin(2 * math.pi * (freq * 2) * t) +
                    0.15 * math.sin(2 * math.pi * (freq * 3) * t)
                )

                # Amplitude modulation for syllabic cadence (~4.5 syllables/sec)
                syllable_cadence = 0.5 + 0.5 * math.cos(2 * math.pi * 4.5 * t)
                val = int(sample_val * syllable_cadence * env * 12000)
                val = max(-32768, min(32767, val))
                frames.extend(struct.pack("<h", val))

            wav_out.writeframes(frames)

        duration_ms = int(base_duration_sec * 1000)
        return SynthesisResult(
            audio_bytes=buf.getvalue(),
            audio_format="wav",
            sample_rate=sample_rate,
            duration_ms=duration_ms,
            provider_metadata={"mock": True, "mode": "studio" if request.studio_mode else "standard"},
        )

    def clone_voice(self, request: CloneRequest) -> CloneResult:
        new_id = f"mock_clone_{int(time.time())}"
        info = VoiceInfo(
            id=new_id,
            name=request.name,
            provider="mock",
            category="cloned",
            gender="custom",
            language=request.language,
            description=request.description or "Locally created mock clone",
        )
        self._voices.append(info)
        return CloneResult(
            success=True,
            voice_id=new_id,
            name=request.name,
            provider="mock",
            metadata={"references_count": len(request.audio_file_paths)},
        )
