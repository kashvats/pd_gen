import pytest
from app.tts.registry import tts_registry
from app.tts.mock_provider import MockProvider

@pytest.fixture
def mock_engine(monkeypatch):
    """Mock tones exercise plumbing only; never used for naturalness validation."""
    provider = MockProvider()
    monkeypatch.setitem(tts_registry._providers, "mock", provider)
    return provider
