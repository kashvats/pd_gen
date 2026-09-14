"""Quality presets defining natural delivery characteristics."""

from dataclasses import dataclass
from typing import Dict
from app.models.voice import VoiceDelivery


@dataclass
class QualityPreset:
    name: str
    description: str
    delivery: VoiceDelivery


QUALITY_PRESETS: Dict[str, QualityPreset] = {
    "Natural Conversation": QualityPreset(
        name="Natural Conversation",
        description="Relaxed, natural dialogue with organic conversational prosody and micro-pauses.",
        delivery=VoiceDelivery(
            pace=1.0,
            energy=0.65,
            expressiveness=0.72,
            warmth=0.68,
            style="natural conversational human dialogue, expressive and nuanced",
        ),
    ),
    "Podcast": QualityPreset(
        name="Podcast",
        description="Warm, engaging, studio-produced podcast host / guest delivery.",
        delivery=VoiceDelivery(
            pace=1.02,
            energy=0.72,
            expressiveness=0.75,
            warmth=0.70,
            style="engaging studio podcast host, crisp articulation and friendly presence",
        ),
    ),
    "Narration": QualityPreset(
        name="Narration",
        description="Evenly paced, clear, controlled storytelling or instructional narration.",
        delivery=VoiceDelivery(
            pace=0.96,
            energy=0.55,
            expressiveness=0.52,
            warmth=0.58,
            style="calm, measured narration with clear articulation and natural cadence",
        ),
    ),
    "Energetic": QualityPreset(
        name="Energetic",
        description="Upbeat, dynamic, high-engagement delivery suitable for excitement or quick pacing.",
        delivery=VoiceDelivery(
            pace=1.08,
            energy=0.85,
            expressiveness=0.88,
            warmth=0.65,
            style="enthusiastic, energetic, lively, and dynamic conversational speech",
        ),
    ),
    "Calm": QualityPreset(
        name="Calm",
        description="Soft, gentle, contemplative delivery with relaxed pacing.",
        delivery=VoiceDelivery(
            pace=0.92,
            energy=0.45,
            expressiveness=0.48,
            warmth=0.78,
            style="soothing, gentle, relaxed conversational delivery with gentle tones",
        ),
    ),
    "Teaching": QualityPreset(
        name="Teaching", description="Slightly slower explanatory speech; preserves the supplied words.",
        delivery=VoiceDelivery(pace=0.95, style="clear teaching delivery"),
    ),
    "Custom": QualityPreset(
        name="Custom",
        description="User-defined custom delivery parameters.",
        delivery=VoiceDelivery(
            pace=1.0,
            energy=0.65,
            expressiveness=0.7,
            warmth=0.65,
            style="custom delivery",
        ),
    ),
}

