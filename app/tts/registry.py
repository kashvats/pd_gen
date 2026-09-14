"""Speech Engine and TTS Provider Registry supporting free local and optional online engines."""

from typing import Dict, List, Optional
from app.tts.base import TTSProvider


class ProviderRegistry:
    """Central registry of all Speech Engines and TTS providers."""

    def __init__(self):
        self._providers: Dict[str, TTSProvider] = {}

    def register(self, provider: TTSProvider) -> None:
        self._providers[provider.provider_id.lower()] = provider

    def get(self, provider_id: str) -> Optional[TTSProvider]:
        if not provider_id:
            return None
        return self._providers.get(provider_id.lower())

    def list_providers(self) -> List[TTSProvider]:
        return list(self._providers.values())

    def list_local_free_providers(self) -> List[TTSProvider]:
        return [p for p in self._providers.values() if p.category == "LOCAL_FREE"]

    def list_configured_providers(self) -> List[TTSProvider]:
        return [p for p in self._providers.values() if p.is_configured()]


# Singleton registry instance
tts_registry = ProviderRegistry()


def register_default_providers():
    from app.tts.kokoro_provider import KokoroProvider
    from app.tts.edge_provider import EdgeTTSProvider
    from app.tts.local_lightweight import LightweightLocalEngine
    from app.tts.local_cloning import LocalCloningEngine
    from app.tts.mock_provider import MockProvider
    tts_registry.register(KokoroProvider())
    tts_registry.register(EdgeTTSProvider())
    tts_registry.register(LocalCloningEngine())
    # Mock is available only when explicitly registered by a test.


register_default_providers()
