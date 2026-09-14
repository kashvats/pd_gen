"""Speech generation engine orchestrating context analysis, caching, TTS calls, takes, and planning."""

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Dict, List
import uuid

from app.models.project import Project, SpeakerProfile
from app.models.ast import DialogueNode
from app.models.generation import SegmentGenerationInfo, Take
from app.parser.text_cleaner import clean_text_for_speech
from app.speech.context import build_context_windows, DialogueContextWindow
from app.speech.director import SpeechDirector
from app.speech.pauses import PauseCalculator
from app.speech.pronunciation import PronunciationEngine
from app.audio.cache import AudioCache, calculate_audio_hash
from app.audio.takes import TakeManager
from app.audio.ffmpeg_utils import FFmpegAudioEngine
from app.tts.registry import tts_registry
from app.tts.base import SynthesisRequest, SynthesisResult


@dataclass
class GenerationPlan:
    """Calculated overview of generation requirements before execution."""
    total_turns: int = 0
    cached_turns: int = 0
    locked_turns: int = 0
    need_synthesis_turns: int = 0
    estimated_seconds: float = 0.0


class AudioGenerationEngine:
    """Coordinates generation, caching, take creation, planning, and progress reporting."""

    def __init__(self, cache: Optional[AudioCache] = None, cache_dir: Optional[Path] = None):
        if cache:
            self.cache = cache
        elif cache_dir:
            self.cache = AudioCache(cache_dir=cache_dir)
        else:
            self.cache = AudioCache()

    @staticmethod
    def _cache_settings(profile):
        settings = dict(profile.settings)
        provider = tts_registry.get(profile.provider or "kokoro")
        if provider and hasattr(provider, "cache_identity"):
            settings["model_files"] = provider.cache_identity()
        return settings

    def plan_generation(self, project: Project) -> GenerationPlan:
        """Analyzes which turns are cached, locked, or require new synthesis."""
        nodes = [DialogueNode.from_dict(n) for n in project.script_nodes if n.get("type") == "dialogue"]
        context_windows = build_context_windows(nodes)
        plan = GenerationPlan(total_turns=len(nodes))

        for idx, node in enumerate(nodes):
            gen_info = project.segments_generation.get(node.id)
            if gen_info and gen_info.is_locked:
                plan.locked_turns += 1
                continue

            speaker_profile = project.speakers.get(node.speaker, SpeakerProfile(name=node.speaker))
            clean_text = clean_text_for_speech(node.text)
            spoken_text = PronunciationEngine.apply_substitutions(
                text=clean_text,
                project_dict=project.pronunciation_dictionary,
                speaker_dict=speaker_profile.pronunciation_overrides,
            )
            direction = SpeechDirector.compose_delivery_instruction(
                context=context_windows[idx],
                speaker_profile=speaker_profile,
                studio_mode=(project.settings.generation_mode == "studio"),
            )
            provider_id = speaker_profile.provider or "kokoro"
            voice_id = speaker_profile.voice_id or "af_heart"

            audio_hash = calculate_audio_hash(
                text=spoken_text,
                provider=provider_id,
                voice_id=voice_id,
                model=speaker_profile.settings.get("model"),
                speed=speaker_profile.delivery.pace,
                delivery_direction=direction,
                delivery_settings=speaker_profile.delivery.to_dict(),
                provider_settings=self._cache_settings(speaker_profile),
                studio_mode=(project.settings.generation_mode == "studio"),
            )

            if gen_info and gen_info.active_take and gen_info.active_take.generation_hash == audio_hash and Path(gen_info.active_take.audio_path).is_file():
                plan.cached_turns += 1
            elif self.cache.get(audio_hash):
                plan.cached_turns += 1
            else:
                plan.need_synthesis_turns += 1

        plan.estimated_seconds = round(plan.need_synthesis_turns * 1.5, 1)
        return plan

    def generate_single_turn(
        self,
        project: Project,
        project_dir: Path,
        segment_id: str,
        force_new_take: bool = False,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> bool:
        """Generates audio for an individual dialogue turn (retry or new take)."""
        nodes = [DialogueNode.from_dict(n) for n in project.script_nodes if n.get("type") == "dialogue"]
        context_windows = build_context_windows(nodes)

        target_node = None
        target_window = None
        for idx, node in enumerate(nodes):
            if node.id == segment_id:
                target_node = node
                target_window = context_windows[idx]
                break

        if not target_node or not target_window:
            return False

        speaker_name = target_node.speaker
        speaker_profile = project.speakers.get(speaker_name, SpeakerProfile(name=speaker_name))

        gen_info = project.segments_generation.get(segment_id)
        if not gen_info:
            gen_info = SegmentGenerationInfo(
                segment_id=segment_id,
                speaker=speaker_name,
                text=target_node.text,
            )
            project.segments_generation[segment_id] = gen_info

        if gen_info.is_locked and not force_new_take:
            return True

        if progress_callback:
            progress_callback(f"Synthesizing {speaker_name}...", 0.5)

        return self._synthesize_segment(
            project=project,
            project_dir=project_dir,
            node=target_node,
            context=target_window,
            speaker_profile=speaker_profile,
            gen_info=gen_info,
            force_new_take=force_new_take,
        )

    def generate_project(
        self,
        project: Project,
        project_dir: Path,
        progress_callback: Optional[Callable[[str, float], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
        pause_check: Optional[Callable[[], bool]] = None,
    ) -> bool:
        """Executes intelligent partial speech generation for all dialogue turns in a script."""
        nodes = [DialogueNode.from_dict(n) for n in project.script_nodes if n.get("type") == "dialogue"]
        if not nodes:
            return False

        context_windows = build_context_windows(nodes)
        total = len(nodes)

        for i, node in enumerate(nodes):
            # Check cancellation
            if cancel_check and cancel_check():
                return False

            # Check pause loop
            while pause_check and pause_check():
                if cancel_check and cancel_check():
                    return False
                time.sleep(0.2)

            seg_id = node.id
            speaker_name = node.speaker
            speaker_profile = project.speakers.get(speaker_name, SpeakerProfile(name=speaker_name))

            gen_info = project.segments_generation.get(seg_id)
            if not gen_info:
                gen_info = SegmentGenerationInfo(
                    segment_id=seg_id,
                    speaker=speaker_name,
                    text=node.text,
                )
                project.segments_generation[seg_id] = gen_info

            source_index = next(j for j, raw in enumerate(project.script_nodes) if raw.get("id") == node.id)
            next_node = project.script_nodes[source_index + 1] if source_index + 1 < len(project.script_nodes) else None
            pause_ms = PauseCalculator.calculate_pause_between(
                current_node=node,
                next_node=next_node,
                default_pause_ms=project.settings.default_pause_ms,
                quick_reaction_ms=project.settings.quick_reaction_pause_ms,
                topic_pause_ms=project.settings.topic_pause_ms,
            )
            gen_info.calculated_pause_after_ms = pause_ms

            direction = SpeechDirector.compose_delivery_instruction(
                context=context_windows[i],
                speaker_profile=speaker_profile,
                studio_mode=(project.settings.generation_mode == "studio"),
            )
            gen_info.inferred_direction = direction

            if progress_callback:
                pct = (i / total) * 0.85
                progress_callback(f"Turn {i+1}/{total} [{speaker_name}]: {node.text[:40]}...", pct)

            turn_success = self._synthesize_segment(
                project=project,
                project_dir=project_dir,
                node=node,
                context=context_windows[i],
                speaker_profile=speaker_profile,
                gen_info=gen_info,
                force_new_take=False,
            )
            if not turn_success:
                if progress_callback:
                    progress_callback(f"Failed [{speaker_name}]: {gen_info.error_message}", i / total)
                return False

        return True

    def _synthesize_segment(
        self,
        project: Project,
        project_dir: Path,
        node: DialogueNode,
        context: DialogueContextWindow,
        speaker_profile: SpeakerProfile,
        gen_info: SegmentGenerationInfo,
        force_new_take: bool = False,
    ) -> bool:
        """Internal worker to process cache, delivery, and speech engine synthesis."""
        clean_text = clean_text_for_speech(node.text)

        spoken_text = PronunciationEngine.apply_substitutions(
            text=clean_text,
            project_dict=project.pronunciation_dictionary,
            speaker_dict=speaker_profile.pronunciation_overrides,
        )

        studio_mode = (project.settings.generation_mode == "studio")
        delivery_direction = SpeechDirector.compose_delivery_instruction(
            context=context,
            speaker_profile=speaker_profile,
            studio_mode=studio_mode,
        )

        provider_id = speaker_profile.provider or "kokoro"
        provider = tts_registry.get(provider_id)
        voice_id = speaker_profile.voice_id or "af_heart"

        audio_hash = calculate_audio_hash(
            text=spoken_text,
            provider=provider_id,
            voice_id=voice_id,
            model=speaker_profile.settings.get("model"),
            speed=speaker_profile.delivery.pace,
            delivery_direction=delivery_direction,
            delivery_settings=speaker_profile.delivery.to_dict(),
            provider_settings=self._cache_settings(speaker_profile),
            studio_mode=studio_mode,
        )

        gen_info.generation_hash = audio_hash
        gen_info.inferred_direction = delivery_direction

        # Locked take check
        if gen_info.is_locked and not force_new_take and gen_info.active_take:
            gen_info.status = "locked"
            return True

        # Existing active take hash match
        if not force_new_take and gen_info.active_take:
            if (
                gen_info.active_take.generation_hash == audio_hash and
                Path(gen_info.active_take.audio_path).exists()
            ):
                gen_info.status = "complete"
                return True

        # Cache check
        cached_file = self.cache.get(audio_hash)
        segments_dir = project_dir / "audio" / "segments"
        takes_dir = project_dir / "audio" / "takes"
        segments_dir.mkdir(parents=True, exist_ok=True)
        takes_dir.mkdir(parents=True, exist_ok=True)

        take_num = len(gen_info.takes) + 1
        dest_filename = f"{node.id}_take_{take_num}{cached_file.suffix if cached_file else '.wav'}"
        dest_path = takes_dir / dest_filename

        if cached_file and not force_new_take:
            import shutil
            shutil.copy2(cached_file, dest_path)
            duration_ms = FFmpegAudioEngine.get_duration_ms(str(dest_path))
            TakeManager.add_take(
                info=gen_info,
                audio_path=str(dest_path),
                generation_hash=audio_hash,
                duration_ms=duration_ms,
                provider=provider_id,
                voice_id=voice_id,
                delivery_direction=delivery_direction,
                auto_activate=True,
            )
            gen_info.status = "cached"
            return True

        # Speech Engine Synthesis
        gen_info.status = "generating"
        try:
            if not provider or provider.category == "DISABLED":
                raise RuntimeError(f"Engine '{provider_id}' is unavailable. Choose a Kokoro or Edge neural voice.")
            if provider.category == "ONLINE_FREE_OPTIONAL" and not project.settings.allow_online:
                raise RuntimeError("Online speech is disabled. Enable script upload to Microsoft or select Kokoro.")
            req = SynthesisRequest(
                text=spoken_text,
                voice_id=voice_id,
                provider=provider_id,
                model=speaker_profile.settings.get("model"),
                speed=speaker_profile.delivery.pace,
                instructions=delivery_direction,
                settings={**speaker_profile.settings, "allow_online": project.settings.allow_online},
                studio_mode=studio_mode,
            )
            result: SynthesisResult = provider.synthesize(req)
            if not result.audio_bytes:
                raise RuntimeError("Speech engine returned empty audio.")

            ext = f".{result.audio_format.lstrip('.')}"
            dest_filename = f"{node.id}_take_{take_num}{ext}"
            dest_path = takes_dir / dest_filename
            dest_path.write_bytes(result.audio_bytes)

            # Probe actual bytes: estimated provider durations corrupt timeline markers.
            duration_ms = FFmpegAudioEngine.get_duration_ms(str(dest_path))
            if duration_ms <= 0:
                raise RuntimeError("Generated audio could not be decoded; no take was accepted.")
            self.cache.store(audio_hash, result.audio_bytes, result.audio_format)


            TakeManager.add_take(
                info=gen_info,
                audio_path=str(dest_path),
                generation_hash=audio_hash,
                duration_ms=duration_ms,
                provider=provider_id,
                voice_id=voice_id,
                delivery_direction=delivery_direction,
                auto_activate=True,
            )
            gen_info.status = "complete"
            gen_info.error_message = None
            return True

        except Exception as err:
            gen_info.status = "failed"
            gen_info.error_message = str(err)
            return False
