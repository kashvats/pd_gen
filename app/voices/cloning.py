"""Voice cloning workflow coordinator with sample preservation and consent logging."""

import shutil
import uuid
from pathlib import Path
from typing import List, Optional, Tuple

from app.models.voice import VoiceProfile, VoiceDelivery, ConsentRecord
from app.voices.library import VoiceLibrary
from app.voices.quality import analyze_reference_audio, AudioQualityReport
from app.tts.registry import tts_registry
from app.tts.base import CloneRequest, CloneResult


class VoiceCloningService:
    """Handles end-to-end voice cloning workflow."""

    def __init__(self, library: Optional[VoiceLibrary] = None):
        self.library = library or VoiceLibrary()

    def clone_voice(
        self,
        name: str,
        provider_id: str,
        reference_file_paths: List[str],
        consent_confirmed: bool,
        consent_notes: str = "",
        language: str = "en",
        description: str = "",
        gender: str = "unspecified",
        delivery: Optional[VoiceDelivery] = None,
    ) -> Tuple[bool, Optional[VoiceProfile], Optional[str]]:
        """Executes cloning, saves reference samples, logs consent, and creates VoiceProfile."""
        if not consent_confirmed:
            return False, None, "Voice cloning requires explicit permission confirmation."

        if not reference_file_paths:
            return False, None, "At least one reference audio recording is required."

        provider = tts_registry.get(provider_id)
        if not provider:
            return False, None, f"Unknown TTS provider '{provider_id}'."

        if not provider.capabilities.voice_cloning:
            return False, None, f"Provider '{provider.display_name}' does not support custom voice cloning."

        # Create unique profile ID and directories
        profile_id = f"clone_{uuid.uuid4().hex[:10]}"
        voice_folder = self.library.root_dir / profile_id
        ref_dest_dir = voice_folder / "references"
        ref_dest_dir.mkdir(parents=True, exist_ok=True)

        # Preserve original reference recordings in local directory
        saved_ref_paths: List[str] = []
        for idx, src_p in enumerate(reference_file_paths, start=1):
            src_path = Path(src_p)
            if src_path.exists():
                dest_file = ref_dest_dir / f"reference_{idx:02d}{src_path.suffix.lower()}"
                shutil.copy2(src_path, dest_file)
                saved_ref_paths.append(str(dest_file))

        if not saved_ref_paths:
            return False, None, "Could not access or copy the reference audio files."

        # Build CloneRequest
        clone_req = CloneRequest(
            name=name,
            audio_file_paths=saved_ref_paths,
            description=description,
            language=language,
            consent_statement="Confirmed speaker ownership or permission.",
        )

        # Dispatch to provider
        result: CloneResult = provider.clone_voice(clone_req)
        if not result.success:
            # Clean up empty folder on fatal error
            shutil.rmtree(voice_folder, ignore_errors=True)
            return False, None, result.error_message or "Cloning failed."

        # Create and save profile
        consent = ConsentRecord(
            confirmed=True,
            speaker_name=name,
            notes=consent_notes,
        )

        profile = VoiceProfile(
            id=profile_id,
            name=name,
            provider=provider_id,
            voice_id=result.voice_id,
            voice_type="instant_clone",
            language=language,
            gender=gender,
            description=description or f"Custom cloned voice on {provider.display_name}",
            delivery=delivery or VoiceDelivery(style="natural cloned conversational speaker"),
            reference_files=saved_ref_paths,
            consent=consent,
            settings={"cloned": True},
        )

        self.library.save_voice(profile)
        return True, profile, None
