"""Real, offline neural speech using explicitly installed Kokoro ONNX weights."""
import importlib.util
import io
import os
from pathlib import Path
import threading
import wave
import numpy as np
from app.config.settings import ROOT_DIR
from app.system.limits import get_system_limits
from app.tts.base import TTSProvider, EngineCapabilities, VoiceInfo, SynthesisResult, CloneResult

MODEL_DIR = ROOT_DIR / "models" / "kokoro"
VOICES = {
    "af_heart": "Heart • American female", "am_michael": "Michael • American male",
    "af_bella": "Bella • American female", "am_fenrir": "Fenrir • American male",
    "bf_emma": "Emma • British female", "bm_george": "George • British male",
    "af_nicole": "Nicole • American female", "am_puck": "Puck • American male",
}


class KokoroProvider(TTSProvider):
    _lock = threading.RLock()  # All instances share one inference slot.

    def __init__(self):
        self._engine = None
        self._loaded_signature = None

    provider_id = property(lambda self: "kokoro")
    display_name = property(lambda self: "Kokoro Neural • LOCAL / FREE • CPU")
    category = property(lambda self: "LOCAL_FREE")
    capabilities = property(lambda self: EngineCapabilities(
        local=True, free=True, cpu=True, cuda=False,
        languages=["en-US", "en-GB"], supported_models=["kokoro-v1.0-onnx"],
        style_instructions=False, emotion_tags=False,
    ))

    @staticmethod
    def paths():
        return (Path(os.environ.get("KOKORO_MODEL_PATH", str(MODEL_DIR / "kokoro-v1.0.onnx"))),
                Path(os.environ.get("KOKORO_VOICES_PATH", str(MODEL_DIR / "voices-v1.0.bin"))))

    def is_configured(self):
        return (importlib.util.find_spec("kokoro_onnx") is not None
                and all(p.is_file() and p.stat().st_size > 0 for p in self.paths()))

    def cache_identity(self):
        # File stat changes invalidate cached takes without hashing 300 MB on the GUI thread.
        return [(str(p.resolve()), p.stat().st_size, p.stat().st_mtime_ns)
                if p.is_file() else (str(p), "missing") for p in self.paths()]

    def list_voices(self):
        return [VoiceInfo(id=k, name=v, provider="kokoro", category="premade",
                          language="en-GB" if k.startswith("b") else "en-US")
                for k, v in VOICES.items()]

    def load(self, device="cpu"):
        with self._lock:
            signature = (self.cache_identity(), get_system_limits().cpu_thread_budget)
            if self._engine is not None and self._loaded_signature == signature:
                return
            if not self.is_configured():
                raise RuntimeError("Kokoro is not installed. Run: python -m pip install -r requirements.txt, "
                                   "then python scripts/install_kokoro.py --download. See START_HERE.md.")
            import onnxruntime as ort
            from kokoro_onnx import Kokoro
            import psutil
            if psutil.virtual_memory().available < 2 * 1024 ** 3:
                raise RuntimeError("Kokoro needs at least 2 GB available RAM. Close other apps and retry.")
            options = ort.SessionOptions()
            options.intra_op_num_threads = min(os.cpu_count() or 1, get_system_limits().cpu_thread_budget)
            options.inter_op_num_threads = 1
            options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
            model, voices = self.paths()
            self._engine = None
            session = ort.InferenceSession(str(model), sess_options=options, providers=["CPUExecutionProvider"])
            self._engine = Kokoro.from_session(session, str(voices))
            self._loaded_signature = signature

    def unload(self):
        with self._lock:
            self._engine = None
            self._loaded_signature = None

    def synthesize(self, request):
        if not request.text.strip():
            raise ValueError("Cannot synthesize empty dialogue.")
        voice = request.voice_id or "af_heart"
        if voice not in VOICES:
            raise ValueError(f"Unknown Kokoro voice: {voice}. Select a Kokoro voice for this speaker.")
        if not 0.7 <= request.speed <= 1.3:
            raise ValueError("Natural speech pace must be between 0.7 and 1.3.")
        with self._lock:
            self.load()
            # Keep the entire turn together. Kokoro handles its own phoneme limit.
            samples, rate = self._engine.create(request.text, voice=voice, speed=request.speed,
                                               lang="en-gb" if voice.startswith("b") else "en-us")
        samples = np.asarray(samples, dtype=np.float32).reshape(-1)
        if not len(samples) or not np.isfinite(samples).all() or np.max(np.abs(samples)) < 1e-5:
            raise RuntimeError("Kokoro returned empty, invalid, or silent audio; no take was saved.")
        pcm = (np.clip(samples, -1, 1) * 32767).astype("<i2")
        output = io.BytesIO()
        with wave.open(output, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(rate)
            wav.writeframes(pcm.tobytes())
        return SynthesisResult(output.getvalue(), "wav", rate, round(len(samples) * 1000 / rate),
                               {"engine": "kokoro", "voice": voice, "local": True, "free": True})

    def clone_voice(self, request):
        return CloneResult(False, error_message="Kokoro uses preset voices; it does not clone reference recordings.")
