"""Never confuse a tone/silence placeholder with real speech."""
import sys
import types
import pytest
from app.tts.local_lightweight import LightweightLocalEngine
from app.tts.local_cloning import LocalCloningEngine
from app.tts.base import SynthesisRequest, CloneRequest
from app.tts.registry import tts_registry


def test_system_failure_is_not_silent_audio(monkeypatch):
    def fail():
        raise RuntimeError("driver missing")
    monkeypatch.setitem(sys.modules, "pyttsx3", types.SimpleNamespace(init=fail))
    with pytest.raises(RuntimeError, match="driver missing"):
        LightweightLocalEngine().synthesize(SynthesisRequest("Actual words", "default", "local_lightweight"))


def test_fake_cloning_disabled():
    engine = LocalCloningEngine()
    assert not engine.is_configured()
    assert not engine.capabilities.voice_cloning
    assert not engine.clone_voice(CloneRequest("Reference", ["sample.wav"])).success
    with pytest.raises(RuntimeError, match="tone generator"):
        engine.synthesize(SynthesisRequest("Actual words", "old_clone", "local_cloning"))


def test_production_registry_has_no_mock_or_paid_engine():
    assert tts_registry.get("mock") is None
    for name in ("openai", "elevenlabs", "cartesia"):
        assert tts_registry.get(name) is None
