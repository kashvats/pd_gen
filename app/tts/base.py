"""Speech Engine and TTS provider abstractions conforming to FREE_OPERATION and ARCHITECTURE specs."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Literal

EngineCategory = Literal["LOCAL_FREE", "ONLINE_FREE_OPTIONAL", "DISABLED"]


@dataclass
class EngineCapabilities:
    """Represents features supported by a specific speech engine."""
    local: bool = True
    free: bool = True
    voice_cloning: bool = False
    instant_clone: bool = False
    built_in_voices: bool = True
    style_instructions: bool = False
    emotion_tags: bool = False
    emotion_control: bool = False
    speed_control: bool = True
    pitch_control: bool = False
    stability_control: bool = False
    similarity_control: bool = False
    latency_optimizations: bool = False
    cpu: bool = True
    cuda: bool = False
    languages: List[str] = field(default_factory=lambda: ["en"])
    supported_models: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.emotion_control:
            self.emotion_tags = True


# Alias for backwards compatibility
ProviderCapabilities = EngineCapabilities


@dataclass
class VoiceInfo:
    """Information about a voice returned from a provider/engine."""
    id: str
    name: str
    provider: str
    category: str = "general"  # 'premade', 'cloned', 'custom'
    gender: str = "unspecified"
    language: str = "en"
    preview_url: Optional[str] = None
    description: str = ""


@dataclass
class SynthesisRequest:
    """Standardized speech synthesis request."""
    text: str
    voice_id: str
    provider: str
    model: Optional[str] = None
    speed: float = 1.0
    instructions: Optional[str] = None
    reference_audio: List[str] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)
    studio_mode: bool = True
    output_sample_rate: int = 44100


@dataclass
class SynthesisResult:
    """Standardized speech synthesis output."""
    audio_bytes: bytes
    audio_format: str = "wav"  # 'wav', 'mp3', etc.
    sample_rate: int = 44100
    duration_ms: int = 0
    provider_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CloneRequest:
    """Request to create or register a cloned voice."""
    name: str
    audio_file_paths: List[str]
    description: str = ""
    language: str = "en"
    consent_statement: str = ""


@dataclass
class CloneResult:
    """Result of a voice cloning operation."""
    success: bool
    voice_id: str = ""
    name: str = ""
    provider: str = ""
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class TTSProvider(ABC):
    """Abstract interface for all speech engines and TTS adapters."""

    @property
    @abstractmethod
    def provider_id(self) -> str:
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        pass

    @property
    @abstractmethod
    def category(self) -> EngineCategory:
        """Categorization: LOCAL_FREE, ONLINE_FREE_OPTIONAL, or DISABLED."""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> EngineCapabilities:
        pass

    def load(self, device: str = "cpu") -> None:
        """Lazy load weights/runtimes onto specified device."""
        pass

    def unload(self) -> None:
        """Release memory/VRAM when switching engines."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Returns True if the engine is ready to synthesize."""
        pass

    @abstractmethod
    def list_voices(self) -> List[VoiceInfo]:
        """Returns available voices."""
        pass

    @abstractmethod
    def synthesize(self, request: SynthesisRequest) -> SynthesisResult:
        """Synthesizes dialogue text into audio bytes."""
        pass

    @abstractmethod
    def clone_voice(self, request: CloneRequest) -> CloneResult:
        """Creates or registers a reference voice clone."""
        pass


# SpeechEngine alias matching ARCHITECTURE.md
SpeechEngine = TTSProvider
