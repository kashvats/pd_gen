"""Tests for audio caching, hash determinism, alternate takes, and locking."""

import pytest
import tempfile
from pathlib import Path
from app.audio.cache import calculate_audio_hash, AudioCache
from app.audio.takes import TakeManager
from app.models.generation import SegmentGenerationInfo, Take


def test_calculate_audio_hash_determinism():
    h1 = calculate_audio_hash(
        text="Hello world.",
        provider="elevenlabs",
        voice_id="voice_123",
        speed=1.0,
        delivery_direction="Warm podcast host",
    )
    h2 = calculate_audio_hash(
        text="Hello world.",
        provider="elevenlabs",
        voice_id="voice_123",
        speed=1.0,
        delivery_direction="Warm podcast host",
    )
    h3 = calculate_audio_hash(
        text="Hello world.",
        provider="elevenlabs",
        voice_id="voice_123",
        speed=1.05,  # altered speed
        delivery_direction="Warm podcast host",
    )
    assert h1 == h2
    assert h1 != h3


def test_audio_cache_store_and_get():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = AudioCache(cache_dir=Path(tmpdir))
        test_bytes = b"RIFF....WAVEfmt...."
        test_hash = "abc123hash"

        dest = cache.store(test_hash, test_bytes, "wav")
        assert dest.exists()

        retrieved = cache.get(test_hash)
        assert retrieved is not None
        assert retrieved.read_bytes() == test_bytes


def test_take_manager_and_locking():
    info = SegmentGenerationInfo(segment_id="seg_1", speaker="Host", text="Hello.")

    # Add Take 1
    t1 = TakeManager.add_take(info, "/path/take1.wav", "hash_1", duration_ms=1200)
    assert len(info.takes) == 1
    assert info.active_take_index == 0
    assert not info.is_locked

    # Add Take 2
    t2 = TakeManager.add_take(info, "/path/take2.wav", "hash_2", duration_ms=1300)
    assert len(info.takes) == 2
    assert info.active_take_index == 1

    # Switch back to Take 1
    TakeManager.set_active_take(info, 0)
    assert info.active_take_index == 0
    assert info.active_take.audio_path == "/path/take1.wav"

    # Lock active take
    is_locked = TakeManager.toggle_lock_active_take(info)
    assert is_locked is True
    assert info.is_locked is True
    assert info.status == "locked"
