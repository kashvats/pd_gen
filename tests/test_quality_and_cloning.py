"""Tests for voice sample quality diagnostics, consent records, and cloning workflow."""

import pytest
import tempfile
import wave
import struct
import math
from pathlib import Path

from app.voices.quality import analyze_reference_audio, AudioQualityReport
from app.voices.library import VoiceLibrary
from app.voices.cloning import VoiceCloningService
from app.models.voice import VoiceProfile, VoiceDelivery, ConsentRecord


def _create_synthetic_wav(file_path: Path, duration_sec: float = 5.0, amplitude: float = 0.5) -> Path:
    sample_rate = 44100
    total_samples = int(duration_sec * sample_rate)
    with wave.open(str(file_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        frames = bytearray()
        for i in range(total_samples):
            t = i / sample_rate
            val = int(amplitude * 32767.0 * math.sin(2 * math.pi * 220.0 * t))
            frames.extend(struct.pack("<h", val))
        wf.writeframes(frames)
    return file_path


def test_audio_quality_diagnostics():
    with tempfile.TemporaryDirectory() as tmpdir:
        wav_file = Path(tmpdir) / "sample.wav"
        _create_synthetic_wav(wav_file, duration_sec=12.0, amplitude=0.6)

        report = analyze_reference_audio(str(wav_file))
        assert report.duration_sec >= 11.0
        assert not report.is_clipping
        assert report.status in ["Excellent", "Good"]
        assert report.score >= 70


def test_voice_cloning_service(mock_engine):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        library = VoiceLibrary(root_dir=tmp_path / "voices")
        cloning_service = VoiceCloningService(library)

        ref_wav = tmp_path / "ref_speech.wav"
        _create_synthetic_wav(ref_wav, duration_sec=10.0, amplitude=0.5)

        success, profile, err = cloning_service.clone_voice(
            name="Alex Clone",
            provider_id="mock",
            reference_file_paths=[str(ref_wav)],
            consent_confirmed=True,
            consent_notes="Self recording authorized.",
        )
        assert success is True
        assert profile is not None
        assert profile.name == "Alex Clone"
        assert profile.voice_type == "instant_clone"
        assert len(profile.reference_files) == 1
        # Verify reference file is preserved in voice's folder
        assert Path(profile.reference_files[0]).exists()

        # Verify saved in library
        retrieved = library.get_voice(profile.id)
        assert retrieved is not None
        assert retrieved.name == "Alex Clone"
