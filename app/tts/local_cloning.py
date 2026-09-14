"""Compatibility adapter for legacy profiles. Never represent generated tones as cloning."""
from app.tts.base import TTSProvider, EngineCapabilities, CloneResult


class LocalCloningEngine(TTSProvider):
    provider_id = property(lambda self: "local_cloning")
    display_name = property(lambda self: "Legacy cloning unavailable • choose a neural voice")
    category = property(lambda self: "DISABLED")
    capabilities = property(lambda self: EngineCapabilities(
        built_in_voices=False, voice_cloning=False, speed_control=False))

    def is_configured(self):
        return False

    def list_voices(self):
        return []

    def synthesize(self, request):
        raise RuntimeError("The supplied cloning engine was a tone generator, not a speech model. "
                           "Your reference files are preserved. Assign a Kokoro or Edge neural voice.")

    def clone_voice(self, request):
        return CloneResult(False, error_message="No real cloning model is installed. "
                           "Reference profiles are preserved, but new cloning is unavailable.")
