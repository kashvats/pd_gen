"""Comprehensive End-to-End integration test for the entire Studio workflow."""

import pytest
import tempfile
import wave
import struct
import math
from pathlib import Path

from app.models.project import Project, SpeakerProfile
from app.projects.manager import ProjectManager
from app.voices.library import VoiceLibrary
from app.voices.cloning import VoiceCloningService
from app.voices.quality import analyze_reference_audio
from app.audio.generator import AudioGenerationEngine, GenerationPlan
from app.audio.takes import TakeManager
from app.audio.assembler import TimelineAssembler
from app.system.resources import SystemResourceManager
from app.system.limits import set_system_profile


def _generate_wav(path: Path, duration_sec: float = 3.0, freq: float = 220.0) -> Path:
    sample_rate = 44100
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        frames = bytearray()
        for i in range(int(sample_rate * duration_sec)):
            t = i / sample_rate
            val = int(0.5 * 32767.0 * math.sin(2 * math.pi * freq * t))
            frames.extend(struct.pack("<h", val))
        wf.writeframes(frames)
    return path


def test_full_studio_lifecycle(mock_engine):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        set_system_profile("balanced")

        # 1. Initialize Voice Library & Reference Cloning
        v_lib = VoiceLibrary(root_dir=tmp_path / "voices")
        cloning_svc = VoiceCloningService(v_lib)

        ref_wav = _generate_wav(tmp_path / "host_ref.wav", duration_sec=5.0, freq=140.0)
        report = analyze_reference_audio(str(ref_wav))
        assert report.score >= 70
        assert not report.is_clipping

        success, cloned_profile, err = cloning_svc.clone_voice(
            name="Custom Cloned Host",
            provider_id="mock",
            reference_file_paths=[str(ref_wav)],
            consent_confirmed=True,
            consent_notes="Owner verified.",
        )
        assert success is True
        assert cloned_profile is not None
        assert Path(cloned_profile.reference_files[0]).exists()

        # 2. Create Project from Markdown Script
        mgr = ProjectManager(root_dir=tmp_path / "projects", voice_library=v_lib)
        script = """# Studio Episode 1

Host: Welcome to the natural voice studio.
Co-Host: It is great to be here!

[PAUSE: 500ms]

Host [curious]: Did you know this entire pipeline runs locally at zero cost?
Guest: Yes, and it respects the target hardware completely.
"""
        project = mgr.create_project("Episode 1", script)
        assert len(project.speakers) == 3
        assert "Host" in project.speakers
        assert "Co-Host" in project.speakers
        assert "Guest" in project.speakers

        # Assign our cloned voice to Host
        for profile in project.speakers.values():
            profile.provider = "mock"
        project.speakers["Host"].provider = "mock"
        project.speakers["Host"].voice_id = cloned_profile.voice_id

        # 3. Generation Planning
        p_dir = mgr.get_project_dir(project.id)
        engine = AudioGenerationEngine(cache_dir=tmp_path / "cache")
        plan: GenerationPlan = engine.plan_generation(project)
        assert plan.total_turns == 4
        assert plan.need_synthesis_turns == 4
        assert plan.cached_turns == 0

        # 4. Generate All Turns
        gen_success = engine.generate_project(project, p_dir)
        assert gen_success is True

        # Verify all dialogue turns have takes
        for node in project.script_nodes:
            if node.get("type") == "dialogue":
                gen_info = project.segments_generation.get(node["id"])
                assert gen_info is not None
                assert gen_info.status in ["complete", "cached"]
                assert gen_info.active_take is not None
                assert Path(gen_info.active_take.audio_path).exists()

        # 5. Alternate Takes & Locking
        first_dialogue_id = [n["id"] for n in project.script_nodes if n.get("type") == "dialogue"][0]
        first_info = project.segments_generation[first_dialogue_id]
        assert len(first_info.takes) == 1

        # Generate Take 2 for the first turn
        take2_success = engine.generate_single_turn(
            project, p_dir, first_dialogue_id, force_new_take=True
        )
        assert take2_success is True
        assert len(first_info.takes) == 2
        assert first_info.active_take_index == 1

        # Lock Take 2
        is_locked = TakeManager.toggle_lock_active_take(first_info)
        assert is_locked is True
        assert first_info.is_locked is True

        # 6. Re-plan & Partial Regeneration Check
        new_plan = engine.plan_generation(project)
        # All turns should now be either cached or locked
        assert new_plan.need_synthesis_turns == 0
        assert new_plan.locked_turns == 1
        assert new_plan.cached_turns == 3

        # 7. Timeline Manifest Assembly & Master File
        manifest = TimelineAssembler.assemble(project, p_dir)
        assert manifest is not None
        assert manifest.total_duration_ms > 2000
        assert project.final_audio_path is not None
        assert Path(project.final_audio_path).exists()

        # 8. Safe Cache Pruning Verification
        removed = SystemResourceManager.prune_cache_safely(max_budget_gb=0.0001, cache_dir=tmp_path / "cache")
        # Ensure user projects, scripts, and references are untouched
        assert Path(project.final_audio_path).exists()
        assert Path(cloned_profile.reference_files[0]).exists()
        assert (p_dir / "script.md").exists()
