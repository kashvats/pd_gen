"""Timeline Assembler for creating the ordered audio manifest and final mastered mix."""

from pathlib import Path
from typing import Optional, List, Tuple
from app.models.project import Project
from app.models.ast import DialogueNode, PauseNode, SoundEffectNode
from app.models.generation import GenerationManifest, ManifestItem
from app.audio.ffmpeg_utils import FFmpegAudioEngine


class TimelineAssembler:
    """Assembles dialogue segments into a cohesive timeline manifest and final audio."""

    @classmethod
    def assemble(cls, project: Project, project_dir: Path) -> Optional[GenerationManifest]:
        """Builds ordered manifest and renders master audio file."""
        segments_dir = project_dir / "audio" / "segments"
        final_dir = project_dir / "audio"
        final_dir.mkdir(parents=True, exist_ok=True)
        segments_dir.mkdir(parents=True, exist_ok=True)

        fmt = project.settings.output_format.lower().lstrip(".")
        final_output_path = final_dir / f"final.{fmt}"

        manifest_items: List[ManifestItem] = []
        assembly_pairs: List[Tuple[str, int]] = []
        current_time_ms = 0

        for idx, node in enumerate(project.script_nodes):
            node_type = node.get("type", "dialogue")

            if node_type == "dialogue":
                seg_id = node.get("id")
                speaker = node.get("speaker", "Unknown")
                text = node.get("text", "")
                gen_info = project.segments_generation.get(seg_id)

                if not gen_info or not gen_info.active_take or gen_info.status == "failed":
                    raise RuntimeError(f"Missing or failed speech for {speaker}: {text[:60]}. Generate it before exporting.")

                take = gen_info.active_take
                file_path = take.audio_path
                duration_ms = take.duration_ms or FFmpegAudioEngine.get_duration_ms(file_path)
                take.duration_ms = duration_ms

                pause_after_ms = gen_info.calculated_pause_after_ms

                manifest_items.append(
                    ManifestItem(
                        order=idx,
                        item_type="audio",
                        segment_id=seg_id,
                        speaker=speaker,
                        file_path=file_path,
                        duration_ms=duration_ms,
                        text_preview=text[:60] + ("..." if len(text) > 60 else ""),
                        start_time_ms=current_time_ms,
                    )
                )
                current_time_ms += duration_ms

                if pause_after_ms > 0:
                    manifest_items.append(
                        ManifestItem(
                            order=idx,
                            item_type="pause",
                            duration_ms=pause_after_ms,
                            text_preview=f"Pause {pause_after_ms}ms",
                            start_time_ms=current_time_ms,
                        )
                    )
                    current_time_ms += pause_after_ms

                assembly_pairs.append((file_path, pause_after_ms))

            elif node_type == "pause":
                pause_duration = node.get("duration_ms", project.settings.default_pause_ms)
                manifest_items.append(
                    ManifestItem(
                        order=idx,
                        item_type="pause",
                        duration_ms=pause_duration,
                        text_preview=f"Explicit Pause {pause_duration}ms",
                        start_time_ms=current_time_ms,
                    )
                )
                current_time_ms += pause_duration
                # Add silence directly to previous or as independent pair
                if assembly_pairs:
                    last_file, last_pause = assembly_pairs[-1]
                    assembly_pairs[-1] = (last_file, last_pause + pause_duration)
                else:
                    silence = segments_dir / f"leading_pause_{idx}.wav"
                    FFmpegAudioEngine.generate_silence_wav(silence, pause_duration)
                    assembly_pairs.append((str(silence), 0))
            elif node_type == "sound_effect":
                raise RuntimeError("This version generates speech and pauses only. Remove [SFX] before exporting.")

        if not assembly_pairs:
            return None

        # Render final audio via FFmpeg
        success = FFmpegAudioEngine.assemble_timeline(
            audio_segments=assembly_pairs,
            output_path=final_output_path,
            crossfade_ms=project.settings.crossfade_ms,
            normalize=project.settings.normalize_loudness,
            target_lufs=project.settings.target_lufs,
            output_format=fmt,
        )

        if not success:
            return None

        manifest = GenerationManifest(
            project_id=project.id,
            items=manifest_items,
            total_duration_ms=current_time_ms,
            final_audio_path=str(final_output_path),
        )

        project.manifest = manifest
        project.final_audio_path = str(final_output_path)
        return manifest
