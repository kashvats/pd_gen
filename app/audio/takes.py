"""Alternate take management and take locking for dialogue segments."""

from typing import List, Optional
from app.models.generation import Take, SegmentGenerationInfo


class TakeManager:
    """Provides operations on dialogue segment takes."""

    @staticmethod
    def add_take(
        info: SegmentGenerationInfo,
        audio_path: str,
        generation_hash: str,
        duration_ms: int = 0,
        provider: str = "",
        voice_id: str = "",
        delivery_direction: str = "",
        auto_activate: bool = True,
    ) -> Take:
        """Appends a newly synthesized take to the segment."""
        take_num = len(info.takes) + 1
        new_take = Take(
            take_number=take_num,
            audio_path=audio_path,
            generation_hash=generation_hash,
            duration_ms=duration_ms,
            provider=provider,
            voice_id=voice_id,
            delivery_direction=delivery_direction,
            is_locked=False,
        )
        info.takes.append(new_take)
        if auto_activate or len(info.takes) == 1:
            info.active_take_index = len(info.takes) - 1
            info.status = "complete"
            info.generation_hash = generation_hash
        return new_take

    @staticmethod
    def set_active_take(info: SegmentGenerationInfo, take_index: int) -> bool:
        """Switches the active take for playback and assembly."""
        if 0 <= take_index < len(info.takes):
            info.active_take_index = take_index
            active = info.takes[take_index]
            info.generation_hash = active.generation_hash
            info.status = "locked" if active.is_locked else "complete"
            return True
        return False

    @staticmethod
    def toggle_lock_active_take(info: SegmentGenerationInfo) -> bool:
        """Toggles the lock state of the currently active take."""
        active = info.active_take
        if active:
            active.is_locked = not active.is_locked
            info.status = "locked" if active.is_locked else "complete"
            return active.is_locked
        return False
